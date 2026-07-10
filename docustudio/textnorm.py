"""Text normalization shared by all matching (quotes/dashes/case-proof)."""
import re

_TRANS = str.maketrans({
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "—": "-", "–": "-", "…": "...",
})


def normalize_words(s: str) -> str:
    """Lowercase word stream: curly quotes folded, punctuation dropped."""
    s = s.translate(_TRANS).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def first_words(s: str, n: int) -> str:
    return " ".join(normalize_words(s).split()[:n])


def last_words(s: str, n: int) -> str:
    return " ".join(normalize_words(s).split()[-n:])
