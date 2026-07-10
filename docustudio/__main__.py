"""CLI:
  python -m docustudio validate <clean.txt> <help.txt> <visual.txt>
  python -m docustudio plan <clean.txt> <help.txt> <visual.txt> <pack.json>
                            [--seed N] [--out plan.json]
  python -m docustudio storyboard <clean.txt> <help.txt> <visual.txt>
                            <pack.json> [--seed N] [--out storyboard.html]
"""
import json
import sys
from .validate import validate, load_project
from .match import match_scenes, match_blocks
from .timing import assign_estimated
from .planner import load_pack, plan, preview

USAGE = __doc__


def _prepare(args):
    seed, out_path = 0, None
    rest = args[5:]
    while rest:
        if rest[0] == "--seed":
            seed = int(rest[1]); rest = rest[2:]
        elif rest[0] == "--out":
            out_path = rest[1]; rest = rest[2:]
        else:
            rest = rest[1:]
    project, hp, vp = load_project(args[1], args[2], args[3])
    match_scenes(project)
    match_blocks(project)
    assign_estimated(project)
    pack = load_pack(args[4])
    return project, pack, plan(project, pack, seed=seed), out_path


def main():
    args = sys.argv[1:]
    if len(args) >= 4 and args[0] == "validate":
        _, errors, _ = validate(args[1], args[2], args[3])
        sys.exit(1 if errors else 0)
    if len(args) >= 5 and args[0] == "plan":
        project, pack, p, out_path = _prepare(args)
        if out_path:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(p, f, indent=1)
            print(f"plan written: {out_path}")
        preview(p)
        sys.exit(0)
    if len(args) >= 5 and args[0] == "storyboard":
        from .storyboard import build_storyboard
        project, pack, p, out_path = _prepare(args)
        out_path = out_path or "storyboard.html"
        build_storyboard(project, p, pack, out_path)
        print(f"storyboard written: {out_path}")
        sys.exit(0)
    print(USAGE)
    sys.exit(2)


if __name__ == "__main__":
    main()
