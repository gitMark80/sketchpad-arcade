#!/usr/bin/env python3
"""Builds No. 2 Pencil's icon sprite sheets from Mark's hand-drawn icons.

Reads 24 transparent PNGs (one per icon, named below) from an art folder and writes two 6x4 sheets with 192px cells,
in the order the game expects (see SHEET / MAIN in src/games/no-2-pencil.html):
  icons-color.webp     Mark's icons as drawn, each fitted and centred in its cell with a little padding
  icons-graphite.webp  the same icons as untouched graphite: desaturated to pencil grey and lightened, black outlines kept

Usage: python3 tools/no2-pencil-sheets.py ART_DIR [OUT_DIR]
  ART_DIR  folder with pencil.png, apple.png, ... trophy.png
  OUT_DIR  defaults to src/assets/no-2-pencil
"""
import os, sys
import numpy as np
from PIL import Image

NAMES = ['pencil', 'apple', 'book', 'backpack', 'crayon', 'star-sticker', 'scissors', 'paperclip', 'eraser', 'ruler',
         'paintbrush', 'notebook', 'globe', 'chalkboard', 'calculator', 'school-bus', 'alarm-clock', 'lunchbox',
         'paint-palette', 'pencil-cup', 'sticky-note', 'magnifying-glass', 'abc-block', 'trophy']
CELL, COLS, ROWS, PAD = 192, 6, 4, 0.05  # PAD: share of the cell left empty on each side


def fit(im):
    im = im.convert('RGBA')
    box = im.getbbox()
    if box:
        im = im.crop(box)
    inner = CELL * (1 - 2 * PAD)
    k = inner / max(im.size)
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


def graphite(im):
    a = np.asarray(im).astype(np.float32)
    rgb, al = a[:, :, :3], a[:, :, 3:]
    lum = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    # dark ink outlines stay dark; colour fills fade towards paper like light pencil shading
    t = np.clip((lum - 55) / 70, 0, 1)
    g = lum * (1 - t) + (lum + (255 - lum) * 0.28) * t
    out = np.stack([g - 2, g - 1, g + 3], -1)
    return Image.fromarray(np.concatenate([np.clip(out, 0, 255), al], -1).astype(np.uint8), 'RGBA')


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    art = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'assets', 'no-2-pencil')
    os.makedirs(out, exist_ok=True)
    color = Image.new('RGBA', (CELL * COLS, CELL * ROWS), (0, 0, 0, 0))
    graph = color.copy()
    for i, name in enumerate(NAMES):
        icon = fit(Image.open(os.path.join(art, name + '.png')))
        x = (i % COLS) * CELL + (CELL - icon.width) // 2
        y = (i // COLS) * CELL + (CELL - icon.height) // 2
        color.alpha_composite(icon, (x, y))
        graph.alpha_composite(graphite(icon), (x, y))
    color.save(os.path.join(out, 'icons-color.webp'), quality=90, method=6)
    graph.save(os.path.join(out, 'icons-graphite.webp'), quality=90, method=6)
    print('wrote', os.path.join(out, 'icons-color.webp'), 'and icons-graphite.webp')


if __name__ == '__main__':
    main()
