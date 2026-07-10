# DocuStudio — User Guide (turnkey, Windows)

## Install (once)
1. Install Python 3.10+ from python.org — tick **"Add to PATH"**.
2. Double-click `setup.bat` (installs everything, incl. ffmpeg — no
   separate ffmpeg install needed).
3. Double-click `run.bat` → DocuStudio opens.

## Setup (once, inside the app)
- **Projects/Output folder** — where all your video projects and final
  MP4s live (e.g. `D:\DocuStudio\Projects`).
- **Music/SFX Library folder** — your collection, organised per
  `SPECS/04_LIBRARY_STRUCTURE.md` (`music/<mood>/`, `ambience/<type>/`,
  `sfx/<type>/`). Leave empty to use the built-in placeholder sound —
  fine for tests, not for uploads.

## Per video
1. **New video project**: name + browse the 3 required files
   (clean script, editing help script, visual help file), optional
   voiceover + data file, and the Collector's scenes folder.
2. Pick **genre pack**, review mode, resolution. "Only first N scenes"
   is for quick tests.
3. **＋ Add project** → it appears in the queue. Add as many as you
   like (overnight batch).
4. **▶ Prepare storyboards** — runs validate → align → plan →
   storyboard for every queued project. Internet is NOT needed by
   DocuStudio itself (the Collector already downloaded the assets).
5. **🗂 Open storyboard** — review the whole edit in your browser:
   pacing graph, every scene's shots + real card previews + reasons,
   ⚠ flagged-only filter.
6. **✔ Approve & render** — makes `output.mp4` inside the project
   folder. Renders are scene-by-scene checkpointed: sleeping or
   closing the laptop loses at most one scene; reopening resumes.

## Where things live
```
Projects/MyVideo/
  inputs/            your files
  scenes/            collector assets
  config.json        the project's settings
  build/             storyboard.html, plan.json, validation.txt, work/
  output.mp4         the finished video
```

## Command line (same engine, optional)
```
py -m docustudio run Projects\MyVideo            → storyboard (pauses)
py -m docustudio run Projects\MyVideo --approve  → output.mp4
py -m docustudio validate <clean> <help> <visual>
```

## Tips
- Voiceover missing? The tool still works with estimated timings —
  add `voiceover.mp3` to `inputs/` later and re-run for word-perfect
  sync (install `faster-whisper` via setup.bat for that).
- Re-run is always safe: finished stages are skipped automatically;
  changing any input file re-runs only what's affected.
