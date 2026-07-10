"""Planner v1 — turns a matched+timed project into a concrete edit plan.

Implements SPEC 08 (placement, copyright caps) + SPEC 09 (dynamic
durations, breath-snapped cuts, motion/texture/transition variation,
style draw, editorial reasons, slideshow risk).
"""
import json
import math
import random
from collections import Counter

from .timing import breath_points, snap

DOC_WORDS = ("document", "letter", "journal", "report", "record", "newspaper",
             "file", "page", "note", "transcript", "poster", "headline")
MAP_WORDS = ("map", "aerial", "location", "route")
FACE_WORDS = ("portrait", "photo of", "close-up", "face", "interview",
              "yearbook")

EVENT_DUR = {"DATE": (3.4, 4.6), "SOURCE": (3.6, 5.0), "TEXT": (2.6, 4.0),
             "STAT": (4.0, 5.5), "MAP": (3.5, 5.0), "NAME": (3.5, 4.5),
             "QUOTE": (3.5, 5.5), "ENTRY": (2.8, 3.8), "CHAPTER": (3.8, 5.0),
             "EVIDENCE": (3.0, 4.0), "TIMELINE": (3.5, 4.5),
             "COMPARE": (4.0, 5.5)}


def load_pack(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ pools ---
def build_pools(project) -> dict:
    """scene num -> list of asset stubs from blocks covering/serving it."""
    direct = {s.num: [] for s in project.scenes}
    for b in project.blocks:
        if b.start_scene is None:
            continue
        end = b.end_scene or b.start_scene
        for n in range(b.start_scene, end + 1):
            if n in direct:
                direct[n].append(b)
    # serve-forward for scenes with no direct block
    starts = sorted([(b.start_scene, b) for b in project.blocks
                     if b.start_scene is not None], key=lambda x: x[0])
    pools = {}
    for sc in project.scenes:
        blocks = direct[sc.num]
        borrowed = False
        if not blocks:
            prior = [b for s, b in starts if s <= sc.num]
            blocks = [prior[-1]] if prior else []
            borrowed = True
        items = []
        for b in blocks:
            for c in b.clips:
                # a long downloaded range yields several separate <=4.5s windows
                budget = 2
                if c.start is not None and c.end:
                    budget = max(1, min(3, int((c.end - c.start) / 6)))
                items.append({"kind": "clip", "desc": b.visual[:90],
                              "block": b.title, "video_id": c.video_id,
                              "start": c.start, "end": c.end, "budget": budget})
            for u in b.images:
                # SPEC 08: one hi-res image = 2-3 framings (wide/face/detail)
                items.append({"kind": "image", "desc": b.visual[:90],
                              "block": b.title, "url": u, "budget": 2})
            for q in b.searches:
                items.append({"kind": "image", "desc": "search: " + q,
                              "block": b.title, "url": None, "budget": 2})
        pools[sc.num] = {"items": items, "borrowed": borrowed,
                         "blocks": [b.title for b in blocks]}
    return pools


# ---------------------------------------------------------------- helpers ---
def _motion_for(item, pack, rng, last_motion):
    desc = (item.get("desc") or "").lower()
    if any(w in desc for w in MAP_WORDS) and "map_zoom" in pack["motions"]:
        cand = ["map_zoom"]
    elif any(w in desc for w in DOC_WORDS) and "doc_scan" in pack["motions"]:
        cand = ["doc_scan", "push_in_slow"]
    elif any(w in desc for w in FACE_WORDS):
        cand = ["face_push", "push_in_slow", "static"]
    elif item["kind"] == "clip":
        cand = ["static", "micro_drift"]      # clips already move
    elif rng.random() < pack["static_hold_prob"]:
        cand = ["static"]
    else:
        cand = [m for m in pack["motions"] if m not in ("doc_scan", "map_zoom")]
    cand = [m for m in cand if m != last_motion] or cand
    return rng.choice(cand)


class _VariantCycle:
    """Per-video shuffled cycles so card variants rotate, never repeat."""

    def __init__(self, variants: dict, rng):
        self._cycles = {}
        self._rng = rng
        for k, opts in variants.items():
            opts = list(opts)
            rng.shuffle(opts)
            self._cycles[k.upper()] = opts
        self._idx = {k: 0 for k in self._cycles}

    def pick(self, kind: str) -> str:
        key = kind.upper()
        if key not in self._cycles:
            return "default"
        opts = self._cycles[key]
        v = opts[self._idx[key] % len(opts)]
        self._idx[key] += 1
        return v


def _transition_sampler(pack, rng):
    budget = pack["transitions"]
    history = []

    def pick():
        r = rng.random()
        if r < budget["cut"]:
            t = "cut"
        elif r < budget["cut"] + budget["dissolve"]:
            t = "dissolve"
        elif r < budget["cut"] + budget["dissolve"] + budget["genre"]:
            t = rng.choice(budget["genre_list"])
        else:
            t = rng.choice(budget["special_list"])
        if len(history) >= 2 and history[-1] == history[-2] == t and t != "cut":
            t = "cut"
        history.append(t)
        return t
    return pick


# ------------------------------------------------------------------- plan ---
def plan(project, pack: dict, seed: int = 0) -> dict:
    rng = random.Random(seed or rng_seed_from(project))
    pools = build_pools(project)
    variants = _VariantCycle(pack.get("variants", {}), rng)
    next_transition = _transition_sampler(pack, rng)

    scene_plans = []
    last_motion, last_video = None, None
    texture_run = []          # last texture kinds, for rotation rule
    all_shot_durs, motion_hist, texture_hist, transition_hist = [], Counter(), Counter(), Counter()

    for sc in project.scenes:
        D = sc.duration
        pacing = sc.pacing or "normal"
        pool = [it for it in pools[sc.num]["items"]
                if it.get("budget", 1) > 0]
        warnings, reasons = [], []
        if pools[sc.num]["borrowed"]:
            warnings.append("no direct visual block — borrowing from previous")

        # --- slot count -----------------------------------------------------
        if pacing == "hold":
            n = 1 if D < 10 else 2
            reasons.append(f"hold scene — {n} long dwell(s), let it sit")
        else:
            per = rng.uniform(*pack["slot_seconds"][pacing])
            n = max(1, math.ceil(D / per))
        n = min(n, max(1, len(pool) * 2)) if pool else n

        # --- boundaries: sample, normalize, snap to breath points -----------
        raw = [rng.uniform(*pack["dwell"][pacing]) for _ in range(n)]
        scale = D / sum(raw)
        durs = [d * scale for d in raw]
        pts = breath_points(sc)
        bounds, t = [], sc.t0
        for d in durs[:-1]:
            t = snap(t + d, pts)
            bounds.append(round(t, 2))
        edges = [sc.t0] + bounds + [sc.t1]

        # --- assign assets to slots ------------------------------------------
        shots = []
        for i in range(n):
            t0, t1 = edges[i], edges[i + 1]
            dur = round(t1 - t0, 2)
            item = _pick_item(pool, rng, texture_run, last_video, pack)
            if item is None:
                shots.append({"t0": t0, "t1": t1, "dur": dur, "kind": "graphic",
                              "desc": "filler card (no asset)", "motion": "static",
                              "block": None})
                warnings.append("slot without asset — graphic filler used")
                texture_run.append("graphic")
                texture_hist["graphic"] += 1
                all_shot_durs.append(dur)
                continue
            kind = item["kind"]
            if kind == "clip":
                dur_cap = pack["clip_max_seconds"]
                if dur > dur_cap + 0.05:
                    reasons.append(f"clip capped at {dur_cap}s (copyright rule), "
                                   f"image continues the slot")
                last_video = item.get("video_id")
            motion = _motion_for(item, pack, rng, last_motion)
            last_motion = motion
            shots.append({"t0": t0, "t1": t1, "dur": dur, "kind": kind,
                          "desc": item["desc"], "motion": motion,
                          "block": item["block"],
                          "video_id": item.get("video_id"),
                          "clip_window": [item.get("start"), item.get("end")]
                          if kind == "clip" else None})
            texture_run.append(kind)
            texture_run[:] = texture_run[-4:]
            all_shot_durs.append(dur)
            motion_hist[motion] += 1
            texture_hist[kind] += 1

        # --- events from tags -------------------------------------------------
        events = []
        for ln in sc.lines:
            for tag in ln.tags:
                k = tag.kind
                if k in ("UNKNOWN",):
                    continue
                if k == "HOLD":
                    reasons.append("HOLD — dwell stretched, minimal cuts")
                    continue
                if k == "SILENCE":
                    events.append({"kind": "MUSIC_DIP", "t": round(ln.t0 + ln.dur, 2),
                                   "dur": round(rng.uniform(0.8, 1.5), 2)})
                    reasons.append("silence after heavy line")
                    continue
                if k == "REVEAL":
                    silent = rng.random() < pack.get("reveal_silence_prob", 0.3)
                    events.append({"kind": "REVEAL",
                                   "t": round(ln.t0, 2),
                                   "style": "silence" if silent else "sting"})
                    reasons.append("reveal — " +
                                   ("silence lands it" if silent else "sting + hold"))
                    continue
                if k == "ARCHIVEAUDIO":
                    events.append({"kind": "ARCHIVE_AUDIO", "t": round(ln.t0, 2),
                                   "dur": round(ln.dur, 2), "what": tag.value})
                    reasons.append("original tape plays — music ducks out")
                    continue
                if k == "CENSOR":
                    events.append({"kind": "CENSOR", "what": tag.value})
                    continue
                lo, hi = EVENT_DUR.get(k, (3.0, 4.5))
                events.append({"kind": k, "value": tag.value,
                               "t": round(ln.t0 + 0.15, 2),
                               "dur": round(rng.uniform(lo, hi), 2),
                               "variant": variants.pick(k)})

        dropped = _schedule_events(events, sc)
        if dropped:
            warnings.append(f"{dropped} card(s) skipped — too many tags "
                            f"fire on the same line (scene too short)")
        trans = next_transition()
        transition_hist[trans] += 1
        music = pack["music_moods"]["map"].get(
            sc.mood, pack["music_moods"]["default"])

        scene_plans.append({
            "scene": sc.num, "t0": sc.t0, "t1": sc.t1, "dur": D,
            "mood": sc.mood, "pacing": pacing, "music": music,
            "transition_in": trans, "shots": shots, "events": events,
            "reasons": reasons, "warnings": warnings,
            "blocks": pools[sc.num]["blocks"],
        })

    fingerprint = _fingerprint(all_shot_durs, motion_hist, texture_hist,
                               transition_hist)
    risk = _slideshow_risk(all_shot_durs, motion_hist, texture_hist)
    return {"pack": pack["name"], "substyle": pack.get("substyle"),
            "seed": seed, "scenes": scene_plans,
            "fingerprint": fingerprint, "slideshow_risk": risk}


def rng_seed_from(project) -> int:
    return abs(hash(project.clean_norm[:200])) % (2 ** 31)


# center-screen / attention-heavy cards: only ONE of these at a time
_BIG_CARDS = {"TEXT", "QUOTE", "CHAPTER", "ENTRY", "COMPARE", "TIMELINE",
              "STAT"}


def _schedule_events(events, sc) -> int:
    """Collision-aware card scheduler (SPEC 09 'no text over text').

    Rules: max 2 cards visible at once, max 1 'big' card, starts at
    least 0.9 s apart. Cards that can't fit inside the scene are
    dropped (count returned) — priority follows tag order.
    """
    cards = [e for e in events
             if e.get("value") is not None and "dur" in e
             and e["kind"] not in ("MUSIC_DIP", "REVEAL", "ARCHIVE_AUDIO",
                                   "CENSOR")]
    cards.sort(key=lambda e: e.get("t", sc.t0))
    placed, dropped = [], 0
    for e in cards:
        t0, dur = e["t"], e["dur"]
        big = e["kind"] in _BIG_CARDS

        def ok(t):
            cur = [p for p in placed if p[0] < t + dur and t < p[1]]
            if len(cur) >= 2:
                return False
            if big and any(p[2] for p in cur):
                return False
            if any(abs(p[0] - t) < 0.9 for p in placed):
                return False
            return True

        while not ok(t0) and t0 + 1.5 <= sc.t1 - 0.2:
            t0 += 0.45
        if not ok(t0):
            e["dropped"] = True
            dropped += 1
            continue
        if t0 + dur > sc.t1 - 0.1:
            dur = max(1.6, sc.t1 - 0.1 - t0)
        e["t"], e["dur"] = round(t0, 2), round(dur, 2)
        placed.append((t0, t0 + dur, big))
    if dropped:
        events[:] = [e for e in events if not e.get("dropped")]
    return dropped


def _pick_item(pool, rng, texture_run, last_video, pack):
    if not pool:
        return None
    def ok(it):
        if it["kind"] == "clip" and it.get("video_id") == last_video:
            return False
        if len(texture_run) >= 3 and all(t == it["kind"] for t in texture_run[-3:]):
            return False
        return True
    cands = [it for it in pool if ok(it)] or pool
    # prefer texture change
    if texture_run:
        changed = [it for it in cands if it["kind"] != texture_run[-1]]
        if changed and rng.random() < 0.6:
            cands = changed
    # prefer fresh (unused) assets over re-framed reuses
    fresh = [it for it in cands if not it.get("used")]
    if fresh and rng.random() < 0.8:
        cands = fresh
    item = rng.choice(cands)
    item["budget"] = item.get("budget", 1) - 1
    picked = dict(item)
    if item.get("used"):
        picked["desc"] = "(re-framed) " + (picked["desc"] or "")
    item["used"] = True
    if item["budget"] <= 0:
        pool.remove(item)
    return picked


def _fingerprint(durs, motions, textures, transitions):
    if not durs:
        return {}
    mean = sum(durs) / len(durs)
    var = sum((d - mean) ** 2 for d in durs) / len(durs)
    return {"shots": len(durs), "dur_mean": round(mean, 2),
            "dur_std": round(var ** 0.5, 2),
            "motions": dict(motions), "textures": dict(textures),
            "transitions": dict(transitions)}


def _slideshow_risk(durs, motions, textures):
    if not durs:
        return "UNKNOWN"
    mean = sum(durs) / len(durs)
    std = (sum((d - mean) ** 2 for d in durs) / len(durs)) ** 0.5
    stills = textures.get("image", 0) + textures.get("graphic", 0)
    ratio = stills / max(1, sum(textures.values()))
    score = 0
    if std / mean < 0.22:
        score += 2          # metronome rhythm
    if len(motions) < 5:
        score += 1          # few motion types
    if ratio > 0.92:
        score += 1          # nearly all stills
    if motions.get("static", 0) == 0:
        score += 1          # every still moves = robotic
    return "HIGH" if score >= 3 else ("MEDIUM" if score == 2 else "LOW")


# ---------------------------------------------------------------- preview ---
def preview(plan_dict, first=6, out=print):
    out(f"pack: {plan_dict['pack']}/{plan_dict['substyle']} | "
        f"risk: {plan_dict['slideshow_risk']} | fp: {plan_dict['fingerprint']}")
    for sp in plan_dict["scenes"][:first]:
        out(f"\nSCENE {sp['scene']}  [{sp['t0']}s → {sp['t1']}s]  "
            f"{sp['mood']}/{sp['pacing']}  music:{sp['music']}  "
            f"in:{sp['transition_in']}")
        for sh in sp["shots"]:
            out(f"  shot {sh['dur']:>5}s  {sh['kind']:<7} {sh['motion']:<13} "
                f"{(sh['desc'] or '')[:58]}")
        for ev in sp["events"]:
            v = ev.get("value", ev.get("what", ev.get("style", "")))
            var = f" [{ev['variant']}]" if "variant" in ev else ""
            out(f"  event {ev['kind']:<12} @{ev.get('t', '-')}s  {str(v)[:44]}{var}")
        for r in sp["reasons"]:
            out(f"  ✎ {r}")
        for w in sp["warnings"]:
            out(f"  ⚠ {w}")
