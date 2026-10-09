#!/usr/bin/env python3
"""Draws every Space Blaster sprite as a coloured-pencil doodle and writes them to src/assets/space-blaster/.

Style: dark ink outline (#1f1f22), a pale wash of colour inside and bright coloured-pencil cross-hatching
(two diagonal line sets, the second a shade darker). Background: cream grid paper with sketched planets.

    python3 tools/space-blaster-sprites.py            # writes all PNGs
    python3 tools/space-blaster-sprites.py --sheet x.png  # also writes a contact sheet

Any PNG can be swapped for a hand-drawn one with the same file name (transparent background, roughly the same
aspect ratio); the game scales each sprite to its slot.
"""
import sys, math, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

OUT = Path(__file__).resolve().parent.parent / "src" / "assets" / "space-blaster"
INK = (31, 31, 34)
PAPER = (246, 243, 234)
V = dict(red="#e0453a", orange="#f08a24", yellow="#f2c230", lime="#8bc34a", green="#4caf50", teal="#2fa7a0",
         sky="#4fb3e8", blue="#3a7bd5", indigo="#4b4fbf", purple="#8e5bc9", pink="#e86aa6", brown="#9b6a3c", grey="#9aa0a6")


def hx(h):
    h = V.get(h, h)
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Pic:
    """An RGBA canvas we paint coloured-pencil shapes onto. `u` = size of one display pixel in canvas pixels."""

    def __init__(self, w, h, u, seed=1, bg=None):
        self.w, self.h, self.u = w, h, u
        self.rgb = np.zeros((h, w, 3), np.float32)
        self.a = np.zeros((h, w), np.float32)
        if bg is not None:
            self.rgb[:] = bg
            self.a[:] = 1
        self.rng = random.Random(seed)
        yy, xx = np.mgrid[0:h, 0:w]
        self.xx, self.yy = xx.astype(np.float32), yy.astype(np.float32)

    # ---- masks ----
    def mask_poly(self, pts, wobble=0.0):
        pts = self._wob(pts, wobble)
        im = Image.new("L", (self.w * 2, self.h * 2), 0)
        ImageDraw.Draw(im).polygon([(x * 2, y * 2) for x, y in pts], fill=255)
        return np.asarray(im.resize((self.w, self.h), Image.LANCZOS), np.float32) / 255

    def ellipse_pts(self, cx, cy, rx, ry, n=90, a0=0, a1=2 * math.pi):
        return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]

    def mask_ell(self, cx, cy, rx, ry, wobble=0.0):
        return self.mask_poly(self.ellipse_pts(cx, cy, rx, ry), wobble)

    def _wob(self, pts, amt):
        if not amt:
            return pts
        n = len(pts)
        ph = [self.rng.random() * 6.28 for _ in range(3)]
        out = []
        for i, (x, y) in enumerate(pts):
            t = i / max(1, n)
            d = amt * self.u * (math.sin(t * 6.28 * 2 + ph[0]) * .5 + math.sin(t * 6.28 * 5 + ph[1]) * .3 + math.sin(t * 6.28 * 9 + ph[2]) * .2)
            out.append((x + d, y - d * .6))
        return out

    # ---- painting ----
    def _over(self, col, alpha):
        alpha = np.clip(alpha, 0, 1)
        if getattr(self, "clip", None) is not None:
            alpha = alpha * self.clip
        c = np.array(col, np.float32)
        na = alpha + self.a * (1 - alpha)
        safe = np.where(na > 0, na, 1)
        self.rgb = (c * alpha[..., None] + self.rgb * (self.a * (1 - alpha))[..., None]) / safe[..., None]
        self.a = na

    def hatch(self, m, col, angle, gap, lw, alpha=1.0):
        """Pencil lines at `angle` degrees inside mask m. gap/lw in display px."""
        g, w = gap * self.u, lw * self.u
        a = math.radians(angle)
        d = self.xx * math.cos(a) + self.yy * math.sin(a)
        off = self.rng.random() * g
        # slight per-line pressure changes, like a real pencil
        idx = np.floor((d + off) / g)
        press = 0.75 + 0.25 * np.sin(idx * 2.7 + self.rng.random() * 6)
        dist = np.abs(((d + off) % g) - g / 2)
        line = np.clip(w / 2 - dist + .5, 0, 1) * press
        # grain along the line
        grain = 0.82 + 0.18 * np.sin((self.xx * math.sin(a) - self.yy * math.cos(a)) * 0.9 / self.u + idx)
        self._over(col, m * line * grain * alpha)

    def fill(self, m, col, wash=0.30, hatch=True, gap=3.2, lw=1.1, dark=0.22, ang=(45, 135), halpha=1.0):
        """Pale wash + two sets of coloured-pencil hatching (second one darker)."""
        c = hx(col) if isinstance(col, str) else col
        self._over(mix(PAPER, c, wash), m)
        if hatch:
            self.hatch(m, c, ang[0], gap, lw, .9 * halpha)
            self.hatch(m, mix(c, INK, dark), ang[1], gap * 1.15, lw * .9, .75 * halpha)

    def outline(self, m, width=2.7, col=INK, alpha=1.0):
        """Ink line centred on the edge of mask m."""
        inside = m > .5
        if not inside.any():
            return
        din = ndimage.distance_transform_edt(inside)
        dout = ndimage.distance_transform_edt(~inside)
        d = np.where(inside, din - .5, dout - .5)
        r = width * self.u / 2
        self._over(col, np.clip(r - d + .5, 0, 1) * alpha)

    def shape(self, m, col, width=2.7, **kw):
        self.fill(m, col, **kw)
        self.outline(m, width)
        return m

    def line(self, pts, width=2.5, col=INK, alpha=1.0):
        im = Image.new("L", (self.w * 2, self.h * 2), 0)
        ImageDraw.Draw(im).line([(x * 2, y * 2) for x, y in pts], fill=255, width=max(1, int(width * self.u * 2)), joint="curve")
        r = width * self.u
        for x, y in (pts[0], pts[-1]):
            ImageDraw.Draw(im).ellipse([x * 2 - r, y * 2 - r, x * 2 + r, y * 2 + r], fill=255)
        m = np.asarray(im.resize((self.w, self.h), Image.LANCZOS), np.float32) / 255
        self._over(col, m * alpha)

    def dot(self, x, y, r, col=INK, alpha=1.0):
        self._over(col, np.clip(r * self.u - np.hypot(self.xx - x, self.yy - y) + .5, 0, 1) * alpha)

    def image(self):
        arr = np.dstack([np.clip(self.rgb, 0, 255), np.clip(self.a, 0, 1) * 255]).astype(np.uint8)
        im = Image.fromarray(arr, "RGBA")
        bb = im.getbbox()
        return im.crop(bb) if bb else im


def star_pts(cx, cy, r1, r2, n=5, rot=-math.pi / 2):
    return [(cx + (r1 if i % 2 == 0 else r2) * math.cos(rot + i * math.pi / n), cy + (r1 if i % 2 == 0 else r2) * math.sin(rot + i * math.pi / n)) for i in range(2 * n + 1)]


S = 256  # working size of each sprite (longest side, roughly)


# ---------------- enemies ----------------
def saucer():  # classic saucer, sky blue (50 pts)
    p = Pic(S, 170, S / 46, seed=2)
    dome = p.mask_ell(128, 72, 52, 46, .3) * (p.yy < 82)
    p.shape(dome, "sky", wash=.18)
    disc = p.mask_ell(128, 98, 118, 34, .35)
    p.shape(disc, "blue")
    rim = p.mask_ell(128, 106, 92, 12)
    p.fill(rim, "indigo", wash=.5, hatch=False)
    for i, x in enumerate((62, 102, 154, 194)):
        m = p.mask_ell(x, 104, 10, 8)
        p.shape(m, ["yellow", "pink", "lime", "orange"][i], width=1.4, gap=2.5)
    p.line([(92, 52), (104, 40)], 2.2, INK)  # glint
    return p.image()


def dome():  # dome saucer with a little alien (80 pts)
    p = Pic(S, 230, S / 44, seed=3)
    glass = p.mask_ell(128, 92, 66, 66, .25) * (p.yy < 132)
    p.fill(glass, "sky", wash=.12, hatch=False)
    # alien
    head = p.mask_ell(128, 92, 34, 30, .3)
    p.shape(head, "lime", width=2.4)
    for sx in (-1, 1):
        p.line([(128 + sx * 14, 66), (128 + sx * 24, 34)], 2.2)
        p.shape(p.mask_ell(128 + sx * 25, 32, 8, 8), "pink", width=1.4, gap=2.4)
        p.dot(128 + sx * 13, 88, 1.3, INK)
    p.line([(116, 106), (128, 112), (140, 106)], 2)
    p.hatch(glass, hx("sky"), 45, 5, .8, .5)
    p.outline(glass, 2.7)
    disc = p.mask_ell(128, 150, 122, 38, .3)
    p.shape(disc, "teal")
    p.fill(p.mask_ell(128, 160, 96, 12), "green", wash=.5, hatch=False)
    for i, x in enumerate((48, 92, 128, 164, 208)):
        p.shape(p.mask_ell(x, 158, 9, 8), ["yellow", "pink", "yellow", "pink", "yellow"][i], width=1.4, gap=2.4)
    # little legs
    for x in (78, 178):
        p.line([(x, 184), (x + (x - 128) * .25, 212)], 2.6)
        p.line([(x + (x - 128) * .25 - 12, 214), (x + (x - 128) * .25 + 12, 214)], 2.6)
    return p.image()


def ring():  # ring / donut UFO, orange (80 pts)
    p = Pic(S, S, S / 44, seed=4)
    outer = p.mask_ell(128, 128, 116, 116, .3)
    hole = p.mask_ell(128, 128, 48, 48, .2)
    donut = np.clip(outer - hole, 0, 1)
    p.fill(donut, "orange")
    # stripes of lights around the ring
    for k in range(8):
        a = k * math.pi / 4 + .39
        x, y = 128 + 82 * math.cos(a), 128 + 82 * math.sin(a)
        p.shape(p.mask_ell(x, y, 12, 12), "yellow" if k % 2 else "red", width=1.4, gap=2.4)
    p.outline(outer, 2.7)
    p.outline(hole, 2.7)
    # pilot pod in the middle hole
    pod = p.mask_ell(128, 128, 26, 26, .2)
    p.shape(pod, "purple", width=2.4)
    p.dot(120, 124, .9, INK)
    p.dot(136, 124, .9, INK)
    return p.image()


def triangle():  # triangle ship pointing down, red (50 pts)
    p = Pic(S, 230, S / 44, seed=5)
    body = p.mask_poly([(128, 220), (14, 34), (128, 64), (242, 34)], .3)
    p.shape(body, "red")
    fin = p.mask_poly([(128, 196), (82, 70), (128, 84), (174, 70)], .2)
    p.fill(fin, "orange", wash=.4, gap=2.6)
    p.outline(fin, 2)
    cock = p.mask_ell(128, 116, 20, 30, .2)
    p.shape(cock, "yellow", width=2.4, gap=2.4)
    for x in (52, 204):
        p.shape(p.mask_ell(x, 42, 14, 10), "yellow", width=1.4, gap=2.2)
    return p.image()


def scout():  # tiny scout: small, round with antenna (bonus parade, 100 pts)
    p = Pic(S, S, S / 30, seed=6)
    body = p.mask_ell(128, 150, 96, 54, .3)
    top = p.mask_ell(128, 124, 50, 44, .3) * (p.yy < 132)
    p.shape(top, "yellow", width=2.4)
    p.shape(body, "lime", width=2.6)
    p.line([(128, 82), (128, 40)], 2.2)
    p.shape(p.mask_ell(128, 36, 14, 14), "pink", width=1.4, gap=2.2)
    for x in (88, 168):
        p.dot(x, 152, 1.3, INK)
    p.line([(112, 170), (128, 178), (144, 170)], 1.6)
    p.line([(70, 200), (60, 226)], 2.4)
    p.line([(186, 200), (196, 226)], 2.4)
    return p.image()


def mothership():  # big two-hit boss: wide purple ship with pink lights
    p = Pic(S + 40, 210, (S + 40) / 54, seed=7)
    cx = (S + 40) / 2
    dome = p.mask_ell(cx, 74, 70, 56, .3) * (p.yy < 92)
    p.shape(dome, "pink", wash=.2)
    for x in (cx - 30, cx, cx + 30):
        p.shape(p.mask_ell(x, 64, 11, 13), "sky", width=1.4, gap=2.2)
    hull = p.mask_poly([(10, 110), (50, 84), (S + 40 - 50, 84), (S + 30, 110), (S + 40 - 40, 150), (40, 150)], .3)
    p.shape(hull, "purple")
    belt = p.mask_poly([(32, 128), (S + 8, 128), (S + 2, 140), (38, 140)])
    p.fill(belt, "indigo", wash=.5, hatch=False)
    for k in range(7):
        x = 46 + k * (S - 52) / 6
        p.shape(p.mask_ell(x, 108, 10, 9), "yellow" if k % 2 else "lime", width=1.4, gap=2.2)
    # tractor beam emitter + spikes
    p.shape(p.mask_poly([(cx - 36, 148), (cx + 36, 148), (cx + 22, 176), (cx - 22, 176)], .2), "pink", width=2.4)
    for x in (cx - 90, cx + 90):
        p.line([(x, 148), (x + (x - cx) * .15, 190)], 2.6)
        p.shape(p.mask_ell(x + (x - cx) * .15, 194, 9, 7), "orange", width=1.4, gap=2.2)
    return p.image()


def power_star():  # golden power-up star
    p = Pic(S, S, S / 40, seed=8)
    st = p.mask_poly(star_pts(128, 136, 118, 50), .2)
    p.shape(st, "yellow", wash=.35)
    p.dot(108, 128, 1.4, INK)
    p.dot(148, 128, 1.4, INK)
    p.line([(112, 152), (128, 162), (144, 152)], 2)
    p.fill(p.mask_ell(96, 146, 9, 6), "pink", wash=.6, hatch=False)
    p.fill(p.mask_ell(160, 146, 9, 6), "pink", wash=.6, hatch=False)
    return p.image()


# ---------------- player, shots, effects ----------------
def rocket():  # cute rocket fighter, nose up
    p = Pic(S, 260, S / 60, seed=9)
    for sx in (-1, 1):  # side wings
        w = p.mask_poly([(128 + sx * 30, 120), (128 + sx * 112, 206), (128 + sx * 104, 236), (128 + sx * 30, 206)], .3)
        p.shape(w, "red")
    body = p.mask_poly(p.ellipse_pts(128, 140, 46, 118, a0=math.pi, a1=2 * math.pi) + [(174, 226), (82, 226)], .2)
    p.shape(body, "#e8eef5", wash=.9, gap=4.2, lw=.9, dark=.35)
    nose = body * (p.yy < 64)
    p.fill(nose, "red", wash=.35)
    p.outline(body, 2.8)
    p.line([(92, 66), (164, 66)], 2.4)
    win = p.mask_ell(128, 124, 26, 26, .2)
    p.shape(win, "sky", width=3, wash=.25)
    p.line([(116, 114), (124, 108)], 1.8)
    fin = p.mask_poly([(118, 170), (138, 170), (138, 240), (118, 240)], .2)
    p.shape(fin, "red", width=2.4)
    nozzle = p.mask_poly([(96, 226), (160, 226), (150, 248), (106, 248)], .2)
    p.shape(nozzle, "grey", width=2.4)
    return p.image()


def goo():  # alien goo drop (enemy shot)
    p = Pic(120, 170, 120 / 13, seed=10)
    drop = p.mask_poly(p.ellipse_pts(60, 110, 46, 50, a0=-.15, a1=math.pi + .15) + [(60, 12)], .25)
    p.shape(drop, "lime", wash=.45, gap=2.6, lw=1.0, width=2.6)
    p.dot(44, 106, .9, INK)
    p.dot(70, 106, .9, INK)
    p.fill(p.mask_ell(76, 128, 9, 9), "green", wash=.7, hatch=False)
    return p.image()


def poof():  # sparkle ring a zapped UFO spins away inside
    p = Pic(S, S, S / 40, seed=11)
    ringm = np.clip(p.mask_ell(128, 128, 118, 118) - p.mask_ell(128, 128, 104, 104), 0, 1)
    p.fill(ringm, "yellow", wash=.5, hatch=False)
    p.outline(p.mask_ell(128, 128, 118, 118, .2), 2.2)
    for k in range(6):
        a = k * math.pi / 3 + .3
        x, y = 128 + 112 * math.cos(a), 128 + 112 * math.sin(a)
        p.shape(p.mask_poly(star_pts(x, y, 22, 9)), ["pink", "sky", "lime", "orange", "purple", "yellow"][k], width=1.4, gap=2.2)
    return p.image()


# ---------------- background ----------------
def background():
    W, H, k = 800, 1280, 2  # 2x of the 400x640 playfield
    paper = Pic(W, H, k, seed=12, bg=PAPER)
    # graph-paper grid: fine every 20 px (display), stronger every 5th
    blue = (79, 140, 205)
    for i in range(0, W + 1, 20 * k):
        strong = (i // (20 * k)) % 5 == 0
        paper.rgb[:, max(0, i - (1 if strong else 0)):i + 1] = paper.rgb[:, max(0, i - (1 if strong else 0)):i + 1] * (1 - (.30 if strong else .17)) + np.array(blue) * (.30 if strong else .17)
    for j in range(0, H + 1, 20 * k):
        strong = (j // (20 * k)) % 5 == 0
        sl = slice(max(0, j - (1 if strong else 0)), j + 1)
        paper.rgb[sl, :] = paper.rgb[sl, :] * (1 - (.30 if strong else .17)) + np.array(blue) * (.30 if strong else .17)
    p = paper
    soft = dict(halpha=.5)
    # ringed planet (top right)
    cx, cy = 640, 250
    back = np.clip(p.mask_ell(cx, cy, 170, 46, .4) - p.mask_ell(cx, cy, 130, 30), 0, 1) * (p.yy < cy)
    p.fill(back, "orange", wash=.2, gap=3.5, **soft)
    p.clip = (p.yy < cy).astype(np.float32)
    p.outline(p.mask_ell(cx, cy, 170, 46, .4), 2.3, alpha=.7)
    p.clip = None
    ball = p.mask_ell(cx, cy, 96, 96, .35)
    p.fill(ball, "yellow", wash=.2, gap=3.5, **soft); p.outline(ball, 2.3, alpha=.7)
    p.clip = ball
    for dy in (-40, 30):
        p.line([(cx - 88, cy + dy), (cx - 30, cy + dy + 8), (cx + 40, cy + dy - 2), (cx + 88, cy + dy + 6)], 1.6, mix(hx("orange"), INK, .3), .8)
    p.clip = None
    front = np.clip(p.mask_ell(cx, cy, 170, 46, .4) - p.mask_ell(cx, cy, 130, 30), 0, 1) * (p.yy >= cy)
    p.fill(front, "orange", wash=.22, gap=3.5, **soft)
    p.clip = (p.yy >= cy).astype(np.float32) * (1 - ball) + front
    p.outline(p.mask_ell(cx, cy, 170, 46, .4), 2.3, alpha=.7)
    p.outline(p.mask_ell(cx, cy, 130, 30), 2.3, alpha=.7)
    p.clip = None
    # moon with craters (left, middle)
    mx, my = 110, 600
    moon = p.mask_ell(mx, my, 84, 84, .35)
    p.fill(moon, "grey", wash=.18, gap=3.5, **soft); p.outline(moon, 2.3, alpha=.7)
    for (ox, oy, r) in ((-30, -24, 20), (26, 10, 14), (-6, 40, 11), (36, -38, 9)):
        c = p.mask_ell(mx + ox, my + oy, r, r * .85, .2)
        p.fill(c, mix(hx("grey"), INK, .25), wash=.35, hatch=False)
        p.outline(c, 1.8, alpha=.6)
    # striped gas giant (bottom right, half off the page)
    gx, gy = 720, 1010
    giant = p.mask_ell(gx, gy, 190, 190, .4)
    bands = ["purple", "pink", "indigo", "pink", "purple", "orange", "purple"]
    for i, b in enumerate(bands):
        band = giant * (p.yy >= gy - 190 + i * 380 / 7) * (p.yy < gy - 190 + (i + 1) * 380 / 7 + 1)
        p.fill(band, b, wash=.2, gap=3.5, **soft)
    p.clip = giant
    for i in range(1, 7):
        y = gy - 190 + i * 380 / 7
        p.line([(gx - 200, y + 6), (gx - 60, y - 4), (gx + 60, y + 6), (gx + 200, y - 2)], 1.6, INK, .55)
    p.clip = None
    spot = p.mask_ell(gx - 70, gy + 40, 34, 20, .2)
    p.fill(spot, "red", wash=.3, gap=3, halpha=.6); p.outline(spot, 2, alpha=.7)
    giant_line = giant.copy()
    p.outline(giant_line, 2.3, alpha=.7)
    # tiny planet (top left) and small Earth-ish planet
    m_ = p.mask_ell(150, 170, 40, 40, .3); p.fill(m_, "teal", wash=.2, gap=3.2, **soft); p.outline(m_, 2.3, alpha=.7)
    p.line([(114, 160), (150, 150), (186, 162)], 1.6, mix(hx("teal"), INK, .3), .8)
    m_ = p.mask_ell(250, 1130, 28, 28, .3); p.fill(m_, "pink", wash=.2, gap=3, **soft); p.outline(m_, 2.3, alpha=.7)
    # sketched stars
    rng = random.Random(5)
    spots = [(330, 110), (470, 420), (60, 330), (300, 820), (520, 640), (90, 900), (420, 1180), (360, 300), (210, 470), (560, 840), (40, 1180), (760, 560), (600, 1220), (180, 1010)]
    cols = ["yellow", "sky", "pink", "yellow", "lime", "orange", "yellow"]
    for i, (x, y) in enumerate(spots):
        r = rng.uniform(13, 22)
        st = p.mask_poly(star_pts(x, y, r, r * .45, rot=-math.pi / 2 + rng.uniform(-.3, .3)), .1)
        p.fill(st, cols[i % len(cols)], wash=.5, gap=2.2, lw=1.0)
        p.outline(st, 2, alpha=.8)
    for _ in range(60):  # little pencil dots and plus-signs
        x, y = rng.uniform(10, W - 10), rng.uniform(10, H - 10)
        if rng.random() < .5:
            p.dot(x, y, rng.uniform(1.1, 1.8), INK, .55)
        else:
            s = rng.uniform(5, 9)
            p.line([(x - s, y), (x + s, y)], 1.3, INK, .5)
            p.line([(x, y - s), (x, y + s)], 1.3, INK, .5)
    arr = np.clip(p.rgb, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


SPRITES = {
    "mothership.png": mothership, "dome-saucer.png": dome, "ring-ufo.png": ring, "saucer.png": saucer,
    "triangle-ship.png": triangle, "scout.png": scout, "power-star.png": power_star,
    "rocket.png": rocket, "goo.png": goo, "poof.png": poof,
}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    ims = {}
    for name, fn in SPRITES.items():
        im = fn()
        im.save(OUT / name, optimize=True)
        ims[name] = im
        print(name, im.size)
    bg = background()
    bg.save(OUT / "bg.jpg", quality=86, optimize=True)
    print("bg.jpg", bg.size)
    if "--sheet" in sys.argv:
        dst = sys.argv[sys.argv.index("--sheet") + 1]
        sheet = Image.new("RGB", (1300, 600), PAPER)
        x = 10
        for i, (n, im) in enumerate(ims.items()):
            t = im.copy()
            t.thumbnail((240, 240))
            sheet.paste(t, (10 + (i % 5) * 258, 10 + (i // 5) * 290), t)
        sheet.save(dst)
