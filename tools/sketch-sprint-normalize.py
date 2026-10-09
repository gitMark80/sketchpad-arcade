#!/usr/bin/env python3
"""Rebuild Sketch Sprint's run cycles from the original frames (kept outside the repo).
For each kid: pick 8 source frames in cycle order (a trailing 'm' = mirrored left-right), register every frame's
head and shoulders to one reference frame (scale + offset), so the body no longer jumps, shrinks or slides between
frames, keep the feet on the ground line, and write <id>-run-1..8.webp on one shared canvas.
Also re-centres <id>-slide.webp so the body's mass sits on the canvas centre.
ORIG_DIR must hold the ORIGINAL frames (as committed before this fix: git show HEAD:src/assets/sketch-sprint/<file>),
not the output of this script.
usage: sketch-sprint-normalize.py ORIG_DIR OUT_DIR"""
import sys, os
import numpy as np
from PIL import Image, ImageOps
from scipy.signal import fftconvolve
SRC, OUT = sys.argv[1].rstrip('/') + '/', sys.argv[2].rstrip('/') + '/'
# cycle slots: 0 left foot up high, 1 left coming down, 2 passing (contact), 3 right lifting,
#              4 right up high, 5 right coming down, 6 passing (contact), 7 left lifting
PLAN = {
  'francis':   (8, ['1', '2', '3', '6', '5', '6', '3', '7']),
  'clare':     (3, ['4', '5', '3', '2', '6', '7', '1', '8']),
  'george':    (8, ['4', '5', '3', '8', '6', '8', '3', '7']),
  'joan':      (3, ['6', '3', '1', '4', '8', '7', '5', '2']),
  'john':      (8, ['6', '8', '5', '8m', '6m', '8m', '5m', '8']),
  'catherine': (1, ['1', '2', '4', '3', '1m', '2m', '4m', '3m']),
  'joseph':    (4, ['1', '3', '2', '8', '4', '6', '2', '7']),
  'therese':   (8, ['2', '1', '8', '6', '4', '6', '8', '5']),
}
FLOAT = .035   # a frame may float this much (of its height) above the ground: flight frames
FLOATX = {'joan': .095}   # Joan's two mid-air frames are drawn crouched with both feet off the ground
def A(im): return (np.asarray(im)[:, :, 3] > 60).astype(np.float32)
def load(i, tok):
  im = Image.open(SRC + '%s-run-%s.webp' % (i, tok.rstrip('m'))).convert('RGBA')
  return ImageOps.mirror(im) if tok.endswith('m') else im
def scaled(im, s):
  if abs(s - 1) < .015: return im
  w, h = round(im.width * s), round(im.height * s)
  return im.convert('RGBa').resize((w, h), Image.LANCZOS).convert('RGBA')
def register(tpl, im):
  best = None
  for s in np.arange(.94, 1.065, .01):
    m = scaled(im, s); a = A(m); pad = np.zeros((a.shape[0] + 80, a.shape[1] + 80), np.float32); pad[40:-40, 40:-40] = a
    c = fftconvolve(pad, tpl[::-1, ::-1], mode='valid'); den = tpl.sum() + fftconvolve(pad, np.ones_like(tpl), mode='valid')
    sc = 2 * c / np.maximum(den, 1); k = np.unravel_index(np.argmax(sc), sc.shape)
    v = sc[k] - .4 * abs(s - 1)  # small prior: the art was drawn at about one size
    if best is None or v > best[0]: best = (v, s, k[0] - 40, k[1] - 40)
  return best
def build(i, ref, slots):
  fl = FLOATX.get(i, FLOAT)
  r = load(i, str(ref)); a0 = A(r); H, W = a0.shape
  t0 = np.nonzero(a0.any(1))[0][0]; hh = int((H - t0) * .38)
  # head and shoulders only, trimmed to the middle so flowing hair and swinging fists don't steer it
  hx = int(np.median(np.nonzero(a0[t0:t0 + hh])[1])); x0 = max(0, hx - int(W * .24))
  tpl = a0[t0:t0 + hh, x0:hx + int(W * .24)]
  placed = []
  for tok in slots:
    im = load(i, tok); sc, s, dy, dx = register(tpl, im); m = scaled(im, s); a = A(m)
    px, py = x0 - dx, t0 - dy                      # where this frame's top-left lands in reference coords (head aligned)
    feet = py + np.nonzero(a.any(1))[0][-1]         # lowest ink, reference coords
    placed.append([tok, m, px, py, feet, round(float(sc), 3), round(float(s), 2)])
  ground = float(np.median([p[4] for p in placed]))   # the ground line: most frames are grounded with the head held still
  for p in placed:
    gap = ground - p[4]                              # >0 floats, <0 sinks
    if gap < 0: p[3] += gap                          # never sink: lift it so the foot is on the ground
    elif gap > fl * H: p[3] += gap - fl * H    # never float too far either
  # body centre: mean x of all ink across the cycle, in reference coords
  xs = []
  for tok, m, px, py, *_ in placed: xs.append(np.nonzero(A(m))[1].mean() + px)
  cx = float(np.mean(xs))
  # one shared canvas: ground on the bottom row, body centre on the middle column
  left = min(p[2] for p in placed); right = max(p[2] + p[1].width for p in placed); top = min(p[3] for p in placed)
  half = int(np.ceil(max(cx - left, right - cx))) + 2; CW = 2 * half; CH = int(np.ceil(ground - top)) + 2
  frames = []
  for tok, m, px, py, feet, sc, s in placed:
    cv = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); cv.alpha_composite(m, (int(round(px - cx + half)), int(round(py - (ground - CH + 1)))))
    frames.append(cv)
  return frames, placed, (CW, CH), ground
def slide(i):
  im = Image.open(SRC + '%s-slide.webp' % i).convert('RGBA'); a = A(im)
  ys, xs = np.nonzero(a); bb = im.getchannel('A').getbbox(); cx = xs.mean()
  half = int(np.ceil(max(cx - bb[0], bb[2] - cx))) + 1
  cv = Image.new('RGBA', (2 * half, bb[3] - bb[1]), (0, 0, 0, 0)); cv.alpha_composite(im.crop(bb), (int(round(bb[0] - cx + half)), 0))
  return cv, cx - im.width / 2
if __name__ == '__main__':
  os.makedirs(OUT, exist_ok=True)
  for i, (ref, slots) in PLAN.items():
    frames, placed, size, ground = build(i, ref, slots)
    for k, f in enumerate(frames): f.save(OUT + '%s-run-%d.webp' % (i, k + 1), 'WEBP', quality=92, method=6)
    print(i, 'canvas', size, ' '.join('%s(s%.2f,m%.2f)' % (p[0], p[6], p[5]) for p in placed))
    cv, off = slide(i); cv.save(OUT + '%s-slide.webp' % i, 'WEBP', quality=92, method=6)
    print('   slide', cv.size, 'was off-centre by %.0f px' % off)
