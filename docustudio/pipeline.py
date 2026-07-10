"""Project orchestrator — the tool's spine (SPEC 05 checkpoints).

A PROJECT FOLDER holds everything for one video:

    MyVideo/
      inputs/
        clean_script.txt           (required)
        editing_help_script.txt    (required)
        visual_help_file.txt       (required)
        voiceover.(mp3|wav|m4a)    (optional until render)
        data.txt                   (optional)
      scenes/                      (Footage Collector output)
      config.json                  {"pack": "crime", "seed": 0,
                                    "review": "storyboard"|"auto",
                                    "library": null, "first": null}
      build/                       (everything the tool produces)
        validation.txt  plan.json  storyboard.html  work/  state.json
      output.mp4

Stages run in order, each checkpointed by input-hash in state.json —
rerunning skips finished stages unless inputs changed or --force.
GUI and queue both call run() per project.
"""
import glob
import hashlib
import io
import json
import os

from .validate import load_project, validate
from .match import match_scenes, match_blocks
from .timing import assign_estimated
from .planner import load_pack, plan
from .assets import bind_assets

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGES = ["validate", "align", "plan", "storyboard", "render"]


def _find(folder, patterns):
    for p in patterns:
        hits = sorted(glob.glob(os.path.join(folder, p)))
        if hits:
            return hits[0]
    return None


def discover(project_dir):
    ip = os.path.join(project_dir, "inputs")
    files = {
        "clean": _find(ip, ["clean*.txt", "*clean*.txt", "script.txt"]),
        "help": _find(ip, ["*help_script*.txt", "editing*.txt", "*editing*.txt"]),
        "visual": _find(ip, ["visual*.txt", "*visual*.txt"]),
        "vo": _find(ip, ["voiceover.*", "vo.*", "*.mp3", "*.wav", "*.m4a"]),
        "data": _find(ip, ["data*.txt"]),
    }
    files["scenes"] = os.path.join(project_dir, "scenes")
    cfgp = os.path.join(project_dir, "config.json")
    cfg = {"pack": "crime", "seed": 0, "review": "storyboard",
           "library": None, "first": None, "resolution": "1080p"}
    if os.path.exists(cfgp):
        cfg.update(json.load(open(cfgp)))
    return files, cfg


def _hash_inputs(files, cfg):
    h = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode())
    for k in ("clean", "help", "visual", "vo", "data"):
        f = files.get(k)
        if f and os.path.exists(f):
            h.update(open(f, "rb").read())
    return h.hexdigest()[:16]


class Runner:
    def __init__(self, project_dir, progress=print):
        self.dir = project_dir
        self.build = os.path.join(project_dir, "build")
        os.makedirs(self.build, exist_ok=True)
        self.files, self.cfg = discover(project_dir)
        self.progress = progress
        self.state_path = os.path.join(self.build, "state.json")
        self.state = (json.load(open(self.state_path))
                      if os.path.exists(self.state_path) else {})
        self.fingerprint = _hash_inputs(self.files, self.cfg)
        if self.state.get("inputs") != self.fingerprint:
            self.state = {"inputs": self.fingerprint, "done": []}
        self.project = None
        self.pack = None
        self.plan = None

    # ------------------------------------------------------------- helpers
    def _save(self):
        json.dump(self.state, open(self.state_path, "w"), indent=1)

    def _done(self, stage):
        if stage not in self.state["done"]:
            self.state["done"].append(stage)
        self._save()

    def _pack_path(self):
        p = self.cfg["pack"]
        if os.path.exists(p):
            return p
        return os.path.join(_HERE, "packs", f"{p}.json")

    # -------------------------------------------------------------- stages
    def stage_validate(self):
        buf = io.StringIO()
        _, errors, warnings = validate(
            self.files["clean"], self.files["help"], self.files["visual"],
            out=lambda s: buf.write(str(s) + "\n"))
        open(os.path.join(self.build, "validation.txt"), "w").write(
            buf.getvalue())
        self.progress(f"validate: {len(errors)} errors, "
                      f"{len(warnings)} warnings (build/validation.txt)")
        if errors:
            raise SystemExit("validation errors — fix inputs first")

    def _load(self):
        if self.project is None:
            self.project, _, _ = load_project(
                self.files["clean"], self.files["help"], self.files["visual"])
            match_scenes(self.project)
            match_blocks(self.project)
            assign_estimated(self.project)
            self.pack = load_pack(self._pack_path())

    def stage_align(self):
        self._load()
        if self.files["vo"] and os.path.exists(self.files["vo"]):
            from .align import align_project
            status = align_project(self.project, self.files["vo"])
            self.progress(f"align: {status}")
        else:
            self.progress("align: no voiceover yet — word-count estimate")

    def stage_plan(self):
        self._load()
        self.plan = plan(self.project, self.pack,
                         seed=int(self.cfg.get("seed") or 0))
        if os.path.isdir(self.files["scenes"]):
            bind_assets(self.plan, self.files["scenes"])
            self.progress(f"plan: {self.plan['fingerprint'].get('shots')} shots, "
                          f"risk {self.plan['slideshow_risk']}, "
                          f"assets {self.plan.get('asset_stats')}")
        json.dump(self.plan, open(os.path.join(self.build, "plan.json"), "w"),
                  indent=1)

    def stage_storyboard(self):
        from .storyboard import build_storyboard
        out = os.path.join(self.build, "storyboard.html")
        title = os.path.basename(os.path.abspath(self.dir))
        build_storyboard(self.project, self.plan, self.pack, out,
                         title=f"Storyboard — {title}")
        self.progress(f"storyboard: {out}")

    def stage_render(self):
        from .renderer import render
        first = self.cfg.get("first")
        scenes = None
        if first:
            scenes = [sp["scene"] for sp in self.plan["scenes"][:int(first)]]
        out = os.path.join(self.dir, "output.mp4")
        render(self.project, self.plan, self.pack,
               os.path.join(self.build, "work"), out, scenes=scenes,
               library=self.cfg.get("library"), progress=self.progress)
        self.progress(f"render: {out}")

    # ----------------------------------------------------------------- run
    def run(self, until="storyboard", force=None, approve=False):
        stop = STAGES.index(until)
        for stage in STAGES[:stop + 1]:
            if stage == "render" and not approve and \
                    self.cfg.get("review") != "auto":
                self.progress("paused at storyboard — approve to render "
                              "(--approve)")
                return "awaiting-approval"
            if stage in self.state["done"] and stage != force and \
                    stage not in ("align", "plan", "storyboard"):
                self.progress(f"{stage}: checkpoint hit, skipped")
                continue
            getattr(self, f"stage_{stage}")()
            self._done(stage)
        return "ok"


def run_project(project_dir, until="render", approve=False, force=None,
                progress=print):
    return Runner(project_dir, progress).run(until=until, force=force,
                                             approve=approve)
