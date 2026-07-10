"""CLI:
  python -m docustudio validate <clean.txt> <help.txt> <visual.txt>
  python -m docustudio plan <clean.txt> <help.txt> <visual.txt> <pack.json>
                            [--seed N] [--out plan.json]
  python -m docustudio storyboard <clean.txt> <help.txt> <visual.txt>
                            <pack.json> [--seed N] [--out storyboard.html]
                            [--scenes-dir DIR]
  python -m docustudio render <clean.txt> <help.txt> <visual.txt>
                            <pack.json> --scenes-dir DIR --out video.mp4
                            [--seed N] [--first N] [--work DIR]
                            [--library DIR]
"""
import json
import sys
from .validate import validate, load_project
from .match import match_scenes, match_blocks
from .timing import assign_estimated
from .planner import load_pack, plan, preview

USAGE = __doc__


def _prepare(args):
    opt = {"seed": 0, "out": None, "scenes-dir": None, "first": None,
           "work": None, "library": None}
    rest = args[5:]
    while rest:
        key = rest[0].lstrip("-")
        if key in opt and len(rest) > 1:
            opt[key] = rest[1]
            rest = rest[2:]
        else:
            rest = rest[1:]
    project, hp, vp = load_project(args[1], args[2], args[3])
    match_scenes(project)
    match_blocks(project)
    assign_estimated(project)
    pack = load_pack(args[4])
    p = plan(project, pack, seed=int(opt["seed"] or 0))
    if opt["scenes-dir"]:
        from .assets import bind_assets
        bind_assets(p, opt["scenes-dir"])
        print("assets:", p.get("asset_stats"))
    return project, pack, p, opt


def main():
    args = sys.argv[1:]
    if len(args) >= 4 and args[0] == "validate":
        _, errors, _ = validate(args[1], args[2], args[3])
        sys.exit(1 if errors else 0)
    if len(args) >= 5 and args[0] == "plan":
        project, pack, p, opt = _prepare(args)
        if opt["out"]:
            with open(opt["out"], "w", encoding="utf-8") as f:
                json.dump(p, f, indent=1)
            print(f"plan written: {opt['out']}")
        preview(p)
        sys.exit(0)
    if len(args) >= 5 and args[0] == "storyboard":
        from .storyboard import build_storyboard
        project, pack, p, opt = _prepare(args)
        out_path = opt["out"] or "storyboard.html"
        build_storyboard(project, p, pack, out_path)
        print(f"storyboard written: {out_path}")
        sys.exit(0)
    if len(args) >= 2 and args[0] == "run":
        from .pipeline import run_project
        until = "render" if "--approve" in args or "--full" in args \
            else "storyboard"
        if "--until" in args:
            until = args[args.index("--until") + 1]
        run_project(args[1], until=until, approve="--approve" in args)
        sys.exit(0)
    if len(args) >= 3 and args[0] == "rescene":
        from .pipeline import rescene
        rescene(args[1], int(args[2]))
        sys.exit(0)
    if len(args) >= 5 and args[0] == "render":
        from .renderer import render
        project, pack, p, opt = _prepare(args)
        out_path = opt["out"] or "video.mp4"
        work = opt["work"] or out_path + ".work"
        scenes = None
        if opt["first"]:
            scenes = [sp["scene"] for sp in p["scenes"][:int(opt["first"])]]
        render(project, p, pack, work, out_path, scenes=scenes,
               library=opt["library"])
        sys.exit(0)
    print(USAGE)
    sys.exit(2)


if __name__ == "__main__":
    main()
