"""Renderer — turns a bound plan into an actual MP4, scene by scene.

Implements the SPEC pipeline stages 5-7 for v1:
  per-shot plates (PIL cover / clip windows) -> zoompan motion ->
  in-scene cuts -> pack grade -> event card overlays (alpha fades,
  breath-timed) -> scene mp4 checkpoints -> transition assembly ->
  synth/library audio bed per mood + SFX + music dips -> -14 LUFS.

Checkpointing: each scene lands in work/scene_NNN.mp4; existing files
are skipped, so sleep/crash loses at most one scene (SPEC 05).
"""
import json
import math
import os
import random
import subprocess

from PIL import Image, ImageOps

from .graphics import render_card
from .themes import theme_for

W, H = 1920, 1080
PW, PH = 2496, 1404
FPS = 30


def _ffmpeg():
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        return get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


FF = _ffmpeg()


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed:\n" + r.stderr[-2500:])


# --------------------------------------------------------------- motions ---
def _motion_expr(motion, D):
    """zoompan (z, x, y) expressions for every planner motion name."""
    cx, cy = "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"
    presets = {
        "push_in_slow": (f"min(1.0+0.08*on/{D},1.10)", cx, cy),
        "push_in_med": (f"min(1.0+0.13*on/{D},1.15)", cx, cy),
        "map_zoom": (f"min(1.0+0.18*on/{D},1.20)", cx, cy),
        "face_push": (f"min(1.0+0.12*on/{D},1.14)", cx, cy),
        "pull_out": (f"max(1.13-0.11*on/{D},1.0)", cx, cy),
        "reveal_crop": (f"max(1.16-0.14*on/{D},1.0)", cx, cy),
        "pan_left": ("1.10", f"(iw-iw/zoom)*(1-on/{D})", cy),
        "pan_right": ("1.10", f"(iw-iw/zoom)*(on/{D})", cy),
        "tilt": ("1.10", cx, f"(ih-ih/zoom)*(on/{D})"),
        "doc_scan": ("1.16", cx, f"(ih-ih/zoom)*(on/{D})"),
        "diag_drift": ("1.11", f"(iw-iw/zoom)*(on/{D})",
                       f"(ih-ih/zoom)*(1-on/{D})"),
        "static": ("1.05", cx, cy),
        "micro_drift": ("1.07", f"{cx}+6*sin(on/37)", f"{cy}+4*sin(on/53)"),
    }
    return presets.get(motion, presets["push_in_slow"])


# ---------------------------------------------------------------- plates ---
def _image_plate(src, out_png):
    img = Image.open(src).convert("RGB")
    ImageOps.fit(img, (PW, PH), Image.LANCZOS).save(out_png)


def _filler_plate(text, theme, out_png):
    card, _ = render_card("CHAPTER", text or " ", "black_screen_title", theme)
    card.convert("RGB").resize((PW, PH)).save(out_png)


def _render_image_shot(plate_png, dur, motion, out_mp4):
    D = max(2, int(dur * FPS))
    z, x, y = _motion_expr(motion, D)
    vf = (f"scale={PW}:{PH},zoompan=z='{z}':x='{x}':y='{y}':d={D}:"
          f"s={W}x{H}:fps={FPS},format=yuv420p")
    run([FF, "-y", "-loop", "1", "-t", str(dur + 0.3), "-i", plate_png,
         "-vf", vf, "-frames:v", str(D), "-r", str(FPS),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out_mp4])


def _render_clip_shot(src, dur, window, out_mp4):
    """Video-file shot: window cut + punch-in transform, clip audio dropped."""
    ss = window[0] if window and window[0] is not None else 0
    vf = (f"scale={int(W*1.08)}:{int(H*1.08)}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},fps={FPS},format=yuv420p")
    run([FF, "-y", "-ss", str(ss), "-t", str(dur), "-i", src, "-vf", vf,
         "-an", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "18", out_mp4])


# ----------------------------------------------------------------- audio ---
_MOOD_SYNTH = {
    # (noise_color, noise_amp, lowpass, sine_freq, sine_amp, trem)
    "tension": ("brown", 0.055, 170, 55, 0.05, 0.14),
    "dark": ("brown", 0.06, 140, 48, 0.06, 0.10),
    "tragic": ("brown", 0.035, 220, 62, 0.045, 0.08),
    "mystery": ("brown", 0.045, 200, 58, 0.05, 0.12),
    "emotional": ("pink", 0.028, 320, 70, 0.035, 0.09),
    "neutral": ("brown", 0.03, 260, 0, 0.0, 0.1),
    "curious": ("pink", 0.03, 300, 66, 0.03, 0.16),
    "calm": ("pink", 0.024, 340, 0, 0.0, 0.08),
    "nostalgic": ("pink", 0.026, 300, 60, 0.03, 0.07),
    "action": ("pink", 0.04, 420, 80, 0.05, 0.5),
    "epic": ("brown", 0.05, 240, 52, 0.06, 0.12),
    "hopeful": ("pink", 0.026, 360, 72, 0.03, 0.1),
    "triumphant": ("pink", 0.032, 380, 76, 0.04, 0.12),
}


def _library_track(library, mood, rng):
    if not library:
        return None
    d = os.path.join(library, "music", mood)
    if not os.path.isdir(d):
        return None
    files = [os.path.join(d, f) for f in os.listdir(d)
             if os.path.splitext(f)[1].lower() in (".mp3", ".wav", ".m4a",
                                                   ".flac", ".ogg")]
    return rng.choice(files) if files else None


def _bed_segment(mood, dur, out_wav, library=None, rng=None):
    track = _library_track(library, mood, rng or random.Random())
    if track:
        run([FF, "-y", "-stream_loop", "-1", "-i", track, "-t", str(dur),
             "-af", "volume=0.5,afade=t=in:d=0.8,"
                    f"afade=t=out:st={max(0, dur-0.8)}:d=0.8",
             "-ar", "48000", "-ac", "2", out_wav])
        return
    nc, na, lp, sf, sa, tr = _MOOD_SYNTH.get(mood, _MOOD_SYNTH["neutral"])
    tr = max(0.1, tr)  # ffmpeg tremolo lower bound
    parts = [f"anoisesrc=color={nc}:amplitude={na}:seed=9,lowpass=f={lp},"
             f"tremolo=f={tr}:d=0.6[n]"]
    mix = "[n]"
    if sf:
        parts.append(f"sine=frequency={sf}:duration={dur},volume={sa}[s]")
        mix = "[n][s]amix=inputs=2:normalize=0"
        fc = ";".join(parts) + f";{mix},atrim=0:{dur}[o]"
    else:
        fc = parts[0].replace("[n]", f",atrim=0:{dur}[o]")
    run([FF, "-y", "-filter_complex", fc, "-map", "[o]",
         "-t", str(dur), "-ar", "48000", "-ac", "2", out_wav])


def _build_audio(plan_scenes, total, work, library, out_wav):
    rng = random.Random(4)
    # group consecutive scenes by mood so music doesn't restart every scene
    runs, cur = [], None
    for sp in plan_scenes:
        mood = sp["music"]
        if cur and cur[0] == mood:
            cur[2] = sp["t1"]
        else:
            cur = [mood, sp["t0"], sp["t1"]]
            runs.append(cur)
    segs = []
    for i, (mood, a, b) in enumerate(runs):
        seg = os.path.join(work, f"bed{i}.wav")
        _bed_segment(mood, round(b - a, 2), seg, library, rng)
        segs.append(seg)
    listfile = os.path.join(work, "beds.txt")
    with open(listfile, "w") as f:
        for s in segs:
            f.write(f"file '{s}'\n")
    bed = os.path.join(work, "bed_all.wav")
    run([FF, "-y", "-f", "concat", "-safe", "0", "-i", listfile,
         "-c", "copy", bed])

    # music dips + sfx booms at event times
    dips, booms = [], []
    for sp in plan_scenes:
        for e in sp["events"]:
            if e["kind"] == "MUSIC_DIP":
                dips.append((e["t"], e["t"] + e.get("dur", 1.2)))
            elif e["kind"] in ("ENTRY", "CHAPTER", "REVEAL") and \
                    e.get("style") != "silence":
                booms.append(e.get("t", 0))
            elif e["kind"] == "REVEAL" and e.get("style") == "silence":
                dips.append((e.get("t", 0), e.get("t", 0) + 1.4))
    vol = "1"
    for a, b in dips:
        vol = f"if(between(t,{a:.2f},{b:.2f}),0.25,{vol})"
    inputs, fc, mix = ["-i", bed], [f"[0:a]volume='{vol}':eval=frame[bed]"], ["[bed]"]
    for i, t in enumerate(booms[:40], start=1):
        fc.append(f"sine=frequency=52:duration=1.3,afade=t=out:st=0.05:d=1.2,"
                  f"volume=0.8,adelay={int(t*1000)}|{int(t*1000)}[b{i}]")
        mix.append(f"[b{i}]")
    fc.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0,"
              f"atrim=0:{total},loudnorm=I=-14:TP=-1.5:LRA=11[out]")
    run([FF, "-y", *inputs, "-filter_complex", ";".join(fc),
         "-map", "[out]", "-ar", "48000", out_wav])


# --------------------------------------------------------------- renderer --
GRADES = {
    "crime_dark_v1": ("eq=saturation=0.62:contrast=1.09:brightness=-0.035,"
                      "colorbalance=bs=0.08:bm=0.03,vignette=PI/4.4,"
                      "noise=alls=8:allf=t"),
    "history_sepia_v1": ("eq=saturation=0.85:contrast=1.05,vignette=PI/4.8,"
                         "noise=alls=12:allf=t"),
    "war_heavy_v1": ("eq=saturation=0.7:contrast=1.12:brightness=-0.03,"
                     "vignette=PI/4.6,noise=alls=10:allf=t"),
}
XFADE = {"cut": None, "dissolve": "fade", "fade_black": "fadeblack",
         "camera_flash": "fadewhite", "flash_white": "fadewhite",
         "file_open": "fade", "film_flicker": "fade", "page_fade": "fade",
         "map_dissolve": "fade", "archive_flicker": "fade",
         "smoke_fade": "fadeblack"}


def render_scene(sp, pack, theme, work, fade_in=None, fade_out=None,
                 force=False):
    """One scene, two encode passes total:
    1) each shot -> small mp4 (no grain yet, cheap)
    2) concat + grade + edge fades + card overlays in ONE ffmpeg run.
    fade_in/fade_out: None (hard cut) or 'black'/'white' baked at the
    scene edges, so final assembly is instant stream-copy concat.
    """
    out = os.path.join(work, f"scene_{sp['scene']:03d}.mp4")
    if os.path.exists(out) and not force:
        return out
    shot_files = []
    for i, sh in enumerate(sp["shots"]):
        smp4 = os.path.join(work, f"s{sp['scene']:03d}_{i}.mp4")
        f = sh.get("file")
        try:
            if f and sh.get("is_video"):
                _render_clip_shot(f, sh["dur"], sh.get("clip_window"), smp4)
            else:
                plate = os.path.join(work, f"s{sp['scene']:03d}_{i}.png")
                if f:
                    _image_plate(f, plate)
                else:
                    _filler_plate((sh.get("desc") or "")[:40], theme, plate)
                _render_image_shot(plate, sh["dur"], sh["motion"], smp4)
        except RuntimeError:
            plate = os.path.join(work, f"s{sp['scene']:03d}_{i}.png")
            _filler_plate("", theme, plate)
            _render_image_shot(plate, sh["dur"], "static", smp4)
        shot_files.append(smp4)
    listfile = os.path.join(work, f"s{sp['scene']:03d}.txt")
    with open(listfile, "w") as fh:
        for s in shot_files:
            fh.write(f"file '{s}'\n")

    # single pass: grade + edge fades + overlays
    chain = [GRADES.get(pack.get("grade"), "null")]
    if fade_in:
        chain.append(f"fade=t=in:st=0:d=0.35:color={fade_in}")
    if fade_out:
        chain.append(f"fade=t=out:st={max(0, sp['dur']-0.35)}:d=0.35:"
                     f"color={fade_out}")
    chain.append("format=yuv420p")
    events = [e for e in sp["events"] if e.get("value") is not None
              and e["kind"] not in ("MUSIC_DIP", "REVEAL", "ARCHIVE_AUDIO",
                                    "CENSOR")]
    ins = ["-f", "concat", "-safe", "0", "-i", listfile]
    fc = [f"[0:v]{','.join(chain)}[g0]"]
    prev = "[g0]"
    for i, e in enumerate(events, start=1):
        img, (ax, ay) = render_card(e["kind"], e.get("value", ""),
                                    e.get("variant", "default"), theme)
        png = os.path.join(work, f"s{sp['scene']:03d}_e{i}.png")
        img.save(png)
        t0 = max(0.0, round(e.get("t", sp["t0"]) - sp["t0"], 2))
        t1 = min(sp["dur"], t0 + e.get("dur", 4.0))
        if img.width >= W and img.height >= H:
            ax, ay = 0, 0
        ins += ["-loop", "1", "-t", str(t1 + 0.4), "-i", png]
        fc.append(f"[{i}:v]format=rgba,fade=t=in:st={t0}:d=0.3:alpha=1,"
                  f"fade=t=out:st={max(t0, t1-0.3)}:d=0.3:alpha=1[c{i}]")
        fc.append(f"{prev}[c{i}]overlay={ax}:{ay}:"
                  f"enable='between(t,{t0},{t1})'[o{i}]")
        prev = f"[o{i}]"
    fc[-1] = fc[-1][:fc[-1].rfind("[")] + "[vout]" if events else fc[-1]
    target = "[vout]" if events else "[g0]"
    run([FF, "-y", *ins, "-filter_complex", ";".join(fc), "-map", target,
         "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "23", out])
    for s in shot_files:  # free disk: shot temps not needed anymore
        try:
            os.remove(s)
        except OSError:
            pass
    return out


def _edge_fades(plan_scenes):
    """Per scene: (fade_in, fade_out) colors baked from transition_in."""
    fades = []
    for i, sp in enumerate(plan_scenes):
        t_in = XFADE.get(sp["transition_in"]) if i > 0 else None
        fi = {"fadeblack": "black", "fadewhite": "white",
              "fade": "black"}.get(t_in)
        t_next = (XFADE.get(plan_scenes[i + 1]["transition_in"])
                  if i + 1 < len(plan_scenes) else None)
        fo = {"fadeblack": "black", "fadewhite": "white",
              "fade": "black"}.get(t_next)
        fades.append((fi, fo))
    return fades


def assemble(scene_files, plan_scenes, work, out_mp4):
    """Instant stream-copy concat — transitions are baked at scene edges."""
    lf = os.path.join(work, "assemble.txt")
    with open(lf, "w") as fh:
        for s in scene_files:
            fh.write(f"file '{s}'\n")
    run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lf,
         "-c", "copy", out_mp4])
    return sum(sp["dur"] for sp in plan_scenes)


def render(project, plan, pack, workdir, out_mp4, scenes=None, library=None,
           progress=print):
    os.makedirs(workdir, exist_ok=True)
    theme = theme_for(pack["name"])
    sel = [sp for sp in plan["scenes"]
           if scenes is None or sp["scene"] in scenes]
    fades = _edge_fades(sel)
    files = []
    for sp, (fi, fo) in zip(sel, fades):
        progress(f"scene {sp['scene']}/{sel[-1]['scene']} "
                 f"({sp['dur']}s, {len(sp['shots'])} shots)")
        files.append(render_scene(sp, pack, theme, workdir,
                                  fade_in=fi, fade_out=fo))
    silent = os.path.join(workdir, "video_silent.mp4")
    total = assemble(files, sel, workdir, silent)
    progress("audio bed + sfx + loudnorm…")
    wav = os.path.join(workdir, "mix.wav")
    # shift event times so audio aligns with the first selected scene
    t_off = sel[0]["t0"]
    shifted = []
    for sp in sel:
        c = json.loads(json.dumps(sp))
        c["t0"], c["t1"] = c["t0"] - t_off, c["t1"] - t_off
        for e in c["events"]:
            if "t" in e:
                e["t"] = max(0.0, e["t"] - t_off)
        shifted.append(c)
    _build_audio(shifted, total, workdir, library, wav)
    run([FF, "-y", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out_mp4])
    progress(f"done: {out_mp4}")
    return out_mp4
