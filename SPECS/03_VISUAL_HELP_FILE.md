# SPEC 03 — Visual Help File (collector-compatible format + generation prompt)

The Visual Help File is written **for the Footage Collector (Tool #1)**
— it tells the collector what to download, scene by scene, into
`scene_<n>/` folders. DocuStudio reads the SAME file (no second file,
no reformatting) to know which asset belongs under which narration line.

The format below is the owner's existing real-world format (from the
essay workflow), kept as-is with three small optional upgrades marked
⭐ that raise clip accuracy.

---

## 1. File format

Plain text. A file header, then one block per **visual beat**:

```
TOPIC / CONTEXT ANCHOR: <topic + the specific episodes/events/sources this video covers>

BLOCK TITLE IN CAPS
 Script Cue (narration): "<exact narration lines this visual belongs to>"
 Visual / Exact Clip to Use: <SHOT NAME IN CAPS> — <what is happening
   in the shot> — about <source work/person> (<year>).
 Spoken Line: <optional: the line spoken INSIDE the clip>
 Clip Links: <video url>?t=<start seconds>   ⭐ optionally: (until mm:ss)
 Image Links: <direct image url(s)>
 Image Search: <query 1> | <query 2> | <query 3>
```

Real example (from the SpongeBob essay):

```
THE FLYER
 Script Cue (narration): "In one episode, a character puts up a flyer
 to recruit people for a marching band. …"
 Visual / Exact Clip to Use: BAND GEEKS FLYER SCENE — SPONGEBOB 2001.
 Bikini Bottom residents crowd around Squidward's recruiting flyer —
 about SpongeBob SquarePants "Band Geeks" (2001).
 Spoken Line: Looking to add fulfillment to your dull, dull life?
 Clip Links: https://youtu.be/J3gOVvWjOmY?t=45
 Image Search: SpongeBob Band Geeks flyer dull dull life | Squidward
 marching band flyer scene | Band Geeks recruitment poster SpongeBob
```

### Field rules

| Field | Required | Used by | Meaning |
|-------|----------|---------|---------|
| `TOPIC / CONTEXT ANCHOR` | once, top | both | grounds every search; prevents off-topic assets |
| Block title (CAPS line) | yes | both | becomes the scene folder label |
| `Script Cue (narration)` | yes | **DocuStudio** | the exact narration lines this visual belongs under — THE mapping key (see §2) |
| `Visual / Exact Clip to Use` | yes | both | what the shot shows + source + year (drives era treatment: archival vs modern) |
| `Spoken Line` | optional ⭐ | DocuStudio | dialogue heard inside the clip — tool transcribes the downloaded clip and cuts precisely around this line |
| `Clip Links` | optional | both | `?t=<sec>` = start point. ⭐ add `(until mm:ss)` for an end point; without it the tool auto-picks a clean out-point |
| `Image Links` | optional | both | direct image URLs |
| `Image Search` | recommended | collector | fallback queries, `\|`-separated, used when links fail or are missing |

Multiple `Clip Links` / `Image Links` per block are fine (one per line
or comma-separated). Field labels are case-insensitive and forgiving.

## 2. How DocuStudio maps blocks to scenes (no numbering needed)

You do NOT have to keep scene numbers in sync between this file and the
Editing Help Script. DocuStudio matches each block's **Script Cue text**
against the clean script (fuzzy match — quotes may be shortened with
`…`). Since the clean script is whisper-aligned to the voiceover, every
block automatically lands on its exact narration timestamps.

- One block may cover one scene, part of a scene, or span two scenes —
  all fine; the Script Cue decides.
- A block whose Script Cue can't be matched → listed by name in a
  validation error BEFORE any downloading, so you fix the quote once.
- Optional override: add a line `Scene: 12` inside a block to pin it
  manually.

## 3. Accuracy boosters (the ⭐ upgrades, all optional)

1. **End point** — `Clip Links: https://youtu.be/XXX?t=45 (until 1:10)`
   → the tool cuts exactly 0:45–1:10 instead of guessing the out-point.
2. **Spoken Line** — when present, the tool transcribes the clip's audio
   and centers the cut on that spoken line. This is the single best
   accuracy feature for dialogue clips.
3. **Year in "about … (year)"** — drives archival treatment (grain/B&W
   for old sources, clean for modern) per genre pack.

## 4. Ready-made LLM prompt (copy-paste)

Give this prompt + the **Editing Help Script** to the LLM/researcher:

```
You are a documentary footage researcher. Using the EDITING HELP SCRIPT
below, produce a VISUAL HELP FILE for a footage-collection tool.
Output plain text only, in exactly this block format:

TOPIC / CONTEXT ANCHOR: <one line: the topic plus the specific
episodes/events/works/people this video covers, with years>

<BLOCK TITLE IN CAPS — a short memorable name for this visual beat>
 Script Cue (narration): "<copy the exact narration lines this visual
 belongs to, word-for-word from the script; you may shorten the middle
 with … but never paraphrase>"
 Visual / Exact Clip to Use: <SHOT NAME IN CAPS> — <one or two lines
 describing exactly what should be on screen> — about <source work or
 person> (<year>).
 Spoken Line: <only if the clip contains a specific spoken/heard line;
 otherwise omit this field>
 Clip Links: <video url>?t=<start seconds> (until <mm:ss>)  ← include a
 real link with start time whenever you are confident; omit otherwise
 Image Links: <direct image urls, only if confident>
 Image Search: <3 alternative search queries separated by | >

RULES
1. Create one block for roughly every scene of the Editing Help Script.
   Scenes marked PACING: dense may get 2 blocks; consecutive tiny
   scenes with the same visual need may share 1 block.
2. Script Cue quotes must be copied verbatim from the narration —
   the editing tool matches them by text. Never reword.
3. Match era and place: archival visuals for historical narration; no
   modern stock under decades-old events. Name the source and year in
   every "about … (year)".
4. For scenes tagged [CENSOR], describe non-graphic angles.
5. Remember: [DATE]/[MAP]/[STAT]/[SOURCE] cards are auto-generated by
   the editor — your visuals are the pictures BEHIND those cards.
6. Every block must have Image Search queries even when links are
   given (they are the fallback if a link dies).

Now here is the Editing Help Script:
<PASTE EDITING HELP SCRIPT HERE>
```

## 5. Flow with the Footage Collector

1. This file → **Footage Collector** downloads/cuts everything into
   `scene_001/, scene_002/ …` folders (its existing behavior).
2. The SAME file + those folders → **DocuStudio**, which QCs assets,
   maps blocks to narration via Script Cues, and builds the storyboard.
3. Blocks whose downloads failed fall back to `Image Search` queries;
   still-empty blocks are ⚠-flagged on the storyboard for manual swap.
