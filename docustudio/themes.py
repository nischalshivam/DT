"""Per-pack visual themes + font resolution for the Graphics Factory."""
import os

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FONT_DIRS = [
    os.path.join(_HERE, "assets", "fonts"),
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
]
_FONT_FILES = {
    "sans": ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
    "serif": ["DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf"],
    "mono": ["DejaVuSansMono-Bold.ttf", "LiberationMono-Bold.ttf"],
}


def font_path(kind: str) -> str:
    for name in _FONT_FILES.get(kind, _FONT_FILES["sans"]):
        for d in _FONT_DIRS:
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
    raise FileNotFoundError(f"no font found for {kind!r}")


# color tuples are RGB; alpha applied by layouts where needed
THEMES = {
    "crime": {
        "panel": (14, 14, 18), "panel_alpha": 228,
        "accent": (196, 30, 44),
        "text": (245, 245, 245), "muted": (198, 198, 205),
        "paper": (230, 224, 208), "paper_ink": (28, 24, 20),
        "font": "sans", "alt_font": "mono", "letterspace": 0,
    },
    "history": {
        "panel": (38, 30, 19), "panel_alpha": 230,
        "accent": (158, 116, 44),
        "text": (240, 231, 210), "muted": (208, 197, 174),
        "paper": (226, 214, 190), "paper_ink": (46, 36, 22),
        "font": "serif", "alt_font": "serif", "letterspace": 0,
    },
    "war": {
        "panel": (18, 22, 24), "panel_alpha": 232,
        "accent": (110, 128, 72),
        "text": (235, 235, 228), "muted": (192, 196, 186),
        "paper": (222, 216, 200), "paper_ink": (32, 34, 28),
        "font": "sans", "alt_font": "mono", "letterspace": 3,
    },
}


def theme_for(pack_name: str) -> dict:
    return THEMES.get(pack_name, THEMES["crime"])
