# SPEC 02 — Editing Help Script (format + generation prompt)

The Editing Help Script is the clean narration script **annotated** with
scene breaks and bracket tags. It tells the tool WHAT matters on every
line: dates, on-screen texts, sources, holds, reveals, censoring.

**GOLDEN RULE:** the narration text stays word-for-word identical to the
clean script (and therefore to the voiceover). Whisper alignment depends
on it. Nothing is rewritten — only structure and tags are ADDED.

**SPELLING RULE (learned from the Kinkel test files):** the narration
may be a raw transcript full of garbled names ("Kiplan Kingl",
"Thirsten") — leave those AS-IS in narration lines. But every TAG VALUE
that renders on screen (`[TEXT]`, `[NAME]`, `[QUOTE]`, `[DATE]`,
`[MAP]`, `[STAT]`, `[SOURCE]`, `[ENTRY]`) must use the **correct
real-world spelling**, and one person must have exactly ONE canonical
spelling across the whole file (never "Al Waran" in one scene and
"Al Wan" in another).

---

## 1. File format

Plain text (`.txt`). One block per scene:

```
=== SCENE 12 ===
MOOD: tension
PACING: normal

On the evening of July 31st, 1999, Tracy left her home in Dothan.
[DATE: July 31, 1999] [MAP: Dothan, Alabama]
Her black Mazda was found on Herring Avenue, the engine still warm.
[TEXT: ENGINE STILL WARM]
Police found no sign of struggle. [SOURCE: Ozark Police Report] [HOLD]
```

### Scene header
- `=== SCENE <n> ===` — sequential numbers.
- `MOOD:` one of: `neutral, curious, tension, dark, tragic, emotional,
  hopeful, triumphant, action, epic, calm, nostalgic, mystery`
  → drives music selection + color grade.
- `PACING:` one of:
  - `hold` — heavy moment; long dwells, slow zoom, room to breathe
  - `normal` — default documentary rhythm
  - `dense` — information-heavy; visuals rotate faster inside the scene

### Tags (inline, placed right AFTER the line they belong to)

| Tag | Meaning | Tool behavior |
|-----|---------|---------------|
| `[ENTRY: title]` | List/iceberg-format videos: a new entry begins ("Confession", "Prozac") | Consistent small entry-title card in the genre's style |
| `[TEXT: ...]` | Shocking phrase to show on screen (max ~6 words) | Kinetic text synced to the spoken word |
| `[DATE: ...]` | A date mentioned | Genre-styled date card |
| `[MAP: place]` | Location change | Map card with pin/zoom |
| `[STAT: value — label]` | A number that DESERVES a panel | Stat panel (uses data file if present) |
| `[SOURCE: ...]` | Citable origin of a specific fact | Small credibility label (corner) |
| `[NAME: person — role]` | Person introduced (first appearance) | Lower-third when their photo shows |
| `[QUOTE: ...]` | Spoken/written quote | Quote card with attribution |
| `[ARCHIVE AUDIO: what plays]` | Original tape/recording plays here (confession tape, 911 call, interview) | Archival clip / waveform treatment, music ducks out, narration pauses |
| `[CHAPTER: title]` | Act/chapter break (long videos) | Full-screen chapter card + music reset |
| `[HOLD]` | Let this moment sit | 8–15 s dwell, slow zoom, minimal cuts |
| `[SILENCE]` | Beat of quiet after the line | Music dips/stops 0.8–1.5 s |
| `[REVEAL]` | Twist/answer lands here | Build-up + sting + hold (silhouette/blur-reveal allowed) |
| `[CENSOR: what]` | Sensitive imagery in this scene | Blur that region/asset |
| `[EVIDENCE: item]` | Crime genre: pin to evidence board | Item appears on the board graphic |
| `[COMPARE: A vs B]` | Two things contrasted | Split-screen / comparison panel |
| `[TIMELINE: event]` | Event on a running timeline | Timeline graphic advances |

Labels are case-insensitive and forgiving. Unknown tags are logged,
never fatal — but transcript artifacts like `[clears throat]` /
`[laughter]` must NOT appear (see Transcript hygiene).

### Density rules (what makes it look pro, not cheap)
- `[ENTRY]` — every entry title in list/iceberg-format videos; this is
  what those titles are FOR (don't use `[TEXT]` for them).
- `[TEXT]` — max 1 per scene, only ~1 in every 3–4 scenes, and only for
  genuinely shocking phrases/numbers. Never tag the same words with
  both `[QUOTE]` and `[TEXT]` — `[QUOTE]` wins.
- `[SOURCE]` — only for SPECIFIC citable facts: court records, police
  reports, named documents, statistics, quotes. **Never** on the
  narrator's own analysis/commentary ("this entry matters because…").
  Max 2 per scene; consecutive lines from the same source → tag once.
- `[STAT]` — only numbers worth a screen panel (casualties, money,
  sentence lengths, big quantities). Ages and casual time-spans
  mentioned in passing do NOT get panels.
- `[HOLD]` — roughly 1 per 8–10 scenes, only on genuinely heavy lines.
- `[DATE]` / `[MAP]` — every date mention and location change.
- `[CHAPTER]` — only for videos > 25 min; every 8–15 min of runtime.

### Transcript hygiene

If the clean script is a raw transcript it may contain artifacts:
`>>` speaker markers, `[clears throat]`, `[laughter]`, glued-on entry
titles. Rules:
- Tape-dialogue lines (`>>` exchanges from a confession/interview
  recording) stay verbatim but the scene gets `[ARCHIVE AUDIO: …]` so
  the tool treats them as tape playback, not narration.
- Square-bracket noise annotations are transcript artifacts — the
  loader flags them; they should be removed from the clean script
  because nobody actually speaks them.

---

## 2. Ready-made LLM prompt (copy-paste)

Give this prompt + your clean script to any LLM to generate the file:

```
You are a professional documentary edit-planner. Convert the clean
narration script below into an EDITING HELP SCRIPT for an automated
editing tool. Follow every rule exactly.

GOLDEN RULE: never rewrite, shorten, reorder, or "improve" the
narration text. Copy every sentence word-for-word — even obvious
transcription errors stay, because the text must match the voiceover.

SPELLING RULE: tag values are the opposite — they render ON SCREEN, so
inside square-bracket tags always use the correct real-world spelling
of names/places (research them from context), and use exactly ONE
canonical spelling per person across the entire file.

STEP 1 — SPLIT INTO SCENES
- A scene = one story unit: one event, one idea, one location, or one
  step of the argument.
- Typical scene = 2–6 narration sentences (~15–30 seconds of speech).
- Target: a 30–40 min script → 80–120 scenes; a 1–2 hr script →
  150–250 scenes. Do NOT over-fragment.

STEP 2 — SCENE HEADER (every scene)
=== SCENE <n> ===
MOOD: one of [neutral, curious, tension, dark, tragic, emotional,
hopeful, triumphant, action, epic, calm, nostalgic, mystery]
PACING: one of [hold, normal, dense]
(blank line, then the scene's narration lines)

STEP 3 — TAGS (place inline, immediately after the line they refer to)
[ENTRY: title]  in list/iceberg-format videos, every time a new entry
               begins ("Confession", "Prozac", "His sentence") — use
               this for entry titles, NOT [TEXT].
[TEXT: ...]    on-screen words, max 6 words — only genuinely shocking
               phrases or numbers. Max 1 per scene, only ~1 in every
               3–4 scenes. Never duplicate a [QUOTE] as [TEXT].
[DATE: ...]    every explicit date mentioned.
[MAP: place]   every location change.
[STAT: value — label]   only numbers that deserve an on-screen panel
               (casualties, money, sentence length, big quantities).
               NOT ages or casual time-spans mentioned in passing.
[SOURCE: ...]  only specific citable facts: court records, police
               reports, named documents, statistics, quotes. NEVER on
               the narrator's own analysis or commentary. Max 2 per
               scene; consecutive lines from one source → tag once.
[NAME: person — role]   first time a person is introduced; correct
               spelling; one canonical spelling per person.
[QUOTE: ...]   direct quotes.
[ARCHIVE AUDIO: what plays]   when the video should play an original
               recording (confession tape, 911 call, interview) —
               including any >> speaker-marker dialogue lines.
[CHAPTER: title]   act breaks, only if script is >25 min; every
               8–15 minutes of runtime; short dramatic titles.
[HOLD]         after genuinely heavy lines. ~1 per 8–10 scenes max.
[SILENCE]      after a shocking reveal line where quiet hits harder.
[REVEAL]       on the line where a mystery/twist is answered.
[CENSOR: what] scenes that will show blood, bodies, graphic injury.
[EVIDENCE: item]   (crime only) items that belong on an evidence board.
[COMPARE: A vs B]  when two things are explicitly contrasted.
[TIMELINE: event]  when events form a running chronology.

NEVER invent other bracket annotations. Transcript noise like
[clears throat] or [laughter] must not appear in your output narration
— list any you removed at the very end under "CLEANUP NOTES:".

OUTPUT: plain text only, exactly in the format of this example:

=== SCENE 12 ===
MOOD: tension
PACING: normal

On the evening of July 31st, 1999, Tracy left her home in Dothan.
[DATE: July 31, 1999] [MAP: Dothan, Alabama]
Her black Mazda was found on Herring Avenue, the engine still warm.
[TEXT: ENGINE STILL WARM]
Police found no sign of struggle. [SOURCE: Ozark Police Report] [HOLD]

Now here is the clean script:
<PASTE CLEAN SCRIPT HERE>
```
