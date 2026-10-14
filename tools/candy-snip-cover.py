#!/usr/bin/env python3
"""Candy Snip cover (src/img/candy-snip.jpg, 640x640): cream paper, the candy swinging on a string from a
pushpin, Pip the kid below with his mouth open, gold star stickers and the title in Gloria Hallelujah.
Uses the game's own sprites from src/assets/candy-snip/ and the pencil helpers in tools/draw-brawl-sprites.py.

    python3 tools/candy-snip-cover.py
"""
import importlib.util, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location('pencil', os.path.join(HERE, 'draw-brawl-sprites.py'))
pen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pen)
Pic, INK, PAPER, YELLOW = pen.Pic, pen.INK, pen.PAPER, pen.YELLOW
ASSETS = os.path.join(ROOT, 'src', 'assets', 'candy-snip')
FONT = '/root/.fonts/GloriaHallelujah.ttf'
S = 640

# paper with a little grain
rng = np.random.RandomState(4)
grain = rng.rand(S, S) * 10 - 5
base = np.array(PAPER, dtype=float)[None, None, :] + grain[..., None]
cover = Image.fromarray(base.clip(0, 255).astype(np.uint8), 'RGB').convert('RGBA')

# pencil scenery: a wobbly sun, a horizon line, the desk edge
p = Pic(S, S, ss=2, line=4, hatch=7, hw=2)
sun = p.ell(572, 272, 40, 40)
p.paint(sun, YELLOW, wash=.5, spacing=7, line=3.5, hatch_col=YELLOW)
for k in range(12):
    a = k / 12 * math.tau + .2
    r0, r1 = 50 + (k % 2) * 3, 68 + (k % 3) * 6
    p.stroke([(572 + math.cos(a) * r0, 272 + math.sin(a) * r0), (572 + math.cos(a) * r1, 272 + math.sin(a) * r1)], w=3.5, color=YELLOW)
p.stroke([(x, 352 + math.sin(x / 90) * 2) for x in range(0, S + 1, 16)], w=2.2, color='#55555c')
for cx, cy, s in ((80, 190, .8),):  # outlined clouds
    m = np.clip(p.ell(cx, cy, 52 * s, 18 * s) + p.ell(cx - 24 * s, cy - 8 * s, 26 * s, 20 * s) + p.ell(cx + 14 * s, cy - 15 * s, 30 * s, 24 * s), 0, 1)
    p.paint(m, PAPER, hatch=False, fill=PAPER, line=3)
# the desk top the kid peeks over
desk = p.poly([(0, 572), (S, 570), (S, S), (0, S)])
p.paint(desk, '#8a8a90', wash=.22, hatch=False, line=0)
p.stroke([(x, 571 + math.sin(x / 70) * 1.5) for x in range(0, S + 1, 12)], w=4)
scene = p.image()
cover.alpha_composite(scene)

def paste(name, cx, cy, w, rot=0.0):
    im = Image.open(os.path.join(ASSETS, name + '.webp')).convert('RGBA')
    h = round(w * im.height / im.width)
    im = im.resize((w, h), Image.LANCZOS)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    # a soft pencil shadow
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    sh.putalpha(im.split()[3].point(lambda a: int(a * .2)))
    sh = sh.filter(ImageFilter.GaussianBlur(3))
    cover.alpha_composite(sh, (cx - im.width // 2 + 5, cy - im.height // 2 + 7))
    cover.alpha_composite(im, (cx - im.width // 2, cy - im.height // 2))

# the string from the pushpin to the candy, a little swung to the left
px, py = 250, 196
cx, cy = 150, 400
string = Image.open(os.path.join(ASSETS, 'rope.webp')).convert('RGBA')
L = int(math.hypot(cx - px, cy - py))
seg = string.resize((L, 16), Image.LANCZOS)
ang = math.degrees(math.atan2(cy - py, cx - px))
seg = seg.rotate(-ang, Image.BICUBIC, expand=True)
cover.alpha_composite(seg, ((px + cx) // 2 - seg.width // 2, (py + cy) // 2 - seg.height // 2))
paste('pin', px, py + 28, 76)  # the knob (14% down the pin) sits at the string's top end
paste('taffy', cx, cy, 160, rot=ang + 14)
paste('star', 300, 300, 80)
paste('star', 290, 470, 70)
paste("star", 568, 420, 66)
# Pip peeks over the desk (clipped by the desk)
pip = Image.open(os.path.join(ASSETS, 'pip-waiting.webp')).convert('RGBA')
w = 250
pip = pip.resize((w, round(w * pip.height / pip.width)), Image.LANCZOS)
layer = Image.new('RGBA', (S, S), (0, 0, 0, 0))
layer.alpha_composite(pip, (430 - w // 2, 572 - 190))
mask = Image.new('L', (S, S), 0)
ImageDraw.Draw(mask).rectangle([0, 0, S, 572], fill=255)
layer.putalpha(Image.fromarray(np.minimum(np.asarray(layer.split()[3]), np.asarray(mask))))
cover.alpha_composite(layer)
# redraw the desk edge line over Pip
edge = Pic(S, S, ss=2, line=4)
edge.stroke([(x, 571 + math.sin(x / 70) * 1.5) for x in range(0, S + 1, 12)], w=4)
cover.alpha_composite(edge.image())

# the title, hand-lettered and a little tilted, with a paper halo
font = ImageFont.truetype(FONT, 86)
t = Image.new('RGBA', (S, 200), (0, 0, 0, 0))
d = ImageDraw.Draw(t)
txt = 'Candy Snip'
tw = d.textlength(txt, font=font)
x0 = (S - tw) / 2
for dx in range(-6, 7, 2):
    for dy in range(-6, 7, 2):
        d.text((x0 + dx, 40 + dy), txt, font=font, fill=PAPER + (255,))
d.text((x0, 40), txt, font=font, fill=INK + (255,))
t = t.rotate(-2.5, Image.BICUBIC, expand=False)
cover.alpha_composite(t, (0, 4))

out = os.path.join(ROOT, 'src', 'img', 'candy-snip.jpg')
cover.convert('RGB').save(out, 'JPEG', quality=88)
print('wrote', out)
