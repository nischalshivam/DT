# SPEC 11 — Controls & Responsibilities (the contract)

Three lists, confirmed with the owner: what the USER PROVIDES, what the
USER CONTROLS manually, and what the TOOL DECIDES automatically.

---

## A. What the user provides

### Once (setup)
| # | Item | Notes |
|---|------|-------|
| 1 | Library folder | music/ambience/sfx per SPEC 04 — drop files in folders |
| 2 | Output folder | where finished videos + reports land |
| 3 | Channel profile(s) | name per channel — fingerprint memory is per-channel |
| 4 | (later) Brand kit | intro/outro card, logo, fonts, colors — final stage |

### Per video
| # | Item | Notes |
|---|------|-------|
| 1 | Clean script (.txt) | word-for-word same as the VO |
| 2 | Editing Help Script (.txt) | generated with the SPEC 02 prompt |
| 3 | Visual Help File (.txt) | generated with the SPEC 03 prompt; same file the Collector uses |
| 4 | Voiceover audio | ONE file, any supported language |
| 5 | Scene folders / assets | Footage Collector output + any local files |
| 6 | Data file (optional) | stats for `[STAT]` cards |

---

## B. Manual controls (the user's dashboard)

### Project setup screen (per video)
- File pickers for the 6 inputs above
- **Genre pack** + substyle + optional format mixing
  (PRIMARY % / SECONDARY % / ACCENT %)
- **Language** dropdown
- **Resolution** 1080p / 4K
- **Pacing slider**: Calm cinematic ←→ Dense retention
- **Retention intensity**: Netflix / YouTube / Social
- **Music intensity** + **SFX intensity** + **silence aggressiveness** sliders
- **Toggles** (ON/OFF): burned-in captions, on-screen `[TEXT]`s,
  credibility cards (date/source/stat/map), evidence board, archival
  treatment, censor auto-blur, curiosity devices (silhouette/reveals),
  ambience layer
- **Variation controls**: "avoid styles from last N projects" (default
  10), style-seed 🔀 reroll button
- **Review mode**: Storyboard-approve (default) / Auto-approve
- **Queue**: add up to 15 videos, order, per-video review mode

### Storyboard screen (per scene card)
- Reorder visuals (drag) · Replace visual (pool / paste link+timestamp)
- **Add own file** from PC (drag-drop)
- Trim/retime a visual · Edit any on-screen text
- Toggle any chip (date card, source label, sting, silence…)
- Change scene MOOD / PACING → that scene re-plans
- Draw/confirm censor blur regions
- "Re-plan this scene" (new variation) · **Lock scene** (regeneration
  never touches it)
- Filter: show ⚠ flagged scenes only
- Approve & Render

### After render
- Watch + **per-scene re-render** (minutes, not hours)
- Quality report review (pacing graph, coverage, slideshow risk,
  loudness, similarity-to-previous score)
- Reopen any old project's storyboard anytime

---

## C. Automatic (the tool decides, background)

**Parse/validate:** all three files cross-checked, Script Cue → scene
mapping, drift/coverage/tag-hygiene report — before anything downloads.

**Acquire:** yt-dlp downloads, `?t=`/`(until)` cutting, Spoken-Line
precision cuts, image fetch, QC reject (black/blur/dupe/low-res),
**burned-in caption/logo detection + crop-out/delogo**, era detection
(archival vs modern treatment).

**Align:** whisper word-level VO sync (any language) → real scene/line
timestamps, breath-gap detection.

**Plan (the brain):** shots per scene, **every duration sampled (never
fixed)**, cut points snapped to breath gaps, motion per still (15
moves, no repeats, some static), texture rotation, video-clip 4.5 s cap
+ source spacing, tag events timed to the spoken word, curiosity
devices on `[REVEAL]`, transition budget (70/15/10/5), editorial reason
written for every choice.

**Graphics:** every card generated in the pack's typography, variant
chosen per video (6-8 per card type), localized (dates/numbers),
readability-checked (size/contrast/on-screen time).

**Sound:** music picked from the library by mood curve, ambience bed,
SFX stings, smooth ducking, `[SILENCE]`/`[HOLD]` swells, ~30 % of
reveals get silence instead of a hit, final **-14 LUFS loudness
normalize**.

**Anti-template:** style draw seeded per video, fingerprint saved after
render, next video biased away from last N fingerprints, slideshow-risk
detector with auto-re-plan.

**Safety:** `[CENSOR]` + auto blood/gore blur, project isolation (only
this project's assets), label-vs-topic sanity warnings.
