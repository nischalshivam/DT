"""Regression lock: the Kinkel fixtures must always parse/match like this.

Run: python3 -m tests.test_fixtures  (from repo root)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from docustudio.validate import load_project
from docustudio.match import match_scenes, match_blocks, coverage

FIX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "testdata", "kinkel_iceberg")


def main():
    p, hp, vp = load_project(os.path.join(FIX, "clean_script.txt"),
                             os.path.join(FIX, "editing_help_script.txt"),
                             os.path.join(FIX, "visual_help_file.txt"))
    assert not hp, f"help-script parse problems: {hp}"
    assert not vp, f"visual-file parse problems: {vp}"
    assert len(p.scenes) == 83, len(p.scenes)
    assert len(p.blocks) == 40, len(p.blocks)
    assert p.topic_anchor.startswith("Kipland"), p.topic_anchor[:40]

    unmatched = match_scenes(p)
    assert unmatched == [], f"unmatched lines: {unmatched[:3]}"
    matched = sum(1 for s in p.scenes for l in s.lines if l.matched)
    assert matched >= 300, matched

    bad_cues = match_blocks(p)
    assert bad_cues == [], f"unmatched cues: {bad_cues}"
    assert all(b.start_scene for b in p.blocks)

    direct, serving = coverage(p)
    assert len(direct) >= 40, len(direct)
    assert all(v is not None for v in serving.values()), "uncovered scenes"

    # spot checks: known ground truth
    by_title = {b.title: b for b in p.blocks}
    assert by_title["THE ICEBERG INTRO"].start_scene == 3
    assert by_title["JONESBORO COMPARISON"].start_scene == 61
    assert by_title["ICEBERG END CARD"].start_scene == 83
    clips = [c for b in p.blocks for c in b.clips]
    assert len(clips) == 8, len(clips)
    assert all(c.start is not None for c in clips)
    assert sum(1 for c in clips if c.end) == 8

    print("OK — all fixture regression checks passed "
          f"({len(p.scenes)} scenes, {len(p.blocks)} blocks, {matched} lines)")


if __name__ == "__main__":
    main()
