# SPEC 11 — Controls & Responsibilities (CONFIRMED with owner)

Three lists: what the USER PROVIDES, what the USER CONTROLS manually,
and what the TOOL DECIDES automatically. Updated after the owner's
line-by-line review — decisions marked ✅.

---

## A. What the user provides

### Once (setup) — only 2 things
| # | Item | Notes |
|---|------|-------|
| 1 | Library folder ✅ | music/ambience/sfx per SPEC 04 — owner will supply |
| 2 | Output folder ✅ | just the folder on the PC where finished videos land — every project gets `<OutputFolder>/<ProjectName>/` containing final MP4 + quality report + storyboard file (reopenable). Same concept as ProStudio's output folder. |

~~Channel name at setup~~ — ✅ REMOVED from setup per owner. Channels
are now an OPTIONAL dropdown on the project screen ("Default" if none,
"+ New channel" inline). Channel profile = fingerprint memory group +
(later) **channel branding**: small logo watermark top-right corner
(size/opacity settings), intro/outro cards, fonts — all per channel,
added in the branding stage.

Brand kit — ✅ later stage, as in-tool options (each channel's
intro/outro/logo differs).

### Per video
| # | Item | Status |
|---|------|--------|
| 1 | Clean script (.txt) | ✅ confirmed |
| 2 | Editing Help Script | ✅ confirmed |
| 3 | Visual Help File | ✅ confirmed |
| 4 | Voiceover audio | ✅ confirmed |
| 5 | Scene folders / assets | ✅ confirmed |
| 6 | Data file — **optional** | explained: a plain text list of exact facts/figures (`UK violent crime per 100k = 2034 \| ONS 2019`). When a `[STAT]` tag matches a label, the stat card shows the exact number + source footer. If absent, the tool uses whatever number the narration says. Skippable — most videos won't need it. |

---

## B. Manual controls (the user's dashboard)

### 🤖 MASTER AUTO MODE ✅ (owner request)
One switch at the top: **Auto**. When ON, the tool reads the script +
visual file and chooses EVERYTHING itself — genre pack, substyle,
format mixing, pacing, retention intensity, music/SFX levels — and the
storyboard shows *what it chose and why* ("detected: true-crime,
1998-era archival topic → crime/yt-investigative, calm-investigative
pacing"). The user can still override anything afterwards. Every
individual control below also has its own `Auto` position.

### Project setup screen (per video)
- File pickers for the 6 inputs above
- **Channel** (optional dropdown, "+ New channel")
- **Genre pack** — the documentary's main category (crime, history,
  war…). Sets the whole editing language: colors, fonts, pacing
  ranges, card styles, music moods. `Auto` = detect from script.
- **Substyle** — the flavor inside a genre (crime → netflix-dark /
  yt-investigative / courtroom…). `Auto` available.
- **Format mixing** — one video can blend styles:
  PRIMARY ~60 % (base look) + SECONDARY ~25 % (some chapters/scenes) +
  ACCENT ~15 % (special moments). Example: WW2 video = history-archive
  base + war-room maps in battle scenes + news-doc accents on evidence.
  `Auto` available (and Auto may choose "no mixing").
- **Language** — dropdown; ✅ default `Auto`: whisper detects the VO
  language and the script text confirms it; mismatch → warning. Manual
  selection always wins.
- **Resolution** — ✅ default **1080p**; 4K selectable.
- **Pacing** — ✅ `Auto` (default): tool decides per scene from the
  MOOD/PACING tags + genre + script density. Manual slider
  (Calm ↔ Dense) overrides globally.
- **Retention intensity** — ✅ `Auto` (default) / Netflix / YouTube /
  Social.
- **Music / SFX / Silence sliders** ✅
- **8 toggles** ✅ (captions, on-screen texts, credibility cards,
  evidence board, archival treatment, censor auto-blur, curiosity
  devices, ambience)
- **Variation controls** ✅ ("avoid styles from last N projects" +
  seed 🔀 reroll)
- **Review mode** ✅ Storyboard-approve (default) / Auto-approve
- **Queue** — explained: the overnight batch system (same idea as
  ProStudio). Line up multiple videos (up to 15), each with its own
  settings; the tool processes them one after another. Storyboard-mode
  videos pause at their storyboard, auto-approve videos render
  straight through. Start it at night, outputs ready by morning.

### Storyboard screen (per scene card)
- Reorder visuals (drag) · Replace visual (pool / paste link+timestamp)
- **Add own file** from PC (drag-drop)
- Trim/retime a visual · Edit any on-screen text
- Toggle any chip (date card, source label, sting, silence…)
- Change scene MOOD / PACING → that scene re-plans
- **Manual blur** ✅ (owner request, clarified): draw a box on any
  thumbnail — face, logo, blood, text, anything — choose blur/pixelate
  strength and the time range; it renders into that scene. This is on
  top of the automatic `[CENSOR]`/gore blur.
- "Re-plan this scene" (new variation) · **Lock scene**
- Filter: show ⚠ flagged scenes only
- Approve & Render

### After render
- Watch + **per-scene re-render** (minutes, not hours)
- Quality report (pacing graph, coverage, slideshow risk, loudness,
  similarity-to-previous score)
- Reopen any old project's storyboard anytime

---

## C. Automatic (the tool decides, background)

**Parse/validate:** all three files cross-checked, Script Cue → scene
mapping, drift/coverage/tag-hygiene report — before anything downloads.

**Auto-detection (new, owner request):** genre/substyle/mixing from
script+visual-file content; language from VO+script; pacing profile
and retention intensity from tags+genre — all shown with reasons on
the storyboard when Auto is on.

**Acquire:** yt-dlp downloads, `?t=`/`(until)` cutting, Spoken-Line
precision cuts, image fetch, QC reject (black/blur/dupe/low-res),
burned-in caption/logo detection + crop-out/delogo, era detection.

**Align:** whisper word-level VO sync → real scene/line timestamps,
breath-gap detection.

**Plan:** shots per scene, every duration sampled (never fixed), cut
points snapped to breath gaps, motion per still (no repeats, some
static), texture rotation, video-clip 4.5 s cap + source spacing, tag
events timed to the spoken word, curiosity devices on `[REVEAL]`,
transition budget (70/15/10/5), editorial reason for every choice.

**Graphics:** cards in the pack's typography, variant rotation per
video, localized dates/numbers, readability-checked.

**Sound:** music by mood curve, ambience bed, SFX stings, smooth
ducking, `[SILENCE]`/`[HOLD]` swells, ~30 % silent reveals, final
-14 LUFS loudness normalize.

**Anti-template:** seeded style draw, fingerprint memory per channel,
bias away from last N projects, slideshow-risk detector.

**Safety:** `[CENSOR]` + auto blood/gore blur + manual blur regions,
project isolation, label-vs-topic sanity warnings.
