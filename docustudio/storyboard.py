"""Storyboard — self-contained HTML review screen for an edit plan.

Shows the whole video at a glance (pacing graph, risk, coverage) and one
card per scene: narration, shots, generated graphics (real rendered
previews), editorial reasons, warnings. v1 is a review/preview screen;
interactive editing arrives with the desktop app.
"""
import base64
import io

from .graphics import render_card
from .themes import theme_for

MOOD_COLORS = {
    "neutral": "#8a8f98", "curious": "#3fa7a3", "tension": "#d4622a",
    "dark": "#8c2f39", "tragic": "#7d4a8f", "emotional": "#c76b8e",
    "hopeful": "#6faf6f", "triumphant": "#c9a13b", "action": "#e08a2e",
    "epic": "#4a6fb5", "calm": "#5f9e7f", "nostalgic": "#a98a63",
    "mystery": "#5a5f9e",
}

KIND_ICONS = {"clip": "🎞", "image": "🖼", "graphic": "🗂", "doc": "📄"}


def _mmss(t: float) -> str:
    t = int(round(t))
    return f"{t // 60}:{t % 60:02d}"


def _b64(img, max_w=460) -> str:
    if img.width > max_w:
        h = int(img.height * max_w / img.width)
        img = img.resize((max_w, h))
    buf = io.BytesIO()
    img.convert("RGBA").save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


_CSS = """
:root{--bg:#111318;--card:#1a1d24;--line:#2a2e38;--tx:#dfe3ea;--mut:#9aa1ad;
--acc:#c9503c;--ok:#6faf6f;--warn:#d9a13b}
*{box-sizing:border-box}body{background:var(--bg);color:var(--tx);
font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;margin:0;padding:0 0 80px}
.top{position:sticky;top:0;z-index:5;background:#14161c;border-bottom:1px solid var(--line);
padding:14px 26px}
.top h1{font-size:19px;margin:0 0 4px}.top .sub{color:var(--mut);font-size:13px}
.badges{margin-top:8px;display:flex;gap:8px;flex-wrap:wrap}
.badge{font-size:12px;padding:3px 10px;border-radius:20px;background:#232733;color:var(--tx)}
.badge.risk-LOW{background:#1e3524;color:#8fd39a}.badge.risk-MEDIUM{background:#3a3018;color:#e5c56b}
.badge.risk-HIGH{background:#3a1a1a;color:#e58a8a}
.paceWrap{margin-top:10px;overflow-x:auto}.pace{display:flex;align-items:flex-end;gap:1px;height:64px}
.pace div{min-width:6px;border-radius:2px 2px 0 0;opacity:.9}
.pace div:hover{opacity:1;outline:1px solid #fff}
.controls{margin:14px 26px 4px;display:flex;gap:10px}
.controls button{background:#232733;border:1px solid var(--line);color:var(--tx);
padding:7px 14px;border-radius:8px;cursor:pointer;font-size:13px}
.controls button.active{background:var(--acc);border-color:var(--acc)}
.chapter{margin:34px 26px 10px;padding:14px 20px;background:linear-gradient(90deg,#232733,transparent);
border-left:4px solid var(--acc);font-size:17px;font-weight:700;letter-spacing:.14em}
.scene{background:var(--card);border:1px solid var(--line);border-radius:12px;
margin:14px 26px;padding:16px 20px}
.scene.flagged{border-color:#5a4218}
.shead{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:8px}
.snum{font-weight:800;font-size:15px}.stime{color:var(--mut);font-size:13px}
.chip{font-size:11px;padding:2px 9px;border-radius:12px;background:#232733;color:var(--tx)}
.narr{color:var(--mut);font-size:13.5px;line-height:1.55;margin:6px 0 12px;max-width:1100px}
.shots{display:flex;flex-direction:column;gap:4px;margin-bottom:10px}
.shot{display:flex;gap:12px;font-size:13px;align-items:baseline}
.shot .d{color:var(--acc);font-weight:700;min-width:52px;text-align:right}
.shot .k{min-width:64px;color:var(--mut)}.shot .m{min-width:120px;color:#7fa7c9}
.shot .t{color:var(--tx);opacity:.85}
.events{display:flex;flex-wrap:wrap;gap:12px;margin:10px 0 4px}
.ev{background:#14161c;border:1px solid var(--line);border-radius:10px;padding:8px;
max-width:300px;text-align:center}
.ev img{max-height:84px;max-width:280px;cursor:zoom-in;border-radius:4px}
.ev .cap{font-size:10.5px;color:var(--mut);margin-top:5px}
.ev.textonly{display:flex;align-items:center;font-size:12px;color:#b9c3d3;padding:10px 14px}
.reason{color:var(--ok);font-size:12.5px;margin:2px 0}
.warn{color:var(--warn);font-size:12.5px;margin:2px 0}
#modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:50;
align-items:center;justify-content:center;cursor:zoom-out}
#modal img{max-width:92vw;max-height:92vh;border-radius:8px}
"""

_JS = """
function flt(on){document.querySelectorAll('.scene').forEach(s=>{
 s.style.display=(!on||s.classList.contains('flagged'))?'':'none'});
 document.getElementById('fbtn').classList.toggle('active',on);
 window._f=on}
document.addEventListener('click',e=>{
 if(e.target.matches('.ev img')){const m=document.getElementById('modal');
  m.querySelector('img').src=e.target.src;m.style.display='flex'}
 else if(e.target.closest('#modal')){document.getElementById('modal').style.display='none'}});
"""


def build_storyboard(project, plan, pack, out_path, title="DocuStudio Storyboard",
                     embed_cards=True):
    theme = theme_for(pack["name"])
    fp = plan.get("fingerprint", {})
    scenes = plan["scenes"]
    total = scenes[-1]["t1"] if scenes else 0
    narr = {s.num: " ".join(l.text for l in s.lines) for s in project.scenes}

    h = [f"<title>{title}</title><style>{_CSS}</style>"]
    # ---- header -------------------------------------------------------------
    warn_scenes = sum(1 for sp in scenes if sp["warnings"])
    h.append('<div class="top">')
    h.append(f"<h1>{title}</h1>")
    h.append(f'<div class="sub">{project.topic_anchor[:160]}</div>')
    h.append('<div class="badges">')
    h.append(f'<span class="badge">pack: {plan["pack"]}/{plan.get("substyle","")}</span>')
    h.append(f'<span class="badge">duration ≈ {_mmss(total)}</span>')
    h.append(f'<span class="badge">{len(scenes)} scenes · {fp.get("shots","?")} shots</span>')
    h.append(f'<span class="badge">shot dur {fp.get("dur_mean","?")}s ± {fp.get("dur_std","?")}s</span>')
    h.append(f'<span class="badge risk-{plan["slideshow_risk"]}">slideshow risk: {plan["slideshow_risk"]}</span>')
    h.append(f'<span class="badge">⚠ {warn_scenes} scenes need review</span>')
    h.append("</div>")
    # pacing graph
    h.append('<div class="paceWrap"><div class="pace">')
    for sp in scenes:
        c = MOOD_COLORS.get(sp["mood"], "#8a8f98")
        bh = max(8, min(64, int(sp["dur"] * 1.6)))
        bw = max(6, int(sp["dur"] * 0.9))
        h.append(f'<div style="height:{bh}px;width:{bw}px;background:{c}" '
                 f'title="S{sp["scene"]} · {sp["dur"]}s · {sp["mood"]}/{sp["pacing"]}"></div>')
    h.append("</div></div></div>")
    h.append('<div class="controls"><button id="fbtn" onclick="flt(!window._f)">'
             "⚠ flagged only</button></div>")

    # ---- scene cards --------------------------------------------------------
    for sp in scenes:
        chap = next((e for e in sp["events"] if e["kind"] == "CHAPTER"), None)
        if chap:
            h.append(f'<div class="chapter">📖 {chap.get("value","")}</div>')
        cls = "scene flagged" if sp["warnings"] else "scene"
        h.append(f'<div class="{cls}" id="s{sp["scene"]}">')
        h.append('<div class="shead">')
        h.append(f'<span class="snum">SCENE {sp["scene"]}</span>')
        h.append(f'<span class="stime">{_mmss(sp["t0"])} → {_mmss(sp["t1"])} '
                 f'({sp["dur"]}s)</span>')
        mc = MOOD_COLORS.get(sp["mood"], "#8a8f98")
        h.append(f'<span class="chip" style="background:{mc}33;color:{mc}">'
                 f'{sp["mood"]}</span>')
        h.append(f'<span class="chip">{sp["pacing"]}</span>')
        h.append(f'<span class="chip">♪ {sp["music"]}</span>')
        h.append(f'<span class="chip">⇥ {sp["transition_in"]}</span>')
        h.append("</div>")
        h.append(f'<div class="narr">{narr.get(sp["scene"], "")[:600]}</div>')
        h.append('<div class="shots">')
        for sh in sp["shots"]:
            icon = KIND_ICONS.get(sh["kind"], "▫")
            win = ""
            if sh.get("clip_window") and sh["clip_window"][0] is not None:
                a = sh["clip_window"][0]
                b = sh["clip_window"][1]
                win = f' <span style="color:#666">[src {_mmss(a)}–{_mmss(b) if b else "?"}]</span>'
            h.append(f'<div class="shot"><span class="d">{sh["dur"]}s</span>'
                     f'<span class="k">{icon} {sh["kind"]}</span>'
                     f'<span class="m">{sh["motion"]}</span>'
                     f'<span class="t">{(sh["desc"] or "")[:110]}{win}</span></div>')
        h.append("</div>")
        # events with rendered card previews
        vis = [e for e in sp["events"] if e["kind"] not in
               ("MUSIC_DIP", "REVEAL", "ARCHIVE_AUDIO", "CENSOR", "CHAPTER")]
        aux = [e for e in sp["events"] if e["kind"] in
               ("MUSIC_DIP", "REVEAL", "ARCHIVE_AUDIO", "CENSOR")]
        if chap:
            vis.insert(0, chap)
        if vis or aux:
            h.append('<div class="events">')
            for e in vis:
                cap = (f'{e["kind"]} · {e.get("variant","")} · @{_mmss(e.get("t",0))}')
                if embed_cards:
                    try:
                        img, _ = render_card(e["kind"], e.get("value", ""),
                                             e.get("variant", "default"), theme)
                        h.append(f'<div class="ev"><img src="data:image/png;base64,'
                                 f'{_b64(img)}"><div class="cap">{cap}</div></div>')
                        continue
                    except Exception:
                        pass
                h.append(f'<div class="ev textonly">{e["kind"]}: '
                         f'{e.get("value","")[:60]}</div>')
            for e in aux:
                lab = {"MUSIC_DIP": "🔇 silence", "REVEAL": "✨ reveal",
                       "ARCHIVE_AUDIO": "📼 tape audio", "CENSOR": "🟦 blur"}[e["kind"]]
                extra = e.get("style") or e.get("what") or ""
                h.append(f'<div class="ev textonly">{lab} {extra} '
                         f'@{_mmss(e.get("t", 0))}</div>')
            h.append("</div>")
        for r in sp["reasons"]:
            h.append(f'<div class="reason">✎ {r}</div>')
        for w in sp["warnings"]:
            h.append(f'<div class="warn">⚠ {w}</div>')
        h.append("</div>")

    h.append('<div id="modal"><img></div>')
    h.append(f"<script>{_JS}</script>")
    html = "\n".join(h)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path
