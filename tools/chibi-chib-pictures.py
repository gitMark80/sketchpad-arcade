#!/usr/bin/env python3
"""Chibi Chib picture maker.

Draws each chibi animal at high resolution (S px per grid cell) with simple shapes
(ellipses, polygons, thick lines) using only the game's 15 coloured-pencil gem colours,
then downsamples to an n x n grid (weighted majority per cell, black outlines and eye
highlights win ties) and writes them into src/games/chibi-chib.html between the
/*PICS-BEGIN*/ ... /*PICS-END*/ markers, in the game's own format:
  {name, n, colors:[hex...], map:"..abba.."}   ("." = not part of the picture, a.. = colour index)

Usage: python3 tools/chibi-chib-pictures.py [--preview DIR] [--no-write]
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, '..', 'src', 'games', 'chibi-chib.html')

PAL = {  # the gem colours (vivid coloured pencil)
    'R': '#e0453a', 'O': '#f08a24', 'Y': '#f2c230', 'L': '#8bc34a', 'G': '#4caf50',
    'T': '#2fa7a0', 'S': '#4fb3e8', 'B': '#3a7bd5', 'P': '#8e5bc9', 'K': '#e86aa6',
    'N': '#9b6a3c', 'E': '#9aa0a6', 'X': '#2b2b2f', 'W': '#fbfaf6', 'H': '#f2c9a5',
}
KEYS = list(PAL)
IDX = {k: i for i, k in enumerate(KEYS)}
X = 'X'
OL = 1.05  # outline width in cells
S = 12     # hi-res pixels per cell


class Pic:
    def __init__(self, name, n):
        self.name, self.n = name, n
        self.W = n * S
        self.u = self.W / 100.0
        self.img = np.full((self.W, self.W), -1, np.int16)
        self.prio = np.zeros((self.W, self.W), bool)
        c = (np.arange(self.W) + .5) / self.u
        self.yy, self.xx = np.meshgrid(c, c, indexing='ij')

    # ---- shapes (all coordinates in units: 0..100 across the picture) ----
    def ell(self, cx, cy, rx, ry, rot=0):
        x, y = self.xx - cx, self.yy - cy
        if rot:
            a = math.radians(rot)
            x, y = x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)
        return (x / rx) ** 2 + (y / ry) ** 2 <= 1

    def circ(self, cx, cy, r):
        return self.ell(cx, cy, r, r)

    def rect(self, x0, y0, x1, y1):
        return (self.xx >= x0) & (self.xx <= x1) & (self.yy >= y0) & (self.yy <= y1)

    def _im(self):
        return Image.new('L', (self.W, self.W), 0)

    def poly(self, pts):
        im = self._im()
        ImageDraw.Draw(im).polygon([(x * self.u, y * self.u) for x, y in pts], fill=255)
        return np.array(im) > 127

    def line(self, pts, w):
        """w in cells"""
        im = self._im(); d = ImageDraw.Draw(im); px = max(1, int(round(w * S)))
        P = [(x * self.u, y * self.u) for x, y in pts]
        d.line(P, fill=255, width=px, joint='curve')
        r = px / 2
        for x, y in (P[0], P[-1]):
            d.ellipse((x - r, y - r, x + r, y + r), fill=255)
        return np.array(im) > 127

    def arc(self, cx, cy, rx, ry, a0, a1, w, k=24):
        pts = [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / k)),
                cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / k))) for i in range(k + 1)]
        return self.line(pts, w)

    def shift(self, m, dx, dy):
        sx, sy = int(round(dx * self.u)), int(round(dy * self.u))
        out = np.zeros_like(m)
        H = m.shape[0]
        ys = slice(max(0, sy), H + min(0, sy)); yd = slice(max(0, -sy), H + min(0, -sy))
        xs = slice(max(0, sx), H + min(0, sx)); xd = slice(max(0, -sx), H + min(0, -sx))
        out[ys, xs] = m[yd, xd]
        return out

    # ---- painting ----
    def paint(self, m, col, ol=OL, prio=False):
        if ol:
            d = distance_transform_edt(~m) <= ol * S * .95
            self.img[d & ~m] = IDX[X]; self.prio[d & ~m] = False
        self.img[m] = IDX[col]; self.prio[m] = prio
        return m

    def fill(self, m, col, prio=False):
        return self.paint(m, col, 0, prio)

    def shade(self, m, col, ox, oy, clip=None):
        """colour the side of shape m facing (ox,oy) (a crescent ox,oy units thick)"""
        r = m & ~self.shift(m, -ox, -oy)
        if clip is not None: r &= clip
        self.fill(r, col)

    def ink(self, m, prio=True):
        return self.fill(m, X, prio)

    # ---- downsample ----
    def grid(self):
        n = self.n
        img = self.img.reshape(n, S, n, S).transpose(0, 2, 1, 3).reshape(n, n, S * S)
        pr = self.prio.reshape(n, S, n, S).transpose(0, 2, 1, 3).reshape(n, n, S * S)
        out = np.full((n, n), -1, int)
        tot = S * S
        for y in range(n):
            for x in range(n):
                v = img[y, x]
                cnt = np.bincount(v + 1, minlength=len(KEYS) + 1)
                if cnt[0] > tot * .5: continue
                pv = v[pr[y, x]]
                if len(pv):
                    pc = np.bincount(pv, minlength=len(KEYS))
                    if pc.max() >= tot * .26:
                        out[y, x] = int(pc.argmax()); continue
                sc = cnt[1:].astype(float)
                sc[IDX['X']] *= 1.55
                out[y, x] = int(sc.argmax())
        return out


# ------------------------------------------------------------------ chibi parts
def eye(p, cx, cy, rx=6.2, ry=7.6, iris=None, glint='W'):
    e = p.ell(cx, cy, rx, ry)
    p.fill(e, X, prio=True)
    if iris:
        p.fill(e & p.ell(cx, cy + ry * .55, rx * .78, ry * .55) & p.ell(cx, cy, rx * .78, ry * .8), iris, prio=True)
    p.fill(p.ell(cx - rx * .3, cy - ry * .33, rx * .44, ry * .38), glint, prio=True)
    p.fill(p.ell(cx + rx * .36, cy + ry * .3, rx * .24, ry * .21), glint, prio=True)


def eyes(p, cx=50, cy=46, dx=14, **k):
    eye(p, cx - dx, cy, **k); eye(p, cx + dx, cy, **k)


def blush(p, cx=50, cy=56, dx=23, rx=5.2, ry=3, col='K'):
    p.fill(p.ell(cx - dx, cy, rx, ry), col)
    p.fill(p.ell(cx + dx, cy, rx, ry), col)


def cat_mouth(p, cx=50, cy=56, r=3.2, w=.9):
    p.ink(p.arc(cx - r, cy, r, r * .9, 10, 170, w))
    p.ink(p.arc(cx + r, cy, r, r * .9, 10, 170, w))


def smile(p, cx=50, cy=57, r=4, w=.9):
    p.ink(p.arc(cx, cy - r * .4, r, r * .8, 20, 160, w))


def head(p, col, cx=50, cy=42, rx=36, ry=30, shade=None, hl=None):
    m = p.paint(p.ell(cx, cy, rx, ry), col)
    if shade: p.shade(m, shade, 4, 5)
    if hl: p.fill(p.ell(cx - rx * .55, cy - ry * .62, rx * .16, ry * .08, -28) & m, hl, prio=True)
    return m


def body(p, col, cx=50, cy=80, rx=20, ry=14, shade=None, belly=None):
    m = p.paint(p.ell(cx, cy, rx, ry), col)
    if shade: p.shade(m, shade, 4, 3)
    if belly: p.fill(p.ell(cx, cy + 2, rx * .55, ry * .7) & m, belly)
    return m


def feet(p, col, cx=50, cy=93, dx=10, rx=7, ry=4.6):
    p.paint(p.ell(cx - dx, cy, rx, ry), col)
    p.paint(p.ell(cx + dx, cy, rx, ry), col)


def arms(p, col, cx=50, cy=79, dx=14, rx=5.5, ry=6.5):
    p.paint(p.ell(cx - dx, cy, rx, ry, 20), col)
    p.paint(p.ell(cx + dx, cy, rx, ry, -20), col)


def flower(p, cx, cy, r, petal='K', mid='Y'):
    for k in range(5):
        a = math.radians(k * 72 - 90)
        p.paint(p.circ(cx + math.cos(a) * r, cy + math.sin(a) * r, r * .72), petal)
    p.paint(p.circ(cx, cy, r * .55), mid)


def heart(p, cx, cy, r, col='R'):
    m = p.circ(cx - r * .5, cy, r * .58) | p.circ(cx + r * .5, cy, r * .58) | \
        p.poly([(cx - r * 1.05, cy + r * .15), (cx + r * 1.05, cy + r * .15), (cx, cy + r * 1.25)])
    p.paint(m, col)


# ------------------------------------------------------------------ the chibis
def kitty(n=40):
    p = Pic('Kitty', n)
    # tail
    p.paint(p.line([(70, 86), (82, 82), (88, 72), (86, 62)], 3.2), 'O')
    p.fill(p.line([(84.5, 70), (87, 66)], 2.6) , 'N')
    # ears
    for s in (-1, 1):
        e = p.paint(p.poly([(50 + s * 33, 36), (50 + s * 30, 4), (50 + s * 12, 18)]), 'O')
        p.fill(p.poly([(50 + s * 29, 30), (50 + s * 28, 11), (50 + s * 17, 20)]), 'K')
    body(p, 'O', shade='N', belly='W')
    feet(p, 'W')
    m = head(p, 'O', shade='N', hl='Y')
    # stripes on the forehead
    for dx in (-7, 0, 7):
        p.fill(p.poly([(50 + dx - 2.4, 12), (50 + dx + 2.4, 12), (50 + dx, 22)]) & m, 'N')
    p.fill(p.ell(50, 60, 16, 9) & m, 'W')  # muzzle
    eyes(p, cy=45, iris='T')
    blush(p, cy=57)
    p.paint(p.poly([(47, 53), (53, 53), (50, 56.5)]), 'K', ol=.6)
    cat_mouth(p, cy=57)
    for s in (-1, 1):  # whiskers
        p.ink(p.line([(50 + s * 28, 60), (50 + s * 40, 58)], .8))
        p.ink(p.line([(50 + s * 28, 64), (50 + s * 39, 66)], .8))
    # collar + bell
    p.paint(p.ell(50, 71, 16, 2.6), 'R', ol=.7)
    p.paint(p.circ(50, 74.5, 3.4), 'Y')
    arms(p, 'O', cy=81)
    return p


def puppy(n=40):
    p = Pic('Puppy', n)
    p.paint(p.line([(68, 86), (80, 80), (84, 70)], 3), 'N')  # wagging tail
    body(p, 'W', shade='E')
    feet(p, 'W')
    p.fill(p.ell(42, 93, 3, 2) , 'K'); p.fill(p.ell(58, 93, 3, 2), 'K')
    m = head(p, 'W', cy=42, rx=35, ry=29, shade='E')
    p.fill(p.ell(36, 42, 11, 11, 20) & m, 'N')  # patch over one eye
    # floppy ears
    for s in (-1, 1):
        e = p.paint(p.ell(50 + s * 34, 40, 9, 17, s * -18), 'N')
        p.shade(e, 'X' if False else 'O', s * -2.5, 3)
    eyes(p, cy=45, iris='N')
    blush(p, cy=57, col='K')
    p.paint(p.ell(50, 53.5, 4.6, 3.2), 'X', ol=0)
    p.fill(p.ell(48.6, 52.6, 1.6, 1), 'W', prio=True)
    p.paint(p.ell(50, 61.5, 3.2, 3.8), 'K', ol=.7)  # tongue
    cat_mouth(p, cy=57, r=3)
    p.paint(p.ell(50, 70.5, 17, 2.8), 'R', ol=.7)
    p.paint(p.circ(50, 74.5, 3.4), 'Y')
    arms(p, 'W', cy=81)
    return p


def bunny(n=42):
    p = Pic('Bunny', n)
    for s in (-1, 1):
        e = p.paint(p.ell(50 + s * 13, 18, 7.5, 18, s * 10), 'W')
        p.fill(p.ell(50 + s * 13.4, 20, 3.8, 13, s * 10), 'K')
    p.shade(p.ell(63, 18, 7.5, 18, 10), 'E', 2.5, 2)
    body(p, 'W', cy=82, shade='E')
    p.paint(p.circ(70, 88, 6), 'W')  # puff tail
    feet(p, 'W')
    m = head(p, 'W', cy=50, rx=34, ry=27, shade='E')
    flower(p, 33, 27, 4.2, 'Y', 'O')
    eyes(p, cy=52, iris='P', dx=13.5)
    blush(p, cy=62, dx=22)
    p.paint(p.poly([(47, 59), (53, 59), (50, 62)]), 'K', ol=.6)
    cat_mouth(p, cy=63, r=2.8)
    arms(p, 'W', cy=82)
    return p


def piglet(n=42):
    p = Pic('Piglet', n)
    p.paint(p.arc(76, 80, 4.5, 4.5, -180, 150, 2.2), 'K')  # curly tail
    for s in (-1, 1):
        e = p.paint(p.poly([(50 + s * 34, 28), (50 + s * 30, 6), (50 + s * 14, 16)]), 'H')
        p.fill(p.poly([(50 + s * 30, 23), (50 + s * 29, 11), (50 + s * 19, 18)]), 'K')
    body(p, 'H', cy=81, shade='K')
    feet(p, 'K', ry=4)
    m = head(p, 'H', cy=44, shade='K', hl='W')
    eyes(p, cy=42, iris='S', dx=15)
    blush(p, cy=55, dx=25, col='R')
    s = p.paint(p.ell(50, 56, 9.5, 6.5), 'K')
    p.fill(p.ell(50, 55, 7, 4) & s, 'K')
    p.ink(p.ell(46.5, 56, 1.6, 2.4)); p.ink(p.ell(53.5, 56, 1.6, 2.4))
    smile(p, cy=67, r=3)
    arms(p, 'H', cy=80)
    return p


def frog(n=44):
    p = Pic('Frog', n)
    body(p, 'G', cy=81, rx=21, shade='T', belly='L')
    for s in (-1, 1):
        p.paint(p.ell(50 + s * 18, 93, 9, 4.5), 'G')
    m = head(p, 'G', cy=48, rx=38, ry=26, shade='T')
    # bulging eyes on top
    for s in (-1, 1):
        e = p.paint(p.circ(50 + s * 18, 28, 13), 'G')
        p.shade(e, 'T', 2.5, 3)
        p.fill(p.circ(50 + s * 18, 28, 9.5), 'W')
        eye(p, 50 + s * 18, 29, 6, 7, iris='S')
    p.paint(p.circ(50, 20, 4.4), 'K')  # little flower crown
    flower(p, 50, 20, 4.2, 'K', 'Y')
    blush(p, cy=52, dx=25, rx=6, ry=3.4)
    p.ink(p.arc(50, 50, 13, 8, 20, 160, 1.0))  # wide smile
    p.ink(p.ell(46, 44, .9, 1)); p.ink(p.ell(54, 44, .9, 1))
    arms(p, 'G', cy=80, dx=15)
    return p


def hamster(n=44):
    p = Pic('Hamster', n)
    for s in (-1, 1):
        p.paint(p.circ(50 + s * 27, 16, 9), 'O')
        p.fill(p.circ(50 + s * 27, 17, 5), 'K')
    m = p.paint(p.ell(50, 54, 38, 38), 'O')  # round loaf body+head
    p.shade(m, 'N', 4, 5)
    p.fill(p.ell(50, 68, 28, 22) & m, 'W')   # white cheeks + belly
    p.fill(p.ell(28, 28, 6, 3, -30) & m, 'Y', prio=True)
    eyes(p, cy=46, dx=15, rx=5.6, ry=6.8, iris='N')
    blush(p, cy=58, dx=26, rx=6.5, ry=3.8)
    p.paint(p.ell(50, 54.5, 2.6, 1.8), 'K', ol=.6)
    cat_mouth(p, cy=58, r=2.6)
    # paws holding a seed
    seed = p.paint(p.ell(50, 74, 6, 9), 'E')
    p.fill(p.line([(50, 66), (50, 82)], 1) & seed, 'X')
    p.paint(p.ell(42, 75, 4.5, 3.5), 'H', ol=.8); p.paint(p.ell(58, 75, 4.5, 3.5), 'H', ol=.8)
    feet(p, 'H', cy=92, dx=16, rx=6, ry=3.6)
    return p


def panda(n=46, name='Panda'):
    p = Pic(name, n)
    for s in (-1, 1):
        p.paint(p.circ(50 + s * 28, 15, 9), 'X')
    body(p, 'W', cy=81, shade='E')
    feet(p, 'X')
    p.fill(p.ell(40, 94, 3.6, 2) , 'E'); p.fill(p.ell(60, 94, 3.6, 2), 'E')
    m = head(p, 'W', shade='E')
    for s in (-1, 1):
        p.fill(p.ell(50 + s * 14, 46, 9, 11, s * -25), X)
        eye(p, 50 + s * 13.5, 46, 4.6, 5.6, iris='B')
    blush(p, cy=59, dx=24, rx=5, ry=2.8)
    p.paint(p.ell(50, 55, 4, 2.6), 'X', ol=0)
    cat_mouth(p, cy=59, r=2.6)
    arms(p, 'X', cy=80, dx=16, rx=5, ry=6.5)
    return p


def penguin(n=46):
    p = Pic('Penguin', n)
    feet(p, 'O', cy=94, dx=11, rx=7.5, ry=4)
    b = p.paint(p.ell(50, 74, 26, 22), 'X')
    p.fill(p.ell(50, 78, 18, 17) & b, 'W')
    p.shade(p.ell(50, 78, 18, 17) & b, 'E', 3, 3)
    for s in (-1, 1):  # flippers
        p.paint(p.ell(50 + s * 26, 72, 5, 12, s * -30), 'X')
    m = p.paint(p.ell(50, 38, 35, 30), 'X')
    p.fill(p.ell(36, 15, 6, 2.6, -25) & m, 'E', prio=True)
    face = p.ell(42, 44, 15, 17) | p.ell(58, 44, 15, 17) | p.ell(50, 54, 24, 13)
    p.fill(face & m, 'W')
    p.shade(face & m, 'E', 2, 3)
    eyes(p, cy=44, dx=12.5, rx=5.4, ry=6.6, iris='S')
    blush(p, cy=55, dx=21, rx=4.8)
    p.paint(p.poly([(44.5, 51), (55.5, 51), (50, 58)]), 'O', ol=.7)
    # scarf
    p.paint(p.ell(50, 66, 24, 4.4), 'R', ol=.8)
    p.paint(p.poly([(58, 66), (68, 66), (70, 82), (61, 81)]), 'R', ol=.8)
    p.fill(p.line([(60, 75), (69, 75)], .8), 'W')
    return p


def fox(n=48):
    p = Pic('Fox', n)
    tail = p.paint(p.ell(78, 72, 11, 19, 35), 'O')
    p.fill(p.ell(86, 60, 6, 7, 35) & tail, 'W')
    p.shade(tail, 'N', 3, 3, clip=~p.ell(86, 60, 6, 7, 35))
    for s in (-1, 1):
        e = p.paint(p.poly([(50 + s * 36, 40), (50 + s * 33, 2), (50 + s * 12, 20)]), 'O')
        p.fill(p.poly([(50 + s * 33.5, 3), (50 + s * 34.5, 13), (50 + s * 27, 9)]), 'X')
        p.fill(p.poly([(50 + s * 31, 32), (50 + s * 31, 14), (50 + s * 18, 22)]), 'H')
    body(p, 'O', cy=81, shade='N', belly='W')
    feet(p, 'N', ry=4.2)
    m = head(p, 'O', cy=44, rx=38, ry=28, shade='N', hl='Y')
    # white cheeks
    p.fill(p.poly([(12, 50), (30, 58), (50, 63), (70, 58), (88, 50), (80, 66), (50, 72), (20, 66)]) & m, 'W')
    eyes(p, cy=45, dx=15, iris='Y')
    blush(p, cy=57, dx=24, col='K')
    p.paint(p.ell(50, 56, 3.4, 2.4), 'X', ol=0)
    cat_mouth(p, cy=60, r=2.6)
    arms(p, 'O', cy=81, rx=4.5, ry=5.5)
    return p


def owl(n=48):
    p = Pic('Owl', n)
    p.paint(p.rect(4, 89, 96, 96), 'N', ol=.9)  # branch
    p.paint(p.ell(90, 86, 6, 3, -30), 'G', ol=.8)
    p.paint(p.ell(10, 86, 6, 3, 30), 'G', ol=.8)
    b = p.paint(p.ell(50, 54, 36, 38), 'N')
    p.shade(b, 'X', 3, 3)
    for s in (-1, 1):  # ear tufts
        p.paint(p.poly([(50 + s * 30, 30), (50 + s * 34, 5), (50 + s * 14, 20)]), 'N')
        p.paint(p.ell(50 + s * 33, 60, 7, 18, s * -12), 'N')  # wings
        p.shade(p.ell(50 + s * 33, 60, 7, 18, s * -12), 'O', s * -2, 2)
    belly = p.fill(p.ell(50, 68, 18, 18) & b, 'H')
    for (x, y) in [(44, 60), (56, 60), (50, 67), (44, 74), (56, 74)]:
        p.ink(p.arc(x, y - 2, 3, 2.4, 30, 150, .8) & belly, prio=False)
    for s in (-1, 1):
        p.paint(p.circ(50 + s * 14, 36, 13), 'H')
        p.fill(p.circ(50 + s * 14, 36, 9.5), 'Y')
        eye(p, 50 + s * 14, 36.5, 6.2, 7, iris='O')
    p.paint(p.poly([(46, 45), (54, 45), (50, 53)]), 'O', ol=.7)
    blush(p, cy=50, dx=26, rx=4.2, ry=2.6)
    for x in (40, 50, 60):
        p.paint(p.ell(x, 89, 3, 3.6), 'Y', ol=.6)
    return p


def bear(n=50):
    p = Pic('Bear Cub', n)
    for s in (-1, 1):
        p.paint(p.circ(50 + s * 28, 15, 10), 'N')
        p.fill(p.circ(50 + s * 28, 16, 5.5), 'H')
    body(p, 'N', cy=81, belly='H')
    feet(p, 'N')
    p.fill(p.ell(40, 93, 4, 2.4), 'H'); p.fill(p.ell(60, 93, 4, 2.4), 'H')
    m = head(p, 'N', hl='O')
    p.fill(p.ell(70, 22, 6, 3, 28) & m, 'O', prio=True)
    p.fill(p.ell(50, 57, 13, 10) & m, 'H')
    eyes(p, cy=44, dx=16, rx=5.8, ry=7, iris='O')
    blush(p, cy=55, dx=25)
    p.paint(p.ell(50, 52.5, 4.4, 3), 'X', ol=0)
    p.fill(p.ell(48.8, 51.6, 1.6, 1), 'W', prio=True)
    cat_mouth(p, cy=57, r=3)
    # honey pot in the paws
    pot = p.paint(p.ell(50, 81, 11, 10), 'Y')
    p.shade(pot, 'O', 3, 3)
    p.paint(p.ell(50, 72, 9, 3), 'N', ol=.8)
    p.paint(p.ell(56, 69, 2.6, 3.6), 'Y', ol=.6)  # drip
    p.paint(p.ell(38, 80, 5, 4.5), 'N'); p.paint(p.ell(62, 80, 5, 4.5), 'N')
    return p


def koala(n=50):
    p = Pic('Koala', n)
    for s in (-1, 1):
        e = p.paint(p.circ(50 + s * 32, 26, 13), 'E')
        p.fill(p.circ(50 + s * 32, 27, 8), 'W')
    body(p, 'E', cy=81, belly='W')
    feet(p, 'E')
    m = head(p, 'E', cy=46, rx=35, ry=28, hl='W')
    eyes(p, cy=44, dx=17, rx=5.2, ry=6.4, iris='N')
    blush(p, cy=55, dx=24)
    nose = p.paint(p.ell(50, 52, 7.5, 10), 'X', ol=0)
    p.fill(p.ell(47.5, 47, 2, 3), 'E', prio=True)
    cat_mouth(p, cy=63.5, r=2.4)
    # eucalyptus sprig
    p.paint(p.line([(70, 92), (84, 70)], 1.4), 'N', ol=.6)
    for (x, y, r) in [(78, 74, 25), (84, 80, -35), (75, 83, 30), (88, 68, -20)]:
        p.paint(p.ell(x, y, 5, 2.6, r), 'T', ol=.7)
    p.paint(p.ell(36, 80, 5.5, 6.5, 20), 'E'); p.paint(p.ell(66, 78, 5.5, 6.5, -40), 'E')
    return p


def bunny_carrot(n=52):
    p = Pic('Bunny & Carrot', n)
    for s in (-1, 1):
        p.paint(p.ell(42 + s * 12, 18, 7, 17, s * 12), 'W')
        p.fill(p.ell(42 + s * 12.3, 20, 3.5, 12, s * 12), 'K')
    p.shade(p.ell(54, 18, 7, 17, 12), 'E', 2.5, 2)
    body(p, 'W', cx=42, cy=82, rx=20, shade='E')
    feet(p, 'W', cx=42)
    m = head(p, 'W', cx=42, cy=48, rx=32, ry=26, shade='E')
    eyes(p, cx=42, cy=50, dx=12.5, rx=5.4, ry=6.8, iris='B')
    blush(p, cx=42, cy=59, dx=20, rx=4.6)
    p.paint(p.poly([(39.5, 56), (44.5, 56), (42, 58.5)]), 'K', ol=.6)
    cat_mouth(p, cx=42, cy=60, r=2.4)
    # big carrot hugged diagonally
    leaves = [(86, 30, -10), (92, 38, 40), (80, 26, -40)]
    for (x, y, r) in leaves:
        lf = p.paint(p.ell(x, y, 4, 11, r), 'G')
        p.fill(p.ell(x - 1, y - 1, 1.6, 7, r) & lf, 'L')
    c = p.paint(p.poly([(78, 36), (92, 48), (56, 92), (52, 88)]), 'O')
    p.shade(c, 'R', 2.5, 2.5)
    for t in (.25, .45, .65):
        x0, y0 = 78 + (54 - 78) * t, 36 + (90 - 36) * t
        p.ink(p.line([(x0 + 1, y0 + 3), (x0 + 6, y0 + 7)], .8) & c)
    p.paint(p.ell(58, 75, 5, 6, 30), 'W'); p.paint(p.ell(70, 62, 5, 6, 30), 'W')  # paws on carrot
    flower(p, 12, 12, 4.4, 'P', 'Y')
    return p


def puppy_ball(n=54):
    p = Pic('Puppy & Ball', n)
    # golden puppy on the left
    p.paint(p.line([(52, 84), (60, 76), (60, 66)], 3), 'Y')
    body(p, 'Y', cx=38, cy=80, rx=19, ry=14, shade='O', belly='W')
    feet(p, 'Y', cx=38, cy=93)
    for s in (-1, 1):
        e = p.paint(p.ell(38 + s * 30, 36, 8, 15, s * -20), 'O')
        p.shade(e, 'N', s * -2, 3)
    m = head(p, 'Y', cx=38, cy=40, rx=30, ry=26, shade='O', hl='W')
    p.fill(p.ell(38, 54, 12, 8) & m, 'W')
    eyes(p, cx=38, cy=42, dx=12, rx=5.2, ry=6.5, iris='N')
    blush(p, cx=38, cy=52, dx=19, rx=4.4)
    p.paint(p.ell(38, 50, 3.8, 2.7), 'X', ol=0)
    p.fill(p.ell(36.8, 49.2, 1.4, .9), 'W', prio=True)
    p.paint(p.ell(38, 58.5, 2.8, 3.4), 'K', ol=.7)
    cat_mouth(p, cx=38, cy=54, r=2.6)
    p.paint(p.ell(38, 66, 14, 2.6), 'B', ol=.7)
    p.paint(p.circ(38, 69.5, 2.8), 'Y')
    # striped ball on the right
    bl = p.paint(p.circ(76, 80, 15), 'W')
    p.fill(p.ell(76, 80, 15, 5.5, -30) & bl, 'R')
    p.fill(p.ell(76, 80, 5.5, 15, -30) & bl, 'B')
    p.fill(p.circ(76, 80, 3.6) & bl, 'Y')
    p.shade(bl, 'E', 3, 3)
    p.ink(p.ell(76, 80, 15, 5.5, -30) & ~p.ell(76, 80, 14, 4.5, -30) & bl, prio=False)
    p.fill(p.ell(70, 71, 3.4, 1.8, -30), 'W', prio=True)
    p.paint(p.ell(28, 78, 5, 6, 15), 'Y'); p.paint(p.ell(50, 80, 5, 6, -15), 'Y')
    # little hearts
    heart(p, 75, 18, 5, 'R'); heart(p, 88, 34, 3.6, 'K')
    return p


def teacup_kitten(n=56):
    p = Pic('Kitten in a Teacup', n)
    # steam hearts
    heart(p, 16, 18, 4.4, 'K'); heart(p, 86, 12, 3.6, 'R')
    # saucer
    sc = p.paint(p.ell(50, 90, 44, 7), 'K')
    p.fill(p.ell(50, 88.5, 30, 3.2) & sc, 'W')
    # kitten head poking out
    for s in (-1, 1):
        p.paint(p.poly([(50 + s * 27, 36), (50 + s * 25, 6), (50 + s * 9, 18)]), 'E')
        p.fill(p.poly([(50 + s * 24, 30), (50 + s * 23.5, 12), (50 + s * 13, 20)]), 'K')
    m = head(p, 'E', cy=38, rx=30, ry=24, hl='W')
    for dx in (-6, 0, 6):
        p.fill(p.poly([(50 + dx - 2, 14), (50 + dx + 2, 14), (50 + dx, 22)]) & m, 'X')
    p.fill(p.ell(50, 51, 12, 7) & m, 'W')
    eyes(p, cy=38, dx=12, rx=5.2, ry=6.4, iris='L')
    blush(p, cy=48, dx=19, rx=4.4)
    p.paint(p.poly([(47.8, 46), (52.2, 46), (50, 48.5)]), 'K', ol=.6)
    cat_mouth(p, cy=49.5, r=2.4)
    for s in (-1, 1):
        p.ink(p.line([(50 + s * 22, 50), (50 + s * 34, 48)], .8))
    # cup in front
    cup = p.paint(p.poly([(14, 56), (86, 56), (80, 76), (70, 88), (30, 88), (20, 76)]), 'S')
    p.shade(cup, 'B', 4, 3)
    h = p.paint(p.ell(88, 68, 9, 9), 'S'); p.fill(p.ell(88, 68, 4.5, 4.5), 'W')
    p.paint(p.ell(50, 56, 36, 4), 'S', ol=.9)
    for (x, y) in [(28, 66), (44, 74), (60, 66), (74, 74), (36, 80), (58, 82)]:
        p.fill(p.circ(x, y, 2.6) & cup, 'W', prio=True)
    for s in (-1, 1):  # paws over the rim
        p.paint(p.ell(50 + s * 13, 56, 5.5, 4), 'E', ol=.8)
    return p


def panda_bamboo(n=58):
    p = Pic('Panda & Bamboo', n)
    # bamboo stalk
    stalk = p.paint(p.rect(73, 6, 81, 96), 'G')
    p.fill(p.rect(74.5, 6, 76.5, 96) & stalk, 'L')
    for y in (26, 50, 74):
        p.paint(p.rect(72, y - 1, 82, y + 1), 'T', ol=.6)
    for (x, y, r) in [(87, 22, -60), (68, 44, 50), (88, 60, -55), (89, 38, -30)]:
        lf = p.paint(p.ell(x, y, 3.4, 9, r), 'L')
        p.fill(p.ell(x, y, .9, 7, r) & lf, 'G')
    # panda
    for s in (-1, 1):
        p.paint(p.circ(42 + s * 25, 17, 8.5), 'X')
    body(p, 'W', cx=42, cy=80, rx=21, ry=15, shade='E')
    feet(p, 'X', cx=42, cy=93)
    m = head(p, 'W', cx=42, cy=42, rx=32, ry=26, shade='E')
    for s in (-1, 1):
        p.fill(p.ell(42 + s * 13, 44, 8, 10, s * -25), X)
        eye(p, 42 + s * 12.5, 44, 4.2, 5.2, iris='B')
    blush(p, cx=42, cy=56, dx=21, rx=4.6, ry=2.6)
    p.paint(p.ell(42, 53, 3.6, 2.4), 'X', ol=0)
    p.paint(p.ell(42, 59, 3, 2.4), 'K', ol=.7)  # munching mouth
    # leafy bamboo sprig held to mouth
    sp = p.paint(p.line([(52, 70), (64, 58)], 2.4), 'G', ol=.7)
    for (x, y, r) in [(66, 52, 30), (58, 50, -20)]:
        p.paint(p.ell(x, y, 2.8, 7, r), 'L', ol=.7)
    p.paint(p.ell(30, 76, 6, 7, 30), 'X'); p.paint(p.ell(56, 70, 6, 7, -30), 'X')  # arms
    return p


def chick(n=44):
    p = Pic('Chick', n)
    feet(p, 'O', cy=94, dx=11, rx=6, ry=3.4)
    m = p.paint(p.ell(50, 56, 38, 37), 'Y')
    p.shade(m, 'O', 4, 5)
    p.fill(p.ell(30, 30, 7, 3, -35) & m, 'W', prio=True)
    for s in (-1, 1):
        p.paint(p.ell(50 + s * 37, 64, 6, 11, s * -35), 'Y')
    p.paint(p.poly([(46, 20), (50, 10), (54, 20)]), 'Y', ol=.8)  # tuft
    p.paint(p.poly([(50, 20), (56, 12), (57, 22)]), 'Y', ol=.8)
    eyes(p, cy=48, dx=15, rx=5.4, ry=6.6, iris='N')
    blush(p, cy=60, dx=25, rx=6)
    p.paint(p.poly([(44.5, 55), (55.5, 55), (50, 62)]), 'O', ol=.7)
    # eggshell bottom
    sh = p.paint(p.poly([(14, 72), (22, 66), (30, 74), (40, 66), (50, 74), (60, 66), (70, 74), (78, 66), (86, 72),
                        (82, 88), (66, 96), (34, 96), (18, 88)]), 'W')
    p.shade(sh, 'E', 3, 3)
    p.fill(p.circ(32, 84, 2.6) & sh, 'S'); p.fill(p.circ(62, 88, 2.2) & sh, 'S'); p.fill(p.circ(48, 82, 2) & sh, 'S')
    return p


PICS = [kitty, puppy, bunny, piglet, chick, frog, hamster, panda, penguin, fox, owl, bear, koala,
        bunny_carrot, puppy_ball, teacup_kitten, panda_bamboo]
SIZES = [40, 40, 42, 42, 44, 44, 46, 46, 48, 48, 50, 50, 52, 52, 54, 56, 58]


def build():
    out = []
    for fn, n in zip(PICS, SIZES):
        p = fn(n)
        g = p.grid()
        used = [i for i in range(len(KEYS)) if (g == i).any()]
        used.sort(key=lambda i: -(g == i).sum())
        remap = {i: k for k, i in enumerate(used)}
        s = ''.join('.' if v < 0 else chr(97 + remap[v]) for v in g.flatten())
        out.append({'name': p.name, 'n': n, 'colors': [PAL[KEYS[i]] for i in used], 'map': s, '_grid': g})
    return out


def preview(pics, d):
    os.makedirs(d, exist_ok=True)
    cell = 7
    cols = 4
    tiles = []
    for pc in pics:
        n = pc['n']; g = pc['_grid']
        im = Image.new('RGB', (n * cell, n * cell), (246, 243, 234))
        dr = ImageDraw.Draw(im)
        for y in range(n):
            for x in range(n):
                v = g[y, x]
                if v < 0: continue
                dr.rectangle((x * cell, y * cell, x * cell + cell - 1, y * cell + cell - 1), fill=PAL[KEYS[v]])
        tiles.append((pc['name'], im))
    T = 58 * cell + 20
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * T, rows * (T + 16)), (246, 243, 234))
    dr = ImageDraw.Draw(sheet)
    for k, (name, im) in enumerate(tiles):
        x, y = (k % cols) * T, (k // cols) * (T + 16)
        sheet.paste(im, (x + 10 + (T - 20 - im.width) // 2, y + 10 + (T - 20 - im.height) // 2))
        dr.text((x + 10, y + T), name, fill=(46, 46, 51))
    sheet.save(os.path.join(d, 'pictures-sheet.png'))


def write(pics):
    src = open(GAME, encoding='utf-8').read()
    body = ',\n'.join('  ' + json.dumps({k: v for k, v in p.items() if not k.startswith('_')}, separators=(',', ':'))
                      for p in pics)
    new = '/*PICS-BEGIN*/\n' + body + '\n/*PICS-END*/'
    src2, k = re.subn(r'/\*PICS-BEGIN\*/.*?/\*PICS-END\*/', lambda m: new, src, flags=re.S)
    if not k: sys.exit('markers not found in ' + GAME)
    open(GAME, 'w', encoding='utf-8').write(src2)


if __name__ == '__main__':
    pics = build()
    for p in pics:
        cnt = sum(ch != '.' for ch in p['map'])
        print(f"{p['name']:<22} n={p['n']} cells={cnt} colours={len(p['colors'])}")
    if '--preview' in sys.argv:
        preview(pics, sys.argv[sys.argv.index('--preview') + 1])
    if '--no-write' not in sys.argv:
        write(pics)
