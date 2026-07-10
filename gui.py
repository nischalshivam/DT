#!/usr/bin/env python3
"""DocuStudio — desktop app (Tkinter, Windows-friendly).

Wraps docustudio.pipeline: create/queue project folders, prepare
storyboards overnight, review in the browser, approve & render.
Everything checkpoints to disk, so closing/sleeping the PC never loses
work (SPEC 05).
"""
import json
import os
import queue
import shutil
import sys
import threading
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SETTINGS_PATH = os.path.join(HERE, "settings.json")


def load_settings():
    s = {"projects_dir": os.path.join(HERE, "Projects"), "library": ""}
    if os.path.exists(SETTINGS_PATH):
        s.update(json.load(open(SETTINGS_PATH, encoding="utf-8")))
    return s


def save_settings(s):
    json.dump(s, open(SETTINGS_PATH, "w", encoding="utf-8"), indent=1)


def list_packs():
    d = os.path.join(HERE, "packs")
    return sorted(os.path.splitext(f)[0] for f in os.listdir(d)
                  if f.endswith(".json"))


def create_project(projects_dir, name, files, scenes_dir, cfg):
    """Create <projects_dir>/<name>/ with inputs copied in + config."""
    pdir = os.path.join(projects_dir, name)
    ip = os.path.join(pdir, "inputs")
    os.makedirs(ip, exist_ok=True)
    names = {"clean": "clean_script.txt", "help": "editing_help_script.txt",
             "visual": "visual_help_file.txt", "data": "data.txt"}
    for key, fname in names.items():
        if files.get(key):
            shutil.copy(files[key], os.path.join(ip, fname))
    if files.get("vo"):
        ext = os.path.splitext(files["vo"])[1]
        shutil.copy(files["vo"], os.path.join(ip, "voiceover" + ext))
    if scenes_dir and os.path.isdir(scenes_dir):
        dst = os.path.join(pdir, "scenes")
        if not os.path.isdir(dst):
            shutil.copytree(scenes_dir, dst)
    json.dump(cfg, open(os.path.join(pdir, "config.json"), "w"), indent=1)
    return pdir


# ------------------------------------------------------------------- GUI ---
def main():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    settings = load_settings()
    log_q = queue.Queue()
    worker = {"t": None}

    root = tk.Tk()
    root.title("DocuStudio — Documentary Editing Brain")
    root.geometry("1080x780")

    # ---------------- settings row
    top = ttk.LabelFrame(root, text="Setup (once)")
    top.pack(fill="x", padx=10, pady=6)
    proj_var = tk.StringVar(value=settings["projects_dir"])
    lib_var = tk.StringVar(value=settings.get("library", ""))

    def pick_dir(var):
        d = filedialog.askdirectory()
        if d:
            var.set(d)
            settings["projects_dir"] = proj_var.get()
            settings["library"] = lib_var.get()
            save_settings(settings)

    for r, (lbl, var) in enumerate([("Projects / Output folder", proj_var),
                                    ("Music/SFX Library folder", lib_var)]):
        ttk.Label(top, text=lbl).grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(top, textvariable=var, width=80).grid(row=r, column=1, padx=4)
        ttk.Button(top, text="Browse…",
                   command=lambda v=var: pick_dir(v)).grid(row=r, column=2)

    # ---------------- new project
    newf = ttk.LabelFrame(root, text="New video project")
    newf.pack(fill="x", padx=10, pady=6)
    name_var = tk.StringVar()
    file_vars = {}
    rows = [("Project name", "name", False),
            ("Clean script (.txt)", "clean", True),
            ("Editing Help Script (.txt)", "help", True),
            ("Visual Help File (.txt)", "visual", True),
            ("Voiceover audio (optional)", "vo", True),
            ("Data file (optional)", "data", True),
            ("Scenes folder (Collector output)", "scenes", "dir")]

    def pick_file(var, isdir):
        p = filedialog.askdirectory() if isdir == "dir" else \
            filedialog.askopenfilename()
        if p:
            var.set(p)

    for r, (lbl, key, kind) in enumerate(rows):
        ttk.Label(newf, text=lbl).grid(row=r, column=0, sticky="w", padx=6)
        var = name_var if key == "name" else tk.StringVar()
        if key != "name":
            file_vars[key] = var
        ttk.Entry(newf, textvariable=var, width=80).grid(row=r, column=1, padx=4)
        if kind:
            ttk.Button(newf, text="Browse…",
                       command=lambda v=var, k=kind: pick_file(v, k)
                       ).grid(row=r, column=2)

    optf = ttk.Frame(newf)
    optf.grid(row=len(rows), column=0, columnspan=3, sticky="w", pady=4)
    pack_var = tk.StringVar(value="crime")
    review_var = tk.StringVar(value="storyboard")
    res_var = tk.StringVar(value="1080p")
    seed_var = tk.StringVar(value="0")
    first_var = tk.StringVar(value="")
    ttk.Label(optf, text="Genre pack").pack(side="left", padx=(6, 2))
    ttk.Combobox(optf, textvariable=pack_var, values=list_packs(),
                 width=12).pack(side="left")
    ttk.Label(optf, text="Review").pack(side="left", padx=(12, 2))
    ttk.Combobox(optf, textvariable=review_var,
                 values=["storyboard", "auto"], width=11).pack(side="left")
    ttk.Label(optf, text="Resolution").pack(side="left", padx=(12, 2))
    ttk.Combobox(optf, textvariable=res_var, values=["1080p", "4K"],
                 width=6).pack(side="left")
    ttk.Label(optf, text="Style seed").pack(side="left", padx=(12, 2))
    ttk.Entry(optf, textvariable=seed_var, width=8).pack(side="left")
    ttk.Label(optf, text="Only first N scenes (test)").pack(side="left",
                                                            padx=(12, 2))
    ttk.Entry(optf, textvariable=first_var, width=6).pack(side="left")

    # ---------------- queue table
    qf = ttk.LabelFrame(root, text="Queue")
    qf.pack(fill="both", expand=True, padx=10, pady=6)
    tree = ttk.Treeview(qf, columns=("status",), height=7)
    tree.heading("#0", text="Project")
    tree.heading("status", text="Status")
    tree.column("#0", width=520)
    tree.column("status", width=380)
    tree.pack(fill="both", expand=True, side="left")

    def set_status(pdir, text):
        for item in tree.get_children():
            if tree.item(item, "text") == pdir:
                tree.set(item, "status", text)
                return
        tree.insert("", "end", text=pdir, values=(text,))

    def add_project():
        if not name_var.get().strip():
            messagebox.showerror("DocuStudio", "Project name required")
            return
        for k in ("clean", "help", "visual"):
            if not file_vars[k].get():
                messagebox.showerror("DocuStudio", f"{k} file required")
                return
        cfg = {"pack": pack_var.get(), "seed": int(seed_var.get() or 0),
               "review": review_var.get(), "resolution": res_var.get(),
               "library": lib_var.get() or None,
               "first": int(first_var.get()) if first_var.get() else None}
        pdir = create_project(
            proj_var.get(), name_var.get().strip(),
            {k: v.get() or None for k, v in file_vars.items()},
            file_vars["scenes"].get() or None, cfg)
        set_status(pdir, "queued")
        log_q.put(f"project created: {pdir}")

    def add_existing():
        d = filedialog.askdirectory()
        if d:
            set_status(d, "queued")

    def selected_project():
        sel = tree.selection()
        return tree.item(sel[0], "text") if sel else None

    # ---------------- worker
    def run_in_thread(fn):
        if worker["t"] and worker["t"].is_alive():
            messagebox.showinfo("DocuStudio", "Already working — wait for "
                                              "the current job")
            return
        worker["t"] = threading.Thread(target=fn, daemon=True)
        worker["t"].start()

    def prepare_all():
        items = [(tree.item(i, "text")) for i in tree.get_children()]

        def job():
            from docustudio.pipeline import run_project
            for pdir in items:
                try:
                    log_q.put(("status", pdir, "preparing…"))
                    r = run_project(pdir, until="storyboard",
                                    progress=lambda m: log_q.put(f"[{os.path.basename(pdir)}] {m}"))
                    log_q.put(("status", pdir,
                               "storyboard ready — review & approve"
                               if r != "ok" else "done"))
                except SystemExit as e:
                    log_q.put(("status", pdir, f"validation failed: {e}"))
                except Exception as e:
                    log_q.put(("status", pdir, f"error: {e}"))
        run_in_thread(job)

    def open_storyboard():
        pdir = selected_project()
        if not pdir:
            return
        sb = os.path.join(pdir, "build", "storyboard.html")
        if os.path.exists(sb):
            webbrowser.open("file://" + os.path.abspath(sb))
        else:
            messagebox.showinfo("DocuStudio", "Storyboard not built yet")

    def approve_render():
        pdir = selected_project()
        if not pdir:
            return

        def job():
            from docustudio.pipeline import run_project
            try:
                log_q.put(("status", pdir, "rendering…"))
                run_project(pdir, until="render", approve=True,
                            progress=lambda m: log_q.put(f"[{os.path.basename(pdir)}] {m}"))
                log_q.put(("status", pdir, "DONE → output.mp4"))
            except Exception as e:
                log_q.put(("status", pdir, f"render error: {e}"))
        run_in_thread(job)

    btns = ttk.Frame(qf)
    btns.pack(side="left", fill="y", padx=8)
    for label, cmd in [("＋ Add project", add_project),
                       ("＋ Add existing folder", add_existing),
                       ("▶ Prepare storyboards", prepare_all),
                       ("🗂 Open storyboard", open_storyboard),
                       ("✔ Approve & render", approve_render)]:
        ttk.Button(btns, text=label, command=cmd, width=24).pack(pady=3)

    # ---------------- log
    logf = ttk.LabelFrame(root, text="Log")
    logf.pack(fill="both", expand=True, padx=10, pady=6)
    logbox = tk.Text(logf, height=10, bg="#14161c", fg="#dfe3ea")
    logbox.pack(fill="both", expand=True)

    def poll():
        try:
            while True:
                msg = log_q.get_nowait()
                if isinstance(msg, tuple) and msg[0] == "status":
                    set_status(msg[1], msg[2])
                else:
                    logbox.insert("end", str(msg) + "\n")
                    logbox.see("end")
        except queue.Empty:
            pass
        root.after(300, poll)

    poll()
    root.mainloop()


if __name__ == "__main__":
    main()
