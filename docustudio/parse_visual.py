"""Parser for the Visual Help File (SPEC 03, collector-compatible format)."""
import re
from .model import VisualBlock, ClipLink

MD_LINK_RE = re.compile(r"\[(https?://[^\]\s]+)\]\((https?://[^)\s]+)\)")
URL_RE = re.compile(r"https?://[^\s|,)\]]+")
UNTIL_RE = re.compile(r"\(\s*until\s+(\d+):(\d{2})(?::(\d{2}))?\s*\)", re.I)
T_PARAM_RE = re.compile(r"[?&]t=(\d+)")
SCENE_PIN_RE = re.compile(r"^\s*scene\s*[:\-]\s*(\d+)\s*$", re.I)

FIELD_ALIASES = [
    ("cue", ("script cue",)),
    ("visual", ("visual / exact clip", "visual/exact clip", "visual:", "exact clip")),
    ("spoken", ("spoken line",)),
    ("clips", ("clip links", "clip link")),
    ("images", ("image links", "image link")),
    ("searches", ("image search", "fallback")),
    ("note", ("note",)),
]


def _field_of(line: str):
    low = line.strip().lower()
    for key, aliases in FIELD_ALIASES:
        for a in aliases:
            if low.startswith(a):
                _, _, rest = line.strip().partition(":")
                return key, rest.strip()
    return None, None


def _is_block_title(line: str) -> bool:
    s = line.strip()
    if not s or ":" in s[:14] and _field_of(s)[0]:
        return False
    letters = [c for c in s if c.isalpha()]
    if len(s) > 90 or len(letters) < 3:
        return False
    upper_ratio = sum(c.isupper() for c in letters) / len(letters)
    return upper_ratio > 0.85


def _video_id(url: str) -> str:
    m = re.search(r"youtu\.be/([\w-]{6,})", url)
    if m:
        return m.group(1)
    m = re.search(r"[?&]v=([\w-]{6,})", url)
    if m:
        return m.group(1)
    return url.split("?")[0]


def _parse_clip_field(text: str):
    clips, was_md = [], False
    if MD_LINK_RE.search(text):
        was_md = True
        text = MD_LINK_RE.sub(lambda m: m.group(1), text)
    until = None
    mu = UNTIL_RE.search(text)
    if mu:
        h_or_m, mm, ss = mu.groups()
        until = (int(h_or_m) * 3600 + int(mm) * 60 + int(ss)) if ss \
            else (int(h_or_m) * 60 + int(mm))
    for url in URL_RE.findall(text):
        mt = T_PARAM_RE.search(url)
        start = float(mt.group(1)) if mt else None
        clips.append(ClipLink(url=url, video_id=_video_id(url), start=start,
                              end=float(until) if until is not None else None,
                              was_markdown=was_md))
    return clips


def parse_visual_file(text: str):
    """Returns (topic_anchor, blocks, problems)."""
    topic, blocks, problems = "", [], []
    cur, cur_field = None, None
    for lineno, rawline in enumerate(text.splitlines(), 1):
        line = rawline.rstrip()
        s = line.strip()
        if not s or s in ("[", "]"):
            continue
        low = s.lower()
        if low.startswith("topic") and ":" in s:
            topic = s.partition(":")[2].strip()
            continue
        m = SCENE_PIN_RE.match(s)
        if m and cur:
            cur.scene_pin = int(m.group(1))
            continue
        key, rest = _field_of(s)
        if key:
            if cur is None:
                problems.append(f"line {lineno}: field before any block title")
                continue
            cur_field = key
            _apply(cur, key, rest, problems)
            continue
        if _is_block_title(s):
            cur = VisualBlock(title=s)
            blocks.append(cur)
            cur_field = None
            continue
        # continuation of the previous field
        if cur and cur_field:
            _apply(cur, cur_field, s, problems)
        elif cur:
            cur.visual += " " + s  # stray prose inside block
        else:
            problems.append(f"line {lineno}: unattached text: {s[:60]!r}")
    return topic, blocks, problems


def _apply(block: VisualBlock, key: str, value: str, problems: list):
    if not value:
        return
    if key == "cue":
        block.cue = (block.cue + " " + value).strip()
    elif key == "visual":
        block.visual = (block.visual + " " + value).strip()
    elif key == "spoken":
        block.spoken_line = (block.spoken_line + " " + value).strip()
    elif key == "clips":
        block.clips.extend(_parse_clip_field(value))
    elif key == "images":
        text = MD_LINK_RE.sub(lambda m: m.group(1), value)
        urls = URL_RE.findall(text)
        block.images.extend(urls)
        for part in re.split(r"[|,]", text):
            p = part.strip()
            if p.lower().startswith("local:"):
                block.images.append(p)
    elif key == "searches":
        block.searches.extend(q.strip() for q in value.split("|") if q.strip())
    elif key == "note":
        block.note = (block.note + " " + value).strip()
