"""Scene/line timings.

Until the real VO is whisper-aligned, timings are estimated from word
counts (~2.55 words/sec). The planner consumes the same fields either
way, so plugging in whisper later changes nothing downstream.
Breath points = line boundaries (later: real inter-sentence silences).
"""

WPS = 2.55


def assign_estimated(project, wps: float = WPS):
    t = 0.0
    for sc in project.scenes:
        sc.t0 = round(t, 2)
        for ln in sc.lines:
            ln.t0 = round(t, 2)
            ln.dur = round(max(0.5, len(ln.text.split()) / wps), 2)
            t += ln.dur
        sc.t1 = round(t, 2)
        sc.duration = round(sc.t1 - sc.t0, 2)
    return project


def breath_points(scene):
    """Candidate cut times inside a scene = line boundaries."""
    pts = []
    for ln in scene.lines:
        pts.append(round(ln.t0 + ln.dur, 2))
    return pts[:-1]  # last boundary is the scene end itself


def snap(t: float, points, tol: float = 0.7) -> float:
    """Snap t to the nearest breath point within tolerance."""
    best, bd = t, tol + 1
    for p in points:
        d = abs(p - t)
        if d < bd and d <= tol:
            best, bd = p, d
    return best
