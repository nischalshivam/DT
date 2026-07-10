# SPEC 01 — Input files overview

Per video, DocuStudio takes:

| # | File | Format | Spec |
|---|------|--------|------|
| 1 | Clean script | `.txt`, word-for-word same as the voiceover | — |
| 2 | Editing Help Script | annotated script: scenes + tags | `02_EDITING_HELP_SCRIPT.md` |
| 3 | Visual Help File | collector-format blocks: Script Cue + clip/image links + search queries | `03_VISUAL_HELP_FILE.md` |
| 4 | Voiceover | ONE audio file for the whole video (30 min – 2 hr), any supported language | — |
| 5 | Data file (optional) | `.txt`/`.csv` of stats & facts | below |
| 6 | Assets/scene folders | Footage Collector output (`scene_001/ …`) + any local files | — |

Plus two project settings: **Genre pack** and **Language** (`07_LANGUAGES.md`).

## How they relate

- The **clean script** is the alignment anchor: whisper maps it to the
  VO so every line gets a timestamp. It must match the narration
  exactly — that is why the Editing Help Script never rewrites lines.
- The **Editing Help Script** defines scene boundaries, moods, pacing
  and tag events.
- The **Visual Help File** is the SAME file the Footage Collector
  consumes. DocuStudio maps each of its blocks to scenes by
  **fuzzy-matching the block's `Script Cue` text against the clean
  script** — no scene-number bookkeeping between files.

## Validation at load (before any downloading/rendering)

1. Every Editing Help Script narration line must exist verbatim in the
   clean script (drift → error listing the exact lines).
2. Every Visual Help File block's Script Cue must match somewhere in
   the clean script (unmatched → error listing block titles).
3. Scenes with no visual coverage from any block → ⚠ storyboard flag
   (not an error — fallback search may fill them).
4. Language setting vs script: quick script-vs-font render check; warns
   if the font can't display the text.

## Data file (optional)

Plain lines of `label = value | source` used to auto-fill `[STAT]`
cards and comparison panels:

```
UK violent crime per 100k = 2034 | ONS 2019
US violent crime per 100k = 466 | FBI UCR 2019
Handguns banned in UK = 1997 | Firearms (Amendment) Act
```

If a `[STAT]` tag matches a label here, the card shows the exact value
+ a source footer; otherwise the tag's own text is used as-is.

## How to generate the data file (LLM prompt)

Give this prompt + your clean script to any LLM (same workflow as the
other two files):

```
You are a documentary fact-checker. From the narration script below,
extract every statistic, count, money amount, sentence length, or
measurable claim that could appear on an on-screen stat card. Output
one line per fact in exactly this format:

<short label> = <exact value> | <most credible source name or type>

RULES
1. Labels under 8 words, corrected real-world spellings.
2. Use the value the script states; if it looks factually wrong,
   prefix the line with "CHECK:" so a human verifies it.
3. Do not invent numbers the script never implies.
4. Plain text only, no headers, no commentary.

Now here is the clean script:
<PASTE CLEAN SCRIPT HERE>
```

The editor matches `[STAT]` tags against these labels; matched cards
show the exact value + a small source footer. Unmatched tags fall back
to the tag's own text. The whole file is optional.
