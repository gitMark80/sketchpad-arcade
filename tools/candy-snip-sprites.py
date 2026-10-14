#!/usr/bin/env python3
"""Candy Snip sprites: the pieces of Taffy Drop that were unmistakably beach things, redrawn as coloured-pencil
doodles for Sketchpad Arcade. Pip the baby seal becomes Pip the kid (waiting with his mouth open, munching,
sad), the starfish a gold star sticker, the boardwalk peg a pushpin, the rail a ruler, the beach ball a bouncy
ball, the rope ring a binder ring and the conch a party blower. The candy, string, bubble and scissor hand come
from sketchify.py (taffy.webp, rope.webp, bubble.webp, snip-hand.webp).

    python3 tools/candy-snip-sprites.py [names...] [--sheet out.png]   # writes src/assets/candy-snip/

Uses the pencil drawing helpers from tools/draw-brawl-sprites.py. Anchor points matter: the game puts the
pushpin's string knot at 14% down the image and Pip's open mouth at (56%, 30%) of his image.
"""
import importlib.util, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('pencil', os.path.join(HERE, 'draw-brawl-sprites.py'))
pen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pen)
Pic, mix, rgb, star = pen.Pic, pen.mix, pen.rgb, pen.star
INK, PAPER = pen.INK, pen.PAPER
RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK, TEAL, BROWN = pen.RED, pen.ORANGE, pen.YELLOW, pen.GREEN, pen.BLUE, pen.PURPLE, pen.PINK, pen.TEAL, pen.BROWN
SKIN = pen.SKIN
GREY = '#8a8a90'
OUT = os.path.join(os.path.dirname(HERE), 'src', 'assets', 'candy-snip')

SK = SKIN[0]
SKF = mix(PAPER, SK, .85)
HAIR = '#c9772a'   # ginger
SHIRT = GREEN


def pip(mood):
    """Pip, head and shoulders, 288x304. Mouth at (161, 91) = (56%, 30%)."""
    p = Pic(288, 304, seed=3, line=7, hatch=9, hw=2.4)
    cx, cy, r = 161, 60, 56
    # body: a striped t-shirt, arms resting on the desk edge
    body = p.blob([(70, 150), (161, 128), (252, 150), (268, 230), (262, 304), (60, 304), (54, 230)])
    p.paint(body, SHIRT, wash=.32, spacing=10)
    for y in (190, 232, 272):  # stripes
        band = np.clip(body * p.rrect(40, y, 282, y + 16, 2), 0, 1)
        p._over(band * .8, mix(PAPER, SHIRT, .7))
    # neck
    p.paint(p.rrect(cx - 20, 108, cx + 20, 140, 8), SK, hatch=False, fill=SKF)
    # arms + hands up on the desk
    for sgn in (-1, 1):
        ax = cx + sgn * 112
        p.paint(p.cap([(cx + sgn * 86, 170), (ax, 250), (ax + sgn * 4, 292)], 20), SHIRT, wash=.32, spacing=10)
        p.paint(p.ell(ax + sgn * 4, 292, 22, 18), SK, hatch=False, fill=SKF)
    # ears
    for sgn in (-1, 1):
        p.paint(p.ell(cx + sgn * (r + 4), cy + 8, 11, 14), SK, hatch=False, fill=SKF)
    # head
    p.paint(p.ell(cx, cy, r, r + 2), SK, hatch=False, fill=SKF)
    # hair: a spiky mop that sits on top of the head
    spikes = []
    n = 8
    for i in range(n + 1):
        a = math.pi * (1.0 + i / n)
        spikes.append((cx + math.cos(a) * (r - 2), cy + math.sin(a) * (r - 2) + 10))
        if i < n:
            b = a + math.pi / (2 * n)
            spikes.append((cx + math.cos(b) * (r + 26), cy + math.sin(b) * (r + 26) + 4))
    hair = np.clip(p.poly(spikes) - p.ell(cx, cy + 34, r - 4, r - 4), 0, 1)
    p.paint(hair, HAIR, wash=.45, spacing=7.5)
    # cheeks
    for sgn in (-1, 1):
        p._over(p.ell(cx + sgn * 36, cy + 22, 11, 7) * .5, PINK)
    # eyes
    ex, ey = 20, cy + 2
    if mood == 'munching':
        for sgn in (-1, 1):
            p.arc(cx + sgn * ex, ey + 4, 9, math.pi * 1.1, math.pi * 1.9, w=4.2)
    else:
        for sgn in (-1, 1):
            p.dot(cx + sgn * ex + (1 if mood == 'sad' else 0), ey + 1, 6.5)
            p.dot(cx + sgn * ex - 2, ey - 2, 2.2, PAPER)
        if mood == 'sad':
            for sgn in (-1, 1):
                p.stroke([(cx + sgn * 30, ey - 20), (cx + sgn * 10, ey - 13)], w=4)
    # nose
    p.arc(cx + 1, cy + 12, 5, .3, math.pi - .6, w=3.4)
    # mouth, at (161, 91)
    my = 91
    if mood == 'waiting':
        m = p.ell(cx, my + 2, 18, 14)
        p.paint(m, '#a0303c', wash=.75, hatch=False, line=4.5)
        p._over(p.ell(cx, my + 9, 10, 5), mix(PAPER, PINK, .8))  # tongue
        p._over(p.rrect(cx - 13, my - 11, cx + 13, my - 5, 2) * p.ell(cx, my + 2, 17, 13), PAPER)  # teeth
    elif mood == 'munching':
        p.arc(cx, my - 6, 14, .25, math.pi - .25, w=4.5)
        # puffed cheek lines
        p.arc(cx - 40, my - 4, 8, math.pi * .3, math.pi * 1.2, w=3)
        p.arc(cx + 40, my - 4, 8, -math.pi * .2, math.pi * .7, w=3)
    else:
        p.arc(cx, my + 10, 12, math.pi + .3, 2 * math.pi - .3, w=4.5)
        # a tear
        p.paint(p.blob([(cx - 34, ey + 8), (cx - 28, ey + 18), (cx - 34, ey + 30), (cx - 40, ey + 18)]), BLUE, wash=.4, hatch=False, line=3.5)
    return p.image()


def gold_star():
    """A gold star sticker: a paper sticker border round a hatched yellow star. Drawn at 40px wide."""
    p = Pic(120, 116, seed=15, line=6, hatch=7, hw=2.2)
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        q = 52 if i % 2 == 0 else 24
        pts.append((60 + math.cos(a) * q, 60 + math.sin(a) * q))
    p.paint(p.poly(pts), PAPER, hatch=False, fill=mix(PAPER, GREY, .12), line=4)  # sticker backing
    star(p, 60, 60, 44, YELLOW, wash=.55, line=5.5)
    p.dot(52, 56, 3.4)
    p.dot(68, 56, 3.4)
    p.arc(60, 63, 7, 0.3, math.pi - 0.3, w=3)
    return p.image()


def pushpin():
    """A pushpin stuck in the page, 120x124. The string ties on at 14% down: the top of the knob."""
    p = Pic(120, 124, seed=5, line=6, hatch=8, hw=2.3)
    # needle
    p.paint(p.poly([(56, 64), (64, 64), (60.5, 122)]), GREY, wash=.5, hatch=False, line=3.5)
    # flared base
    p.paint(p.poly([(30, 64), (90, 64), (82, 46), (38, 46)]), RED, wash=.42, spacing=7)
    # knob (its top sits at y = 17 = 14%)
    p.paint(p.rrect(44, 12, 76, 50, 10), RED, wash=.42, spacing=7)
    # the string knot
    p.arc(60, 17, 7, 0, 2 * math.pi, w=3.6, color='#8a6a3a')
    return p.image()


def ruler():
    """A 320x34 strip tiled along the sliding-pin track."""
    p = Pic(320, 34, seed=8, line=5, hatch=8, hw=2)
    p.paint(p.rrect(2, 5, 318, 29, 3), YELLOW, wash=.3, hatch=False, line=4)
    p.paint(p.rrect(2, 5, 318, 29, 3), YELLOW, wash=0, hatch=True, line=0, angles=(60,), hatch_alpha=.35, spacing=9)
    for x in range(6, 320, 8):
        h = 12 if x % 40 == 6 else 7 if x % 40 == 26 else 4
        p.stroke([(x, 6), (x, 6 + h)], w=2.2)
    return p.image()


def bouncy_ball():
    """A rubber bouncy ball with a swirl, 128x128."""
    p = Pic(128, 128, seed=11, line=6.5, hatch=8, hw=2.4)
    c = 64
    p.paint(p.ell(c, c, 58, 58), RED, wash=.35, spacing=9)
    # a blue swirl band through the middle
    band = p.blob([(10, 40), (44, 30), (84, 50), (118, 44), (112, 78), (76, 90), (40, 74), (8, 84)])
    band = np.clip(band * p.ell(c, c, 58, 58), 0, 1)
    p.paint(band, BLUE, wash=.4, line=3.5, spacing=8)
    p._over(p.outline_of(p.ell(c, c, 58, 58), 6.5), INK)
    # a pencil highlight arc
    p.arc(c - 22, c - 22, 14, math.pi * 1.05, math.pi * 1.6, w=3, color=GREY)
    return p.image()


def binder_ring():
    """A metal binder ring with a little hinge, 128x128."""
    p = Pic(128, 128, seed=12, line=6, hatch=8, hw=2.2)
    c = 64
    ring = np.clip(p.ell(c, c, 56, 56) - p.ell(c, c, 38, 38), 0, 1)
    p.paint(ring, BLUE, wash=.3, spacing=8, angles=(45,), hatch_alpha=.6)
    # hinge and clasp
    p.paint(p.rrect(c - 14, 4, c + 14, 22, 5), GREY, wash=.5, hatch=False, line=4)
    p.paint(p.rrect(c - 10, 106, c + 10, 124, 4), GREY, wash=.5, hatch=False, line=4)
    p.stroke([(c, 106), (c, 124)], w=2.4)
    return p.image()


def party_blower():
    """A party blower, mouthpiece on the left, paper roll pointing right (the puff direction). 160x118."""
    p = Pic(160, 118, seed=13, line=6, hatch=8, hw=2.3)
    # mouthpiece
    p.paint(p.rrect(4, 42, 46, 76, 10), YELLOW, wash=.45, spacing=7)
    p.paint(p.rrect(40, 36, 60, 82, 6), GREY, wash=.45, hatch=False, line=4)
    # the stretched-out paper tube with stripes
    tube = p.rrect(56, 46, 140, 72, 8)
    p.paint(tube, PINK, wash=.4, hatch=False)
    for x in range(64, 136, 14):
        p._over(np.clip(tube * p.rrect(x, 40, x + 7, 80, 1), 0, 1) * .85, mix(PAPER, PURPLE, .6))
    p._over(p.outline_of(tube, 5), INK)
    # the curled end
    p.paint(p.ell(146, 50, 13, 13), PINK, wash=.45, spacing=6)
    p.arc(146, 50, 6, 0, 5.5, w=3)
    # a few motion lines out of the end
    for dy in (-10, 0, 10):
        p.stroke([(150 + abs(dy) * .2, 72 + dy * 1.6), (158, 74 + dy * 1.8)], w=2.4, color=GREY)
    return p.image()


SPRITES = {
    'pip-waiting': lambda: pip('waiting'),
    'pip-munching': lambda: pip('munching'),
    'pip-sad': lambda: pip('sad'),
    'star': gold_star,
    'pin': pushpin,
    'ruler': ruler,
    'ball': bouncy_ball,
    'ring': binder_ring,
    'blower': party_blower,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    only = [a for a in sys.argv[1:] if not a.startswith('--') and a in SPRITES]
    imgs = {}
    for k, f in SPRITES.items():
        if only and k not in only:
            continue
        im = f()
        im.save(os.path.join(OUT, k + '.webp'), 'WEBP', quality=88, method=6)
        imgs[k] = im
        print(k, im.size)
    if '--sheet' in sys.argv:
        path = sys.argv[sys.argv.index('--sheet') + 1]
        cols = 5
        cell = 240
        rows = (len(imgs) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * cell, rows * cell), PAPER + (255,))
        for i, (k, im) in enumerate(imgs.items()):
            t = im.copy()
            t.thumbnail((cell - 16, cell - 16))
            sheet.paste(t, ((i % cols) * cell + 8, (i // cols) * cell + 8), t)
        sheet.save(path)


if __name__ == '__main__':
    main()
