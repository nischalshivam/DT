"""Parser for the Editing Help Script (SPEC 02)."""
import re
from .model import Scene, Line, Tag, KNOWN_TAGS, BARE_TAGS

SCENE_RE = re.compile(r"^\s*=+\s*scene\s+(\d+)\s*=+\s*$", re.I)
MOOD_RE = re.compile(r"^\s*mood\s*[:\-]\s*(.+)$", re.I)
PACING_RE = re.compile(r"^\s*pacing\s*[:\-]\s*(.+)$", re.I)
TAG_RE = re.compile(r"\[([^\[\]]{1,220})\]")
TAPE_RE = re.compile(r"^\s*>\s*>?")


def _canon_label(label: str) -> str:
    return re.sub(r"[^A-Z]", "", label.upper())


def parse_tag(raw: str) -> Tag:
    if ":" in raw:
        label, value = raw.split(":", 1)
        kind = _canon_label(label)
        if kind in KNOWN_TAGS:
            return Tag(kind=kind, value=value.strip(), raw=raw)
        return Tag(kind="UNKNOWN", value=value.strip(), raw=raw)
    kind = _canon_label(raw)
    if kind in BARE_TAGS or kind in KNOWN_TAGS:
        return Tag(kind=kind, value="", raw=raw)
    return Tag(kind="UNKNOWN", value="", raw=raw)


def parse_help_script(text: str):
    """Returns (scenes, problems) — problems is a list of strings."""
    scenes, problems = [], []
    cur = None
    for lineno, rawline in enumerate(text.splitlines(), 1):
        line = rawline.rstrip()
        if not line.strip():
            continue
        m = SCENE_RE.match(line)
        if m:
            cur = Scene(num=int(m.group(1)))
            scenes.append(cur)
            continue
        if cur is None:
            # tolerate stray leading brackets like "[" from copy-paste
            if line.strip() in ("[", "]"):
                continue
            problems.append(f"line {lineno}: content before first scene header: {line[:60]!r}")
            continue
        m = MOOD_RE.match(line)
        if m and not cur.lines:
            cur.mood = m.group(1).strip().lower()
            continue
        m = PACING_RE.match(line)
        if m and not cur.lines:
            cur.pacing = m.group(1).strip().lower()
            continue
        # narration line (possibly with inline tags)
        tags = [parse_tag(t) for t in TAG_RE.findall(line)]
        stripped = TAG_RE.sub(" ", line)
        is_tape = bool(TAPE_RE.match(stripped))
        stripped = TAPE_RE.sub(" ", stripped)
        stripped = re.sub(r"\s+", " ", stripped).strip()
        stripped = stripped.strip("[]").strip()
        ln = Line(text=stripped, tags=tags, is_tape=is_tape)
        cur.lines.append(ln)
    # per-scene bookkeeping
    for sc in scenes:
        sc.word_count = sum(len(l.text.split()) for l in sc.lines)
        sc.est_duration = round(sc.word_count / 2.55, 1)
    return scenes, problems
