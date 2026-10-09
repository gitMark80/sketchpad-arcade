#!/usr/bin/env python3
"""slice2.py sheet.png outdir name1,name2,...  — items on white with a black caption under each.
Captions are found by shape (short, wide, black), sorted in reading order and matched to the given names."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
src, out, names = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
os.makedirs(out, exist_ok=True)
im = Image.open(src).convert('RGB'); a = np.asarray(im).astype(int); H, W = a.shape[:2]
gray = a.mean(2); sat = a.max(2) - a.min(2)
ink = (gray < 215) | (sat > 40)
dark = (gray < 130) & (sat < 40)
# caption candidates: merge letters horizontally
st = np.ones((3, 19), bool)
lab, n = ndimage.label(ndimage.binary_dilation(ink, structure=st))
caps = []
for k, sl in enumerate(ndimage.find_objects(lab), 1):
    ys, xs = sl; h = ys.stop - ys.start; w = xs.stop - xs.start
    if not (12 <= h <= int(os.environ.get('MAXH','30')) and w >= 1.9 * h and w > 40): continue
    m = (lab[sl] == k) & ink[sl]
    if m.sum() < 60: continue
    if (sat[sl][m] > 60).mean() > .05: continue
    if (dark[sl] & m).sum() / m.sum() < .30: continue
    # text has many separate small pieces (letters)
    pl, pn = ndimage.label(m)
    if pn < 3: continue
    caps.append([ys.start, ys.stop, xs.start, xs.stop])
for b in (sys.argv[4].split(';') if len(sys.argv) > 4 and sys.argv[4] else []):
    x0, y0, x1, y1 = map(int, b.split(':'))
    ys, xs = np.where(dark[y0:y1, x0:x1]); caps.append([y0 + ys.min(), y0 + ys.max() + 1, x0 + xs.min(), x0 + xs.max() + 1])
if os.environ.get('LIST'): print(sorted(caps))
# reading order: rows by caption centre y
caps.sort(key=lambda c: (c[0] + c[1]) / 2)
rows, cur = [], []
for c in caps:
    cy = (c[0] + c[1]) / 2
    if cur and cy - (cur[0][0] + cur[0][1]) / 2 > 45: rows.append(cur); cur = []
    cur.append(c)
if cur: rows.append(cur)
caps = []
for r in rows:
    r = sorted(r, key=lambda c: c[2]); m = [r[0][:]]
    for c in r[1:]:
        if c[2] - m[-1][3] < 30 and abs(c[0] - m[-1][0]) < 12: m[-1] = [min(m[-1][0], c[0]), max(m[-1][1], c[1]), m[-1][2], c[3]]
        else: m.append(c[:])
    caps += m
if len(caps) != len(names):
    print('MISMATCH', src, len(caps), 'captions vs', len(names), 'names')
    dbg = im.copy(); d = ImageDraw.Draw(dbg)
    for i, c in enumerate(caps): d.rectangle([c[2], c[0], c[3], c[1]], outline=(255, 0, 0), width=3); d.text((c[2], c[0] - 12), str(i), fill=(255, 0, 0))
    dbg.save(f'{out}/_mismatch-{os.path.basename(src)}'); sys.exit(1)
capmask = np.zeros((H, W), bool)
for y0, y1, x0, x1 in caps: capmask[max(0, y0 - 4):y1 + 4, max(0, x0 - 4):x1 + 4] = True
item = ink & ~capmask
lab, n = ndimage.label(ndimage.binary_dilation(item, iterations=5))
assign = {i: [] for i in range(len(caps))}
for k, sl in enumerate(ndimage.find_objects(lab), 1):
    ys, xs = sl
    if ((lab[sl] == k) & item[sl]).sum() < 25: continue
    cx = (xs.start + xs.stop) / 2; cy = (ys.start + ys.stop) / 2
    best, bs = None, 1e9
    for i, (y0, y1, x0, x1) in enumerate(caps):
        if y0 < cy - 20: continue          # caption must be below the blob centre
        d = abs((x0 + x1) / 2 - cx) + 0.8 * max(0, y0 - ys.stop)
        if d < bs: bs, best = d, i
    if best is not None: assign[best].append(k)
dbg = im.copy(); dr = ImageDraw.Draw(dbg)
paper = np.array([246, 243, 234.])
for i, ks in assign.items():
    nm = names[i]
    if not ks: print('EMPTY', nm); continue
    region = np.isin(lab, ks)
    ys, xs = np.where(region & item)
    y0, y1, x0, x1 = max(0, ys.min() - 4), min(H, ys.max() + 5), max(0, xs.min() - 4), min(W, xs.max() + 5)
    crop = a[y0:y1, x0:x1].astype(float); reg = ndimage.binary_fill_holes(region[y0:y1, x0:x1])
    white = (crop.mean(2) > 226) & ((crop.max(2) - crop.min(2)) < 30)
    cink = ~white
    seal = ndimage.binary_dilation(cink, iterations=int(os.environ.get('SEAL', '4')))
    openw = np.pad(~seal, 1, constant_values=True)
    wl, _ = ndimage.label(openw)
    outside = (wl == wl[0, 0])[1:-1, 1:-1]
    outside = ndimage.binary_dilation(outside, iterations=int(os.environ.get('SEAL', '4')) + 1) & white
    bg = outside | ~reg
    lum = crop.mean(2)
    edge = ndimage.binary_dilation(~bg, iterations=1)
    alpha = np.where(bg, np.clip((238 - lum) / 70, 0, 1) * edge, 1.0)
    crop[(~bg) & white] = paper
    Image.fromarray(np.dstack([crop, alpha * 255]).clip(0, 255).astype(np.uint8), 'RGBA').save(f'{out}/{nm}.png')
    dr.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=2); dr.text((x0 + 3, y0 + 3), nm, fill=(255, 0, 0))
dbg.resize((W // 2, H // 2)).save(f'{out}/_debug-{os.path.basename(src)[:-4]}.jpg', quality=70)
print('ok', src, len(caps))
