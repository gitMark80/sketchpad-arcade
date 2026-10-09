#!/usr/bin/env python3
"""Sidewalk Hop sprites: Milo (the curly-haired kid with the backpack) in every hop pose, the street traffic,
the creek floats, the sidewalk props, the gold star and the three lane tiles, all as coloured-pencil doodles.

    python3 tools/sidewalk-hop-sprites.py [names...] [--sheet out.png]   # writes src/assets/sidewalk-hop/

Uses the pencil drawing helpers from tools/draw-brawl-sprites.py.
"""
import importlib.util, math, os, random, sys
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
OUT = os.path.join(os.path.dirname(HERE), 'src', 'assets', 'sidewalk-hop')

SK = SKIN[0]
SKF = mix(PAPER, SK, .85)
HAIR = BROWN
SHIRT = ORANGE
SHORTS = BLUE
PACK = RED
SHOE = RED


def skinpaint(p, m, line=None):
    p.paint(m, SK, hatch=False, fill=SKF, line=line)


def curls(p, cx, cy, r, back=False, n=13):
    """a cloud of curls around a head centre"""
    rng = random.Random(7)
    pts = []
    for i in range(n):
        a = math.pi * (0.92 + 1.16 * i / (n - 1)) if not back else 2 * math.pi * i / n
        rr = r * (1.08 + 0.1 * rng.random())
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.98))
    if not back:
        # fringe across the forehead
        pts += [(cx + r * 0.95, cy - r * 0.05), (cx + r * 0.55, cy - r * 0.38), (cx + r * 0.15, cy - r * 0.3), (cx - r * 0.25, cy - r * 0.42), (cx - r * 0.6, cy - r * 0.3), (cx - r * 0.95, cy)]
    m = p.poly(pts)
    for (x, y) in pts[: n]:
        m = np.maximum(m, p.ell(x, y, r * 0.24, r * 0.24))
    p.paint(np.clip(m, 0, 1), HAIR, wash=.35, spacing=7.5)
    for (x, y) in pts[: n: 2]:  # little curl loops
        p.arc(x, y, r * 0.11, 0, 5.2, w=3)


def face(p, cx, cy, r, mood='smile', side=0):
    ex = r * 0.38
    if side:
        eyes = [(cx + r * 0.45 * side, cy)]
    else:
        eyes = [(cx - ex, cy), (cx + ex, cy)]
    for x, y in eyes:
        if mood == 'dizzy':
            d = r * 0.13
            p.stroke([(x - d, y - d), (x + d, y + d)], w=4)
            p.stroke([(x + d, y - d), (x - d, y + d)], w=4)
        else:
            p.dot(x, y, r * 0.105)
            p.dot(x - r * 0.03, y - r * 0.04, r * 0.035, PAPER)
    bx = [cx + r * 0.62 * side] if side else [cx - r * 0.66, cx + r * 0.66]
    for x in bx:
        p._over(p.ell(x, cy + r * 0.3, r * 0.17, r * 0.1) * .55, PINK)
    mx = cx + (r * 0.4 * side if side else 0)
    if mood == 'dizzy':
        pts = [(mx - r * 0.25 + k * r * 0.1, cy + r * 0.42 + (k % 2) * r * 0.08) for k in range(6)]
        p.stroke(pts, w=3.6)
    elif mood == 'yay':
        p.paint(p.blob([(mx - r * 0.24, cy + r * 0.3), (mx + r * 0.24, cy + r * 0.3), (mx + r * 0.14, cy + r * 0.58), (mx - r * 0.14, cy + r * 0.58)]), RED, wash=.6, hatch=False, line=3.6)
    else:
        p.arc(mx, cy + r * 0.28, r * 0.26, 0.25, math.pi - 0.25, w=3.8)
    for dx, dy in ((-0.62, 0.12), (-0.55, 0.2), (0.55, 0.2), (0.62, 0.12)):  # freckles
        if not side or dx * side > 0:
            p.dot(cx + r * dx, cy + r * dy, 1.5, BROWN)


def legs_front(p, cx, top, hop):
    for sx in (-1, 1):
        if hop:
            pts = [(cx + sx * 14, top), (cx + sx * 28, top + 18), (cx + sx * 20, top + 34)]
        else:
            pts = [(cx + sx * 13, top), (cx + sx * 14, top + 32)]
        skinpaint(p, p.cap(pts, 7.5), line=5.5)
        fx, fy = pts[-1]
        p.paint(p.ell(fx + sx * 7, fy + 6, 14, 8), SHOE, wash=.35, spacing=6)
        p.stroke([(fx + sx * 7 - 11, fy + 9), (fx + sx * 7 + 11, fy + 9)], w=3, color=mix(PAPER, INK, .9))


def arms_front(p, cx, sy, hop, back=False):
    hands = []
    for sx in (-1, 1):
        if hop:
            pts = [(cx + sx * 26, sy), (cx + sx * 44, sy - 10), (cx + sx * 60, sy - 22)]
        else:
            pts = [(cx + sx * 26, sy), (cx + sx * 36, sy + 18), (cx + sx * 38, sy + 34)]
        skinpaint(p, p.cap(pts, 7), line=5)
        hands.append(pts[-1])
    for x, y in hands:
        skinpaint(p, p.ell(x, y, 8.5, 8.5), line=4.5)


def body_front(p, cx, top):
    p.paint(p.poly([(cx - 30, top + 46), (cx + 30, top + 46), (cx + 34, top + 66), (cx + 4, top + 66), (cx, top + 58), (cx - 4, top + 66), (cx - 34, top + 66)], wob=1), SHORTS, wash=.3, spacing=7)
    p.paint(p.blob([(cx - 26, top + 4), (cx, top), (cx + 26, top + 4), (cx + 36, top + 22), (cx + 32, top + 50), (cx, top + 54), (cx - 32, top + 50), (cx - 36, top + 22)]), SHIRT, wash=.32, spacing=7)


def kid_front(hop=False, mood='smile'):
    p = Pic(180, 226, seed=41, line=6.5, hatch=8, hw=2.3)
    p.oy = 14
    cx = 90
    legs_front(p, cx, 160, hop)
    arms_front(p, cx, 118, hop)
    body_front(p, cx, 104)
    for sx in (-1, 1):  # backpack straps
        p.paint(p.rrect(cx + sx * 18 - 4, 106, cx + sx * 18 + 4, 140, 3), PACK, wash=.6, hatch=False, line=3.5)
    hx, hy, hr = cx, 62, 46
    curls(p, hx, hy, hr, back=True, n=14)
    skinpaint(p, p.ell(hx, hy + 4, hr * .9, hr * .86))
    curls(p, hx, hy - 6, hr * .92)
    face(p, hx, hy + 8, hr * .9, mood='yay' if hop and mood == 'smile' else mood)
    if mood == 'dizzy':
        for i, (x, y, r) in enumerate(((30, 22, 15), (150, 26, 13), (90, 6, 0))):
            if r:
                star(p, x, y, r, YELLOW, wash=.5, line=4.5, spacing=5)
    return p.image()


def kid_back(hop=False):
    p = Pic(180, 226, seed=42, line=6.5, hatch=8, hw=2.3)
    p.oy = 14
    cx = 90
    legs_front(p, cx, 160, hop)
    arms_front(p, cx, 118, hop)
    body_front(p, cx, 104)
    # big backpack
    p.paint(p.rrect(cx - 30, 104, cx + 30, 166, 14), PACK, wash=.32, spacing=7)
    p.paint(p.rrect(cx - 20, 134, cx + 20, 160, 8), PACK, wash=.5, spacing=6, angles=(45,))
    p.stroke([(cx - 14, 140), (cx + 14, 140)], w=3)
    p.paint(p.rrect(cx - 10, 96, cx + 10, 106, 4), PACK, wash=.6, hatch=False, line=3.5)  # handle
    hx, hy, hr = cx, 60, 46
    curls(p, hx, hy, hr, back=True, n=15)
    rng = random.Random(3)
    for a, d in ((0.3, .45), (2.2, .5), (4.0, .45), (5.4, .2), (1.2, .1)):  # curls drawn over the back of the head
        p.arc(hx + math.cos(a) * d * hr, hy + math.sin(a) * d * hr, 7, 0, 5.0, w=3)
    return p.image()


def kid_side(hop=False):
    """profile facing right"""
    p = Pic(190, 226, seed=43, line=6.5, hatch=8, hw=2.3)
    p.oy = 14
    cx = 92
    # far arm + far leg first
    if hop:
        far_leg = [(cx - 4, 160), (cx - 30, 168), (cx - 46, 182)]
        near_leg = [(cx + 6, 160), (cx + 28, 168), (cx + 30, 192)]
        far_arm = [(cx + 4, 118), (cx + 30, 104), (cx + 50, 92)]
        near_arm = [(cx - 4, 118), (cx - 26, 108), (cx - 46, 96)]
    else:
        far_leg = [(cx - 4, 160), (cx - 12, 192)]
        near_leg = [(cx + 6, 160), (cx + 14, 192)]
        far_arm = [(cx + 4, 118), (cx + 18, 136), (cx + 26, 150)]
        near_arm = [(cx - 2, 118), (cx - 12, 138), (cx - 14, 152)]
    for leg, shade in ((far_leg, .7), (near_leg, .85)):
        p.paint(p.cap(leg, 7.5), SK, hatch=False, fill=mix(PAPER, SK, shade), line=5.5)
        fx, fy = leg[-1]
        p.paint(p.ell(fx + 8, fy + 6, 15, 8), SHOE, wash=.35, spacing=6)
    p.paint(p.cap(far_arm, 7), SK, hatch=False, fill=mix(PAPER, SK, .7), line=5)
    skinpaint(p, p.ell(far_arm[-1][0], far_arm[-1][1], 8, 8), line=4.5)
    # shorts + shirt (narrower in profile)
    p.paint(p.poly([(cx - 22, 148), (cx + 22, 148), (cx + 26, 168), (cx - 24, 168)], wob=1), SHORTS, wash=.3, spacing=7)
    p.paint(p.blob([(cx - 18, 106), (cx + 6, 102), (cx + 24, 110), (cx + 28, 130), (cx + 24, 152), (cx - 22, 154), (cx - 26, 130)]), SHIRT, wash=.32, spacing=7)
    # backpack on the back (left)
    p.paint(p.rrect(cx - 50, 106, cx - 14, 160, 12), PACK, wash=.32, spacing=7)
    p.paint(p.rrect(cx - 56, 126, cx - 44, 154, 5), PACK, wash=.5, hatch=False, line=4)
    p.paint(p.rrect(cx - 18, 106, cx - 10, 150, 3), PACK, wash=.6, hatch=False, line=3.5)
    # near arm
    p.paint(p.cap(near_arm, 7), SK, hatch=False, fill=SKF, line=5)
    skinpaint(p, p.ell(near_arm[-1][0], near_arm[-1][1], 8.5, 8.5), line=4.5)
    hx, hy, hr = cx + 4, 60, 46
    curls(p, hx - 6, hy - 2, hr, back=True, n=14)
    skinpaint(p, p.ell(hx + 6, hy + 6, hr * .86, hr * .84))
    # nose bump
    skinpaint(p, p.ell(hx + hr * .88, hy + 12, 8, 7), line=4)
    skinpaint(p, p.ell(hx + 6, hy + 6, hr * .86, hr * .84), line=0)
    # curls over the top/back, leaving the face clear
    rng = random.Random(5)
    pts = []
    for i in range(10):
        a = math.pi * (0.5 + 1.25 * i / 9)
        pts.append((hx - 4 + math.cos(a) * hr, hy - 4 + math.sin(a) * hr))
    pts += [(hx + hr * .7, hy - hr * .55), (hx + hr * .4, hy - hr * .2), (hx + hr * .05, hy - hr * .3), (hx - hr * .15, hy + hr * .1), (hx - hr * .3, hy + hr * .55)]
    m = p.poly(pts)
    for (x, y) in pts[:10]:
        m = np.maximum(m, p.ell(x, y, hr * .25, hr * .25))
    p.paint(np.clip(m, 0, 1), HAIR, wash=.35, spacing=7.5)
    for (x, y) in pts[:10:2]:
        p.arc(x, y, hr * 0.11, 0, 5.2, w=3)
    face(p, hx + 8, hy + 10, hr * .86, mood='yay' if hop else 'smile', side=1)
    return p.image()


# ------------------------------------------------------------------ traffic (side views facing right)
def car(body, w=300, h=150, seed=51):
    p = Pic(w, h, seed=seed, line=7, hatch=9, hw=2.6)
    p.paint(p.blob([(24, 108), (22, 76), (54, 66), (96, 30), (186, 28), (230, 64), (276, 74), (284, 108)]), body, wash=.3)
    # windows
    p.paint(p.poly([(104, 40), (146, 38), (146, 66), (76, 68)]), BLUE, wash=.18, hatch=False, line=5)
    p.paint(p.poly([(158, 38), (184, 38), (218, 66), (158, 66)]), BLUE, wash=.18, hatch=False, line=5)
    # driver
    skinpaint(p, p.ell(176, 54, 11, 11), line=4)
    p.paint(p.ell(176, 46, 11, 6), BROWN, wash=.5, hatch=False, line=3.5)
    p.stroke([(150, 72), (150, 104)], w=4)
    p.paint(p.ell(274, 84, 8, 6), YELLOW, wash=.6, hatch=False, line=4)  # headlight
    p.paint(p.rrect(16, 96, 34, 106, 3), GREY, wash=.4, hatch=False, line=4)
    for x in (78, 228):
        p.paint(p.ell(x, 112, 24, 24), GREY, wash=.25, spacing=6)
        p.dot(x, 112, 9, mix(PAPER, GREY, .5))
        p.arc(x, 112, 9, 0, 6.3, w=3.5)
    return p.image()


def icecream_van():
    p = Pic(300, 150, seed=55, line=7, hatch=9, hw=2.6)
    p.paint(p.blob([(18, 112), (18, 34), (196, 30), (232, 58), (282, 70), (286, 112)]), PINK, wash=.25)
    # awning stripes
    for k in range(6):
        x0 = 30 + k * 26
        p.paint(p.poly([(x0, 40), (x0 + 26, 40), (x0 + 26, 56), (x0, 60)]), RED if k % 2 == 0 else YELLOW, wash=.5, hatch=False, line=4)
    p.paint(p.rrect(36, 62, 172, 92, 6), BLUE, wash=.18, hatch=False, line=5)
    p.paint(p.poly([(206, 44), (228, 62), (228, 76), (206, 76)]), BLUE, wash=.18, hatch=False, line=5)
    # big cone on the roof
    p.paint(p.poly([(98, 30), (122, 30), (110, 4)][::-1]), ORANGE, wash=.4, spacing=5)
    p.paint(p.ell(110, 26, 15, 13), PINK, wash=.45, hatch=False, line=4.5)
    for x in (72, 236):
        p.paint(p.ell(x, 114, 22, 22), GREY, wash=.25, spacing=6)
        p.dot(x, 114, 8, mix(PAPER, GREY, .5))
        p.arc(x, 114, 8, 0, 6.3, w=3.5)
    return p.image()


def rider(kind, color, seed):
    """a kid going right on a bike / scooter / skateboard, 200 x 150"""
    p = Pic(200, 172, seed=seed, line=6.5, hatch=8, hw=2.4)
    p.oy = 22
    skin = SKIN[seed % 3]
    sk = mix(PAPER, skin, .85)
    if kind == 'bike':
        for x in (46, 156):
            p.arc(x, 112, 28, 0, 6.3, w=6)
            p.stroke([(x - 20, 112), (x + 20, 112)], w=2.5)
        p.paint(p.cap([(46, 112), (90, 84), (146, 84), (156, 112)], 4.5), color, wash=.6, hatch=False, line=3)
        p.paint(p.cap([(90, 84), (106, 112), (146, 84)], 4.5), color, wash=.6, hatch=False, line=3)
        p.stroke([(146, 84), (140, 56), (154, 52)], w=5)
        p.paint(p.ell(86, 76, 14, 6), INK, wash=1, hatch=False, fill=(70, 70, 76))
        hip, foot, hand = (88, 70), (110, 108), (152, 54)
    elif kind == 'scooter':
        p.paint(p.rrect(40, 112, 150, 124, 5), color, wash=.5, hatch=False, line=4.5)
        p.stroke([(144, 114), (154, 42)], w=6)
        p.stroke([(140, 42), (168, 42)], w=6)
        for x in (48, 146):
            p.paint(p.ell(x, 128, 12, 12), GREY, wash=.3, hatch=False, line=4.5)
        hip, foot, hand = (92, 70), (96, 110), (150, 46)
    else:  # skateboard
        p.paint(p.blob([(26, 112), (40, 118), (160, 118), (176, 110), (170, 122), (30, 124)]), color, wash=.55, hatch=False, line=4.5)
        for x in (54, 146):
            p.paint(p.ell(x, 130, 9, 9), GREY, wash=.3, hatch=False, line=4)
        hip, foot, hand = (98, 66), (70, 110), (138, 56)
    shirt = [GREEN, PURPLE, TEAL, YELLOW][seed % 4]
    # legs
    p.paint(p.cap([hip, ((hip[0] + foot[0]) / 2 + 12, (hip[1] + foot[1]) / 2), foot], 7), skin, hatch=False, fill=sk, line=5)
    if kind == 'skateboard':
        p.paint(p.cap([hip, (124, 90), (130, 110)], 7), skin, hatch=False, fill=sk, line=5)
    for f in ([foot] + ([(130, 110)] if kind == 'skateboard' else [])):
        p.paint(p.ell(f[0] + 6, f[1] + 3, 12, 7), RED, wash=.4, hatch=False, line=4)
    # body
    p.paint(p.blob([(hip[0] - 14, hip[1] + 4), (hip[0] - 12, hip[1] - 34), (hip[0] + 10, hip[1] - 40), (hip[0] + 20, hip[1] - 20), (hip[0] + 14, hip[1] + 4)]), shirt, wash=.32, spacing=7)
    p.paint(p.cap([(hip[0] + 6, hip[1] - 30), hand], 6.5), skin, hatch=False, fill=sk, line=5)
    # head + helmet
    hx, hy = hip[0] + 10, hip[1] - 56
    p.paint(p.ell(hx, hy, 22, 21), skin, hatch=False, fill=sk)
    p.paint(p.blob([(hx - 25, hy + 2), (hx - 20, hy - 20), (hx + 4, hy - 28), (hx + 24, hy - 14), (hx + 28, hy - 2)]), color, wash=.45, spacing=6)
    p.dot(hx + 10, hy + 4, 3.2)
    p.arc(hx + 10, hy + 9, 6, 0.3, 2.2, w=3)
    p._over(p.ell(hx + 2, hy + 10, 5, 3) * .5, PINK)
    return p.image()


# ------------------------------------------------------------------ creek floats (seen from above, long side horizontal)
def log():
    p = Pic(360, 100, seed=61, line=7, hatch=9, hw=2.6)
    p.paint(p.rrect(14, 16, 330, 84, 30), BROWN, wash=.32, angles=(15, -60))
    p.paint(p.ell(330, 50, 20, 34), BROWN, wash=.15, hatch=False)
    for r in (8, 16):
        p.arc(330, 50, r * .6, 0, 6.3, w=3, ry=r)
    for x0, y0 in ((70, 34), (160, 64), (240, 30)):
        p.stroke([(x0, y0), (x0 + 50, y0 + 2)], w=3.2)
    p.stroke([(110, 18), (118, 4), (128, 10)], w=4, color=rgb(GREEN))  # a twig with a leaf
    p.paint(p.ell(132, 8, 8, 5), GREEN, wash=.5, hatch=False, line=3)
    return p.image()


def plank():
    p = Pic(240, 100, seed=62, line=7, hatch=9, hw=2.6)
    p.paint(p.poly([(10, 22), (228, 16), (232, 80), (12, 84)], wob=1.2), ORANGE, wash=.25, angles=(10, -70))
    for y in (40, 62):
        p.stroke([(14, y), (228, y - 2)], w=3, color=mix(PAPER, INK, .8))
    for x in (30, 210):
        for y in (30, 72):
            p.dot(x, y, 3.2)
    return p.image()


def crate():
    p = Pic(120, 110, seed=63, line=6.5, hatch=8, hw=2.4)
    p.paint(p.rrect(12, 12, 108, 98, 6), BROWN, wash=.3)
    for y in (40, 70):
        p.stroke([(14, y), (106, y)], w=4)
    p.stroke([(16, 16), (104, 94)], w=5)
    return p.image()


# ------------------------------------------------------------------ sidewalk props
def tree():
    p = Pic(200, 220, seed=71, line=7, hatch=10, hw=2.6)
    p.paint(p.poly([(84, 216), (90, 130), (110, 130), (116, 216)], wob=1.2), BROWN, wash=.35)
    rng = random.Random(2)
    pts = []
    for i in range(14):
        a = i / 14 * 2 * math.pi
        r = (88 if i % 2 else 76) * rng.uniform(.94, 1.04)
        pts.append((100 + math.cos(a) * r, 92 + math.sin(a) * r * .86))
    p.paint(p.blob(pts), GREEN, wash=.3)
    for x, y in ((66, 70), (130, 96), (100, 46), (150, 60), (70, 118)):
        p.arc(x, y, 14, 3.6, 5.6, w=3.6)
    return p.image()


def bench():
    p = Pic(220, 160, seed=72, line=7, hatch=9, hw=2.6)
    for x in (40, 180):
        p.stroke([(x, 92), (x, 146)], w=8)
    p.paint(p.rrect(16, 26, 204, 52, 6), BROWN, wash=.3, angles=(20, -70))
    p.paint(p.rrect(10, 78, 210, 100, 6), BROWN, wash=.3, angles=(20, -70))
    for x in (46, 174):
        p.stroke([(x, 52), (x - 4, 80)], w=6)
    return p.image()


def bush():
    p = Pic(180, 150, seed=73, line=7, hatch=9, hw=2.6)
    m = np.zeros((p.H, p.W))
    for x, y, r in ((52, 96, 42), (96, 70, 50), (134, 100, 40), (90, 110, 44)):
        m = np.maximum(m, p.ell(x, y, r, r * .9))
    p.paint(m, GREEN, wash=.32)
    for x, y in ((70, 80), (112, 62), (126, 104), (60, 112)):
        p.paint(p.ell(x, y, 7, 7), PINK, wash=.55, hatch=False, line=3.5)
    return p.image()


def hydrant():
    p = Pic(130, 170, seed=74, line=7, hatch=8, hw=2.4)
    p.paint(p.rrect(24, 148, 106, 164, 4), RED, wash=.4, hatch=False)
    p.paint(p.rrect(36, 56, 94, 152, 10), RED, wash=.3)
    p.paint(p.ell(65, 52, 32, 24), RED, wash=.3)
    p.paint(p.rrect(55, 16, 75, 34, 4), RED, wash=.4, hatch=False)
    for sx in (-1, 1):
        p.paint(p.rrect(65 + sx * 30 - 12, 82, 65 + sx * 30 + 12, 104, 5), RED, wash=.45, hatch=False)
    p.paint(p.ell(65, 98, 11, 11), YELLOW, wash=.5, hatch=False, line=4.5)
    return p.image()


def trashcan():
    p = Pic(130, 170, seed=75, line=7, hatch=8, hw=2.4)
    p.paint(p.poly([(24, 44), (106, 44), (98, 162), (32, 162)], wob=1), GREEN, wash=.3, angles=(80, 35))
    for x in (48, 65, 82):
        p.stroke([(x, 56), (x - (x - 65) * .08, 150)], w=3.2)
    p.paint(p.rrect(14, 28, 116, 46, 8), GREEN, wash=.45, hatch=False)
    p.paint(p.rrect(54, 16, 76, 28, 5), GREY, wash=.4, hatch=False, line=4.5)
    return p.image()


def gold_star():
    p = Pic(96, 96, seed=81, line=6, hatch=7, hw=2.2)
    star(p, 48, 50, 42, YELLOW, wash=.5)
    p.dot(38, 46, 3.8)
    p.dot(58, 46, 3.8)
    p.arc(48, 54, 8, 0.3, math.pi - 0.3, w=3.4)
    return p.image()


# ------------------------------------------------------------------ lane tiles (jpg, seamless sideways)
def tile_base(w, h, seed, tone=PAPER):
    p = Pic(w, h, ss=2, seed=seed, line=4, hatch=11, hw=1.6)
    p._over(np.ones((p.H, p.W)), tone)
    return p


def sidewalk_tile():
    """3 lanes tall, 9 slabs wide -> one slab per grid cell"""
    w, h = 765, 255
    p = tile_base(w, h, 91, mix(PAPER, '#d9d7cf', .35))
    hm = p.hatchmask((60,), spacing=11, width=1.3, broken=.45) * .28
    p._over(hm, (85, 85, 92))
    s = 85
    for k in range(10):
        x = k * s
        p._over(p.cap([(x, 0), (x, h)], 1.3), (112, 112, 118))
    for k in range(4):
        y = k * s
        p._over(p.cap([(0, y), (w, y)], 1.3), (112, 112, 118))
    rng = random.Random(4)
    for _ in range(26):  # cracks and pebbles
        x, y = rng.uniform(10, w - 10), rng.uniform(10, h - 10)
        if rng.random() < .5:
            p._over(p.cap([(x, y), (x + rng.uniform(-14, 14), y + rng.uniform(4, 14)), (x + rng.uniform(-16, 16), y + rng.uniform(14, 24))], .9), (85, 85, 92))
        else:
            p._over(p.ell(x, y, 2, 1.6), (120, 120, 126))
    for _ in range(9):  # grass poking out of the joints
        gx = rng.randrange(1, 9) * s
        gy = rng.uniform(10, h - 10)
        for d in (-6, 0, 6):
            p._over(p.cap([(gx + d * .3, gy), (gx + d, gy - 12)], 1.2), rgb(GREEN))
    return p.image().convert('RGB')


def road_tile():
    """2 lanes tall: grey asphalt pencil, with a dashed middle line in each lane edge handled by the game"""
    w, h = 768, 256
    p = tile_base(w, h, 92, mix(PAPER, '#a9a7a0', .38))
    hm = p.hatchmask((35, -55), spacing=9, width=1.3, broken=.35) * .32
    p._over(hm, (70, 70, 76))
    rng = random.Random(6)
    for _ in range(60):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        p._over(p.ell(x, y, 1.6, 1.3), (70, 70, 76))
    return p.image().convert('RGB')


def creek_tile():
    w, h = 768, 256
    p = tile_base(w, h, 93, mix(PAPER, BLUE, .2))
    hm = p.hatchmask((8,), spacing=12, width=1.4, broken=.5) * .35
    p._over(hm, rgb(BLUE))
    rng = random.Random(8)
    for _ in range(26):
        x, y = rng.uniform(0, w - 60), rng.uniform(8, h - 8)
        L = rng.uniform(30, 70)
        pts = [(x + t, y + math.sin(t / 9) * 3) for t in np.linspace(0, L, 10)]
        p._over(p.cap(pts, 1.3), rgb(BLUE))
    return p.image().convert('RGB')


SPRITES = {
    'kid_up': lambda: kid_back(), 'kid_up_hop': lambda: kid_back(True),
    'kid_down': lambda: kid_front(), 'kid_down_hop': lambda: kid_front(True),
    'kid_side': lambda: kid_side(), 'kid_side_hop': lambda: kid_side(True),
    'kid_dizzy': lambda: kid_front(mood='dizzy'),
    'car_0': lambda: car(RED, seed=51), 'car_1': lambda: car(BLUE, seed=52), 'car_2': lambda: icecream_van(), 'car_3': lambda: car(GREEN, seed=54),
    'ride_0': lambda: rider('bike', PURPLE, 56), 'ride_1': lambda: rider('scooter', TEAL, 57), 'ride_2': lambda: rider('skateboard', ORANGE, 58), 'ride_3': lambda: rider('bike', PINK, 59),
    'log': log, 'plank': plank, 'crate': crate,
    'tree': tree, 'bench': bench, 'bush': bush, 'hydrant': hydrant, 'trashcan': trashcan, 'star': gold_star,
}
TILES = {'sidewalk': sidewalk_tile, 'road': road_tile, 'creek': creek_tile}


def main():
    os.makedirs(OUT, exist_ok=True)
    only = [a for a in sys.argv[1:] if a in SPRITES or a in TILES]
    imgs = {}
    for k, f in SPRITES.items():
        if only and k not in only:
            continue
        im = f()
        im.save(os.path.join(OUT, k + '.webp'), 'WEBP', quality=88, method=6)
        imgs[k] = im
        print(k, im.size)
    for k, f in TILES.items():
        if only and k not in only:
            continue
        im = f()
        im.save(os.path.join(OUT, k + '.jpg'), 'JPEG', quality=86)
        imgs[k] = im.convert('RGBA')
        print(k, im.size)
    if '--sheet' in sys.argv:
        path = sys.argv[sys.argv.index('--sheet') + 1]
        cols, cell = 6, 240
        rows = (len(imgs) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * cell, rows * cell), (200, 200, 200, 255))
        for i, (k, im) in enumerate(imgs.items()):
            t = im.copy()
            t.thumbnail((cell - 16, cell - 16))
            sheet.paste(t, ((i % cols) * cell + 8, (i // cols) * cell + 8), t)
        sheet.save(path)


if __name__ == '__main__':
    main()
