# DocuStudio — Documentary Editing Brain

Turns **script + voiceover + assets** into a fully edited, genre-aware
documentary video (final MP4, 1080p or 4K, 16:9), in **any supported
language**, with a **storyboard approval step before render** and
per-scene re-render after.

> **This repo (`nischalshivam/DT`) is the home of the tool** — all
> specs, code, and docs live here. The earlier tools (Footage
> Collector, auto_editor, ProStudio) live in `nischalshivam/Claude`;
> DocuStudio reuses ProStudio's proven engine pieces (whisper
> word-sync, Ken Burns + drift, planner, QC, renderer).
>
> STATUS: design/spec phase — `SPECS/` is the foundation. **No
> Filmora/.wfpbundle export** (that approach failed and is dropped);
> output is a rendered MP4. The reviewable/editable artifact is our own
> **storyboard**, not a third-party project file.

## The user's inputs (per video)

| # | Input | What it is |
|---|-------|------------|
| 1 | Clean script | Word-for-word narration text (same words as the VO) |
| 2 | Editing Help Script | Clean script + scene breaks + bracket tags (`SPECS/02`) |
| 3 | Visual Help File | Collector-format blocks: Script Cue + links + queries (`SPECS/03`) — same file the Footage Collector uses |
| 4 | Voiceover audio | ONE full narration file (30 min – 2 hr) |
| 5 | Data file (optional) | Stats/facts used by `[STAT]` cards |
| 6 | Scene folders / assets | Footage Collector output + local files |
| 7 | Library folder | User's music/ambience/SFX collection (`SPECS/04`) |

Project settings: **Genre pack** (`SPECS/06`) · **Language**
(`SPECS/07` — Spanish/French/German/Polish/Hungarian/etc. out of the
box) · resolution 1080p/4K · toggles.

## Pipeline (7 stages)

1. **Parse** — read the input files into one project model; validate
   (Script Cue matching, narration drift checks) before any downloads.
2. **Acquire** — download/cut clips (yt-dlp, `?t=` starts, optional
   `(until …)` ends, Spoken-Line precision cutting), fetch images, QC
   every asset (reject black/blur/dupe/low-res), detect
   archival-vs-modern era for treatment.
3. **Align** — whisper word-level sync of clean script ↔ VO (any
   language) → every scene gets exact start/end times. Scene durations
   come from the narration, never from a retention timer.
4. **Plan** — the editing brain: per-scene shot plan from the genre
   grammar pack (visual order, dwell times, Ken Burns/holds,
   split-screens), tag events (date cards, texts, sources synced to
   the spoken word), curiosity devices on `[REVEAL]`, variation ranges
   so no two videos look templated.
5. **Graphics** — generate date cards, source labels, stat panels, map
   cards, lower-thirds, chapter cards, evidence-board frames in the
   pack's typography, localized to the video's language.
6. **Sound design** — 4 tracks: VO / music (mood curve per scene) /
   ambience / SFX stings, with smooth ducking and `[SILENCE]`/`[HOLD]`
   swells.
7. **Storyboard → Render** — storyboard opens in the browser for
   approval (`SPECS/05`); after approve, render final MP4 + quality
   report; any scene can be re-rendered alone afterwards.

## Pacing philosophy (owner's rule)

Documentaries are information-first. A 30–40 min video is ~80–120
scenes (avg scene 18–25 s), a 1–2 hr lore video ~150–250. A scene may
rotate 2–4 visuals internally, but cuts follow the story, not a timer.
Accuracy of clip-to-line matching beats speed of cutting.

## Genres (grammar packs)

history, war, machinery, farming, sports, science, nature/wildlife,
crime, lore (long-form). One engine + per-genre JSON packs — see
`SPECS/06_GENRE_PACKS.md`. Build order: history, war, crime first.

## Censorship

Anything tagged `[CENSOR]` gets blurred; the tool also auto-blurs
detected blood/gore regions by default (YouTube-policy safety). The
always-blur list is configurable in the UI.

## Spec index

| File | Contents |
|------|----------|
| `SPECS/01_INPUT_FILES.md` | the input files + how they relate + validation |
| `SPECS/02_EDITING_HELP_SCRIPT.md` | scene/tag format + LLM prompt to generate it |
| `SPECS/03_VISUAL_HELP_FILE.md` | collector-compatible visual format + LLM prompt |
| `SPECS/04_LIBRARY_STRUCTURE.md` | music/ambience/SFX folders + minimum counts |
| `SPECS/05_STORYBOARD_WORKFLOW.md` | review-before-render flow, per-scene re-render |
| `SPECS/06_GENRE_PACKS.md` | the 12 editing dimensions × 9 genres |
| `SPECS/07_LANGUAGES.md` | multi-language behavior |
| `SPECS/08_SHOT_PLANNER.md` | asset placement algorithm + copyright-safe clip rules (max 4–5 s per video shot) |
