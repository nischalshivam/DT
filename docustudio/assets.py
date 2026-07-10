"""Asset binding — attach real files from scene folders to a plan.

The Footage Collector drops files into scene_001/, scene_002/ … folders.
bind_assets() walks the plan and assigns a concrete file to every shot:
matching kind when possible (video file for clip shots, image for image
shots), cycling within the folder, borrowing from neighbours when a
folder is empty. Unbound shots keep file=None (renderer uses a styled
filler card; storyboard flags them).
"""
import os

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VID_EXT = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}


def _folder_files(scenes_dir, num):
    for name in (f"scene_{num:03d}", f"scene_{num:02d}", f"scene_{num}"):
        p = os.path.join(scenes_dir, name)
        if os.path.isdir(p):
            files = sorted(os.path.join(p, f) for f in os.listdir(p))
            return [f for f in files
                    if os.path.splitext(f)[1].lower() in IMG_EXT | VID_EXT]
    return []


def bind_assets(plan, scenes_dir):
    """Mutates plan: every shot gets sh['file'] (or None) + stats dict."""
    cache = {}

    def files_for(num):
        if num not in cache:
            cache[num] = _folder_files(scenes_dir, num)
        return cache[num]

    stats = {"bound": 0, "unbound": 0, "borrowed": 0}
    use_count = {}
    for sp in plan["scenes"]:
        num = sp["scene"]
        pool = files_for(num)
        borrowed = False
        if not pool:  # borrow from nearest earlier folder, then later
            for d in range(1, 6):
                pool = files_for(num - d) or files_for(num + d)
                if pool:
                    borrowed = True
                    break
        for sh in sp["shots"]:
            if not pool:
                sh["file"] = None
                stats["unbound"] += 1
                continue
            want_vid = sh["kind"] == "clip"
            cands = [f for f in pool
                     if (os.path.splitext(f)[1].lower() in VID_EXT) == want_vid]
            cands = cands or pool
            # least-used first so files rotate instead of repeating
            f = min(cands, key=lambda x: (use_count.get(x, 0), x))
            use_count[f] = use_count.get(f, 0) + 1
            sh["file"] = f
            sh["is_video"] = os.path.splitext(f)[1].lower() in VID_EXT
            stats["bound"] += 1
            if borrowed:
                stats["borrowed"] += 1
    plan["asset_stats"] = stats
    return plan
