# SPEC 10 — Asset Cleanup (burned-in captions / logos) & Output QA

## Part A — Dirty source assets (owner's problem statement)

The Footage Collector sometimes downloads YouTube clips that carry
**burned-in captions** or a **channel logo/watermark**. Untreated,
these scream "stolen clip" and break immersion.

### A1. Detection (at QC stage, before planning)

Sample 5–8 frames spread across every downloaded clip:
1. **Caption detection** — text-region detection (OCR pass) on the
   lower third; the same region showing changing text across frames =
   burned-in captions. Also check top band (some channels caption at
   top).
2. **Logo/watermark detection** — pixel-stable region across sampled
   frames in a corner (high similarity where the rest of the frame
   changes) = static logo/bug.
3. Result stored per asset: `captions: bottom_band 12%`,
   `logo: top_right 8%x6%`, or `clean`.

### A2. Treatment ladder (in order of preference)

1. **Crop-out (default, usually free).** We already punch in 4–12 %
   on every clip (SPEC 08 transform rule). If the caption band is in
   the bottom ~15 % or the logo sits in a corner, the planner raises
   the punch-in and shifts the crop window AWAY from the dirty region
   — subject detection keeps the framing sensible. A 12 % bottom
   caption band disappears inside a 115 % punch-in reframed upward.
2. **Canvas framing.** In framed-canvas genres (history paper frame,
   sports editorial panel) the frame mask can simply cut the dirty
   edge off — the crop is part of the design.
3. **`delogo` patch** (static corner logos only): ffmpeg delogo /
   small blur patch over the logo box. Used when cropping would cut
   the subject.
4. **Graphic cover.** Place a genre element (source label, small card)
   over the dirty corner — only when it doesn't look forced.
5. **Reject.** Captions across the middle, huge center watermarks, or
   text over the subject → asset rejected, fallback search kicks in,
   scene ⚠-flagged on the storyboard.

### A3. Prevention (collector side)

When the collector has multiple candidate results for a search query,
it runs the same detection on candidates BEFORE committing the
download and prefers clean sources. Setting: `allow news station bugs`
(ON by default — a broadcaster bug on archival news often reads as
authentic; channel logos of random YouTubers never do).

## Part B — Output QA standards (from sample feedback)

1. **Loudness normalization** — final mix normalized to
   **-14 LUFS integrated** (YouTube standard; configurable -16…-12),
   true peak ≤ -1 dBTP, VO-vs-music ducking depth checked. The style
   samples measured -31…-37 LUFS: placeholder audio, but the renderer
   gets a mandatory `loudnorm` pass so this can never ship.
2. **Text readability checker** — every generated graphic is validated:
   minimum font size relative to 1080p (mobile-readable), on-screen
   time ≥ reading time × 1.3, contrast ratio vs the frame behind it
   (auto-add scrim/shadow if low), safe margins.
3. **Label-vs-topic sanity warning** — if a burned-in or generated
   label conflicts with the video's era/topic keywords (e.g. a modern
   spec label inside a 1911 history piece), the storyboard flags it
   for review. Best-effort, warning-only.
4. **Project isolation (hard rule)** — the planner may ONLY use assets
   from THIS project's scene folders + explicitly added files. There
   is no global asset pool shared between projects, so cross-story
   contamination is impossible by construction.
