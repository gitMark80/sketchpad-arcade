#!/usr/bin/env python3
"""Screenshots every /play page at a desktop size (start screen, then after pressing the main Play button if there is one),
and tiles them into contact sheets. For checking the wide desktop layout. Usage: python3 tools/desktop-shots.py [slug ...]"""
import asyncio, json, sys, http.server, threading, functools, pathlib
from PIL import Image, ImageDraw
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'; OUT = pathlib.Path('/home/claude/desktop-shots'); OUT.mkdir(exist_ok=True)
PORT = 8769; VW, VH = 1600, 900
GAMES = [g['slug'] for g in json.load(open(ROOT / 'games.json'))['games']]
PLAY_SEL = '#playBtn, #play, #start button, button.big, button.play, [data-start], button#startBtn, #go'

def serve():
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE)))
    srv.daemon_threads = True; threading.Thread(target=srv.serve_forever, daemon=True).start()

async def shoot(ctx, slug):
    page = await ctx.new_page(); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.goto(f'http://127.0.0.1:{PORT}/play/{slug}.html', wait_until='networkidle'); await page.wait_for_timeout(900)
    info = await page.evaluate('''() => ({sw: document.documentElement.scrollWidth > innerWidth, sh: document.body.scrollHeight > innerHeight + 2,
        cv: [...document.querySelectorAll('canvas')].filter(c=>c.offsetWidth>100).map(c=>[c.id, c.offsetWidth, c.offsetHeight])})''')
    await page.screenshot(path=OUT / f'{slug}-1.png')
    clicked = False
    for sel in PLAY_SEL.split(', '):
        loc = page.locator(sel).first
        try:
            if await loc.count() and await loc.is_visible():
                await loc.click(timeout=1500); clicked = True; break
        except Exception: pass
    if clicked:
        await page.wait_for_timeout(1800)
        # one generic input so canvases that draw on first input show something
        try: await page.keyboard.press('Space')
        except Exception: pass
        await page.wait_for_timeout(600)
        await page.screenshot(path=OUT / f'{slug}-2.png')
    await page.close()
    return {'slug': slug, 'errors': errs, 'clicked': clicked, **info}

async def main():
    serve(); slugs = sys.argv[1:] or GAMES; res = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--autoplay-policy=no-user-gesture-required'])
        ctx = await b.new_context(viewport={'width': VW, 'height': VH}, has_touch=False)
        for s in slugs:
            try: res.append(await shoot(ctx, s))
            except Exception as e: res.append({'slug': s, 'errors': [f'SHOT FAILED {e}'], 'clicked': False})
            print(res[-1], flush=True)
        await b.close()
    json.dump(res, open(OUT / 'report.json', 'w'), indent=1)
    # contact sheets: 3 columns x 4 rows per sheet, prefer the in-play shot
    tiles = []
    for r in res:
        p = OUT / f"{r['slug']}-2.png"
        if not p.exists(): p = OUT / f"{r['slug']}-1.png"
        if p.exists(): tiles.append((r['slug'], p))
    tw, th = 520, 292; cols = 3; rows = 4
    for i in range(0, len(tiles), cols * rows):
        sheet = Image.new('RGB', (cols * tw, rows * (th + 22)), (40, 40, 44)); d = ImageDraw.Draw(sheet)
        for j, (slug, p) in enumerate(tiles[i:i + cols * rows]):
            im = Image.open(p).convert('RGB').resize((tw, th), Image.LANCZOS); x, y = (j % cols) * tw, (j // cols) * (th + 22)
            sheet.paste(im, (x, y)); d.text((x + 6, y + th + 4), slug, fill=(255, 255, 255))
        sheet.save(OUT / f'sheet-{i // (cols * rows) + 1}.png')
    print('sheets:', len(tiles))

asyncio.run(main())
