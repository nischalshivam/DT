"""Project model: what the parsers produce and the planner consumes."""
from dataclasses import dataclass, field


MOODS = {"neutral", "curious", "tension", "dark", "tragic", "emotional",
         "hopeful", "triumphant", "action", "epic", "calm", "nostalgic",
         "mystery"}
PACINGS = {"hold", "normal", "dense"}

# canonical tag kinds (labels normalized to A-Z only)
KNOWN_TAGS = {"ENTRY", "TEXT", "DATE", "MAP", "STAT", "SOURCE", "NAME",
              "QUOTE", "ARCHIVEAUDIO", "CHAPTER", "HOLD", "SILENCE",
              "REVEAL", "CENSOR", "EVIDENCE", "COMPARE", "TIMELINE"}
BARE_TAGS = {"HOLD", "SILENCE", "REVEAL"}


@dataclass
class Tag:
    kind: str          # canonical label or "UNKNOWN"
    value: str         # text after ':' ('' for bare tags)
    raw: str           # original bracket content


@dataclass
class Line:
    text: str          # narration text with tags stripped
    tags: list = field(default_factory=list)
    is_tape: bool = False       # '>>' speaker-marker dialogue line
    # matching results
    offset: int = -1            # char offset in normalized clean script
    matched: bool = False
    fuzzy: bool = False


@dataclass
class Scene:
    num: int
    mood: str = ""
    pacing: str = ""
    lines: list = field(default_factory=list)
    # derived
    start_off: int = -1
    end_off: int = -1
    word_count: int = 0
    est_duration: float = 0.0   # seconds, words/2.55 until real VO align

    def all_tags(self):
        for ln in self.lines:
            yield from ln.tags


@dataclass
class ClipLink:
    url: str
    video_id: str = ""
    start: float | None = None   # seconds
    end: float | None = None
    was_markdown: bool = False


@dataclass
class VisualBlock:
    title: str
    cue: str = ""
    visual: str = ""
    spoken_line: str = ""
    clips: list = field(default_factory=list)
    images: list = field(default_factory=list)      # direct urls / LOCAL:
    searches: list = field(default_factory=list)
    note: str = ""
    scene_pin: int | None = None   # explicit "Scene: N" override
    # matching results
    cue_off: int = -1
    cue_end_off: int = -1
    start_scene: int | None = None
    end_scene: int | None = None
    cue_matched: bool = False


@dataclass
class Project:
    clean_text: str = ""
    clean_norm: str = ""
    scenes: list = field(default_factory=list)
    blocks: list = field(default_factory=list)
    topic_anchor: str = ""
