# SPEC 09 — Human Rhythm & Anti-Template Engine

Owner's rule: output must NEVER feel like a slideshow, never have fixed
timings, and no two videos may share an obvious editing fingerprint.
This is not about dodging detection — it is about real editorial
variation, which is also exactly what makes edits feel human.

## 1. Dynamic shot duration (the #1 rule)

There is no global shot length anywhere in the engine. Every shot's
duration is sampled from a **purpose-based range**:

| Shot purpose | Range |
|---|---|
| hook montage beat | 0.8–2.0 s |
| action / fast cut | 1.2–2.8 s |
| standard b-roll | 3–5 s |
| emotional photo | 5–9 s |
| document proof (readable) | 6–10 s |
| map explanation | 7–12 s |
| quote card | reading time × 1.4 |
| suspense reveal | 3 s visual + ~1 s silence |
| ending reflection | 6–12 s |
| calm nature/farming wide | 6–15 s |

**Breath-cutting:** because we have word-level whisper timestamps, cut
points snap to the narrator's real breath gaps (inter-sentence silences
≥ 250 ms) or to emphasized words — never mid-word, never on a metronome.
A small share of cuts intentionally land just BEFORE a line ends
(tension) or a beat AFTER silence (weight).

**Anti-pattern guard:** never 3 consecutive shots within ±10 % of the
same duration; a rolling variance check re-samples offenders.

## 2. Motion library (stills must not all move the same way)

15 moves: push-in (slow/med), pull-out, pan L, pan R, diagonal drift,
**static hold**, handheld micro-drift, document scan (top→bottom), map
zoom, face-crop push, reveal crop, subtle tilt, rack-focus simulation,
split-screen compare, parallax-lite (fg/bg separation, optional).

Rules: 15–25 % of stills get NO motion (static holds read as human);
never the same move twice in a row; move fits purpose (document→scan,
map→zoom, face→push-in); framing follows rule-of-thirds via subject
detection (ProStudio `subjects`), so subjects are asymmetric, not
always centered.

## 3. Controlled variation, not randomness

Randomness looks cheap; variation must be coherent.
- Every graphic type ships **≥6 variants per genre**. Example — date
  card variants: black-screen, old-paper, map-pin, lower-third,
  typewriter, newspaper, timeline-dot, corner label.
- Intro openings (10 types), endings (12 types), chapter cards
  (9 types) — chosen by topic/mood, not dice.
- At plan time the tool makes ONE seeded "style draw" per video from
  the pack's ranges → consistent inside the video, different across
  videos.

## 4. Visual texture rotation

Texture classes: video clip, photo, document, map, timeline, quote
card, stat panel, newspaper, diagram, symbolic b-roll, screen
recording, pure graphics. Rules: max 3 of the same class back-to-back
(unless an intentional emotional sequence); macro-level texture change
every 60–90 s.

## 5. Transition budget

Per video: ~70 % straight cuts, ~15 % dissolves/fades, ~10 % genre
transitions, ~5 % specials. Never the same transition more than 3× in
a row. Serious topics: pack forbids flashy transitions entirely.

## 6. Format packs & mixing (the 20–30 formats)

The catalog = 9 genre packs × named substyles ≈ 30 formats:
- **crime:** netflix-dark, yt-investigative, evidence-board, courtroom,
  police-procedural, dark-mystery, high-retention-social
- **history/war:** archive-classic, war-room-map, royal-profile,
  minimal-archive-essay, cinematic-biography
- **sports:** comeback, analysis, magazine-profile
- **science/tech:** visual-explainer, space-cinematic, tech-timeline
- **business:** scam-investigation, startup-rise-fall
- **nature/farming:** wildlife-cinematic, rural-observational,
  environmental-impact
- **entertainment/gaming:** movie-timeline, music-journey, gaming-doc
- **general:** news-documentary, social-issue-human, travel-culture,
  long-form-serious, dark-explainer

**Mixing:** a video declares PRIMARY (~60 %) + SECONDARY (~25 %) +
ACCENT (~15 %); chapters/blocks may switch flavor (e.g., WW2 video =
archive-classic + war-room-map + news-doc accents).

## 7. Style fingerprint & memory (channel-level anti-sameness)

After every render the tool stores a fingerprint JSON: shot-duration
mean/variance, transition histogram, motion histogram, caption style,
card variants used, intro/ending types, music moods, texture ratios,
grade parameters.

At plan time it loads the channel's last N (default 10) fingerprints
and **biases the style draw away from recently used choices**. The
storyboard shows a similarity score; above ~70 % similarity with any
recent video it warns and suggests concrete swaps ("different intro
type, slower first act, alternate caption style"). UI: "avoid styles
used in last N projects".

## 8. Imperfection layer

Handheld micro-drift on some stills; music entries NOT aligned to every
scene boundary; ~30 % of reveals get silence instead of a bass hit;
pause lengths vary with emotion; text position varies within the
pack's allowed slots; J/L cuts (audio leads or trails the cut) reused
from ProStudio.

## 9. Slideshow Risk Detector (in the QC report)

Checks: stills-vs-video ratio, duration variance, motion diversity,
texture rotation, transition histogram, text density, audio mood
changes, breath-cut usage, per-scene editorial reasons present.
Output: **Slideshow Risk: LOW / MEDIUM / HIGH** + reasons + one-click
"re-plan with more variation".

## 10. Hard rules (the never-list)

no fixed image duration · no transition >3× in a row · no texture >3×
in a row · no motion on every still · no bass hit on every reveal · no
text on every line · no same intro template twice in a row · no
generic stock under specific facts · no flashy transitions on serious
topics · no metronome rhythm anywhere.

## Editorial reasons (human value)

Every storyboard card shows WHY the planner chose what it chose
("held 9 s — victim introduction", "silence — heavy line", "map —
location may confuse"). The user can also write per-scene notes that
override the planner, and lock scenes so regeneration never touches
them.
