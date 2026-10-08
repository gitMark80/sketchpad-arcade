# Sketchpad Arcade style guide

Every game on Sketchpad Arcade is a Beach Day Arcade game redrawn to look like a **10-year-old's pencil sketchbook**: graphite lines on cream paper, a little hatching for shading, wobbly hand-drawn borders, handwriting fonts, and coloured pencil only where a kid would reach for one (the thing you must grab, the thing you must avoid). Gameplay, sounds, save data and layout stay exactly as they are. Only the look changes.

Reference twins, already done: `src/games/seaside-sprint.html` and `src/games/lighthouse-drop.html` (compare with the originals in the Beach Day Arcade repo's `src/games/`; clone it next to this repo as `../beach-day-arcade` or point `BDA_REPO` at it).

## How to make a twin

1. `cp ../beach-day-arcade/src/games/<slug>.html src/games/<slug>.html` — same file name, same slug.
2. `python3 sketchify.py <slug>` — makes the pencil cover (`src/img/<slug>.jpg`) and, if the game has `src/assets/<slug>/` in Beach Day Arcade, pencil versions of every image in `src/assets/<slug>/` (sounds and other files are copied through). Asset paths in the game stay unchanged. If something should keep a colour, add it to `TINTS[<slug>]` in `sketchify.py` first (key = file-name prefix, value = pencil colour as 0–1 RGB) and run again.
3. If the game embeds `data:image/...;base64` pictures, run `python3 sketchify.py <slug> --inline` after step 1 to sketch them in place.
4. Restyle the page CSS (see below).
5. Restyle everything the canvas draws in colour (see below).
6. Check it: serve `src/` and screenshot the start screen, mid-game and game-over with Playwright at 390×780 @2x (see "Checking"). No console errors, nothing invisible, nothing still in the old bright palette.

## Page CSS

Replace the game's `:root` palette, fonts and component styles with the paper system. Keep every selector, layout rule and media query the game already has; change only colours, fonts, borders and shadows. The `<link>` to Google Fonts becomes `family=Gloria+Hallelujah&family=Patrick+Hand`.

```css
:root{
  --paper:#f6f3ea; --paper-2:#efeadd; --ink:#2e2e33; --pencil:#55555c; --muted:#7a7a80; --faint:#c9c6bc;
  --yellow:#c99a1a; --yellow-wash:#f3e6b0; --orange:#d9661a; --blue:#2f6fb5; --blue-wash:#d6e4f2;
  --green:#5a9a6a; --green-wash:#dcebdd; --purple:#6f4a9a; --purple-wash:#e6dcef; --pink:#c45a8a; --pink-wash:#f0d5e2;
  --display:"Gloria Hallelujah","Comic Sans MS","Chalkboard SE",cursive;   /* titles, big numbers, buttons */
  --body:"Patrick Hand","Comic Sans MS","Chalkboard SE",cursive;           /* everything else */
  --wob:255px 15px 225px 15px/15px 225px 15px 255px;      /* hand-drawn border radius */
  --wob2:15px 255px 15px 225px/225px 15px 255px 15px;     /* the other way round, for variety */
  color-scheme:light;
}
body{background-color:var(--paper);color:var(--ink);font-family:var(--body);
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 .3 0 0 0 0 .3 0 0 0 0 .3 0 0 0 .07 0'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)'/%3E%3C/svg%3E")}
```

Rules of thumb:
- Title (`.brand` / `h1`): `font-family:var(--display);font-weight:400;text-transform:uppercase;letter-spacing:.04em;color:var(--ink);transform:rotate(-1.5deg);transform-origin:left center;font-size:clamp(1.05rem,6.2vw,1.6rem);overflow:hidden;text-overflow:ellipsis`. No gradients, shimmer or text shadows.
- Cards, HUD, panels, the playfield frame: `background:var(--paper);border:2px solid var(--ink);border-radius:var(--wob);box-shadow:3px 3px 0 var(--pencil)` (use `--wob2` on some so they don't all match). Cover overlays: `background:rgba(246,243,234,.55)`.
- Primary button (`.big`, Play): `background:var(--yellow-wash);border:2px solid var(--ink);border-radius:var(--wob2);color:var(--ink);font:400 2rem/1 var(--display);text-transform:uppercase;letter-spacing:.05em;box-shadow:4px 4px 0 var(--pencil)`; on `:active` translate (3px,3px) and shrink the shadow. Secondary buttons: paper fill, ink border, `--body` font, 2px shadow. Remove `::before`/`::after` gloss and sweep animations.
- Small labels (`small`, stat captions): `--body`, `color:var(--muted)`, slightly bigger than before (handwriting runs small). Weights: handwriting fonts have one weight, so drop `font-weight:800` etc. (use 400).
- Numbered rule badges: paper fill, 2px ink border, `--wob2` radius, ink text.
- Selected state (a chosen tile, runner, level): `--yellow-wash` fill with a solid ink border; unselected: dashed `--faint` border.
- Banners / floating text: ink text with a paper halo: `text-shadow:0 0 6px var(--paper),0 0 12px var(--paper),2px 2px 0 var(--paper)`, rotated -2deg.
- Inline SVG icons (help, sound, share): strokes and fills in `#2e2e33`; the "off"/mute cross in `#d9661a`.
- Progress bars: paper track with a 2px ink border; fill `repeating-linear-gradient(135deg,var(--yellow) 0 2px,var(--yellow-wash) 2px 6px)`.
- Words the rules highlight (dangers, bonuses): `color:var(--purple)` (or the matching accent) with `text-decoration:underline wavy`.
- Keep `[hidden]{display:none!important}`, reduced-motion rules and all existing media queries.

## Canvas / in-game drawing

Define once near the top of the script: `const PAPER='#f6f3ea',INK='#2e2e33',GRAPH='#55555c',PENCIL='rgba(46,46,51,.55)';`

- Backgrounds and sky: paper. If the game paints a sky/sea gradient, replace it with paper plus a pencil horizon line, a wobbly sun with rays (`ctx.lineWidth 2`, 12 rays) and one or two outlined clouds. See `buildBg` in `seaside-sprint.html` for a ready-made version.
- Surfaces (boards, grids, decks, sand, water): light paper tones `#f0ece1 #e9e6db #e4e2d8 #dedcd4 #d9d7cf` with ink or `PENCIL` outlines. Water is a slightly darker paper tone with a few short grey ripple lines; sand/wood is paper with pencil seam lines.
- Outlines everywhere: anything that used to be a solid colour shape gets a paper (or light tone) fill and a `1.5–2px` ink stroke. Shading = a few diagonal hatch lines in `GRAPH` at 0.4–0.6 alpha, not gradients.
- Highlights and gloss (white ellipses, `rgba(255,255,255,…)`, radial glows): remove, or turn into a short grey pencil arc.
- Shadows: `rgba(46,46,51,.2)` ellipses.
- Colour accents (coloured pencil, i.e. a mid-saturation line colour with a pale wash fill): yellow `#c99a1a`/`#f3e6b0` for points, coins, gold; orange `#d9661a`/`#f0c9a8` for speed and fire; blue `#2f6fb5`/`#d6e4f2` for water power-ups and bubbles; green `#5a9a6a`/`#dcebdd` for plants and "good"; purple `#6f4a9a`/`#e6dcef` and pink `#c45a8a`/`#f0d5e2` for hazards. Use at most two or three accents per game, only on the things the player has to read fast.
- Things drawn from colour tables (tile palettes, gem colours, bubble colours, match-3 pieces, word tiles): the game still needs them told apart, so keep one hue per kind but as coloured pencil: line colour from the accent list above (add `#8a3b3b` brick red and `#3d7a8a` teal if you need more than five), fill = that line colour at ~.22 alpha over paper, plus an ink outline. Never leave saturated fills.
- Particles, confetti, sparkles: coloured-pencil accent colours or `GRAPH`; never white (invisible on paper).
- Canvas text: `font:'<size>px "Gloria Hallelujah","Comic Sans MS",cursive'` for scores and pops, `"Patrick Hand"` for small labels; fill `INK`, stroke `PAPER` (lineWidth ≈ size*.25) for a halo. Floating "+10" style text: ink; gold moments can be `#c99a1a`.
- Fade/flash overlays: `rgba(246,243,234,a)`.
- Fallback hand-drawn sprites (the ones the game draws when an image hasn't loaded): either recolour them to graphite + accents or leave them; the sketched images replace them on load.
- Start-card mini illustrations (`drawMini` and the like): redraw as a simple doodle — paper fill, ink outlines, a bit of hatching. See `drawMini` in `lighthouse-drop.html`.
- Image-based games (sprites from `src/assets/<slug>/`): once sketchify has run they load the pencil versions automatically; you only need to fix the code-drawn parts around them.

## Checking

```python
from playwright.sync_api import sync_playwright
import http.server, threading, functools
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
H=functools.partial(Q,directory='src'); srv=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),H)
threading.Thread(target=srv.serve_forever,daemon=True).start()
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':780},device_scale_factor=2)
    errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/games/<slug>.html'); pg.wait_for_timeout(2500); pg.screenshot(path='…/<slug>-1.png')
    # click Play, wait, screenshot; drive the game a little (keys/taps) and screenshot again; errs must be []
srv.shutdown()
```

Use a port of your own (8800–8899) so parallel checks don't collide. Look at the screenshots: everything on paper, nothing invisible (white-on-paper text, white particles), nothing still bright blue/teal/coral, play still works.

Do **not** edit `games.json` here; it is generated from the Beach Day Arcade entries for every game present in `src/games/`. Do not touch the Beach Day Arcade checkout except to read from it.
