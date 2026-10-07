#!/usr/bin/env python3
"""Generate a video clip with Google Veo through the Gemini API.

Needs: pip install google-genai   and   GEMINI_API_KEY in the environment.
Each run makes one clip (4, 6 or 8 s, 24 fps, with audio) and saves it as .mp4.

Examples
  veo.py "A cat waves at the camera" -o cat.mp4
  veo.py --template talking-pet --set subject="a cream cat" --set line="Hi!" -o pet.mp4
  veo.py "The mascot waves" --ref mascot.png -o intro.mp4          # keep a character
  veo.py "Logo assembles" --first logo.png --last logo_end.png -o logo.mp4
  veo.py "Then it jumps" --extend previous.json -o part2.mp4        # extend a Veo clip
  veo.py --list                                                     # template names
"""
import argparse, json, mimetypes, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent / "assets" / "templates.json"
DEFAULT_MODEL = os.environ.get("VEO_MODEL", "veo-3.1-generate-preview")


def load_templates():
    return json.loads(TEMPLATES.read_text())["templates"]


def fill(prompt, values):
    out = prompt
    for k, v in values.items():
        out = out.replace("{" + k + "}", v)
    missing = sorted(set(re.findall(r"\{(\w+)\}", out)))
    if missing:
        sys.exit(f"Template needs values for: {', '.join(missing)} (use --set name=value)")
    return out


def image(path):
    from google.genai import types
    mime = mimetypes.guess_type(path)[0] or "image/png"
    return types.Image(image_bytes=Path(path).read_bytes(), mime_type=mime)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt", nargs="?", help="what to film; put dialogue in double quotes")
    ap.add_argument("-o", "--out", default="veo.mp4")
    ap.add_argument("--template", help="template id from assets/templates.json")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="fill a {placeholder}")
    ap.add_argument("--list", action="store_true", help="list templates and exit")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--aspect", choices=["16:9", "9:16"])
    ap.add_argument("--resolution", choices=["720p", "1080p", "4k"], default="720p")
    ap.add_argument("--seconds", type=int, choices=[4, 6, 8], default=8)
    ap.add_argument("--first", help="image to use as the first frame")
    ap.add_argument("--last", help="image to use as the last frame (needs --first)")
    ap.add_argument("--ref", action="append", default=[], help="reference image to keep a character/product (up to 3)")
    ap.add_argument("--extend", help="the .json saved next to an earlier Veo clip, to continue it")
    ap.add_argument("--negative", help="things to avoid")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--dry-run", action="store_true", help="print the request and stop")
    a = ap.parse_args()

    if a.list:
        for t in load_templates():
            print(f"{t['id']:16} {t['category']:12} {t['title']:16} needs: {t['needs'] or '-'}")
        return

    prompt, aspect = a.prompt, a.aspect
    if a.template:
        t = next((t for t in load_templates() if t["id"] == a.template), None)
        if not t:
            sys.exit(f"Unknown template {a.template}; try --list")
        values = dict(s.split("=", 1) for s in a.set)
        prompt = fill(t["prompt"], values) + (" " + a.prompt if a.prompt else "")
        aspect = aspect or t.get("aspect")
    if not prompt:
        sys.exit("Give a prompt or --template")
    aspect = aspect or "16:9"
    if (a.ref or a.extend or a.resolution != "720p") and a.seconds != 8:
        sys.exit("Reference images, extension, 1080p and 4k need --seconds 8")
    if len(a.ref) > 3:
        sys.exit("At most 3 reference images")
    if a.last and not a.first:
        sys.exit("--last needs --first")

    req = dict(model=a.model, prompt=prompt, aspect=aspect, resolution=a.resolution, seconds=a.seconds,
               first=a.first, last=a.last, refs=a.ref, extend=a.extend)
    if a.dry_run:
        print(json.dumps(req, indent=2)); return

    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        sys.exit("Set GEMINI_API_KEY (create one at https://aistudio.google.com/apikey)")
    from google import genai
    from google.genai import types
    client = genai.Client()

    cfg = dict(aspect_ratio=aspect, resolution=a.resolution, duration_seconds=a.seconds, number_of_videos=1)
    if a.negative: cfg["negative_prompt"] = a.negative
    if a.seed is not None: cfg["seed"] = a.seed
    if a.last: cfg["last_frame"] = image(a.last)
    if a.ref:
        cfg["reference_images"] = [types.VideoGenerationReferenceImage(image=image(p), reference_type="asset") for p in a.ref]
    kw = dict(model=a.model, prompt=prompt, config=types.GenerateVideosConfig(**cfg))
    if a.first: kw["image"] = image(a.first)
    if a.extend:
        prev = json.loads(Path(a.extend).read_text())
        kw["video"] = types.Video(uri=prev["video_uri"])
        cfg["resolution"] = "720p"; kw["config"] = types.GenerateVideosConfig(**cfg)

    op = client.models.generate_videos(**kw)
    t0 = time.time()
    while not op.done:
        print(f"  generating… {int(time.time()-t0)}s", file=sys.stderr, flush=True)
        time.sleep(10)
        op = client.operations.get(op)
    if op.error:
        sys.exit(f"Veo error: {op.error}")
    vids = (op.response.generated_videos if op.response else None) or []
    if not vids:
        sys.exit("No video returned (it may have been blocked by safety filters; blocked clips are not billed)")
    v = vids[0]
    client.files.download(file=v.video)
    v.video.save(a.out)
    meta = dict(req, video_uri=getattr(v.video, "uri", None), seconds_taken=int(time.time()-t0))
    Path(a.out).with_suffix(".json").write_text(json.dumps(meta, indent=2))
    print(a.out)


if __name__ == "__main__":
    main()
