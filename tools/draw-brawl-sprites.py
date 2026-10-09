#!/usr/bin/env python3
"""Draw Brawl sprites: the kids, their paint gear and the backyard props, drawn as
coloured-pencil doodles (ink outline, pale wash, bright two-way cross-hatching).

    python3 tools/draw-brawl-sprites.py            # writes src/assets/draw-brawl/*.webp
    python3 tools/draw-brawl-sprites.py --sheet x.png   # also a contact sheet for checking

Everything is drawn from code so it can be tweaked and re-run. Kid shirts are drawn in
purple: the game recolours that hue per player slot (orange / blue / green / yellow).
"""
import math, os, sys, random
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'src', 'assets', 'draw-brawl')

INK = (31, 31, 34)
PAPER = (246, 243, 234)
RED, ORANGE, YELLOW, GREEN = '#e0453a', '#f08a24', '#f2c230', '#4caf50'
BLUE, PURPLE, PINK, TEAL, BROWN = '#3a7bd5', '#8e5bc9', '#e86aa6', '#2fa7a0', '#9b6a3c'
SKIN = ['#f2c9a5', '#d9a37a', '#a8714a']
GREY = '#8a8a90'


def rgb(c):
    if isinstance(c, tuple):
        return c
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


class Pic:
    """A supersampled drawing surface. Coordinates are in final pixels."""

    def __init__(self, w, h, ss=3, line=7.0, hatch=9.0, hw=2.4, seed=1):
        self.w, self.h, self.ss = w, h, ss
        self.W, self.H = w * ss, h * ss
        self.col = np.zeros((self.H, self.W, 3))  # premultiplied colour
        self.a = np.zeros((self.H, self.W))
        self.line, self.hatch, self.hw = line, hatch, hw
        self.rng = random.Random(seed)
        self.ox = self.oy = 0.0  # shifts every shape (lets a drawing be moved inside its canvas)
        yy, xx = np.mgrid[0:self.H, 0:self.W]
        self.xx, self.yy = xx / ss, yy / ss
        # low-frequency noise used to break hatch lines into pencil strokes
        n = np.random.RandomState(seed).rand(self.H // 24 + 2, self.W // 24 + 2)
        n = ndimage.zoom(n, 24, order=1)[:self.H, :self.W]
        self.noise = n

    # ---- masks ----
    def _m(self, fn):
        img = Image.new('L', (self.W, self.H), 0)
        fn(ImageDraw.Draw(img), self.ss)
        return np.asarray(img, dtype=np.float64) / 255.0

    def ell(self, cx, cy, rx, ry):
        cx, cy = cx + self.ox, cy + self.oy
        return self._m(lambda d, s: d.ellipse([(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], fill=255))

    def poly(self, pts, wob=0.0):
        if wob:
            pts = [(x + self.rng.uniform(-wob, wob), y + self.rng.uniform(-wob, wob)) for x, y in pts]
        return self._m(lambda d, s: d.polygon([((x + self.ox) * s, (y + self.oy) * s) for x, y in pts], fill=255))

    def rrect(self, x0, y0, x1, y1, r):
        x0, x1, y0, y1 = x0 + self.ox, x1 + self.ox, y0 + self.oy, y1 + self.oy
        return self._m(lambda d, s: d.rounded_rectangle([x0 * s, y0 * s, x1 * s, y1 * s], radius=r * s, fill=255))

    def cap(self, pts, r):
        """thick polyline with round caps/joins (limbs, handles)"""
        def f(d, s):
            P = [((x + self.ox) * s, (y + self.oy) * s) for x, y in pts]
            d.line(P, fill=255, width=int(2 * r * s), joint='curve')
            for x, y in P:
                d.ellipse([x - r * s, y - r * s, x + r * s, y + r * s], fill=255)
        return self._m(f)

    def smooth(self, pts, n=12):
        """Catmull-Rom closed curve through points -> polygon"""
        out = []
        L = len(pts)
        for i in range(L):
            p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % L], pts[(i + 2) % L]
            for k in range(n):
                t = k / n
                t2, t3 = t * t, t * t * t
                out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
        return out

    def blob(self, pts):
        return self.poly(self.smooth(pts))

    # ---- painting ----
    def _over(self, alpha, color):
        c = np.array(rgb(color), dtype=np.float64) / 255.0
        alpha = np.clip(alpha, 0, 1)
        self.col = self.col * (1 - alpha[..., None]) + c * alpha[..., None]
        self.a = self.a * (1 - alpha) + alpha

    def hatchmask(self, angles=(45, -45), spacing=None, width=None, broken=0.25):
        sp = spacing or self.hatch
        w = width or self.hw
        tot = np.zeros((self.H, self.W))
        for k, ang in enumerate(angles):
            th = math.radians(ang)
            u = self.xx * math.cos(th) + self.yy * math.sin(th) + k * sp * 0.37
            d = np.abs(((u + sp / 2) % sp) - sp / 2)
            line = np.clip((w / 2 - d) * self.ss * 0.7 + 0.5, 0, 1)
            # pressure varies along the stroke, with a few gaps
            press = np.clip((self.noise if k == 0 else self.noise[::-1, ::-1]) * 1.6 - broken, 0, 1)
            tot = np.maximum(tot, line * (0.55 + 0.45 * press))
        return tot

    def outline_of(self, m, w):
        b = m > 0.5
        din = ndimage.distance_transform_edt(b)
        dout = ndimage.distance_transform_edt(~b)
        dist = np.where(b, din, dout) / self.ss
        return np.clip((w / 2 - dist) * self.ss + 0.5, 0, 1)

    def paint(self, m, color, wash=0.28, hatch=True, line=None, hatch_col=None, angles=(45, -45), hatch_alpha=0.9, spacing=None, fill=None):
        line = self.line if line is None else line
        self._over(m, fill if fill is not None else mix(PAPER, color, wash))
        if hatch:
            inner = ndimage.binary_erosion(m > 0.5, iterations=max(1, int(line * self.ss * 0.3))).astype(float)
            hm = self.hatchmask(angles, spacing) * inner * hatch_alpha
            self._over(hm, hatch_col or color)
        if line > 0:
            self._over(self.outline_of(m, line), INK)

    def stroke(self, pts, w=None, color=INK, closed=False):
        w = w or self.line * 0.6
        if closed:
            pts = list(pts) + [pts[0]]
        self._over(self.cap(pts, w / 2), color)

    def arc(self, cx, cy, r, a0, a1, w=None, color=INK, ry=None):
        ry = ry or r
        n = 24
        pts = [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
        self.stroke(pts, w, color)

    def dot(self, cx, cy, r, color=INK):
        self._over(self.ell(cx, cy, r, r), color)

    def image(self):
        # self.col is premultiplied (see _over): box-downsample, then un-premultiply
        s = self.ss
        pre = np.dstack([self.col, self.a])
        small = pre.reshape(self.h, s, self.w, s, 4).mean(axis=(1, 3)) * 255
        al = small[..., 3:4] / 255.0
        c = np.where(al > 0.003, small[..., :3] / np.maximum(al, 1e-6), 0)
        return Image.fromarray(np.dstack([c, small[..., 3:4]]).clip(0, 255).astype(np.uint8), 'RGBA')


# ------------------------------------------------------------------ kids
SHIRT = '#8f45e6'  # a vivid violet: the game recolours this hue per player slot, keeping its strength


def kid(name, pose='idle'):
    """front-facing kid, 170 x 210. Feet at y~200, head centre (85,70)."""
    p = Pic(170, 210, seed={'max': 3, 'ruby': 5, 'leo': 7}[name])
    skin = {'max': SKIN[0], 'ruby': SKIN[1], 'leo': SKIN[2]}[name]
    hx, hy, hr = 85, 72, 50
    yell = pose == 'attack'
    # back hair (ponytail sits behind the head)
    if name == 'ruby':
        sw = 6 if not yell else -4
        p.paint(p.blob([(118, 46), (150 + sw, 40), (166 + sw, 66), (156 + sw, 104), (140 + sw, 92), (132, 66)]), RED, wash=.3)
        p.paint(p.ell(128, 50, 10, 10), PINK, wash=.4, spacing=6)
    # legs + shoes
    for sx in (-1, 1):
        lx = hx + sx * 17
        p.paint(p.cap([(lx, 168), (lx + sx * (4 if yell else 2), 192)], 8.5), skin, wash=.0, hatch=False, fill=mix(PAPER, skin, .85))
        shoe = {'max': RED, 'ruby': PINK, 'leo': GREEN}[name]
        p.paint(p.ell(lx + sx * 7, 198, 15, 8.5), shoe, wash=.35, spacing=6)
    # shorts / skirt
    if name == 'ruby':
        p.paint(p.poly([(54, 150), (116, 150), (126, 178), (44, 178)], wob=1), TEAL, wash=.3)
    else:
        pc = BLUE if name == 'max' else BROWN
        p.paint(p.poly([(56, 148), (114, 148), (118, 178), (90, 178), (85, 166), (80, 178), (52, 178)], wob=1), pc, wash=.3)
    # shirt
    p.paint(p.blob([(60, 116), (85, 110), (110, 116), (122, 132), (116, 156), (85, 160), (54, 156), (48, 132)]), SHIRT, wash=.36, spacing=7.5)
    # arms: out of the sleeves, hands meeting in front of the tummy (the paint gear is drawn there by the game)
    arms = []
    for sx in (-1, 1):
        if yell:
            pts = [(hx + sx * 32, 128), (hx + sx * 41, 141), (hx + sx * 15, 137)]
        else:
            pts = [(hx + sx * 32, 128), (hx + sx * 39, 145), (hx + sx * 14, 143)]
        arms.append(pts)
        p.paint(p.cap(pts, 7), skin, hatch=False, fill=mix(PAPER, skin, .85), line=5)
    for sx in (-1, 1):  # short sleeves over the shoulders
        p.paint(p.ell(hx + sx * 30, 124, 13, 11), SHIRT, wash=.36, line=5.5, spacing=7.5)
    for pts in arms:
        p.paint(p.ell(pts[-1][0], pts[-1][1], 9.5, 9), skin, hatch=False, fill=mix(PAPER, skin, .85), line=4.5)
    # neck + head
    p.paint(p.ell(hx, hy, hr, hr * 0.94), skin, hatch=False, fill=mix(PAPER, skin, .8))
    # hair on top
    if name == 'max':
        spikes = []
        for i in range(11):
            a = math.pi + i / 10 * math.pi
            r = hr + (12 if i % 2 else 2)
            spikes.append((hx + math.cos(a) * r * 1.05, hy - 2 + math.sin(a) * r))
        spikes += [(hx + 50, hy + 4), (hx + 34, hy - 18), (hx + 14, hy - 12), (hx - 6, hy - 22), (hx - 26, hy - 12), (hx - 44, hy - 16), (hx - 52, hy + 4)]
        p.paint(p.poly(spikes, wob=1.5), BROWN, wash=.35)
    elif name == 'ruby':
        p.paint(p.blob([(hx - 52, hy + 10), (hx - 50, hy - 30), (hx - 20, hy - 54), (hx + 20, hy - 54), (hx + 50, hy - 30), (hx + 52, hy + 8), (hx + 38, hy - 16), (hx + 10, hy - 22), (hx - 14, hy - 14), (hx - 36, hy - 18)]), RED, wash=.3)
    else:  # leo: cap, hair tufts, glasses
        p.paint(p.blob([(hx - 50, hy - 6), (hx - 44, hy - 40), (hx, hy - 56), (hx + 44, hy - 40), (hx + 50, hy - 6), (hx, hy - 16)]), BLUE, wash=.3)
        p.paint(p.blob([(hx - 6, hy - 14), (hx + 40, hy - 18), (hx + 74, hy - 12), (hx + 70, hy - 2), (hx + 30, hy - 4), (hx - 2, hy - 4)]), BLUE, wash=.45, spacing=6)
        p.dot(hx, hy - 54, 5)
    # face
    ey = hy + 6
    if name == 'leo':
        for sx in (-1, 1):
            p.arc(hx + sx * 19, ey, 13, 0, 2 * math.pi, w=4.2)
        p.stroke([(hx - 6, ey - 1), (hx + 6, ey - 1)], w=4)
    if yell:
        for sx in (-1, 1):  # determined brows
            p.stroke([(hx + sx * 30, ey - 15), (hx + sx * 11, ey - 9)], w=4.2)
    for sx in (-1, 1):
        p.dot(hx + sx * 19, ey, 5.2)
        p.dot(hx + sx * 19 - 1.5, ey - 2, 1.6, PAPER)
        p._over(p.ell(hx + sx * 33, ey + 15, 8, 5) * .55, PINK)
    if yell:
        m = p.blob([(hx - 11, ey + 18), (hx + 11, ey + 18), (hx + 7, ey + 31), (hx - 7, ey + 31)])
        p.paint(m, RED, wash=.6, hatch=False, line=4)
    else:
        p.arc(hx, ey + 14, 13, 0.25, math.pi - 0.25, w=4.2)
    if name == 'max':  # freckles
        for dx, dy in ((-30, 10), (-26, 15), (26, 15), (30, 10)):
            p.dot(hx + dx, ey + dy, 1.6, BROWN)
    return p.image()


# ------------------------------------------------------------------ gear (drawn pointing right, grip at the left third)
def roller():
    p = Pic(150, 80, seed=11)
    p.paint(p.cap([(12, 48), (62, 44)], 6), BROWN, wash=.35, spacing=6)
    p.stroke([(62, 44), (80, 44), (86, 24), (100, 24)], w=5)
    p.paint(p.rrect(96, 8, 142, 40, 10), ORANGE, wash=.35, spacing=7)
    # paint drips
    for x, l in ((108, 14), (124, 22), (136, 10)):
        p.paint(p.cap([(x, 38), (x, 38 + l)], 4), ORANGE, wash=.6, hatch=False, line=3)
    return p.image()


def blaster():
    p = Pic(130, 80, seed=12)
    p.paint(p.rrect(14, 34, 104, 56, 10), GREEN, wash=.3, spacing=7)
    p.paint(p.rrect(98, 38, 122, 52, 5), YELLOW, wash=.4, spacing=6)
    p.paint(p.ell(52, 24, 18, 16), PINK, wash=.4, spacing=6)  # paint tank
    p.stroke([(52, 40), (52, 34)], w=4)
    p.paint(p.rrect(24, 52, 40, 74, 5), GREEN, wash=.3, hatch=False)
    return p.image()


def cannon():
    p = Pic(160, 90, seed=13)
    p.paint(p.rrect(14, 22, 136, 68, 14), BROWN, wash=.28, spacing=8)
    p.paint(p.ell(138, 45, 12, 24), BROWN, wash=.2, hatch=False)
    p.dot(138, 45, 12, INK)
    p.dot(138, 45, 8, mix(PAPER, BLUE, .45))
    for x in (46, 96):  # tape bands
        p.paint(p.rrect(x, 18, x + 14, 72, 3), YELLOW, wash=.35, spacing=5)
    return p.image()


def boxshield():
    p = Pic(120, 110, seed=14)
    p.paint(p.poly([(10, 26), (88, 26), (88, 104), (10, 104)], wob=1), BROWN, wash=.25, spacing=8)
    p.paint(p.poly([(10, 26), (34, 6), (112, 6), (88, 26)], wob=1), BROWN, wash=.12, spacing=8, angles=(20,))
    p.paint(p.poly([(88, 26), (112, 6), (112, 84), (88, 104)], wob=1), BROWN, wash=.45, spacing=6)
    p.stroke([(49, 26), (49, 50)], w=4)
    star(p, 49, 70, 20, YELLOW)
    return p.image()


def star(p, cx, cy, r, color, wash=.4, line=None, spacing=None):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        q = r if i % 2 == 0 else r * 0.47
        pts.append((cx + math.cos(a) * q, cy + math.sin(a) * q))
    p.paint(p.poly(pts), color, wash=wash, line=line, spacing=spacing)


def gold_star():
    p = Pic(96, 96, seed=15, line=6, hatch=7, hw=2.2)
    star(p, 48, 50, 42, YELLOW, wash=.5)
    p.dot(38, 46, 3.8)
    p.dot(58, 46, 3.8)
    p.arc(48, 54, 8, 0.3, math.pi - 0.3, w=3.4)
    return p.image()


def paint_blob(color, w=110, h=80, seed=16):
    p = Pic(w, h, seed=seed, line=5.5, hatch=6.5, hw=2)
    # a fat drop flying to the upper right, with a trail of droplets (the game rotates it)
    p.paint(p.blob([(52, 40), (66, 18), (92, 14), (104, 34), (94, 60), (66, 64)]), color, wash=.45)
    for x, y, r in ((36, 50, 8), (20, 58, 5.5), (9, 64, 3.5)):
        p.paint(p.ell(x, y, r, r), color, wash=.55, hatch=False, line=4)
    return p.image()


def ko_splat():
    p = Pic(256, 222, seed=17, line=7)
    pts = []
    rng = random.Random(4)
    for i in range(14):
        a = i / 14 * 2 * math.pi
        r = (78 if i % 2 else 52) * rng.uniform(0.85, 1.12)
        pts.append((128 + math.cos(a) * r * 1.2, 128 + math.sin(a) * r * 0.8))
    p.paint(p.blob(pts), PINK, wash=.4)
    for x, y, r in ((30, 150, 10), (226, 112, 12), (60, 196, 8), (200, 190, 9), (128, 30, 7)):
        p.paint(p.ell(x, y, r, r), PINK, wash=.5, hatch=False, line=5)
    for x, y, r in ((70, 52, 22), (186, 44, 26), (128, 18, 0)):
        if r:
            star(p, x, y, r, YELLOW, wash=.5)
    return p.image()


# ------------------------------------------------------------------ yard props
def box_fort():
    """the bank: a cardboard-box fort; the game hangs a team flag on the pole top at (51.5%, 6%)."""
    p = Pic(320, 300, seed=21, line=7.5, hatch=10, hw=2.6)
    pole_x = 320 * 0.515
    p.stroke([(pole_x, 18), (pole_x, 150)], w=6)
    def box(x0, y0, x1, y1, d=22, wash=.22, deco=None):
        p.paint(p.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], wob=1.2), BROWN, wash=wash, spacing=10)
        p.paint(p.poly([(x0, y0), (x0 + d, y0 - d * .8), (x1 + d, y0 - d * .8), (x1, y0)], wob=1), BROWN, wash=.1, spacing=10, angles=(15,), hatch_alpha=.6)
        p.paint(p.poly([(x1, y0), (x1 + d, y0 - d * .8), (x1 + d, y1 - d * .8), (x1, y1)], wob=1), BROWN, wash=.45, spacing=7)
        p.paint(p.rrect((x0 + x1) / 2 - 7, y0 - 2, (x0 + x1) / 2 + 7, y0 + 26, 2), YELLOW, wash=.4, hatch=False, line=3.5)
        if deco == 'star':
            star(p, (x0 + x1) / 2, (y0 + y1) / 2 + 10, 22, YELLOW)
        elif deco == 'window':
            p.paint(p.rrect((x0 + x1) / 2 - 22, (y0 + y1) / 2, (x0 + x1) / 2 + 22, (y0 + y1) / 2 + 14, 3), INK, wash=1, hatch=False, fill=(70, 70, 76))
        elif deco == 'splat':
            p.paint(p.blob([((x0 + x1) / 2 + math.cos(a) * r, (y0 + y1) / 2 + 8 + math.sin(a) * r * .8) for a, r in zip([i / 8 * 6.283 for i in range(8)], [20, 10, 22, 9, 18, 11, 21, 8])]), BLUE, wash=.5, line=4)
    box(30, 160, 130, 272, deco='splat')
    box(176, 150, 288, 272, deco='star')
    box(96, 76, 216, 176, deco='window')
    # little flag-pole cap
    p.dot(pole_x, 16, 6)
    return p.image()


def crate():
    p = Pic(284, 286, seed=22, line=7.5, hatch=10, hw=2.6)
    p.paint(p.poly([(30, 90), (226, 90), (226, 270), (30, 270)], wob=1.2), BROWN, wash=.3, spacing=10)
    p.paint(p.poly([(30, 90), (76, 40), (272, 40), (226, 90)], wob=1), BROWN, wash=.14, spacing=10, angles=(15,), hatch_alpha=.7)
    p.paint(p.poly([(226, 90), (272, 40), (272, 222), (226, 270)], wob=1), BROWN, wash=.5, spacing=7)
    for y in (140, 200):
        p.stroke([(34, y), (222, y)], w=5)
    p.stroke([(36, 96), (220, 264)], w=6)
    for y in (60, 76):
        p.stroke([(52 + (y - 60), y), (250 - (60 - y) * 0 - (y - 60), y)], w=3.5, color=mix(INK, PAPER, .3))
    return p.image()


def boxes():
    p = Pic(284, 286, seed=23, line=7.5, hatch=10, hw=2.6)
    def box(x0, y0, x1, y1, d, deco):
        p.paint(p.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], wob=1.2), BROWN, wash=.22, spacing=10)
        p.paint(p.poly([(x0, y0), (x0 + d, y0 - d * .8), (x1 + d, y0 - d * .8), (x1, y0)], wob=1), BROWN, wash=.1, spacing=10, angles=(15,), hatch_alpha=.6)
        p.paint(p.poly([(x1, y0), (x1 + d, y0 - d * .8), (x1 + d, y1 - d * .8), (x1, y1)], wob=1), BROWN, wash=.45, spacing=7)
        p.paint(p.rrect((x0 + x1) / 2 - 8, y0 - 2, (x0 + x1) / 2 + 8, y0 + 30, 2), YELLOW, wash=.4, hatch=False, line=3.5)
        if deco:
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 + 12
            p.paint(p.blob([(cx + math.cos(a) * r, cy + math.sin(a) * r * .85) for a, r in zip([i / 10 * 6.283 for i in range(10)], [24, 12, 26, 10, 22, 13, 25, 9, 21, 12])]), deco, wash=.5, line=4.5)
    box(20, 130, 150, 270, 30, RED)
    box(140, 150, 250, 270, 26, None)
    box(66, 50, 186, 150, 28, GREEN)
    return p.image()


def barrel():
    p = Pic(181, 180, seed=24, line=6.5, hatch=8.5, hw=2.4)
    p.paint(p.rrect(26, 34, 156, 168, 26), BROWN, wash=.3, spacing=8, angles=(60, -30))
    for y in (62, 140):
        p.paint(p.rrect(22, y - 6, 160, y + 6, 6), GREY, wash=.35, hatch=False, line=4)
    p.paint(p.ell(91, 36, 66, 22), BROWN, wash=.15, hatch=True, spacing=8, angles=(10,), hatch_alpha=.5)
    p.paint(p.ell(91, 36, 46, 13), BLUE, wash=.5, hatch=False, line=4)  # paint inside
    p.paint(p.cap([(140, 50), (146, 96)], 6), BLUE, wash=.55, hatch=False, line=4)
    return p.image()


def tires():
    p = Pic(181, 180, seed=25, line=6.5, hatch=8.5, hw=2.4)
    for cy in (128, 82):
        m = p.ell(90, cy, 74, 34) - p.ell(90, cy - 4, 34, 13)
        p.paint(np.clip(m, 0, 1), GREY, wash=.35, spacing=8)
    p.paint(p.ell(90, 78, 34, 13), GREEN, wash=.2, hatch=False, line=4)
    for x in (70, 88, 108):  # grass growing out of the top tyre
        p.stroke([(x, 82), (x + 6, 52)], w=4.5, color=rgb(GREEN))
    return p.image()


def tree():
    """backyard tree: trunk base at (33%, 98%) of the image (the game anchors it there)."""
    p = Pic(352, 337, seed=26, line=7.5, hatch=11, hw=2.8)
    bx, by = 352 * 0.33, 337 * 0.98
    p.paint(p.poly([(bx - 20, by), (bx - 12, by - 120), (bx + 14, by - 120), (bx + 24, by), (bx + 2, by - 10)], wob=1.5), BROWN, wash=.35, spacing=9)
    rng = random.Random(9)
    pts = []
    for i in range(16):
        a = i / 16 * 2 * math.pi
        r = (118 if i % 2 else 98) * rng.uniform(.95, 1.05)
        pts.append((190 + math.cos(a) * r * 1.35, 120 + math.sin(a) * r * .95))
    p.paint(p.blob(pts), GREEN, wash=.3)
    for x, y in ((140, 90), (230, 130), (196, 60), (262, 82), (130, 150)):
        p.arc(x, y, 18, 3.6, 5.6, w=4.2)
    for x, y in ((170, 120), (250, 160), (220, 70)):  # apples
        p.paint(p.ell(x, y, 10, 10), RED, wash=.6, hatch=False, line=4.5)
    return p.image()


def deco_grass():
    p = Pic(72, 72, seed=31, line=4)
    for x, a in ((22, -0.5), (34, -0.15), (46, 0.2), (56, 0.55)):
        p.stroke([(x, 64), (x + math.sin(a) * 34, 64 - math.cos(a) * 44)], w=4, color=rgb(GREEN))
    return p.image()


def deco_daisy():
    p = Pic(72, 72, seed=32, line=4, hatch=5, hw=1.6)
    for i in range(7):
        a = i / 7 * 2 * math.pi
        p.paint(p.ell(36 + math.cos(a) * 17, 36 + math.sin(a) * 17, 10, 10), PINK, wash=.25, hatch=False)
    p.paint(p.ell(36, 36, 11, 11), YELLOW, wash=.6, hatch=False)
    return p.image()


def deco_splat():
    p = Pic(72, 72, seed=33, line=4, hatch=5, hw=1.6)
    p.paint(p.blob([(36 + math.cos(a) * r, 36 + math.sin(a) * r) for a, r in zip([i / 10 * 6.283 for i in range(10)], [26, 13, 28, 11, 24, 14, 27, 10, 23, 13])]), BLUE, wash=.4)
    return p.image()


SPRITES = {
    'max_idle': lambda: kid('max'), 'max_attack': lambda: kid('max', 'attack'),
    'ruby_idle': lambda: kid('ruby'), 'ruby_attack': lambda: kid('ruby', 'attack'),
    'leo_idle': lambda: kid('leo'), 'leo_attack': lambda: kid('leo', 'attack'),
    'gear_roller': roller, 'gear_blaster': blaster, 'gear_cannon': cannon, 'gear_box': boxshield,
    'ko_splat': ko_splat, 'fort': box_fort, 'crate': crate, 'boxes': boxes, 'barrel': barrel, 'tires': tires,
    'tree': tree, 'star': gold_star, 'blob_purple': lambda: paint_blob(PURPLE), 'blob_blue': lambda: paint_blob(BLUE, seed=18),
    'deco_grass': deco_grass, 'deco_daisy': deco_daisy, 'deco_splat': deco_splat,
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
        cols = 6
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
