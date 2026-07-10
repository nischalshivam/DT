# SPEC 08 — Shot Planner: how assets get placed on the timeline

This is the core of the editing brain: how scene-wise collected data
(clips/images) actually lands under the right narration words, and what
the viewer sees. Also encodes the **copyright-safety rules** (owner's
policy).

## 0. Copyright-safety rules (hard constraints)

1. **Video clips: max 4–5 seconds on screen per shot** (default 4.5 s,
   configurable). Never longer, from ANY source video, at any one time.
2. A long downloaded range (e.g. 80 s of news footage) is a *quarry*,
   not a shot — the planner cuts multiple separate ≤5 s windows out of
   it and never plays them back-to-back.
3. Same source video never appears in two consecutive shots; reuse
   requires a different time-window and at least one other visual in
   between.
4. **Every clip is transformed**: slight punch-in (104–112 %), genre
   grade, grain/canvas/frame treatment — never raw full-frame pixels.
5. Clip audio is muted by default (VO + music on top). Exception:
   `[ARCHIVE AUDIO]` moments, which are deliberate editorial use.
6. **Images are the backbone**: an image may hold 10 s–2 min with
   Ken Burns + drift (this matches the reference true-crime videos:
   51-second no-cut photo chains). Video clips are the spice
   (~20–30 % of screen time), images + graphics are the meal.

## 1. The mapping chain (how data finds its narration line)

```
Visual Help File block
  └─ Script Cue text  ──fuzzy-match──▶  clean script lines
                                            └─ whisper word timestamps
                                                  └─ exact seconds on the timeline
Collector scene folder (scene_012/)
  └─ files, each remembering which block/link they came from
        └─ "shows:" description  ──semantic match──▶  specific line inside the scene
```

So placement precision has two levels: the **block** lands on its cue's
time-range; each **asset** inside the block lands on the line its
"shows:" text matches best (e.g. *"police walking around the car"* goes
under the narration words about police, not under the victim's bio).

## 2. Per-scene algorithm

Input: scene duration D (from whisper), PACING, tag events with anchor
words, asset pool (QC-scored), genre pack.

1. **Slot plan** — how many visuals fit:
   - `hold`: 1–2 slots (one strong image, long dwell)
   - `normal`: ~1 slot per 6–8 s
   - `dense`: ~1 slot per 4–5 s
   Clip slots are 3–4.5 s; image slots 5–12 s (longer on hold).
2. **Assignment order**:
   a. Line-matched assets pin to their lines' timestamps first.
   b. `priority:` fields and `NOTE:` directions order the rest.
   c. Default: establishing clip first, then images deepening detail.
3. **Clip window selection**: from a long downloaded range the planner
   picks the best ≤4.5 s window — centered on the `Spoken Line` (if
   given), else highest motion/quality segment. A second use later must
   pick a non-overlapping window.
4. **Image motion**: Ken Burns direction from subject position
   (reuse ProStudio `subjects`), drift, era treatment (grain/B&W for
   archival). A high-res image can yield 2–3 DIFFERENT framings
   (wide → face crop → detail crop) = multiple shots from one asset.
5. **Tag events overlay** on top of the base visuals, synced to their
   anchor word: `[ENTRY]` card near scene start (~2.5–3.5 s),
   `[DATE]`/`[MAP]`/`[STAT]` cards enter ON the spoken word,
   `[SOURCE]` corner label during the fact line, `[TEXT]` pops on its
   word, `[SILENCE]`/`[HOLD]` stretch the current visual + duck music.
6. **Shortfall ladder** (pool smaller than slot plan):
   ① re-frame existing images (different crops) →
   ② full-screen graphics (date card, map, document mock, quote card) →
   ③ borrow from the SAME entry's neighbor scene pool →
   ④ fallback search queries →
   ⑤ ⚠ flag the scene on the storyboard.
7. **Cross-scene checks**: no identical asset window in two scenes, no
   same-source back-to-back across a scene boundary, variation sampling
   so consecutive scenes don't share identical shot rhythm.

## 3. What the viewer sees (worked example)

Scene 4–5 of the Kinkel fixture (attack + casualties, ~28 s total,
MOOD tension→tragic):

| Time | On screen |
|------|-----------|
| 0.0 | Archival news clip: school exterior + police tape (4.5 s max), punch-in + grain, clip audio muted, tension drone under |
| 2.1 (word "May 21st") | Red date card slides in: **MAY 21, 1998** + whoosh; holds 4 s |
| 4.5 | Cut → photo: school sign, slow Ken Burns push-in (6 s) |
| 8.3 (word "rifle") | Corner label: *POLICE REPORT*; photo continues |
| 10.5 | Cut → 2nd ≤4.5 s window from the news footage (students evacuating) |
| 15.0 (casualty line) | Photo: memorial flowers, slow zoom; small stat panel **2 KILLED · 25 WOUNDED** on the spoken numbers |
| 21.4 (REVEAL line "murdered both of his parents") | Music drops (SILENCE), cut to family-home photo, very slow push, holds 8 s into scene 6 |

One 80-second downloaded news video contributed exactly two 4.5 s
windows; images + cards carried everything else. That is the
copyright-safe documentary formula, and it is exactly how the reference
videos the owner supplied are edited.
