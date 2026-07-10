"""VO alignment — real word-level timings from the voiceover.

Two levels, best available wins:
1. faster-whisper (word timestamps) -> script words matched to
   transcript words -> exact line/scene times. Language auto-detected.
2. Fallback: duration scaling — stretch the word-count estimate so the
   total exactly matches the VO length (keeps everything usable even
   without whisper installed).
Either way the planner downstream sees the same fields.
"""
import difflib
import re
import subprocess

from .textnorm import normalize_words


def vo_duration(path: str) -> float:
    from .renderer import FF
    r = subprocess.run([FF, "-i", path], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", r.stderr)
    if not m:
        raise RuntimeError(f"cannot read duration of {path}")
    h, mnt, s = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(s)


def _scale(project, total: float):
    est = project.scenes[-1].t1 if project.scenes else 0
    if not est:
        return "no-scenes"
    k = total / est
    for sc in project.scenes:
        sc.t0, sc.t1 = round(sc.t0 * k, 2), round(sc.t1 * k, 2)
        sc.duration = round(sc.t1 - sc.t0, 2)
        for ln in sc.lines:
            ln.t0, ln.dur = round(ln.t0 * k, 2), round(ln.dur * k, 2)
    return f"duration-scaled x{k:.3f}"


def _whisper_words(vo_path: str, language=None):
    from faster_whisper import WhisperModel  # optional dependency
    model = WhisperModel("base", compute_type="int8")
    segments, info = model.transcribe(vo_path, word_timestamps=True,
                                      language=language)
    words = []
    for seg in segments:
        for w in (seg.words or []):
            words.append((normalize_words(w.word), w.start, w.end))
    return [w for w in words if w[0]], getattr(info, "language", None)


def align_project(project, vo_path: str, language=None):
    """Mutates scene/line timings in place; returns a status string."""
    total = vo_duration(vo_path)
    try:
        words, detected = _whisper_words(vo_path, language)
    except Exception as exc:  # whisper missing / model unavailable
        status = _scale(project, total)
        return f"{status} (whisper unavailable: {type(exc).__name__})"
    if not words:
        return _scale(project, total)

    # sequence-match script words to transcript words
    script_tokens, owners = [], []   # owners[i] = (scene, line)
    for sc in project.scenes:
        for ln in sc.lines:
            for w in normalize_words(ln.text).split():
                script_tokens.append(w)
                owners.append((sc, ln))
    trans_tokens = [w for w, _, _ in words]
    sm = difflib.SequenceMatcher(None, script_tokens, trans_tokens,
                                 autojunk=False)
    # word index -> (start, end) for matched words
    times = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            times[a + k] = (words[b + k][1], words[b + k][2])
    if len(times) < len(script_tokens) * 0.5:
        status = _scale(project, total)
        return f"{status} (weak whisper match {len(times)}/{len(script_tokens)})"

    # per line: first/last matched word; interpolate gaps
    idx = 0
    prev_end = 0.0
    for sc in project.scenes:
        for ln in sc.lines:
            n = len(normalize_words(ln.text).split())
            span = [times[j] for j in range(idx, idx + n) if j in times]
            if span:
                ln.t0 = round(span[0][0], 2)
                ln.dur = round(max(0.4, span[-1][1] - span[0][0]), 2)
                prev_end = span[-1][1]
            else:
                ln.t0 = round(prev_end, 2)
                ln.dur = round(max(0.4, n / 2.55), 2)
                prev_end += ln.dur
            idx += n
        lts = [(l.t0, l.t0 + l.dur) for l in sc.lines]
        sc.t0 = round(min(t for t, _ in lts), 2)
        sc.t1 = round(max(t for _, t in lts), 2)
        sc.duration = round(sc.t1 - sc.t0, 2)
    # enforce monotonic, gap-free scene boundaries
    for a, b in zip(project.scenes, project.scenes[1:]):
        if b.t0 < a.t1:
            b.t0 = a.t1
        a.t1 = b.t0
        a.duration = round(a.t1 - a.t0, 2)
    project.scenes[-1].t1 = max(project.scenes[-1].t1, round(total, 2))
    project.scenes[-1].duration = round(
        project.scenes[-1].t1 - project.scenes[-1].t0, 2)
    lang = f", language={detected}" if detected else ""
    return (f"whisper word-aligned {len(times)}/{len(script_tokens)} "
            f"words{lang}")
