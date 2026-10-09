#!/usr/bin/env python3
"""scribble-slice-colorize.py - coloured-pencil + bold ink outline versions of the Scribble Slice sprites.

Reads the original colour art from Beach Day Arcade (src/assets/splash-slice/, or $BDA_REPO) and writes
src/assets/scribble-slice/<same name>.webp at the size the current file already has (so the game's
aspect ratios and anchors stay the same). Each sprite gets:
  * its real colours, flattened (k-means regions blended with a little of the original shading),
    slightly lightened and with a diagonal coloured-pencil hatching texture,
  * a bold dark ink (#1f1f22) outline round the silhouette (about 3-4 css px at the size the game draws it),
  * thinner ink contour lines between strongly different colour regions inside.

    python3 tools/scribble-slice-colorize.py            # all sprites
    python3 tools/scribble-slice-colorize.py kiwi mango # just these (file stems)
    python3 tools/scribble-slice-colorize.py --preview out.png   # also save a contact sheet
"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.cluster.vq import kmeans2

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BDA = os.environ.get('BDA_REPO', os.path.join(os.path.dirname(REPO), 'beach-day-arcade'))
SRC = os.path.join(BDA, 'src', 'assets', 'splash-slice')
DST = os.path.join(REPO, 'src', 'assets', 'scribble-slice')
INK = np.array([0x1f, 0x1f, 0x22], float)

# roughly how wide (css px) the game draws each sprite at a 390px-wide phone (R~30):
#   whole fruit r*2.3, halves r*2.1, splats r*1.25*2.6, drops p.r*2.6, spray r*3..4, HUD shells 26px
DISP = {'watermelon': 83, 'pineapple': 77, 'coconut': 66, 'mango': 66, 'orange': 62, 'kiwi': 59,
        'starfruit': 69, 'banana': 109, 'gold': 72, 'urchin': 66, 'ball': 69}
def display_css(stem):
    if stem.startswith('splat-'): return 97, 3.0
    if stem.startswith('drop-'): return 11, 1.3
    if stem == 'spray': return 105, 1.4
    if stem.startswith('life'): return 26, 1.9
    base = stem.split('-')[0]
    w = DISP.get(base, 66)
    if stem.endswith('-a') or stem.endswith('-b'): w = w * 2.1 / 2.3 / (1.5 if base == 'banana' else 1) * (1.05 if base == 'banana' else 1)
    return w, 3.5

def majority(lab, k, size):
    votes = np.stack([ndimage.uniform_filter((lab == i).astype(np.float32), size) for i in range(k)])
    return votes.argmax(0)

def process(stem):
    src = Image.open(os.path.join(SRC, stem + '.webp')).convert('RGBA')
    dst_path = os.path.join(DST, stem + '.webp')
    tw, th = Image.open(dst_path).size
    im = np.asarray(src.resize((tw, th), Image.LANCZOS)).astype(float)
    rgb, a = im[..., :3], im[..., 3] / 255
    disp, target = display_css(stem)
    w = max(2.5, target * tw / disp)                      # outline width in sprite px
    # silhouette: smoothed alpha, tiny specks dropped
    m = ndimage.gaussian_filter(a, max(.8, w * .12)) > .5
    lab, n = ndimage.label(m)
    if n:
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        keep = np.zeros(n + 1, bool); keep[1:] = sizes >= max(12, (w * .9) ** 2)
        if stem != 'spray': keep[1:] &= sizes >= sizes.max() * .03   # stray specks next to a single sprite
        m = keep[lab]
    # ---- flatten the colours ----
    ks = max(3, int(tw / 70) | 1)
    sm = np.stack([ndimage.median_filter(rgb[..., c], ks) for c in range(3)], -1)
    sm = ndimage.gaussian_filter(sm, (1, 1, 0))
    K = 7 if not stem.startswith(('drop-', 'splat-', 'spray')) else 4
    px = sm[m]
    if len(px) > K * 4:
        rng = np.random.default_rng(7)
        sample = px[rng.choice(len(px), min(len(px), 20000), replace=False)]
        cent, _ = kmeans2(sample, K, minit='++', seed=7)
        d = ((sm[..., None, :] - cent[None, None]) ** 2).sum(-1)
        lab = d.argmin(-1)
        lab = majority(lab, K, max(3, int(tw / 32)))
        flat = cent[lab] * .6 + sm * .4
    else:
        lab = np.zeros((th, tw), int); cent = np.array([px.mean(0) if len(px) else [128, 128, 128]]); flat = sm
    # a touch more saturation, then lighten like coloured pencil on paper
    mean = flat.mean(-1, keepdims=True)
    col = np.clip(mean + (flat - mean) * 1.15, 0, 255)
    col = col * .84 + 255 * .16
    lum = (col @ [.299, .587, .114]) / 255
    # ---- pencil hatching texture ----
    yy, xx = np.mgrid[0:th, 0:tw].astype(float)
    sp = max(4.0, tw / 48)
    noise = ndimage.gaussian_filter(np.random.default_rng(3).standard_normal((th, tw)), 1.2)
    jit = ndimage.gaussian_filter(np.random.default_rng(5).standard_normal((th, tw)), sp * 2) * sp * 2.5
    ph1 = np.mod(xx + yy + jit, sp) / sp
    h1 = np.clip(1 - np.abs(ph1 - .5) / (.22), 0, 1)            # strokes down-left
    ph2 = np.mod(xx - yy + jit * .7, sp * 1.3) / (sp * 1.3)
    h2 = np.clip(1 - np.abs(ph2 - .5) / (.18), 0, 1) * np.clip((.62 - lum) / .25, 0, 1)   # cross-hatch only in the darker parts
    dark = (.10 + .22 * (1 - lum)) * h1 + .22 * h2
    col = col * (1 - dark[..., None])
    gap = (1 - h1) * .10 * lum                                     # paper showing between strokes in the light parts
    col = col + (255 - col) * gap[..., None]
    col = col * (1 - .05 * noise[..., None])
    # ---- interior contour lines between strongly different regions ----
    cl = cent @ [.299, .587, .114]
    diff = np.sqrt(((cent[:, None] - cent[None]) ** 2).sum(-1)) if len(cent) > 1 else np.zeros((1, 1))
    strong = (diff > 70) | (np.abs(cl[:, None] - cl[None]) > 55)
    edge = np.zeros((th, tw), bool)
    for dy, dx in ((0, 1), (1, 0)):
        l2 = np.roll(lab, (-dy, -dx), (0, 1))
        e = strong[lab, l2]
        edge |= e
    din = ndimage.distance_transform_edt(m)
    edge &= din > w * 1.2
    lw = max(1.5, w * .38)
    # no ink round glossy highlights: small, pale, greyish blobs
    sat = cent.max(1) - cent.min(1)
    hl = np.zeros((th, tw), bool)
    for i in np.where((cl > 180) & (sat < 110))[0]:
        rl, rn = ndimage.label((lab == i) & m)
        if not rn: continue
        rs = ndimage.sum(np.ones_like(rl), rl, range(1, rn + 1))
        small = np.zeros(rn + 1, bool); small[1:] = rs < m.sum() * .04
        hl |= small[rl]
    if hl.any(): edge &= ~ndimage.binary_dilation(hl, iterations=int(lw * 2) + 2)
    if stem.startswith(('drop-', 'splat-', 'spray')): edge[:] = False   # juice: just the bold outline
    if edge.any():
        de = ndimage.distance_transform_edt(~edge)
        inner = np.clip(lw / 2 - de + .5, 0, 1) * .85
        # drop specks: contour fragments that are tiny
        el, en = ndimage.label(inner > .3)
        if en:
            s = ndimage.sum(inner > .3, el, range(1, en + 1))
            ok = np.zeros(en + 1, bool); ok[1:] = s >= (lw * 6) ** 1.5
            inner *= ok[el]
    else:
        inner = np.zeros((th, tw))
    col = col * (1 - inner[..., None]) + INK * inner[..., None]
    # ---- bold outline round the silhouette ----
    dout = ndimage.distance_transform_edt(~m)
    sd = dout - din                                                 # >0 outside
    c = -w * .3
    line = np.clip(w / 2 - np.abs(sd - c) + .5, 0, 1)
    fill = np.clip(w * .2 - sd + .5, 0, 1)
    col = col * (1 - line[..., None]) + INK * line[..., None]
    out = np.dstack([np.clip(col, 0, 255), fill * 255]).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(dst_path, 'WEBP', quality=90, method=6)
    return dst_path

def main():
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    prev = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    if prev in args: args.remove(prev)
    stems = args or sorted(f[:-5] for f in os.listdir(DST) if f.endswith('.webp') and f != 'beach.webp')
    done = [process(s) for s in stems]
    for d in done: print('wrote', os.path.relpath(d, REPO))
    if prev:
        cell = 150; cols = 8; rows = (len(stems) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * cell, rows * cell), (246, 243, 234))
        for i, s in enumerate(stems):
            im = Image.open(os.path.join(DST, s + '.webp')); im.thumbnail((cell - 8, cell - 8), Image.LANCZOS)
            sheet.paste(im, ((i % cols) * cell + 4, (i // cols) * cell + 4), im)
        sheet.save(prev)

if __name__ == '__main__':
    main()
