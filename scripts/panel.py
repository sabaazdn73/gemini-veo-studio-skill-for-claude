#!/usr/bin/env python3
"""Build the starter panel: a gallery of video templates, like the Videos page in the Gemini app.

  panel.py                 -> writes panel.html next to the templates (open it in a browser)
  panel.py --thumbs        -> first makes a thumbnail per template with Gemini's image model
                              (needs GEMINI_API_KEY; images saved in assets/thumbs/)
  panel.py --out my.html
"""
import argparse, base64, html, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "assets" / "templates.json").read_text())
THUMBS = ROOT / "assets" / "thumbs"
IMAGE_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview")
GRADS = ["#3d63f2,#8a5cc9", "#f5c24a,#e8605a", "#18a85c,#3d63f2", "#e8605a,#8a5cc9", "#0e1222,#3d63f2", "#f0a070,#f5c24a"]


def make_thumbs():
    from google import genai
    from google.genai import types
    client = genai.Client()
    THUMBS.mkdir(parents=True, exist_ok=True)
    for t in DATA["templates"]:
        out = THUMBS / f"{t['id']}.png"
        if out.exists():
            continue
        p = t["prompt"].replace("{subject}", "a fluffy cream cat").replace("{place}", "a sunny city street") \
            .replace("{line}", "Hello!").replace("{name}", "MIA")
        r = client.models.generate_content(model=IMAGE_MODEL, contents=f"A single cinematic still frame, 16:9, no text: {p}",
                                           config=types.GenerateContentConfig(response_modalities=["IMAGE"]))
        for part in r.candidates[0].content.parts:
            if getattr(part, "inline_data", None):
                out.write_bytes(part.inline_data.data); print("thumb", out.name); break


def card(t, i):
    th = THUMBS / f"{t['id']}.png"
    bg = (f"background-image:url(data:image/png;base64,{base64.b64encode(th.read_bytes()).decode()})"
          if th.exists() else f"background:linear-gradient(135deg,{GRADS[i % len(GRADS)]})")
    emoji = "" if th.exists() else f"<span class=e>{t['emoji']}</span>"
    return (f"<button class=c data-cat='{t['category']}' data-id='{t['id']}' style='{bg}'>{emoji}"
            f"<b>{html.escape(t['title'])}</b></button>")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--thumbs", action="store_true"); ap.add_argument("--out", default=str(ROOT / "panel.html"))
    a = ap.parse_args()
    if a.thumbs:
        make_thumbs()
    cats = "".join(f"<button class=t data-c='{c}'>{c}</button>" for c in DATA["categories"])
    cards = "".join(card(t, i) for i, t in enumerate(DATA["templates"]))
    doc = f"""<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Video templates</title><style>
:root{{--bg:#0b0d16;--fg:#e8ecf8;--mut:#8f98bd;--card:#151a2e}}
@media (prefers-color-scheme: light){{:root{{--bg:#f4f5fb;--fg:#14172b;--mut:#5a6080;--card:#fff}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font-family:system-ui,sans-serif;padding:28px 16px}}
.w{{max-width:900px;margin:auto}}h1{{font-weight:500;font-size:28px;text-align:center;margin:0 0 18px}}
.tabs{{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-bottom:20px}}
.t{{border:0;border-radius:999px;padding:8px 16px;background:var(--card);color:var(--fg);cursor:pointer;font-size:15px}}.t.on{{background:#3d63f2;color:#fff}}
.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}}
.c{{position:relative;aspect-ratio:16/10;border:0;border-radius:22px;background-size:cover;background-position:center;cursor:pointer;overflow:hidden;color:#fff;text-align:left}}
.c b{{position:absolute;left:14px;bottom:12px;font-size:16px;text-shadow:0 1px 6px #0009}}.c .e{{position:absolute;top:14px;left:14px;font-size:38px}}
.c:after{{content:"";position:absolute;inset:0;background:linear-gradient(transparent 55%,#0008)}}.c b{{z-index:1}}
.box{{margin-top:22px;background:var(--card);border-radius:20px;padding:18px;display:none}}.box.on{{display:block}}
.box h2{{margin:0 0 6px;font-size:20px}}.box p{{color:var(--mut);margin:4px 0 10px}}
pre{{white-space:pre-wrap;background:var(--bg);padding:12px;border-radius:12px;font-size:13px}}
.cp{{border:0;border-radius:12px;padding:9px 14px;background:#3d63f2;color:#fff;cursor:pointer}}
</style></head><body><div class=w><h1>What should we film?</h1>
<div class=tabs><button class="t on" data-c=All>All</button>{cats}</div><div class=g>{cards}</div>
<div class=box id=box><h2 id=bt></h2><p id=bn></p><pre id=bp></pre><pre id=bc></pre><button class=cp id=cp>Copy command</button></div></div>
<script>
const T={json.dumps({t['id']: t for t in DATA['templates']})};
document.querySelectorAll('.t').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.t').forEach(x=>x.classList.remove('on'));b.classList.add('on');
 document.querySelectorAll('.c').forEach(c=>c.style.display=(b.dataset.c==='All'||c.dataset.cat===b.dataset.c)?'':'none')}});
document.querySelectorAll('.c').forEach(c=>c.onclick=()=>{{const t=T[c.dataset.id];
 const keys=[...new Set((t.prompt.match(/\\{{(\\w+)\\}}/g)||[]).map(k=>k.slice(1,-1)))];
 box.classList.add('on');bt.textContent=t.title;bn.textContent=t.needs?('Needs: '+t.needs):'';bp.textContent=t.prompt;
 bc.textContent='python3 scripts/veo.py --template '+t.id+' '+keys.map(k=>'--set '+k+'="..."').join(' ')+' -o '+t.id+'.mp4';
 box.scrollIntoView({{behavior:'smooth'}})}});
cp.onclick=()=>{{try{{navigator.clipboard.writeText(bc.textContent);cp.textContent='Copied'}}catch(e){{}}}};
</script></body></html>"""
    Path(a.out).write_text(doc)
    print(a.out)


if __name__ == "__main__":
    main()
