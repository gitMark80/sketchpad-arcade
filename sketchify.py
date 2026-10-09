#!/usr/bin/env python3
"""Turns a Beach Day Arcade game's painted art into pencil sketches for Sketchpad Arcade.

Reads every image in <beach-day-arcade>/src/assets/<slug> and writes a line-drawn, hatched version
to src/assets/<slug> (same file names), so the sketch twin keeps the original's
asset paths and sprite logic unchanged. Also sketches the game's cover
(<beach-day-arcade>/src/img/<slug>.jpg -> src/img/<slug>.jpg).

The Beach Day Arcade checkout is found at $BDA_REPO, or next to this repo as ../beach-day-arcade.

    python3 sketchify.py seaside-sprint
    python3 sketchify.py sea-merge          # a game with no asset folder: cover only
    python3 sketchify.py sea-merge --inline # also sketch the base64 images embedded in
                                            # sketch/src/games/sea-merge.html, in place

Needs Pillow, numpy and scipy. Add coloured-pencil tints for a game in TINTS.
"""
import sys
import numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).parent          # the sketch/ site
import os
BDA = Path(os.environ.get("BDA_REPO") or ROOT.parent / "beach-day-arcade")  # the Beach Day Arcade checkout
if not (BDA / "src/games").exists():
    sys.exit(f"Beach Day Arcade checkout not found at {BDA}; set BDA_REPO to its path")
SRC_SLUG = sys.argv[1]
# Sketchpad Arcade renamed its games (Oct 2026). Pass the Beach Day Arcade slug; output goes to the Sketchpad slug.
RENAMED = {
    "seaside-sprint": "sketch-sprint",
    "plank-plunk": "pencil-plunk",
    "letter-lagoon": "letter-links",
    "lighthouse-drop": "doodle-drop",
    "tide-clash": "draw-brawl",
    "shore-search": "sketch-search",
    "shell-stacks": "doodle-stacks",
    "tiki-putt": "pencil-putt",
    "splash-slice": "scribble-slice",
    "sea-merge": "margin-merge",
    "boardwalk-darts": "doodle-darts",
    "word-waves": "word-workshop",
    "tide-pop": "bubble-doodle",
    "crab-hop": "sidewalk-hop",
    "tide-gates": "paper-gates",
    "four-by-sea": "four-in-a-frame",
    "whirlpool-gulp": "eraser-gulp",
    "bottle-words": "note-quest",
    "octo-swing": "scribble-swing",
    "treasure-trio": "margin-match",
    "beach-link": "pencil-pairs",
    "pearl-blocks": "graph-blocks",
    "shell-swap": "scribble-swap",
    "turtle-dash": "pencil-path",
    "sonar-sub": "paper-sub",
    "sea-glass": "color-by-pencil",
    "gem-cove": "gem-sketch",
    "word-plop": "word-scribble",
}
SLUG = RENAMED.get(SRC_SLUG, SRC_SLUG)
SRC = BDA / "src/assets" / SRC_SLUG
DST = ROOT / "src/assets" / SLUG

INK = np.array([.20, .20, .22])       # graphite
PAPER = np.array([.965, .953, .918])  # sketchbook page

# A few things get coloured-pencil lines so they still read at speed.
TINTS = {
    "seaside-sprint": {
        "ring": [.78, .55, .05], "ring-sparkle": [.78, .55, .05],
        "pad": [.85, .40, .05], "boost": [.85, .40, .05], "board": [.80, .35, .10],
        "bubble": [.15, .45, .80], "magnet": [.80, .25, .30],
        "glider": [.10, .50, .70], "kite": [.10, .50, .70],
    },
    "lighthouse-drop": {
        "urchin": [.45, .25, .65], "jelly": [.85, .35, .60], "pool": [.20, .50, .75],
    },
    "plank-plunk": {
        "pin-red": [.54, .23, .23], "pail-red": [.54, .23, .23],
        "pin-blue": [.18, .44, .71], "pail-blue": [.18, .44, .71],
        "pin-yellow": [.79, .60, .10], "pail-yellow": [.79, .60, .10],
        "pin-green": [.35, .60, .42], "pail-green": [.35, .60, .42],
        "pin-purple": [.44, .29, .60], "pail-purple": [.44, .29, .60],
        "pin-pink": [.77, .35, .54], "pail-pink": [.77, .35, .54],
        "pin-orange": [.85, .40, .10], "pail-orange": [.85, .40, .10],
    },
    "tiki-putt": {
        "water": [.18, .44, .71], "tide": [.18, .44, .71],
        "crab": [.77, .35, .54], "dizzy": [.77, .35, .54], "flag": [.85, .40, .10],
    },
    "splash-slice": {
        "urchin": [.45, .25, .65], "gold": [.78, .55, .05], "ball": [.18, .44, .71],
        "splat-red": [.54, .23, .23], "drop-red": [.54, .23, .23],
        "splat-yellow": [.78, .55, .05], "drop-yellow": [.78, .55, .05],
        "splat-orange": [.85, .40, .10], "drop-orange": [.85, .40, .10],
        "splat-green": [.35, .60, .42], "drop-green": [.35, .60, .42],
    },
    "whirlpool-gulp": {
        "swirl": [.18, .44, .71], "face": [.18, .44, .71],
    },
    "shore-search": {
        "cap-coral": [.54, .23, .23], "cap-turq": [.24, .48, .54], "cap-yellow": [.78, .55, .05],
        "cap-pink": [.77, .35, .54], "cap-lime": [.35, .60, .42], "cap-blue": [.18, .44, .71],
        "hint": [.78, .55, .05], "stars": [.78, .55, .05],
    },
    "letter-lagoon": {
        "buoy-gold": [.78, .55, .05], "star-gold": [.78, .55, .05], "buoy-sel": [.85, .40, .10],
        "buoy-hint": [.18, .44, .71], "hint-shell": [.77, .35, .54], "shell-pink": [.77, .35, .54],
    },
    "shell-stacks": {
        "d-coral": [.54, .23, .23], "d-aqua": [.24, .48, .54], "d-sun": [.78, .55, .05],
        "d-violet": [.44, .29, .60], "d-kelp": [.35, .60, .42], "d-pink": [.77, .35, .54],
        "d-ocean": [.18, .44, .71], "wave": [.18, .44, .71],
    },
    "crab-hop": {
        "crab": [.85, .40, .10], "dizzy": [.85, .40, .10],
        "bike": [.44, .29, .60], "cart": [.44, .29, .60],
    },
    "tide-gates": {
        "coral": [.54, .23, .23], "sky": [.18, .44, .71], "sun": [.78, .55, .05],
        "kelp": [.35, .60, .42], "urchin": [.44, .29, .60], "bubble": [.77, .35, .54],
    },
    "bottle-words": {
        "tile-hit": [.35, .60, .42], "tile-near": [.78, .55, .05], "shell-lost": [.20, .20, .22], "shell": [.77, .35, .54],
    },
    "octo-swing": {
        "star": [.78, .55, .05], "pearl-pink": [.77, .35, .54], "pearl-bubble": [.18, .44, .71],
    },
}
TINT = TINTS.get(SRC_SLUG, {})

def tint_for(name):
    for k, v in TINT.items():
        if name == k or name.startswith(k + "-") or name.startswith(k):
            return np.array(v)
    return INK

def sketch_sprite(im, tint):
    scale = 1
    while max(im.size) * scale < 300:
        scale += 1
    scale = min(scale, 4)
    if scale > 1:
        im = im.resize((im.width * scale, im.height * scale), Image.BICUBIC)
    a = np.asarray(im.convert("RGBA")).astype(float) / 255
    al = a[..., 3]
    rgb = a[..., :3] * al[..., None] + (1 - al[..., None])
    lum = .3 * rgb[..., 0] + .59 * rgb[..., 1] + .11 * rgb[..., 2]
    luma = ndimage.gaussian_filter(lum, 1.2)
    e = np.hypot(ndimage.sobel(luma, axis=1), ndimage.sobel(luma, axis=0))
    ala = ndimage.gaussian_filter(al, 1.0)
    ea = np.hypot(ndimage.sobel(ala, axis=1), ndimage.sobel(ala, axis=0))
    edge = np.clip(np.maximum(e * 1.2, ea), 0, 1)
    edge = np.where(edge > .18, np.clip((edge - .18) / .5, 0, 1), 0)
    H, W = lum.shape
    yy, xx = np.mgrid[0:H, 0:W]
    hatch = ((xx + yy) % 9 < 2.2) & (lum < .55) & (al > .5)
    hatch2 = ((xx - yy) % 9 < 2.2) & (lum < .3) & (al > .5)
    ink = np.clip(edge * .9 + hatch * .35 + hatch2 * .35, 0, 1)
    ink *= np.clip(ndimage.maximum_filter(al, 3) * 1.2, 0, 1)
    # a light wash of the tint colour inside, graphite stays plain paper
    wash = PAPER if np.allclose(tint, INK) else PAPER * .55 + np.clip(tint * 1.5, 0, 1) * .45 * .35 + PAPER * .1
    out = np.zeros((H, W, 4))
    out[..., :3] = wash * (1 - ink[..., None]) + tint * ink[..., None]
    out[..., 3] = np.clip(al * .92 + ink, 0, 1)
    return Image.fromarray((out * 255).astype("uint8"), "RGBA")

def sketch_backdrop(im):
    a = np.asarray(im.convert("RGB")).astype(float) / 255
    lum = .3 * a[..., 0] + .59 * a[..., 1] + .11 * a[..., 2]
    luma = ndimage.gaussian_filter(lum, 2.0)
    e = np.hypot(ndimage.sobel(luma, axis=1), ndimage.sobel(luma, axis=0))
    edge = np.where(e > .25, np.clip((e - .25) / .6, 0, 1), 0)
    H, W = lum.shape
    yy, xx = np.mgrid[0:H, 0:W]
    hatch = ((xx + yy) % 10 < 2.2) & (lum < .5)
    ink = np.clip(edge * .7 + hatch * .22, 0, 1)
    out = PAPER * (1 - ink[..., None]) + INK * ink[..., None]
    return Image.fromarray((out * 255).astype("uint8"), "RGB")

def sketch_inline(html_path):
    """Replaces every data:image/...;base64 picture in an HTML file with its pencil version."""
    import re, base64, io
    s = html_path.read_text()
    def one(m):
        mime, b64 = m.group(1), m.group(2)
        try:
            im = Image.open(io.BytesIO(base64.b64decode(b64)))
        except Exception:
            return m.group(0)
        buf = io.BytesIO()
        if im.mode in ("RGBA", "LA", "P") and "png" in mime or "webp" in mime:
            sketch_sprite(im.convert("RGBA"), INK).save(buf, format="WEBP", quality=72)
            out_mime = "image/webp"
        else:
            sketch_backdrop(im).save(buf, format="JPEG", quality=82)
            out_mime = "image/jpeg"
        return f"data:{out_mime};base64," + base64.b64encode(buf.getvalue()).decode()
    n = len(re.findall(r"data:(image/[a-z+]+);base64,([A-Za-z0-9+/=]+)", s))
    s = re.sub(r"data:(image/[a-z+]+);base64,([A-Za-z0-9+/=]+)", one, s)
    html_path.write_text(s)
    print(f"sketched {n} embedded images in {html_path.name}")

def main():
    import shutil
    if "--inline" in sys.argv:
        sketch_inline(ROOT / "src/games" / f"{SLUG}.html")
    cover = BDA / "src/img" / f"{SRC_SLUG}.jpg"
    if cover.exists():
        (ROOT / "src/img").mkdir(parents=True, exist_ok=True)
        sketch_backdrop(Image.open(cover)).save(ROOT / "src/img" / f"{SLUG}.jpg", quality=86)
        print(f"sketched cover src/img/{SLUG}.jpg")
    if not SRC.exists():
        print(f"no asset folder for {SRC_SLUG}; cover only")
        return
    DST.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(SRC.iterdir()):
        if f.is_dir():  # sound effects and other non-image folders come along unchanged
            if not (DST / f.name).exists():
                shutil.copytree(f, DST / f.name)
            continue
        if f.suffix.lower() not in (".webp", ".jpg", ".png"):
            shutil.copy(f, DST / f.name)
            continue
        im = Image.open(f)
        if f.name.startswith("bg") or f.suffix.lower() == ".jpg":
            sketch_backdrop(im).save(DST / f.name, quality=82)
        else:
            sketch_sprite(im, tint_for(f.stem)).save(DST / f.name, quality=72)
        n += 1
    print(f"sketched {n} images into src/assets/{SLUG}")

if __name__ == "__main__":
    main()
