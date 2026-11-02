#!/usr/bin/env python3
"""Slice Mark's hand-drawn Pencil Putt sheets into src/assets/pencil-putt/*.webp.

    python3 tools/pencil-putt-slice.py SPRITES.png TEXTURES.png DESK.png

SPRITES.png  4 x 5 grid, labelled (ball, cup, flag, tee / ruler wall, eraser post,
             paper ball, bouncy ball / bouncy ball squashed, eraser walk A, eraser
             walk B, eraser dizzy / pinwheel, crayon, pencil, star / paper clip,
             ink splash, puff, confetti). Labels are cropped off, the paper is
             knocked out to transparency by flood-filling from the cell edges.
TEXTURES.png 2 x 2 grid of tiles: shavings, ink / stream, slope. Each is cropped
             to its best-repeating square (edge matching) so it tiles.
DESK.png     the wooden desk background (replaces beach.webp).
"""
import sys, os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'src', 'assets', 'pencil-putt')

# sheet cell (col,row) -> asset name, max output width
CELLS = {
    (0,0):('ball',256), (1,0):('cup',380), (2,0):('flag',440), (3,0):('tee',360),
    (0,1):('wall',520), (1,1):('cap',300), (2,1):('rock',360), (3,1):('bball',390),
    (0,2):('bsq',390), (1,2):('crabA',360), (2,2):('crabB',360), (3,2):('dizzy',390),
    (0,3):('umb',368), (1,3):('surf',200), (2,3):('tiki',200), (3,3):('star',256),
    (0,4):('shell',240), (1,4):('splash',400), (2,4):('puff',360), (3,4):('confetti',400),
}
TILES = {(0,0):'sandtrap', (1,0):'water', (0,1):'tide', (1,1):'slope'}

def knockout(im, tol=38):
    """Make the paper transparent: flood-fill near-white from the border."""
    a = np.asarray(im.convert('RGB')).astype(int)
    paper = np.median(np.concatenate([a[0], a[-1], a[:,0], a[:,-1]]), axis=0)
    dist = np.abs(a - paper).max(axis=2)
    near = dist < tol
    lab, n = ndimage.label(near)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:,0], lab[:,-1]])))
    border.discard(0)
    outside = np.isin(lab, list(border))
    # soft edge: within the outside region, fade by how close to paper the pixel is
    alpha = np.where(outside, 0, 255).astype(np.uint8)
    alpha = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.8))
    al = np.asarray(alpha).astype(float) / 255
    # un-premultiply-ish: pull edge pixels away from paper colour so halos don't show
    rgb = a.astype(float)
    rgb = np.where(al[...,None] > 0, (rgb - paper * (1 - al[...,None])) / np.maximum(al[...,None], .05), rgb)
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    out = Image.fromarray(rgb).convert('RGBA')
    out.putalpha(alpha)
    return out

def tight(im, pad=4):
    al = np.asarray(im.getchannel('A')) > 8
    lab, n = ndimage.label(al); sz = ndimage.sum(al, lab, range(1, n+1))
    keep = np.isin(lab, [i+1 for i, v in enumerate(sz) if v >= 60])
    im = im.copy(); im.putalpha(Image.fromarray(np.where(keep, np.asarray(im.getchannel('A')), 0).astype(np.uint8)))
    bb = im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
    x0,y0,x1,y1 = bb
    return im.crop((max(0,x0-pad), max(0,y0-pad), min(im.width,x1+pad), min(im.height,y1+pad)))

def sprites(path):
    sheet = Image.open(path).convert('RGB')
    cw, ch = sheet.width/4, sheet.height/5
    for (c,r),(name,maxw) in CELLS.items():
        x0, y0 = int(c*cw), int(r*ch)
        cell = sheet.crop((x0, y0, int(x0+cw), int(y0+ch)))
        # drop the caption: keep only the top 82% of the cell (labels sit in the bottom strip)
        cell = cell.crop((0, 0, cell.width, int(cell.height*.82)))
        im = tight(knockout(cell))
        if im.width > maxw:
            im = im.resize((maxw, round(im.height*maxw/im.width)), Image.LANCZOS)
        im.save(os.path.join(OUT, name+'.webp'), quality=90, method=6)
        print(name, im.size)

def best_period(a, axis, lo, hi):
    """Crop length along axis whose far edge best matches the near edge."""
    best, bl = None, 1e18
    for n in range(lo, hi-3):
        if axis == 0: d = np.abs(a[0:3].astype(int) - a[n:n+3].astype(int)).mean()
        else:         d = np.abs(a[:,0:3].astype(int) - a[:,n:n+3].astype(int)).mean()
        if d < bl: bl, best = d, n
    return best, bl

def wrap_blend(im, f):
    """Crossfade the last f px into the first f px (both axes) so the tile repeats cleanly."""
    a = np.asarray(im).astype(float)
    def blend(a, f):
        n = a.shape[1]; out = a[:, :n-f].copy()
        r = np.linspace(0, 1, f)[None, :, None]
        out[:, :f] = a[:, n-f:] * (1-r) + a[:, :f] * r
        return out
    a = blend(a, f)
    a = blend(a.transpose(1,0,2), f).transpose(1,0,2)
    return Image.fromarray(a.astype(np.uint8))

def tiles(path):
    sheet = Image.open(path).convert('RGB')
    cw, ch = sheet.width//2, sheet.height//2
    for (c,r),name in TILES.items():
        cell = sheet.crop((c*cw, r*ch, (c+1)*cw, (r+1)*ch))
        a = np.asarray(cell)
        lim = int(ch*.88)   # stay above the caption
        w, dw = best_period(a[:lim], 1, int(cw*.6), lim)
        h, dh = best_period(a[:lim], 0, int(ch*.6), lim)
        tile = cell.crop((0, 0, w, h))
        if name in ('sandtrap', 'water'):
            # non-directional scribble: wrap-blend the edges so the repeat is seamless
            tile = wrap_blend(cell.crop((0, 0, min(w+60, lim), min(h+60, lim))), 60)
        tile = tile.resize((1024, round(tile.height*1024/tile.width)), Image.LANCZOS) if tile.width > 1024 else tile
        tile.save(os.path.join(OUT, name+'.webp'), quality=88, method=6)
        print(name, (w,h), 'edge diff %.1f/%.1f' % (dw, dh), '->', tile.size)

def desk(path):
    im = Image.open(path).convert('RGB').resize((700, 1244), Image.LANCZOS)
    im.save(os.path.join(OUT, 'beach.webp'), quality=85, method=6)
    print('beach', im.size)

if __name__ == '__main__':
    sprites(sys.argv[1]); tiles(sys.argv[2]); desk(sys.argv[3])
