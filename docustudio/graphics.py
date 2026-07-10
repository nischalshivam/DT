"""Graphics Factory — renders every card kind × variant as a PIL image.

One recipe engine: ~16 base layouts parameterized by the pack THEME, and
a table mapping every variant name in the packs to (layout, params).
render_card(kind, value, variant, theme) -> (RGBA image, anchor)
anchor: suggested (x, y) on a 1920x1080 frame ("auto" positions).
"""
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from .themes import font_path

W, H = 1920, 1080


# ------------------------------------------------------------- utilities ---
_font_cache = {}


def _font(kind: str, size: int):
    key = (kind, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(font_path(kind), size)
    return _font_cache[key]


def _measure(text, f):
    img = Image.new("RGBA", (8, 8))
    return ImageDraw.Draw(img).textlength(text, f)


def _spaced(text: str, n: int) -> str:
    return (" " * n).join(list(text)) if n else text


def _paper(w, h, base, seed=7):
    img = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for _ in range(max(60, w * h // 1400)):
        x, y = rnd.randrange(w), rnd.randrange(h)
        v = rnd.randint(-12, 9)
        c = tuple(max(0, min(255, b + v)) for b in base)
        d.rectangle([x, y, x + 2, y + 2], fill=c)
    return img.filter(ImageFilter.GaussianBlur(0.8)).convert("RGBA")


def _shadow_text(d, xy, text, f, fill, shadow=(0, 0, 0, 235), off=(3, 4)):
    d.text((xy[0] + off[0], xy[1] + off[1]), text, font=f, fill=shadow)
    d.text(xy, text, font=f, fill=fill)


def _rr(d, box, r, fill, outline=None, width=0):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def _split_value(value: str):
    """'main — sub' or 'main - sub' -> (main, sub)."""
    for sep in (" — ", " – ", " - "):
        if sep in value:
            a, b = value.split(sep, 1)
            return a.strip(), b.strip()
    return value.strip(), ""


# ---------------------------------------------------------- base layouts ---
def _pill(value, t, p):
    small = p.get("small")
    f = _font(p.get("font", t["font"]) if not p.get("font") == "alt"
              else t["alt_font"], 34 if small else 56)
    text = _spaced(value.upper() if not small else value, t["letterspace"] and 1)
    pad = 26 if small else 36
    w = int(_measure(text, f) + pad * 2 + (30 if p.get("dot") else 0))
    h = 66 if small else 108
    img = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _rr(d, (0, 0, w, h), h // 2 if small else 12,
        (*t["panel"], t["panel_alpha"]))
    if p.get("dot"):
        cy = h // 2
        d.ellipse([pad - 6, cy - 8, pad + 10, cy + 8], fill=(*t["accent"], 255))
        d.text((pad + 26, (h - f.size) // 2 - 4), text, font=f,
               fill=(*t["text"], 255))
    else:
        d.rectangle([0, 0, 12, h], fill=(*t["accent"], 255))
        d.text((pad + 8, (h - f.size) // 2 - 4), text, font=f,
               fill=(*t["text"], 255))
    return img, (90, H - 240) if not small else (W - w - 80, 66)


def _strip(value, t, p):
    fkind = t["alt_font"] if p.get("font") == "alt" else t["font"]
    f = _font(fkind, 30 if p.get("small") else 44)
    h = 64 if p.get("small") else 92
    img = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, h], fill=(*t["panel"], 205))
    d.rectangle([0, h - 5, W, h], fill=(*t["accent"], 255))
    tw = _measure(value, f)
    d.text(((W - tw) / 2, (h - f.size) / 2 - 3), value, font=f,
           fill=(*t["text"], 255))
    return img, (0, H - 200 if not p.get("small") else H - 120)


def _band(value, t, p):
    text = _spaced(value.upper(), p.get("spacing", t["letterspace"]))
    f = _font(t["font"], 72)
    img = Image.new("RGBA", (W, 190), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 20, W, 168], fill=(*t["panel"], 216))
    tw = _measure(text, f)
    d.text(((W - tw) / 2, 54), text, font=f, fill=(*t["text"], 255))
    if p.get("underline"):
        d.rectangle([(W - 220) / 2, 148, (W + 220) / 2, 158],
                    fill=(*t["accent"], 255))
    return img, (0, 110)


def _fullscreen(value, t, p):
    img = Image.new("RGBA", (W, H), (8, 8, 10, 255))
    d = ImageDraw.Draw(img)
    main, sub = _split_value(value)
    text = _spaced(main.upper(), p.get("spacing", t["letterspace"]))
    f = _font(t["font"], 110)
    while _measure(text, f) > W - 240 and f.size > 48:
        f = _font(t["font"], f.size - 8)
    tw = _measure(text, f)
    d.text(((W - tw) / 2, H / 2 - f.size), text, font=f, fill=(*t["text"], 255))
    if p.get("rule"):
        d.rectangle([(W - 260) / 2, H / 2 + 40, (W + 260) / 2, H / 2 + 50],
                    fill=(*t["accent"], 255))
    if sub:
        f2 = _font(t["font"], 42)
        tw2 = _measure(sub, f2)
        d.text(((W - tw2) / 2, H / 2 + 90), sub, font=f2,
               fill=(*t["muted"], 255))
    return img, (0, 0)


def _panel(value, t, p):
    main, sub = _split_value(value)
    f1 = _font(t["font"], 60 if p.get("small") else 84)
    f2 = _font(t["font"], 36)
    pw = int(max(_measure(main, f1), _measure(sub, f2)) + 96)
    ph = 168 if p.get("small") else 236
    img = Image.new("RGBA", (pw + 10, ph + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if p.get("paper"):
        paper = _paper(pw, ph, t["paper"])
        img.paste(paper, (0, 0))
        ink = (*t["paper_ink"], 255)
    else:
        _rr(d, (0, 0, pw, ph), 14, (*t["panel"], t["panel_alpha"]))
        ink = (*t["text"], 255)
    d = ImageDraw.Draw(img)
    if p.get("topbar"):
        d.rectangle([0, 0, pw, 14], fill=(*t["accent"], 255))
    if p.get("split"):
        d.rectangle([pw // 2 - 3, 20, pw // 2 + 3, ph - 20],
                    fill=(*t["accent"], 200))
    d.text((44, 38), main, font=f1, fill=ink)
    if sub:
        d.text((46, ph - 62), sub, font=f2,
               fill=(*t["muted"], 255) if not p.get("paper") else ink)
    return img, (90, H - ph - 170)


def _papercard(value, t, p):
    main = value.strip()
    f = _font(t["font"], 84 if p.get("big") else 58)
    while _measure(main, f) > 1500 and f.size > 40:
        f = _font(t["font"], f.size - 6)
    pw = int(_measure(main, f) + 110)
    ph = 190 if p.get("big") else 140
    img = Image.new("RGBA", (pw + 14, ph + 14), (0, 0, 0, 0))
    paper = _paper(pw, ph, t["paper"])
    dp = ImageDraw.Draw(paper)
    dp.rectangle([0, 0, pw - 1, ph - 1], outline=(*t["paper_ink"], 90), width=3)
    dp.rectangle([0, 0, 14, ph], fill=(*t["accent"], 255))
    dp.text((44, (ph - f.size) / 2 - 4), main, font=f,
            fill=(*t["paper_ink"], 255))
    img.paste(paper, (4, 4))
    # soft shadow
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([10, 12, pw + 6, ph + 8], fill=(0, 0, 0, 90))
    out = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), img)
    return out, (90, H - ph - 190)


def _newspaper(value, t, p):
    main, sub = _split_value(value)
    f1 = _font("serif", 44 if p.get("small") else 56)
    f2 = _font("serif", 28)
    pw = int(max(_measure(main.upper(), f1), 360) + 90)
    ph = 150 if not sub else 190
    img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, pw - 1, ph - 1], fill=(246, 242, 232, 250),
                outline=(40, 38, 34, 255), width=3)
    d.rectangle([16, 14, pw - 16, 20], fill=(40, 38, 34, 255))
    d.text((26, 34), main.upper(), font=f1, fill=(28, 26, 24, 255))
    if sub:
        d.text((28, ph - 52), sub, font=f2, fill=(90, 86, 80, 255))
    d.rectangle([16, ph - 20, pw - 16, ph - 15], fill=(40, 38, 34, 255))
    return img, (90, H - ph - 180)


def _timeline(value, t, p):
    f = _font(t["font"], 44)
    tw = int(_measure(value, f))
    pw = max(tw + 140, 560)
    img = Image.new("RGBA", (pw, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = 108
    line = (*t["accent"], 255) if p.get("string") else (*t["muted"], 220)
    d.line([(10, y), (pw - 10, y)], fill=line, width=5)
    for x in (10, pw - 10):
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(*t["muted"], 200))
    cx = pw // 2
    d.ellipse([cx - 15, y - 15, cx + 15, y + 15], fill=(*t["accent"], 255))
    _rr(d, (cx - tw // 2 - 24, 8, cx + tw // 2 + 24, 78), 10,
        (*t["panel"], t["panel_alpha"]))
    d.text((cx - tw // 2, 16), value, font=f, fill=(*t["text"], 255))
    d.line([(cx, 78), (cx, y - 16)], fill=line, width=3)
    return img, ((W - pw) // 2, H - 330)


def _bignum(value, t, p):
    main, sub = _split_value(value)
    text = _spaced(main, p.get("spacing", 0))
    f1 = _font(t["font"], 150)
    while _measure(text, f1) > W - 500 and f1.size > 70:
        f1 = _font(t["font"], f1.size - 10)
    f2 = _font(t["font"], 44)
    pw = int(max(_measure(text, f1), _measure(sub, f2)) + 90)
    ph = 180 + (66 if sub else 0)
    img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _shadow_text(d, (40, 16), text, f1, (*t["text"], 255), off=(6, 8))
    if sub:
        d.rectangle([44, 176, 44 + int(_measure(sub, f2)) + 8, 180],
                    fill=(*t["accent"], 255))
        _shadow_text(d, (46, 188), sub, f2, (*t["text"], 255), off=(2, 3))
    return img, ((W - pw) // 2, 360)


def _lowerthird(value, t, p):
    main, sub = _split_value(value)
    main = _spaced(main, p.get("spacing", 0))
    f1 = _font(t["font"], 52)
    f2 = _font(t["font"], 32)
    pw = int(max(_measure(main, f1), _measure(sub, f2)) + 110)
    img = Image.new("RGBA", (pw, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _rr(d, (0, 0, pw, 140), 8, (*t["panel"], t["panel_alpha"]))
    d.rectangle([0, 0, 14, 140], fill=(*t["accent"], 255))
    d.text((42, 18), main, font=f1, fill=(*t["text"], 255))
    if sub:
        d.text((44, 88), sub.upper(), font=f2, fill=(*t["muted"], 255))
    return img, (90, H - 300)


def _tab(value, t, p):
    f = _font(t["font"], 56)
    tw = int(_measure(value.upper(), f))
    pw, ph = tw + 120, 120
    img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # folder-tab silhouette
    d.polygon([(0, ph), (0, 34), (26, 10), (tw + 70, 10), (tw + 96, 34),
               (pw, ph)], fill=(*t["panel"], t["panel_alpha"]))
    d.rectangle([0, ph - 12, pw, ph], fill=(*t["accent"], 255))
    d.text((52, 40), value.upper(), font=f, fill=(*t["text"], 255))
    return img, (70, 60)


def _stampbox(value, t, p):
    f = _font(t["alt_font"], 44)
    text = _spaced(value.upper(), p.get("spacing", 2))
    tw = int(_measure(text, f))
    pw, ph = tw + 84, 100
    card = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rectangle([10, 10, pw - 10, ph - 10], fill=(*t["panel"], 215))
    d.rectangle([4, 4, pw - 4, ph - 4], outline=(*t["accent"], 255), width=6)
    d.text((42, (ph - f.size) / 2 - 2), text, font=f, fill=(*t["text"], 255))
    if p.get("rotate"):
        card = card.rotate(p["rotate"], expand=True,
                           resample=Image.BICUBIC)
    return card, (W - card.width - 90, 64)


def _tag(value, t, p):
    f = _font(t["font"], 42)
    tw = int(_measure(value, f))
    pw, ph = tw + 150, 104
    img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # tag shape with hole
    d.polygon([(70, 8), (pw - 8, 8), (pw - 8, ph - 8), (70, ph - 8),
               (12, ph // 2)], fill=(*t["paper"], 250))
    d.ellipse([44, ph // 2 - 12, 68, ph // 2 + 12],
              fill=(0, 0, 0, 0), outline=(*t["paper_ink"], 255), width=5)
    d.text((92, (ph - f.size) / 2 - 2), value, font=f,
           fill=(*t["paper_ink"], 255))
    if p.get("pin"):
        d.ellipse([pw - 42, 14, pw - 18, 38], fill=(*t["accent"], 255))
    img = img.rotate(random.Random(value).uniform(-3, 3), expand=True,
                     resample=Image.BICUBIC)
    return img, (W - img.width - 100, H - 320)


def _pinned(value, t, p):
    f = _font(t["font"], 46)
    tw = int(_measure(value, f))
    pw, ph = max(tw + 170, 460), 168
    img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if p.get("paper"):
        card = _paper(pw, 100, t["paper"])
        img.paste(card, (0, 40))
        ink = (*t["paper_ink"], 255)
    else:
        _rr(d, (0, 40, pw, 140), 12, (*t["panel"], t["panel_alpha"]))
        ink = (*t["text"], 255)
    d = ImageDraw.Draw(img)
    # location pin glyph
    px, py = 64, 88
    d.ellipse([px - 26, py - 44, px + 26, py + 8], fill=(*t["accent"], 255))
    d.polygon([(px - 18, py), (px + 18, py), (px, py + 44)],
              fill=(*t["accent"], 255))
    d.ellipse([px - 10, py - 30, px + 10, py - 10], fill=(255, 255, 255, 230))
    if p.get("route"):
        d.line([(px + 40, 118), (pw - 40, 70)], fill=(*t["accent"], 255),
               width=5)
        d.ellipse([pw - 50, 60, pw - 30, 80], fill=(*t["accent"], 255))
    d.text((px + 56, 66), value, font=f, fill=ink)
    return img, (90, H - 380)


def _bigpop(value, t, p):
    f = _font(t["font"], 116)
    text = _spaced(value.upper(), p.get("spacing", 0))
    while _measure(text, f) > W - 320 and f.size > 54:
        f = _font(t["font"], f.size - 8)
    tw = int(_measure(text, f))
    img = Image.new("RGBA", (tw + 90, f.size + 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fill = (*t["accent"], 255) if p.get("accent_text") else (*t["text"], 255)
    _shadow_text(d, (40, 34), text, f, fill, off=(6, 8))
    return img, ((W - tw - 90) // 2, 380)


def _quote(value, t, p):
    main, sub = _split_value(value)
    fkind = t["alt_font"] if p.get("font") == "alt" else t["font"]
    f1 = _font(fkind, 54)
    while _measure(f'"{main}"', f1) > 1400 and f1.size > 34:
        f1 = _font(fkind, f1.size - 4)
    tw = int(_measure(f'"{main}"', f1))
    pw, ph = tw + 190, 210
    img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if p.get("paper"):
        card = _paper(pw, ph - 10, t["paper"], seed=3)
        img.paste(card.rotate(random.Random(main).uniform(-1.5, 1.5),
                              expand=False), (0, 6))
        ink = (*t["paper_ink"], 255)
    else:
        _rr(ImageDraw.Draw(img), (0, 6, pw, ph - 6), 14,
            (*t["panel"], t["panel_alpha"]))
        ink = (*t["text"], 255)
    d = ImageDraw.Draw(img)
    fq = _font("serif", 130)
    d.text((28, -18), '"', font=fq, fill=(*t["accent"], 255))
    d.text((120, 66), f'"{main}"', font=f1, fill=ink)
    return img, ((W - pw) // 2, 330)


_LAYOUTS = {
    "pill": _pill, "strip": _strip, "band": _band, "fullscreen": _fullscreen,
    "panel": _panel, "papercard": _papercard, "newspaper": _newspaper,
    "timeline": _timeline, "bignum": _bignum, "lowerthird": _lowerthird,
    "tab": _tab, "stampbox": _stampbox, "tag": _tag, "pinned": _pinned,
    "bigpop": _bigpop, "quote": _quote,
}

# every variant name used by the packs -> (layout, params)
VARIANTS = {
    # date
    "corner_label": ("pill", {}), "black_screen": ("fullscreen", {}),
    "typewriter": ("strip", {"font": "alt"}), "newspaper": ("newspaper", {}),
    "paper_card": ("papercard", {}), "timeline_dot": ("timeline", {}),
    "stencil_card": ("stampbox", {"spacing": 3}), "map_pin": ("pinned", {}),
    # entry
    "dark_band_red_underline": ("band", {"underline": True}),
    "case_file_tab": ("tab", {}),
    "black_screen_title": ("fullscreen", {"rule": True}),
    "typewriter_reveal": ("strip", {"font": "alt"}),
    "serif_band_gold": ("band", {"underline": True}),
    "parchment_title": ("papercard", {"big": True}),
    "stencil_band": ("band", {"spacing": 4}),
    "map_bg_title": ("band", {"underline": True}),
    # source
    "corner_pill": ("pill", {"small": True, "dot": True}),
    "file_stamp": ("stampbox", {"rotate": -3}),
    "footer_strip": ("strip", {"small": True}),
    "archive_stamp": ("stampbox", {"rotate": 2}),
    "military_stamp": ("stampbox", {"rotate": -2, "spacing": 3}),
    # stat
    "dark_panel_red_top": ("panel", {"topbar": True}),
    "evidence_tag": ("tag", {}),
    "big_number_black": ("bignum", {}),
    "parchment_panel": ("panel", {"paper": True, "topbar": True}),
    "big_number_sepia": ("bignum", {}),
    "ledger_card": ("newspaper", {"small": True}),
    "ops_panel": ("panel", {"topbar": True}),
    "big_number_stencil": ("bignum", {"spacing": 3}),
    "casualty_ledger": ("newspaper", {"small": True}),
    # name
    "lower_third_red_bar": ("lowerthird", {}),
    "case_card": ("panel", {"small": True}),
    "serif_lower_third": ("lowerthird", {}),
    "portrait_card": ("panel", {"small": True}),
    "rank_lower_third": ("lowerthird", {"spacing": 2}),
    "dossier_card": ("panel", {"small": True}),
    # map
    "dark_map_pin": ("pinned", {}), "route_line": ("pinned", {"route": True}),
    "satellite_zoom": ("pinned", {}),
    "parchment_map_pin": ("pinned", {"paper": True}),
    "route_ink": ("pinned", {"route": True, "paper": True}),
    "old_map_zoom": ("pinned", {"paper": True}),
    "ops_map_pin": ("pinned", {}),
    "arrow_advance": ("pinned", {"route": True}),
    "front_line": ("pinned", {"route": True}),
    # text
    "big_pop_center": ("bigpop", {}),
    "typewriter_line": ("strip", {"font": "alt"}),
    "red_keyword": ("bigpop", {"accent_text": True}),
    "serif_center": ("bigpop", {}),
    "ink_reveal": ("bigpop", {}),
    "gold_keyword": ("bigpop", {"accent_text": True}),
    "stencil_pop": ("bigpop", {"spacing": 4}),
    "radio_ticker": ("strip", {"font": "alt", "small": True}),
    # quote
    "dark_quote_card": ("quote", {}),
    "typewriter_quote": ("quote", {"font": "alt"}),
    "paper_scrap": ("quote", {"paper": True}),
    "parchment_quote": ("quote", {"paper": True}),
    "serif_quote_card": ("quote", {}),
    "dispatch_card": ("quote", {"font": "alt"}),
    "stencil_quote": ("quote", {"spacing": 3}),
    # chapter
    "archive_photo_bg": ("fullscreen", {"rule": True}),
    "map_bg": ("fullscreen", {"rule": True}),
    # evidence
    "board_pin": ("tag", {"pin": True}), "file_photo": ("tag", {}),
    "ledger_pin": ("tag", {"pin": True}), "artifact_tag": ("tag", {}),
    "dossier_pin": ("tag", {"pin": True}), "ops_tag": ("tag", {}),
    # timeline
    "dot_advance": ("timeline", {}), "red_string": ("timeline", {"string": True}),
    "file_row": ("timeline", {}), "era_band": ("timeline", {}),
    "scroll_row": ("timeline", {}), "campaign_band": ("timeline", {}),
    # compare
    "split_screen": ("panel", {"split": True}),
    "side_cards": ("panel", {"split": True}),
    "twin_portraits": ("panel", {"split": True}),
    "force_cards": ("panel", {"split": True}),
    "default": ("pill", {}),
}


def render_card(kind: str, value: str, variant: str, theme: dict):
    """Render one card; returns (RGBA image, (x, y) anchor on 1920x1080)."""
    layout, params = VARIANTS.get(variant, VARIANTS["default"])
    value = (value or kind.title()).strip()
    if len(value) > 90:
        value = value[:88] + "…"
    return _LAYOUTS[layout](value, theme, dict(params))
