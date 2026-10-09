#!/usr/bin/env python3
"""Builds the Space Glass colour-by-number pictures and writes them into src/games/space-glass.html.

Each picture is drawn from simple shapes (circles, ellipses, polygons) on a grid of cells, then every cell takes the
colour that covers most of it. The result is written as ASCII rows (one letter per colour, '.' = empty) between the
`/*PICTURES*/` and `/*END PICTURES*/` markers in the game, so the pictures stay easy to read and hand-edit.

    python3 tools/space-glass-pictures.py            # rewrite the pictures in the game
    python3 tools/space-glass-pictures.py --print    # just print them

Letters (colours are set in the game's BASE table): R red, O orange, Y yellow, L lime, G green, T teal, S sky, B blue,
I indigo, U purple, P pink, N brown, A grey, D dark grey, K black, W white, C peach.
"""
import sys, math, re
from pathlib import Path
import numpy as np

GAME = Path(__file__).resolve().parent.parent / "src" / "games" / "space-glass.html"
SUB = 4  # samples per cell side


class Grid:
    def __init__(self, w, h, k=1.0):
        """w x h cells; shapes are given in units of 1/k cells (k < 1 squeezes a drawing onto fewer cells)."""
        self.w, self.h = w, h
        ys, xs = np.mgrid[0:h * SUB, 0:w * SUB]
        self.x = (xs + .5) / SUB / k
        self.y = (ys + .5) / SUB / k
        self.lab = np.full((h * SUB, w * SUB), ".", dtype="<U1")

    def paint(self, ch, m):
        self.lab[m] = ch

    # shapes return boolean masks over the samples
    def circ(self, cx, cy, r):
        return (self.x - cx) ** 2 + (self.y - cy) ** 2 <= r * r

    def ell(self, cx, cy, rx, ry, rot=0):
        c, s = math.cos(rot), math.sin(rot)
        dx, dy = self.x - cx, self.y - cy
        u, v = dx * c + dy * s, -dx * s + dy * c
        return (u / rx) ** 2 + (v / ry) ** 2 <= 1

    def rect(self, x0, y0, x1, y1):
        return (self.x >= x0) & (self.x < x1) & (self.y >= y0) & (self.y < y1)

    def poly(self, pts):
        n = len(pts)
        inside = np.zeros(self.x.shape, bool)
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]
            xj, yj = pts[j]
            cond = ((yi > self.y) != (yj > self.y)) & (self.x < (xj - xi) * (self.y - yi) / ((yj - yi) or 1e-9) + xi)
            inside ^= cond
            j = i
        return inside

    def line(self, x0, y0, x1, y1, w):
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        t = np.clip(((self.x - x0) * dx + (self.y - y0) * dy) / L2, 0, 1)
        return (self.x - (x0 + t * dx)) ** 2 + (self.y - (y0 + t * dy)) ** 2 <= (w / 2) ** 2

    def star(self, cx, cy, r1, r2, rot=-math.pi / 2, n=5):
        return self.poly([(cx + (r1 if i % 2 == 0 else r2) * math.cos(rot + i * math.pi / n),
                           cy + (r1 if i % 2 == 0 else r2) * math.sin(rot + i * math.pi / n)) for i in range(2 * n)])

    def rows(self):
        out = []
        for cy in range(self.h):
            row = ""
            for cx in range(self.w):
                block = self.lab[cy * SUB:(cy + 1) * SUB, cx * SUB:(cx + 1) * SUB].ravel()
                vals, cnt = np.unique(block, return_counts=True)
                filled = {v: c for v, c in zip(vals, cnt) if v != "."}
                if sum(filled.values()) * 2 < SUB * SUB:
                    row += "."
                else:
                    row += max(filled.items(), key=lambda kv: kv[1])[0]
            out.append(row)
        # trim empty margins
        while out and set(out[0]) == {"."}: out.pop(0)
        while out and set(out[-1]) == {"."}: out.pop()
        left = min(len(r) - len(r.lstrip(".")) for r in out)
        right = max(len(r.rstrip(".")) for r in out)
        return [r[left:right] for r in out]


PICS = []


def pic(name):
    def deco(fn):
        PICS.append((name, fn))
        return fn
    return deco


@pic("Rocket")
def rocket():
    g = Grid(20, 26)
    g.paint("O", g.poly([(7, 21), (13, 21), (10, 26)]))
    g.paint("Y", g.poly([(8.5, 21), (11.5, 21), (10, 24.2)]))
    g.paint("R", g.poly([(6.5, 13), (2, 19.5), (2.5, 22), (6.5, 20)]))
    g.paint("R", g.poly([(13.5, 13), (18, 19.5), (17.5, 22), (13.5, 20)]))
    body = g.poly([(10, 0.5), (12.5, 3), (13.8, 7), (14, 12), (13.6, 21.2), (6.4, 21.2), (6, 12), (6.2, 7), (7.5, 3)])
    g.paint("W", body)
    g.paint("R", body & (g.y < 5.5))
    g.paint("B", body & (g.y >= 16) & (g.y < 17.6))
    g.paint("A", g.rect(7, 20, 13, 21.6))
    g.paint("B", g.circ(10, 10, 2.9))
    g.paint("S", g.circ(10, 10, 2.0))
    g.paint("W", g.circ(9.3, 9.3, .7))
    g.paint("R", g.rect(9.2, 17.6, 10.8, 22.5))
    return g


@pic("Astronaut")
def astronaut():
    g = Grid(22, 26)
    g.paint("A", g.rect(3, 10, 6, 19))  # backpack
    g.paint("W", g.ell(11, 18, 6.2, 6))  # body
    g.paint("W", g.line(5.5, 15, 2.5, 20, 3.2))  # arms
    g.paint("W", g.line(16.5, 15, 19.5, 11, 3.2))
    g.paint("A", g.circ(2.6, 20.6, 1.6))
    g.paint("A", g.circ(19.6, 10.4, 1.6))
    g.paint("W", g.rect(6.6, 21, 10.4, 25))  # legs
    g.paint("W", g.rect(11.6, 21, 15.4, 25))
    g.paint("A", g.rect(6.2, 23.6, 10.8, 25.6))
    g.paint("A", g.rect(11.2, 23.6, 15.8, 25.6))
    g.paint("B", g.rect(8, 16, 14, 20.4))  # chest panel
    g.paint("R", g.circ(9.6, 18.2, .9))
    g.paint("Y", g.circ(12.4, 18.2, .9))
    g.paint("W", g.circ(11, 7.5, 6.6))  # helmet
    g.paint("I", g.ell(11, 7.8, 4.6, 3.8))  # visor
    g.paint("S", g.ell(9.4, 6.6, 1.7, 1.1, .5))
    g.paint("O", g.rect(16, 1, 17, 4))  # little flag on the helmet antenna
    g.paint("O", g.rect(17, 1, 19.5, 2.6))
    return g


@pic("UFO")
def ufo():
    g = Grid(26, 22)
    g.paint("Y", g.poly([(9, 15), (17, 15), (21, 22), (5, 22)]))  # beam
    g.paint("S", g.ell(13, 8.5, 6.2, 6.2) & (g.y < 10.5))  # dome
    g.paint("L", g.ell(13, 7.4, 3.0, 2.8))  # alien head
    g.paint("L", g.line(11.6, 5, 10.4, 1.6, 0.9))
    g.paint("L", g.line(14.4, 5, 15.6, 1.6, 0.9))
    g.paint("P", g.circ(10.3, 1.5, 1))
    g.paint("P", g.circ(15.7, 1.5, 1))
    g.paint("K", g.circ(11.8, 7.2, .75))
    g.paint("K", g.circ(14.2, 7.2, .75))
    g.paint("U", g.ell(13, 12.2, 12.5, 3.6))  # saucer
    g.paint("P", g.ell(13, 13.7, 9.5, 1.6))
    for x in (4.5, 8.8, 13, 17.2, 21.5):
        g.paint("Y", g.circ(x, 11.8, 1.05))
    return g


@pic("Ringed Planet")
def ringed():
    g = Grid(28, 20)
    back = g.ell(14, 10.5, 13.5, 4.2, -.22) & ~g.ell(14, 10.5, 9.5, 2.3, -.22)
    g.paint("U", back)
    ball = g.circ(14, 10, 7.6)
    g.paint("Y", ball)
    g.paint("O", ball & (((g.y - 2.4 + (g.x - 14) * .2) % 4) < 1.4))
    g.paint("N", ball & ~g.circ(13, 9, 7.2))  # shade on the edge
    front = back & (g.y > 10.5 + (g.x - 14) * -.22)
    g.paint("U", front)
    g.paint("P", front & g.ell(14, 10.5, 11.8, 3.3, -.22))
    return g


@pic("Moon")
def moon():
    g = Grid(24, 24)
    m = g.circ(12, 12, 9.6)
    g.paint("A", m)
    g.paint("D", m & ~g.circ(10.6, 10.8, 9.4))
    g.paint("W", g.circ(8.5, 8, 2))
    for cx, cy, r in ((13.5, 7.5, 2.1), (7.5, 14, 2.4), (15, 15.5, 2.8), (11, 19, 1.3), (18, 10, 1.3)):
        g.paint("D", g.circ(cx, cy, r))
        g.paint("A", g.circ(cx + .5, cy + .5, r * .55))
    g.paint("Y", g.star(2.8, 2.8, 2.8, 1.2))
    g.paint("Y", g.star(21.2, 21.2, 2.8, 1.2))
    return g


@pic("Earth")
def earth():
    g = Grid(22, 22)
    e = g.circ(11, 11, 10)
    g.paint("B", e)
    g.paint("S", e & g.circ(9.5, 9.5, 8.6) & ~g.circ(13, 13, 6))
    land = (g.ell(7, 7, 4.2, 3, .6) | g.ell(5.5, 12, 2, 3.5) | g.ell(14.5, 13, 3.5, 4.5, -.4) | g.ell(16, 6, 2.2, 1.5) | g.ell(9, 17.5, 2, 1.3))
    g.paint("G", e & land)
    g.paint("L", e & land & g.circ(7, 6, 3.4))
    g.paint("L", e & land & g.circ(13.5, 11.5, 2.5))
    g.paint("W", e & (g.ell(13.5, 3.2, 3.4, .9) | g.ell(4.5, 17, 2.8, .8) | g.ell(17, 16.5, 2, .7)))
    return g


@pic("Sun")
def sun():
    g = Grid(24, 24)
    for k in range(12):
        a = k * math.pi / 6
        c = (12 + 11.6 * math.cos(a), 12 + 11.6 * math.sin(a))
        l = (12 + 7.5 * math.cos(a - .24), 12 + 7.5 * math.sin(a - .24))
        r = (12 + 7.5 * math.cos(a + .24), 12 + 7.5 * math.sin(a + .24))
        g.paint("R" if k % 2 else "O", g.poly([l, c, r]))
    g.paint("O", g.circ(12, 12, 7.6))
    g.paint("Y", g.circ(12, 12, 6.4))
    g.paint("K", g.circ(9.6, 10.6, .9))
    g.paint("K", g.circ(14.4, 10.6, .9))
    g.paint("P", g.ell(8.4, 13.4, 1.3, .8))
    g.paint("P", g.ell(15.6, 13.4, 1.3, .8))
    g.paint("R", g.ell(12, 14.6, 2.2, 1.4) & (g.y > 14.4))
    return g


@pic("Comet")
def comet():
    g = Grid(26, 17, .93)
    g.paint("U", g.line(1, 2, 19, 12, 3))
    g.paint("S", g.line(1, 7.5, 19, 12.6, 3))
    g.paint("P", g.line(4, 15.5, 19, 13, 2.4))
    g.paint("W", g.line(6, 4.4, 19, 11.6, 1.6))
    g.paint("O", g.circ(21.5, 12.5, 5.2))
    g.paint("Y", g.circ(21.8, 12.3, 3.8))
    g.paint("W", g.circ(20.6, 11, 1.1))
    g.paint("Y", g.star(8, 13.5, 2.6, 1.1))
    g.paint("Y", g.star(24.2, 2.8, 2.8, 1.2))
    return g


@pic("Satellite")
def satellite():
    g = Grid(26, 18)
    g.paint("A", g.rect(8, 8, 18, 9))  # struts
    for x0 in (0, 18):
        g.paint("B", g.rect(x0, 4, x0 + 8, 14))
        for k in (2, 5):
            g.paint("S", g.rect(x0 + k, 4, x0 + k + 1, 14))
        g.paint("S", g.rect(x0, 8, x0 + 8, 9))
    g.paint("Y", g.rect(9, 4, 17, 14))
    g.paint("O", g.rect(9, 6, 17, 7) | g.rect(9, 11, 17, 12))
    g.paint("A", g.rect(12, 2, 14, 4))
    g.paint("W", g.ell(13, 1.2, 4, 1.7) & (g.y > .5))
    g.paint("A", g.rect(12.5, 14, 13.5, 15.5))
    g.paint("R", g.circ(13, 16.4, 1.3))
    return g


@pic("Telescope")
def telescope():
    g = Grid(24, 24)
    g.paint("N", g.line(10, 13, 5, 23.5, 1.6))
    g.paint("N", g.line(11, 13, 17, 23.5, 1.6))
    g.paint("N", g.line(10.5, 13, 11, 23.5, 1.4))
    g.paint("B", g.line(3, 16, 17.5, 6.5, 4.6))
    g.paint("I", g.line(9.2, 12, 11.8, 10.3, 5.2))
    g.paint("A", g.line(1.2, 17.2, 3.4, 15.8, 2.8))
    g.paint("S", g.ell(18.5, 5.9, 1.4, 2.8, -.58))
    g.paint("A", g.circ(10.5, 13, 1.2))
    g.paint("Y", g.star(20.5, 15.5, 3, 1.3))
    g.paint("Y", g.star(4.5, 4, 2.9, 1.2))
    return g


@pic("Alien")
def alien():
    g = Grid(22, 26)
    g.paint("L", g.line(7.5, 6, 4.6, 1.8, 1.1))
    g.paint("L", g.line(14.5, 6, 17.4, 1.8, 1.1))
    g.paint("P", g.circ(4.4, 1.8, 1.5))
    g.paint("P", g.circ(17.6, 1.8, 1.5))
    g.paint("U", g.poly([(6.5, 15.5), (15.5, 15.5), (17.5, 24.5), (4.5, 24.5)]))  # suit
    g.paint("L", g.line(6.8, 17, 3, 21.5, 2))
    g.paint("L", g.line(15.2, 17, 19, 21.5, 2))
    g.paint("Y", g.circ(11, 19.5, 1.5))
    g.paint("L", g.ell(11, 10, 7.6, 6.6))  # head
    g.paint("G", g.ell(11, 10, 7.6, 6.6) & ~g.ell(10.3, 9.4, 7.3, 6.3))
    g.paint("K", g.ell(8, 9, 2.1, 2.6, .35))
    g.paint("K", g.ell(14, 9, 2.1, 2.6, -.35))
    g.paint("W", g.circ(7.6, 8.1, .75))
    g.paint("W", g.circ(13.6, 8.1, .75))
    g.paint("K", g.ell(11, 13.4, 2, 1) & (g.y > 13.3))
    return g


@pic("Space Shuttle")
def shuttle():
    g = Grid(24, 28)
    g.paint("O", g.ell(16, 13, 3.2, 10.5))  # fuel tank
    g.paint("N", g.ell(16, 13, 3.2, 10.5) & (g.x > 17.6))
    g.paint("W", g.ell(20.6, 14.5, 1.5, 9) | g.ell(11.4, 14.5, 1.5, 9))  # boosters
    g.paint("R", g.rect(10, 22.5, 12.8, 24) | g.rect(19.2, 22.5, 22, 24))
    orbiter = g.poly([(7, 3), (8.5, 6), (9, 20), (13.5, 24), (13.5, 26), (0.5, 26), (0.5, 24), (5, 20), (5, 6)])
    g.paint("W", orbiter)
    g.paint("D", orbiter & (g.y < 5.4))
    g.paint("D", orbiter & (g.y > 24.4))
    g.paint("K", g.rect(6, 6.6, 8, 7.8))
    g.paint("B", g.rect(6.4, 12, 7.6, 16))
    g.paint("Y", g.poly([(4.2, 26), (9.8, 26), (7, 27.9)]))
    g.paint("Y", g.poly([(18, 23.5), (21.5, 23.5), (19.75, 27.6)]))
    return g


@pic("Star Cluster")
def stars():
    g = Grid(26, 24)
    g.paint("Y", g.star(9, 10, 8.4, 3.6))
    g.paint("O", g.star(9, 10.6, 4.3, 1.9))
    g.paint("P", g.star(20, 5, 4.4, 1.9, -1.4))
    g.paint("S", g.star(20, 17.5, 5.2, 2.3, -1.7))
    g.paint("U", g.star(5, 20, 3.8, 1.6))
    g.paint("L", g.star(14.5, 20.8, 3.2, 1.4))
    g.paint("O", g.star(3, 3, 3, 1.3))
    return g


@pic("Moon Rover")
def rover():
    g = Grid(28, 20)
    g.paint("B", g.poly([(4, 6.5), (20, 6.5), (22, 4.5), (6, 4.5)]))  # solar panel
    g.paint("S", g.poly([(4, 6.5), (20, 6.5), (22, 4.5), (6, 4.5)]) & (((g.x - g.y) % 3.2) < .7))
    g.paint("A", g.rect(20.5, 2, 21.5, 9))  # mast
    g.paint("D", g.rect(19.5, .5, 25, 3.4))
    g.paint("S", g.circ(23.6, 1.95, 1))
    g.paint("Y", g.rect(3, 8, 23, 13))  # body
    g.paint("O", g.rect(3, 11.3, 23, 13))
    g.paint("R", g.circ(6.5, 9.8, 1.1))
    g.paint("A", g.line(1.5, 13.5, 26.5, 13.5, 1.2))
    for x in (4.5, 13, 21.5):
        g.paint("K", g.circ(x, 16, 3.3))
        g.paint("A", g.circ(x, 16, 1.4))
    return g


@pic("Galaxy")
def galaxy():
    g = Grid(26, 26)
    cx = cy = 13
    r = np.hypot(g.x - cx, g.y - cy)
    th = np.arctan2(g.y - cy, g.x - cx)
    disk = r < 12.6
    arm = np.cos(2 * (th - np.log(r + .5) * 1.9))
    g.paint("I", disk & (arm > .1) & (r > 2))
    g.paint("U", disk & (arm > .45) & (r > 2))
    g.paint("P", disk & (arm > .8) & (r > 3))
    g.paint("S", disk & (arm < -.6) & (r > 5) & (r < 10))
    g.paint("Y", g.circ(cx, cy, 3.4))
    g.paint("W", g.circ(cx, cy, 1.5))
    for sx, sy in ((3, 3), (23, 22), (22, 3.5), (3.5, 22.5)):
        g.paint("Y", g.star(sx, sy, 2.7, 1.15))
    return g


def build():
    out = []
    for name, fn in PICS:
        rows = fn().rows()
        out.append((name, rows))
    return out


def js(pics):
    parts = []
    for name, rows in pics:
        parts.append("{name:'%s',a:`\n%s`}" % (name, "\n".join(rows)))
    return "const RAW=[\n" + ",\n".join(parts) + "\n];"


if __name__ == "__main__":
    pics = build()
    for name, rows in pics:
        cells = sum(ch != "." for r in rows for ch in r)
        cols = sorted(set("".join(rows)) - {"."})
        print(f"{name}: {max(map(len, rows))}x{len(rows)} grid, {cells} squares, {len(cols)} colours {''.join(cols)}", file=sys.stderr)
        if "--print" in sys.argv:
            print("\n".join(rows), file=sys.stderr)
    if "--print" not in sys.argv:
        s = GAME.read_text()
        new, n = re.subn(r"/\*PICTURES\*/.*?/\*END PICTURES\*/", lambda m: "/*PICTURES*/\n" + js(pics) + "\n/*END PICTURES*/", s, flags=re.S)
        assert n == 1, "markers not found"
        GAME.write_text(new)
        print("wrote", GAME, file=sys.stderr)
