# SPEC 07 — Multi-language support

DocuStudio is language-aware end to end. One dropdown in the GUI
(`Language`) per video; everything else adapts automatically.

## Supported out of the box

All **Latin-script languages** work with zero setup — bundled fonts
cover accents/diacritics (proven in ProStudio):

English, Spanish, French, German, Italian, Portuguese, Polish,
Hungarian, Czech, Dutch, Romanian, and similar.

Non-Latin scripts (Hindi/Devanagari, Arabic, Chinese, …) work for
audio/alignment, but on-screen text needs a matching Unicode font via
`PS_FONT_SANS` / `PS_FONT_SERIF` / `PS_FONT_MONO` env vars — same
mechanism as ProStudio; the tool warns if the font can't render the
script.

## What the language setting controls

| Layer | Behavior |
|-------|----------|
| **VO alignment** | Whisper is multilingual (90+ languages) — the clean script in Spanish + Spanish VO align word-perfect the same way as English |
| **Script & tags** | Tag NAMES stay English (`[DATE: …]`, `[TEXT: …]`) so parsing never changes; tag VALUES and narration are in the video's language |
| **On-screen text / captions** | Rendered in the video language with the genre pack's fonts; per-language line-length limits (German words run long — text layout accounts for it) |
| **Date cards** | Localized month/format: `June 14, 2026` → `14 de junio de 2026` (es) → `14 juin 2026` (fr) → `2026. június 14.` (hu) |
| **Number/stat panels** | Locale separators: `1,234.5` vs `1.234,5` |
| **Chapter cards / built-in labels** | The tool's few generated words (e.g. "CHAPTER", archive labels like "ARCHIVE FOOTAGE") come from `presets/languages.json` — add a language by adding one JSON entry |
| **Spoken Line matching** | Whisper transcribes clips in their own language; a Spanish Spoken Line matches a Spanish clip |
| **Music / SFX / ambience** | Language-agnostic (instrumental-only rule in SPEC 04 exists partly for this) |

## Rules for the input files in another language

1. Clean script + narration lines in the Editing Help Script: fully in
   the target language, verbatim vs the VO (alignment anchor — same
   golden rule as always).
2. Bracket tag labels stay English; values in the target language:
   `[TEXT: MOTOR TODAVÍA CALIENTE]`, `[SOURCE: Informe policial de Ozark]`.
3. Visual Help File `Image Search` queries may mix languages — often
   English queries find more footage; the collector doesn't care.
4. The storyboard UI itself stays English; the content it previews is
   in the video's language.
