"""Matching: help-script lines -> clean script; visual cues -> scenes."""
import difflib
from .textnorm import normalize_words, first_words, last_words

FUZZY_OK = 0.82


def _fuzzy_find(hay: str, needle: str, hint: int = 0) -> tuple[int, float]:
    """Best-effort sliding fuzzy search; returns (offset, ratio)."""
    if not needle:
        return -1, 0.0
    L = len(needle)
    step = max(20, L // 2)
    best_off, best_ratio = -1, 0.0
    # search around the hint first, then everywhere
    zones = [(max(0, hint - 4000), min(len(hay), hint + 8000)), (0, len(hay))]
    for lo, hi in zones:
        i = lo
        while i < hi:
            window = hay[i:i + L + step]
            r = difflib.SequenceMatcher(None, needle, window).ratio()
            if r > best_ratio:
                best_ratio, best_off = r, i
            i += step
        if best_ratio >= FUZZY_OK:
            break
    return best_off, best_ratio


def match_scenes(project):
    """Anchor every scene line inside the normalized clean script."""
    hay = project.clean_norm
    cursor = 0
    unmatched = []
    for sc in project.scenes:
        offs = []
        for ln in sc.lines:
            needle = normalize_words(ln.text)
            if len(needle.split()) < 3:
                continue  # too short to anchor reliably
            pos = hay.find(needle, cursor)
            if pos < 0:
                pos = hay.find(needle)
            if pos >= 0:
                ln.offset, ln.matched = pos, True
                offs.append((pos, len(needle)))
                cursor = max(cursor, pos)
            else:
                pos, ratio = _fuzzy_find(hay, needle, cursor)
                if ratio >= FUZZY_OK:
                    ln.offset, ln.matched, ln.fuzzy = pos, True, True
                    offs.append((pos, len(needle)))
                else:
                    unmatched.append((sc.num, ln.text[:70], round(ratio, 2)))
        if offs:
            sc.start_off = min(p for p, _ in offs)
            sc.end_off = max(p + l for p, l in offs)
    return unmatched


def match_blocks(project):
    """Map every visual block to its start/end scene via the Script Cue."""
    hay = project.clean_norm
    scenes = [s for s in project.scenes if s.start_off >= 0]
    unmatched = []
    cursor = 0
    for b in project.blocks:
        if b.scene_pin is not None:
            b.start_scene = b.end_scene = b.scene_pin
            b.cue_matched = True
            continue
        head = first_words(b.cue, 8)
        tail = last_words(b.cue, 8)
        pos = hay.find(head, cursor)
        if pos < 0:
            pos = hay.find(head)
        if pos < 0:
            pos, ratio = _fuzzy_find(hay, head, cursor)
            if ratio < FUZZY_OK:
                unmatched.append((b.title, round(ratio, 2)))
                continue
        b.cue_off, b.cue_matched = pos, True
        cursor = max(cursor, pos)
        endpos = hay.find(tail, pos)
        if endpos < 0:
            endpos, ratio = _fuzzy_find(hay, tail, pos)
            if ratio < FUZZY_OK:
                endpos = pos
        b.cue_end_off = endpos + len(tail)
        b.start_scene = _scene_at(scenes, pos)
        b.end_scene = _scene_at(scenes, b.cue_end_off)
    return unmatched


def _scene_at(scenes, off: int):
    """Scene containing offset; else the last scene starting before it."""
    best = None
    for s in scenes:
        if s.start_off <= off <= s.end_off:
            return s.num
        if s.start_off <= off:
            best = s.num
    return best if best is not None else (scenes[0].num if scenes else None)


def coverage(project):
    """Direct-cover set + serve-forward map {scene: block or None}."""
    direct = set()
    for b in project.blocks:
        if b.start_scene is None:
            continue
        end = b.end_scene if b.end_scene is not None else b.start_scene
        for n in range(b.start_scene, end + 1):
            direct.add(n)
    # serve-forward: a block serves until the next block's start scene
    starts = sorted({b.start_scene for b in project.blocks
                     if b.start_scene is not None})
    serving = {}
    for sc in project.scenes:
        prior = [s for s in starts if s <= sc.num]
        serving[sc.num] = max(prior) if prior else None
    return direct, serving
