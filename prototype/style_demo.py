#!/usr/bin/env python3
"""DocuStudio style prototype — renders short genre-styled sample clips.

Proves the render formula before the full tool is built:
  PIL canvas/graphics -> ffmpeg zoompan shots -> xfade concat ->
  grade/grain/vignette -> card overlays (alpha fades) -> synth audio bed.

Usage: python3 style_demo.py <assets_dir> <out_dir> [crime|history|sports|all]
Placeholder visuals: frames from the owner's reference videos (private test only).
"""
import os, subprocess, sys, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
FPS = 30
W, H = 1920, 1080
PW, PH = 2496, 1404          # plate size (headroom for zoompan)
FONTS = {
    "sans":  "/home/user/Claude/prostudio/assets/fonts/DejaVuSans-Bold.ttf",
    "serif": "/home/user/Claude/prostudio/assets/fonts/DejaVuSerif-Bold.ttf",
    "mono":  "/home/user/Claude/prostudio/assets/fonts/DejaVuSansMono-Bold.ttf",
}

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed:\n" + r.stderr[-3000:])

def font(kind, size):
    return ImageFont.truetype(FONTS[kind], size)

# ---------------------------------------------------------------- plates ----
def cover(img, w, h):
    return ImageOps.fit(img, (w, h), Image.LANCZOS)

def add_noise(img, strength=14):
    import numpy as _np  # optional; fall back to PIL-only grain
    return img

def paper_texture(w, h, base=(226, 214, 190)):
    img = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(img)
    rnd = random.Random(7)
    for _ in range(w * h // 900):
        x, y = rnd.randrange(w), rnd.randrange(h)
        v = rnd.randint(-14, 10)
        c = tuple(max(0, min(255, b + v)) for b in base)
        d.rectangle([x, y, x + 2, y + 2], fill=c)
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    # edge darkening
    vig = Image.new("L", (w, h), 0)
    dv = ImageDraw.Draw(vig)
    dv.rectangle([int(w*0.06), int(h*0.08), int(w*0.94), int(h*0.92)], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(180))
    dark = Image.new("RGB", (w, h), tuple(int(b*0.72) for b in base))
    return Image.composite(img, dark, vig)

def sepia(img):
    g = ImageOps.grayscale(img)
    return ImageOps.colorize(g, black=(38, 28, 18), white=(238, 224, 198), mid=(150, 126, 96))

def drop_shadow(canvas, box, blur=28, alpha=110):
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle(box, fill=(0, 0, 0, alpha))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))

def plate_fullbleed(src):
    return cover(Image.open(src).convert("RGB"), PW, PH)

def plate_history(src):
    """Framed sepia photo on paper canvas (reference video 4 style)."""
    canvas = paper_texture(PW, PH).convert("RGBA")
    photo = sepia(cover(Image.open(src).convert("RGB"), int(PW*0.62), int(PH*0.66)))
    bw, bh = photo.size
    frame = Image.new("RGB", (bw + 44, bh + 44), (246, 240, 226))
    frame.paste(photo, (22, 22))
    frame = frame.rotate(random.Random(src).uniform(-1.4, 1.4), expand=True,
                         fillcolor=(0, 0, 0))
    fx = (PW - frame.width) // 2
    fy = (PH - frame.height) // 2 - 20
    drop_shadow(canvas, [fx + 18, fy + 26, fx + frame.width + 18, fy + frame.height + 26])
    canvas.paste(frame, (fx, fy))
    return canvas.convert("RGB")

def plate_sports(src, kicker=None):
    """Photo panel on light editorial canvas + red accent (video 5 style)."""
    canvas = Image.new("RGBA", (PW, PH), (243, 243, 245, 255))
    d = ImageDraw.Draw(canvas)
    for gx in range(0, PW, 156):  # faint grid
        d.line([(gx, 0), (gx, PH)], fill=(234, 234, 237), width=2)
    photo = cover(Image.open(src).convert("RGB"), int(PW*0.60), int(PH*0.74))
    px, py = int(PW*0.30), int(PH*0.11)
    drop_shadow(canvas, [px + 14, py + 20, px + photo.width + 14, py + photo.height + 20],
                blur=34, alpha=90)
    canvas.paste(photo, (px, py))
    d.rectangle([px - 26, py, px - 8, py + photo.height], fill=(196, 30, 44))
    if kicker:
        f = font("sans", 74)
        d.text((int(PW*0.045), int(PH*0.16)), kicker, font=f, fill=(24, 24, 28))
        d.rectangle([int(PW*0.045), int(PH*0.16) + 92, int(PW*0.045) + 150,
                     int(PH*0.16) + 104], fill=(196, 30, 44))
    return canvas.convert("RGB")

# ---------------------------------------------------------------- cards -----
def _rounded(d, box, r, fill):
    d.rounded_rectangle(box, radius=r, fill=fill)

def card_img(kind, text, style, sub=None):
    """Return RGBA card image + (x,y) position on 1920x1080."""
    S = style
    if kind == "entry":
        img = Image.new("RGBA", (W, 190), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if S["name"] == "sports":
            f = font("sans", 84); tw = d.textlength(text, f)
            _rounded(d, (60, 30, 60 + tw + 90, 170), 8, (196, 30, 44, 255))
            d.text((105, 62), text, font=f, fill=(255, 255, 255, 255))
            return img, (0, 60)
        band = (12, 12, 14, 216) if S["name"] == "crime" else (40, 30, 18, 210)
        d.rectangle([0, 20, W, 170], fill=band)
        f = font(S["font"], 76); tw = d.textlength(text, f)
        d.text(((W - tw) / 2, 55), text, font=f, fill=S["accent_text"])
        d.rectangle([(W - 220) / 2, 150, (W + 220) / 2, 158], fill=S["accent"])
        return img, (0, 120)
    if kind == "date":
        f = font(S["font"], 58)
        pad, tw = 34, ImageDraw.Draw(Image.new("RGBA", (8, 8))).textlength(text, f)
        img = Image.new("RGBA", (int(tw + pad * 2), 112), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        _rounded(d, (0, 0, img.width, 104), 10, S["card_bg"])
        d.rectangle([0, 0, 14, 104], fill=S["accent"])
        d.text((pad + 6, 22), text, font=f, fill=(255, 255, 255, 255))
        return img, (90, H - 250)
    if kind == "source":
        f = font("mono" if S["name"] == "crime" else S["font"], 34)
        tw = ImageDraw.Draw(Image.new("RGBA", (8, 8))).textlength(text, f)
        img = Image.new("RGBA", (int(tw + 56), 72), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        _rounded(d, (0, 0, img.width, 64), 32, (10, 10, 12, 200))
        d.ellipse([20, 24, 36, 40], fill=S["accent"])
        d.text((48, 14), text, font=f, fill=(235, 235, 235, 255))
        return img, (W - img.width - 80, 70)
    if kind == "stat":
        f1, f2 = font("sans", 86), font(S["font"], 40)
        meas = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
        pw = int(max(meas.textlength(text, f1), meas.textlength(sub or "", f2)) + 100)
        img = Image.new("RGBA", (pw, 250), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        _rounded(d, (0, 0, pw, 240), 14, S["card_bg"])
        d.rectangle([0, 0, pw, 16], fill=S["accent"])
        d.text((44, 44), text, font=f1, fill=(255, 255, 255, 255))
        if sub:
            d.text((46, 156), sub, font=f2, fill=(200, 200, 205, 255))
        return img, (90, H - 420)
    if kind == "textpop":
        f = font("sans", 120)
        tw = ImageDraw.Draw(Image.new("RGBA", (8, 8))).textlength(text, f)
        img = Image.new("RGBA", (int(tw + 80), 220), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for ox, oy in ((6, 8), (0, 0)):
            col = (0, 0, 0, 230) if (ox, oy) != (0, 0) else S["pop_fill"]
            d.text((40 + ox, 40 + oy), text, font=f, fill=col)
        return img, (int((W - img.width) / 2), 400)
    if kind == "caption":
        f = font(S["cap_font"], S["cap_size"])
        tw = ImageDraw.Draw(Image.new("RGBA", (8, 8))).textlength(text, f)
        img = Image.new("RGBA", (int(tw + 60), S["cap_size"] + 60), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if S["name"] == "sports":
            _rounded(d, (0, 6, img.width, img.height - 6), 10, (255, 255, 255, 235))
            d.text((30, 26), text, font=f, fill=(22, 22, 26, 255))
        else:
            for ox, oy in ((3, 4), (0, 0)):
                col = (0, 0, 0, 235) if (ox, oy) != (0, 0) else (245, 245, 245, 255)
                d.text((30 + ox, 26 + oy), text, font=f, fill=col)
        return img, (int((W - img.width) / 2), H - 170)
    if kind == "name":
        f1, f2 = font(S["font"], 52), font(S["font"], 32)
        img = Image.new("RGBA", (860, 150), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        _rounded(d, (0, 0, 860, 140), 8, S["card_bg"])
        d.rectangle([0, 0, 14, 140], fill=S["accent"])
        d.text((40, 18), text, font=f1, fill=(255, 255, 255, 255))
        if sub:
            d.text((42, 88), sub, font=f2, fill=(205, 205, 210, 255))
        return img, (90, H - 300)
    raise ValueError(kind)

# ---------------------------------------------------------------- motion ----
ZOOMS = {
    "in":   ("min(1.0+0.11*on/{D},1.13)", "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"),
    "out":  ("max(1.13-0.11*on/{D},1.0)", "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"),
    "left": ("1.10", "(iw-iw/zoom)*(1-on/{D})", "(ih-ih/zoom)/2"),
    "right": ("1.10", "(iw-iw/zoom)*(on/{D})", "(ih-ih/zoom)/2"),
}

def render_shot(plate_png, dur, move, out_mp4):
    D = int(dur * FPS)
    z, x, y = (e.format(D=D) for e in ZOOMS[move])
    vf = (f"scale={PW}:{PH},zoompan=z='{z}':x='{x}':y='{y}':d={D}:s={W}x{H}:fps={FPS},"
          f"format=yuv420p")
    run([FF, "-y", "-loop", "1", "-t", str(dur + 0.2), "-i", plate_png,
         "-vf", vf, "-frames:v", str(D), "-r", str(FPS), "-c:v", "libx264",
         "-preset", "veryfast", "-crf", "18", out_mp4])

# ---------------------------------------------------------------- styles ----
STYLES = {
    "crime": dict(name="crime", font="sans", cap_font="sans", cap_size=44,
                  accent=(196, 30, 44, 255), accent_text=(240, 240, 240, 255),
                  card_bg=(14, 14, 18, 225), pop_fill=(235, 232, 228, 255),
                  grade=("eq=saturation=0.62:contrast=1.09:brightness=-0.035,"
                         "colorbalance=bs=0.08:bm=0.03,vignette=PI/4.4,"
                         "noise=alls=9:allf=t"),
                  xfade="fadeblack", audio="crime"),
    "history": dict(name="history", font="serif", cap_font="serif", cap_size=46,
                    accent=(150, 108, 40, 255), accent_text=(240, 230, 210, 255),
                    card_bg=(36, 28, 18, 228), pop_fill=(238, 226, 200, 255),
                    grade=("eq=saturation=0.88:contrast=1.05,vignette=PI/4.8,"
                           "noise=alls=13:allf=t"),
                    xfade="fade", audio="history"),
    "sports": dict(name="sports", font="sans", cap_font="sans", cap_size=42,
                   accent=(196, 30, 44, 255), accent_text=(255, 255, 255, 255),
                   card_bg=(22, 22, 28, 235), pop_fill=(196, 30, 44, 255),
                   grade="eq=saturation=1.12:contrast=1.05:brightness=0.01",
                   xfade="smoothleft", audio="sports"),
}

# ------------------------------------------------------------- timelines ----
def timeline_crime(A):
    shots = [(A("crime_church1"), 5.5, "in", "full"),
             (A("crime_church2"), 5.0, "left", "full"),
             (A("crime_poster"), 6.0, "in", "full"),
             (A("crime_victim"), 6.5, "in", "full"),
             (A("crime_corkboard"), 5.5, "right", "full"),
             (A("crime2_carscene"), 4.0, "in", "full"),
             (A("crime_roof"), 5.0, "out", "full")]
    cards = [("entry", "CASE 47: THE VANISHING", 0.8, 4.6, None),
             ("caption", "In the autumn of 1994, a quiet town lost its brightest student.", 0.8, 5.2, None),
             ("date", "OCTOBER 14, 1994", 6.0, 9.6, None),
             ("caption", "She was last seen leaving evening choir practice.", 11.0, 15.6, None),
             ("source", "POLICE CASE FILE 47-B", 11.4, 16.0, None),
             ("textpop", "LAST SEEN 9:42 PM", 17.4, 21.6, None),
             ("stat", "3 WITNESSES", 23.4, 27.6, "ZERO SUSPECTS NAMED"),
             ("caption", "Her car was found with the engine still running.", 28.6, 32.2, None),
             ("caption", "What the police found next made no sense at all.", 33.0, 37.0, None)]
    booms = [0.8, 6.0, 17.4, 33.0]
    return shots, cards, booms

def timeline_history(A):
    shots = [(A("hist_shooter"), 6.0, "in", "hist"),
             (A("hist_blueprint"), 6.0, "right", "hist"),
             (A("hist_workbench"), 6.0, "in", "hist"),
             (A("hist_ammo"), 6.0, "left", "hist"),
             (A("hist_pistols"), 6.0, "in", "hist"),
             (A("hist_notes"), 6.0, "out", "hist")]
    cards = [("entry", "CHAPTER I — THE LAST GUNFIGHTER", 0.8, 4.8, None),
             ("caption", "By 1911, the army wanted a pistol that could not fail.", 1.0, 5.6, None),
             ("date", "MARCH 29, 1911", 6.4, 10.4, None),
             ("source", "U.S. ARMY ORDNANCE RECORDS", 6.8, 11.4, None),
             ("caption", "Every part was filed, fitted and tested by hand.", 12.4, 17.0, None),
             ("stat", "2,000,000 BUILT", 18.6, 23.0, "BY THE END OF 1945"),
             ("name", "COL. JAMES TAYLOR", 24.6, 29.0, "ORDNANCE OFFICER, 1907-1946"),
             ("caption", "A century later, collectors still argue about why it worked.", 30.4, 35.4, None)]
    booms = [0.8, 6.4, 18.6]
    return shots, cards, booms

def timeline_sports(A):
    shots = [(A("sport_silhouette"), 5.0, "in", ("sport", "WHO IS NEXT?")),
             (A("sport_arena"), 5.0, "right", ("sport", None)),
             (A("sport_map"), 5.0, "in", ("sport", "AUCKLAND, NZ")),
             (A("sport_belt"), 5.5, "in", ("sport", None)),
             (A("sport_punch"), 4.5, "left", ("sport", None)),
             (A("sport_celebrate"), 6.0, "out", ("sport", "THE COMEBACK"))]
    cards = [("entry", "THE COMEBACK — PART ONE", 0.7, 4.4, None),
             ("date", "JUNE 14, 2026", 5.6, 9.4, None),
             ("caption", "Nobody believed the story could turn around this fast.", 5.8, 10.0, None),
             ("source", "OFFICIAL FIGHT RECORDS", 10.6, 14.6, None),
             ("stat", "24 WINS · 13 KO", 16.0, 20.4, "THREE TITLE DEFENSES"),
             ("textpop", "ONE PUNCH", 21.4, 24.8, None),
             ("caption", "And in round two, everything changed.", 26.6, 30.8, None)]
    booms = [0.7, 5.6, 21.4]
    return shots, cards, booms

# ---------------------------------------------------------------- audio -----
def build_audio(kind, total, booms, out_wav):
    if kind == "crime":
        bed = ("anoisesrc=color=brown:amplitude=0.05:seed=11,lowpass=f=170,"
               "tremolo=f=0.14:d=0.6")
    elif kind == "history":
        bed = ("anoisesrc=color=brown:amplitude=0.03:seed=5,lowpass=f=300,"
               "tremolo=f=0.1:d=0.4")
    else:
        bed = ("anoisesrc=color=pink:amplitude=0.028:seed=3,bandpass=f=220:w=180,"
               "tremolo=f=2.0:d=0.7")
    inputs, filters, mix = [], [], []
    filters.append(f"{bed},atrim=0:{total},afade=t=in:d=1,afade=t=out:st={total-2}:d=2[bed]")
    mix.append("[bed]")
    for i, t in enumerate(booms):
        filters.append(
            f"sine=frequency=52:duration=1.4,afade=t=out:st=0.05:d=1.3,"
            f"volume=0.85,adelay={int(t*1000)}|{int(t*1000)}[b{i}]")
        mix.append(f"[b{i}]")
    fc = ";".join(filters) + f";{''.join(mix)}amix=inputs={len(mix)}:normalize=0[out]"
    run([FF, "-y", "-filter_complex", fc, "-map", "[out]", "-t", str(total),
         "-ar", "48000", out_wav])

# ---------------------------------------------------------------- build -----
def build(style_key, assets, outdir):
    S = STYLES[style_key]
    tl = {"crime": timeline_crime, "history": timeline_history,
          "sports": timeline_sports}[style_key]
    A = lambda n: os.path.join(assets, n + ".png")
    shots, cards, booms = tl(A)
    work = os.path.join(outdir, "work_" + style_key)
    os.makedirs(work, exist_ok=True)

    # 1. plates + shots
    shot_files = []
    for i, (src, dur, move, plate_kind) in enumerate(shots):
        plate = os.path.join(work, f"plate{i}.png")
        if plate_kind == "full":
            plate_fullbleed(src).save(plate)
        elif plate_kind == "hist":
            plate_history(src).save(plate)
        else:
            plate_sports(src, plate_kind[1]).save(plate)
        mp4 = os.path.join(work, f"shot{i}.mp4")
        render_shot(plate, dur, move, mp4)
        shot_files.append((mp4, dur))

    # 2. concat with xfade
    TR = 0.5
    total = sum(d for _, d in shot_files) - TR * (len(shot_files) - 1)
    ins, fc = [], []
    for f, _ in shot_files:
        ins += ["-i", f]
    prev, off = "[0:v]", 0.0
    for i in range(1, len(shot_files)):
        off += shot_files[i - 1][1] - TR
        out = f"[v{i}]"
        fc.append(f"{prev}[{i}:v]xfade=transition={S['xfade']}:duration={TR}:"
                  f"offset={off:.3f}{out}")
        prev = out
    fc.append(f"{prev}{S['grade']},format=yuv420p[graded]")
    base = os.path.join(work, "base.mp4")
    run([FF, "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[graded]",
         "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", base])

    # 3. overlay cards (alpha fade in/out)
    ins, fc = ["-i", base], []
    prev = "[0:v]"
    for i, (kind, text, t0, t1, sub) in enumerate(cards, start=1):
        img, (x, y) = card_img(kind, text, S, sub)
        png = os.path.join(work, f"card{i}.png")
        img.save(png)
        ins += ["-loop", "1", "-t", str(t1 + 0.4), "-i", png]
        fc.append(f"[{i}:v]format=rgba,fade=t=in:st={t0}:d=0.35:alpha=1,"
                  f"fade=t=out:st={t1 - 0.35}:d=0.35:alpha=1[c{i}]")
        fc.append(f"{prev}[c{i}]overlay={x}:{y}:enable='between(t,{t0},{t1})'[o{i}]")
        prev = f"[o{i}]"
    fc[-1] = fc[-1].replace(f"[o{len(cards)}]", "[vout]")
    withcards = os.path.join(work, "cards.mp4")
    run([FF, "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[vout]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", withcards])

    # 4. audio + mux
    wav = os.path.join(work, "audio.wav")
    build_audio(S["audio"], total, booms, wav)
    final = os.path.join(outdir, f"docustudio_sample_{style_key}.mp4")
    run([FF, "-y", "-i", withcards, "-i", wav, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", final])
    print(style_key, "->", final, f"({total:.1f}s)")
    return final

if __name__ == "__main__":
    assets, outdir = sys.argv[1], sys.argv[2]
    which = sys.argv[3] if len(sys.argv) > 3 else "all"
    os.makedirs(outdir, exist_ok=True)
    for k in (["crime", "history", "sports"] if which == "all" else [which]):
        build(k, assets, outdir)
