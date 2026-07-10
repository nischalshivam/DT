"""Validation report: parse all inputs, run every SPEC check, print report."""
import difflib
from collections import Counter, defaultdict
from .model import Project, MOODS, PACINGS
from .textnorm import normalize_words
from .parse_help import parse_help_script
from .parse_visual import parse_visual_file
from .match import match_scenes, match_blocks, coverage


def load_project(clean_path, help_path, visual_path) -> tuple[Project, list, list]:
    p = Project()
    p.clean_text = open(clean_path, encoding="utf-8").read()
    p.clean_norm = normalize_words(p.clean_text)
    scenes, hp = parse_help_script(open(help_path, encoding="utf-8").read())
    topic, blocks, vp = parse_visual_file(open(visual_path, encoding="utf-8").read())
    p.scenes, p.blocks, p.topic_anchor = scenes, blocks, topic
    return p, hp, vp


def validate(clean_path, help_path, visual_path, out=print):
    p, help_problems, vis_problems = load_project(clean_path, help_path, visual_path)
    errors, warnings = [], []
    errors += [f"help-script: {x}" for x in help_problems]
    errors += [f"visual-file: {x}" for x in vis_problems]

    # ---- structural checks -------------------------------------------------
    nums = [s.num for s in p.scenes]
    for a, b in zip(nums, nums[1:]):
        if b != a + 1:
            errors.append(f"scene numbering jumps {a} -> {b}")
    for s in p.scenes:
        if s.mood and s.mood not in MOODS:
            errors.append(f"scene {s.num}: unknown MOOD '{s.mood}'")
        if s.pacing and s.pacing not in PACINGS:
            errors.append(f"scene {s.num}: unknown PACING '{s.pacing}'")
        if not s.mood:
            warnings.append(f"scene {s.num}: MOOD missing")
        if not s.pacing:
            warnings.append(f"scene {s.num}: PACING missing")

    # ---- matching ----------------------------------------------------------
    unmatched_lines = match_scenes(p)
    for num, text, ratio in unmatched_lines:
        errors.append(f"scene {num}: narration drift, line not in clean script "
                      f"(best {ratio}): {text!r}")
    unmatched_cues = match_blocks(p)
    for title, ratio in unmatched_cues:
        errors.append(f"block {title!r}: Script Cue not found in clean script "
                      f"(best {ratio})")

    # ---- tag hygiene -------------------------------------------------------
    tag_counts = Counter()
    artifact_tags, per_scene_source, per_scene_text = [], Counter(), Counter()
    quote_text_dups, tape_scenes = [], []
    for s in p.scenes:
        quotes, texts = [], []
        has_tape = any(l.is_tape for l in s.lines)
        has_archive = False
        for t in s.all_tags():
            tag_counts[t.kind] += 1
            if t.kind == "UNKNOWN":
                artifact_tags.append((s.num, t.raw))
            elif t.kind == "SOURCE":
                per_scene_source[s.num] += 1
            elif t.kind == "TEXT":
                per_scene_text[s.num] += 1
                texts.append(normalize_words(t.value))
            elif t.kind == "QUOTE":
                quotes.append(normalize_words(t.value))
            elif t.kind == "ARCHIVEAUDIO":
                has_archive = True
        for tx in texts:
            for q in quotes:
                if tx and (tx in q or
                           difflib.SequenceMatcher(None, tx, q).ratio() > 0.7):
                    quote_text_dups.append(s.num)
        if has_tape and not has_archive:
            tape_scenes.append(s.num)
    for num, raw in artifact_tags:
        warnings.append(f"scene {num}: unknown/artifact tag [{raw}] — remove "
                        f"from clean script or fix spelling")
    over_source = [n for n, c in per_scene_source.items() if c > 2]
    if over_source:
        warnings.append(f"[SOURCE] overuse (> 2/scene) in {len(over_source)} "
                        f"scenes: {over_source[:12]}{'…' if len(over_source) > 12 else ''} "
                        f"(total SOURCE tags: {tag_counts['SOURCE']})")
    text_scenes = len(per_scene_text)
    if text_scenes > max(1, len(p.scenes) // 3):
        warnings.append(f"[TEXT] density high: {text_scenes} of {len(p.scenes)} "
                        f"scenes (target ~1 in 3-4) — iceberg entry titles "
                        f"should use [ENTRY] instead")
    for n in sorted(set(quote_text_dups)):
        warnings.append(f"scene {n}: same words tagged as both [QUOTE] and "
                        f"[TEXT] — QUOTE wins, drop the TEXT")
    for n in tape_scenes:
        warnings.append(f"scene {n}: '>>' tape dialogue without "
                        f"[ARCHIVE AUDIO] tag — planner will treat as narration")

    # ---- NAME canonical-spelling suspects ---------------------------------
    names = sorted({t.value.split("—")[0].split("-")[0].strip()
                    for s in p.scenes for t in s.all_tags()
                    if t.kind == "NAME" and t.value})
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            na, nb = normalize_words(a), normalize_words(b)
            if na and nb and na != nb:
                r = difflib.SequenceMatcher(None, na, nb).ratio()
                if r > 0.78:
                    warnings.append(f"[NAME] possible same person, two "
                                    f"spellings: {a!r} vs {b!r} ({r:.2f})")

    # ---- clip link checks --------------------------------------------------
    md_links = sum(1 for b in p.blocks for c in b.clips if c.was_markdown)
    if md_links:
        warnings.append(f"{md_links} clip links were markdown-wrapped "
                        f"[url](url) — parsed OK, but prompt says raw URLs")
    by_video = defaultdict(list)
    for b in p.blocks:
        for c in b.clips:
            by_video[c.video_id].append((b.title, c))
    for vid, uses in by_video.items():
        ranged = [(t, c) for t, c in uses if c.start is not None and c.end]
        for i in range(len(ranged)):
            for j in range(i + 1, len(ranged)):
                (t1, c1), (t2, c2) = ranged[i], ranged[j]
                if c1.start < c2.end and c2.start < c1.end:
                    warnings.append(
                        f"overlapping time-ranges of video {vid}: "
                        f"{t1!r} ({c1.start:.0f}-{c1.end:.0f}s) vs {t2!r} "
                        f"({c2.start:.0f}-{c2.end:.0f}s) — QC will keep only the first")
        if len(uses) > 1 and not ranged:
            warnings.append(f"video {vid} used in {len(uses)} blocks without "
                            f"time-ranges — add (until …) to avoid duplicate footage")

    # ---- coverage ----------------------------------------------------------
    direct, serving = coverage(p)
    uncovered = [s.num for s in p.scenes if serving.get(s.num) is None]
    thin_holds = [s.num for s in p.scenes
                  if s.pacing == "hold" and s.num not in direct]
    for n in uncovered:
        warnings.append(f"scene {n}: no visual block serves it at all")
    if thin_holds:
        warnings.append(f"HOLD scenes with no direct visual block (repetition "
                        f"risk at the heaviest moments): {thin_holds}")

    # ---- report ------------------------------------------------------------
    total_words = sum(s.word_count for s in p.scenes)
    est_min = total_words / 2.55 / 60
    out("=" * 64)
    out("DocuStudio validation report")
    out("=" * 64)
    out(f"scenes: {len(p.scenes)} | narration words: {total_words} "
        f"(~{est_min:.0f} min at 153 wpm)")
    out(f"visual blocks: {len(p.blocks)} | clip links: "
        f"{sum(len(b.clips) for b in p.blocks)} | image searches: "
        f"{sum(len(b.searches) for b in p.blocks)}")
    out(f"tags: " + ", ".join(f"{k}:{v}" for k, v in tag_counts.most_common()))
    fuzzy = sum(1 for s in p.scenes for l in s.lines if l.fuzzy)
    matched = sum(1 for s in p.scenes for l in s.lines if l.matched)
    out(f"line anchoring: {matched} matched ({fuzzy} fuzzy), "
        f"{len(unmatched_lines)} failed")
    out(f"block mapping: {sum(1 for b in p.blocks if b.cue_matched)}/"
        f"{len(p.blocks)} cues matched | direct scene coverage: "
        f"{len(direct)}/{len(p.scenes)} | serve-forward coverage: "
        f"{len(p.scenes) - len(uncovered)}/{len(p.scenes)}")
    out("-" * 64)
    out(f"ERRORS ({len(errors)}):")
    for e in errors:
        out("  ✗ " + e)
    out(f"WARNINGS ({len(warnings)}):")
    for w in warnings:
        out("  ⚠ " + w)
    out("-" * 64)
    out("scene->block map (first 12): " + ", ".join(
        f"S{b.start_scene}{'-' + str(b.end_scene) if b.end_scene and b.end_scene != b.start_scene else ''}"
        f"={b.title[:22]!r}" for b in p.blocks[:12] if b.start_scene))
    return p, errors, warnings
