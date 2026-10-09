#!/usr/bin/env python3
"""Builds the Sketchpad Arcade static site into ./site from games.json and ./src.

Sketchpad Arcade is the pencil-sketchbook twin of Beach Day Arcade (the repo root). Each game here is a
restyled copy of a Beach Day Arcade game under the same slug; sketchify.py makes its pencil art.

Add a game: put its standalone HTML file in src/games/<slug>.html, a square
thumbnail in src/img/<slug>.jpg, add an entry to games.json, then run
`python3 build.py`. Upload the ./site folder to Vercel or Netlify.
"""
import json, html, shutil, re, os
from pathlib import Path

ROOT = Path(__file__).parent
CFG = json.loads((ROOT / "games.json").read_text())
SITE = CFG["site"]
GAMES = CFG["games"]

# Every game needs an "added" date (YYYY-MM-DD) for the "New this week" row.
# A game without one gets today's date (Central time) written into games.json.
def stamp_added_dates():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d")
    changed = False
    for g in GAMES:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(g.get("added", ""))):
            items = [(k, v) for k, v in g.items() if k != "added"]
            at = next((i + 1 for i, (k, _) in enumerate(items) if k == "genre"), len(items))
            items.insert(at, ("added", today))
            g.clear(); g.update(items)
            changed = True
    if changed:
        (ROOT / "games.json").write_text(json.dumps(CFG, indent=2, ensure_ascii=False) + "\n")
stamp_added_dates()
OUT = ROOT / "site"
E = html.escape

ADSENSE = ""  # no AdSense on this site until it is approved
# Vercel Web Analytics - official script from https://vercel.com/docs/analytics/quickstart
ANALYTICS = '<script>\n  window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };\n</script>\n<script defer src="/_vercel/insights/script.js"></script>\n'
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gloria+Hallelujah&family=Patrick+Hand&display=swap">'

CSS = """
/* Sketchpad Arcade: every page is a sketchbook page. Paper with a faint grain, graphite ink, wobbly hand-drawn borders,
   handwriting fonts, and coloured-pencil accents only where a kid would have reached for one. */
:root{--paper:#f6f3ea;--paper-2:#efeadd;--ink:#2e2e33;--pencil:#55555c;--muted:#7a7a80;--faint:#c9c6bc;
--yellow:#c99a1a;--yellow-wash:#f3e6b0;--orange:#d9661a;--blue:#2f6fb5;--blue-wash:#d6e4f2;--green:#5a9a6a;--green-wash:#dcebdd;--pink:#c45a8a;--pink-wash:#f0d5e2;
--display:"Gloria Hallelujah","Comic Sans MS","Chalkboard SE",cursive;--body:"Patrick Hand","Comic Sans MS","Chalkboard SE",cursive;
--wob:255px 15px 225px 15px/15px 225px 15px 255px;--wob2:15px 255px 15px 225px/225px 15px 255px 15px;color-scheme:light}
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background-color:var(--paper);color:var(--ink);font-family:var(--body);font-size:19px;line-height:1.45;
background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 .3 0 0 0 0 .3 0 0 0 0 .3 0 0 0 .07 0'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)'/%3E%3C/svg%3E")}
a{color:inherit}
img{max-width:100%;display:block}
.wrap{max-width:1100px;margin:0 auto;padding-inline:16px}
.top{border-bottom:2px solid var(--ink)}
.nav{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-block:12px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;font-family:var(--display);font-size:1.5rem;line-height:1;letter-spacing:.04em;text-transform:uppercase;color:var(--ink);transform:rotate(-1.5deg);white-space:nowrap}
.logo svg{width:34px;height:34px;flex:none}
.homehead{display:grid;gap:4px;padding-block:22px 6px;text-align:center}
.homehead h1{font-size:clamp(2.2rem,7vw,4rem);line-height:1.05;text-transform:uppercase;letter-spacing:.04em;transform:rotate(-1.5deg)}
.homehead p{margin:6px auto 0;max-width:46ch;color:var(--pencil);font-size:1.15rem}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
.nav ul{display:flex;gap:6px;list-style:none;margin:0;padding:0}
.nav a.link{text-decoration:none;padding:8px 12px}
a:focus-visible,button:focus-visible{outline:3px solid var(--ink);outline-offset:3px;border-radius:8px}
h1,h2,h3{font-family:var(--display);font-weight:400;line-height:1.15;text-wrap:balance;margin:0}
.chips{display:flex;gap:10px;justify-content:center;padding-block:14px 22px;flex-wrap:wrap}
.chip{appearance:none;cursor:pointer;font-family:var(--body);font-size:1.1rem;line-height:1;padding:9px 18px;border:2px dashed var(--pencil);border-radius:var(--wob);white-space:nowrap;background:var(--paper);color:var(--ink);transition:transform .12s}
.chip:hover{transform:translateY(-1px)}
.chip[aria-pressed="true"]{border-style:solid;border-color:var(--ink);background:var(--yellow-wash);box-shadow:2px 2px 0 var(--pencil)}
@media (max-width:520px){.chips{gap:7px}.chip{flex:1;min-width:0;font-size:1rem;padding:8px 6px}}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:20px}
.card{display:flex;flex-direction:column;background:var(--paper);border:2px solid var(--ink);border-radius:var(--wob);overflow:hidden;text-decoration:none;box-shadow:3px 3px 0 var(--pencil);transition:transform .15s,box-shadow .15s}
.card:nth-child(2n){border-radius:var(--wob2)}
.card:hover{transform:translate(-2px,-2px) rotate(-.6deg);box-shadow:5px 5px 0 var(--pencil)}
.card .thumb{aspect-ratio:1;width:100%;height:auto;object-fit:cover;background:var(--paper-2);border-bottom:2px solid var(--ink)}
.card .body{padding:8px 12px 10px;display:flex;justify-content:center;min-width:0}
.card h3{font-size:1.35rem}
.card p{margin:0;color:var(--muted);font-size:.95rem;line-height:1.4}
.tag{align-self:center;font-size:.9rem;text-transform:uppercase;letter-spacing:.08em;padding:2px 10px;border:2px solid var(--pink);border-radius:var(--wob);background:var(--pink-wash);color:var(--ink)}
.tag.arcade{border-color:var(--blue);background:var(--blue-wash)}
.tag.word{border-color:var(--yellow);background:var(--yellow-wash)}
.tag.puzzle{border-color:var(--green);background:var(--green-wash)}
.also{margin-top:28px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;background:var(--paper);border:2px dashed var(--pencil);border-radius:var(--wob2);padding:18px 20px}
.also p{margin:0}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;font-family:var(--display);font-size:1.25rem;letter-spacing:.04em;text-transform:uppercase;text-decoration:none;color:var(--ink);background:var(--yellow-wash);border:2px solid var(--ink);border-radius:var(--wob2);padding:10px 28px;box-shadow:4px 4px 0 var(--pencil);transition:transform .1s}
.btn:active{transform:translate(3px,3px);box-shadow:1px 1px 0 var(--pencil)}
.btn.small{font-size:1rem;padding:7px 16px;box-shadow:3px 3px 0 var(--pencil)}
.crumbs{font-size:1rem;color:var(--muted);padding-block:18px 8px}
.crumbs a{text-decoration:none}.crumbs a:hover{text-decoration:underline}
.hero{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.1fr);gap:32px;align-items:center;padding-block:8px 28px}
.cover{position:relative;border:2px solid var(--ink);border-radius:var(--wob);overflow:hidden;box-shadow:5px 5px 0 var(--pencil);background:var(--paper-2)}
.cover img{aspect-ratio:1;width:100%;height:auto;object-fit:cover}
.cover .btn{position:absolute;left:50%;bottom:22px;transform:translateX(-50%)}
.cover .btn:active{transform:translate(calc(-50% + 3px),3px)}
.info{display:flex;flex-direction:column;gap:14px;min-width:0}
.info h1{font-size:clamp(2.2rem,5vw,3.2rem);text-transform:uppercase;letter-spacing:.03em}
.lead{margin:0;font-size:1.15rem;color:var(--pencil);max-width:60ch}
.facts{display:flex;flex-wrap:wrap;gap:8px;margin:0;padding:0;list-style:none}
.facts li{background:var(--paper);border:2px solid var(--pencil);border-radius:var(--wob);padding:4px 12px;font-size:.95rem;color:var(--ink)}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;padding-block:8px 28px}
.panel{background:var(--paper);border:2px solid var(--ink);border-radius:var(--wob2);padding:18px 22px;box-shadow:3px 3px 0 var(--pencil)}
.panel:nth-child(2n){border-radius:var(--wob)}
.panel.about{margin:0 0 28px}
.panel.about p{margin:0 0 10px;line-height:1.5;max-width:70ch}
.panel h2{font-size:1.5rem;margin-bottom:10px;text-transform:uppercase;letter-spacing:.03em}
.panel ol,.panel ul{margin:0;padding-left:1.3em;display:flex;flex-direction:column;gap:8px}
.panel li{max-width:65ch}
.prose{max-width:68ch;padding-block:24px 40px}
.prose h1{font-size:2.4rem;margin-bottom:14px;text-transform:uppercase}
.prose h2{font-size:1.5rem;margin:28px 0 8px}
.prose p,.prose li{color:var(--ink)}
section>h2.sec{font-size:1.8rem;margin:10px 0 16px;text-transform:uppercase;letter-spacing:.03em}
footer{margin-top:40px;border-top:2px solid var(--ink);color:var(--pencil)}
footer a{color:var(--ink)}
footer .wrap{display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px;padding-block:22px;font-size:1rem}
footer ul{display:flex;gap:16px;list-style:none;margin:0;padding:0}
@media (max-width:720px){.hero{grid-template-columns:1fr;gap:20px}.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.card h3{font-size:1.1rem}.card p{font-size:.85rem}.card .body{padding:6px 10px 8px}.nav{flex-wrap:wrap}}
@media (max-width:360px){.grid{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){.card{transition:none}.card:hover{transform:none}}
.navr{display:flex;align-items:center;gap:8px}
.sharebtn{appearance:none;cursor:pointer;display:inline-flex;align-items:center;gap:7px;font-family:var(--body);font-size:1.1rem;line-height:1;padding:8px 14px 8px 12px;border:2px solid var(--ink);border-radius:var(--wob);background:var(--paper);color:var(--ink);box-shadow:2px 2px 0 var(--pencil);transition:transform .12s}
.sharebtn:active{transform:translate(2px,2px);box-shadow:none}
.homebtn{text-decoration:none;background:var(--yellow-wash);border-radius:var(--wob2)}
.sharebtn svg{flex:none;width:18px;height:18px}
@media (max-width:720px){.nav{flex-wrap:nowrap!important}}
@media (max-width:460px){.nav{gap:6px}.navr{gap:4px}.logo{font-size:1.15rem}.logo svg{width:26px;height:26px}.sharebtn{font-size:1rem;padding:7px 10px 7px 9px;gap:5px}}
@media (max-width:379px){.sharebtn span{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}.sharebtn{padding:8px}}
.btn.share{background:var(--paper);cursor:pointer}
.btnrow{display:flex;flex-wrap:wrap;gap:12px;align-items:center}
/* Home rows: sideways-scrolling strips above the full grid */
.row{margin-bottom:22px}
.row>h2.sec{margin:6px 0 12px;font-size:1.6rem}
.strip{display:grid;grid-auto-flow:column;grid-auto-columns:200px;gap:16px;overflow-x:auto;overscroll-behavior-x:contain;scroll-snap-type:x mandatory;scroll-padding-inline:16px;
  margin-inline:-16px;padding:4px 16px 18px;scrollbar-width:thin;scrollbar-color:var(--faint) transparent}
.strip .card{scroll-snap-align:start}
@media (max-width:720px){.strip{grid-auto-columns:40%;gap:12px}.row>h2.sec{font-size:1.35rem}}
@media (max-width:360px){.strip{grid-auto-columns:62%}}
"""

def page(title, desc, body, active="", full=True, canonical=None, extra_head="", share=None):
    share = share or site_share()
    t = E(title)
    base = SITE.get("url", "").rstrip("/")
    canon = f'<link rel="canonical" href="{base}/{canonical}">\n<meta property="og:url" content="{base}/{canonical}">\n' if (base and canonical is not None) else ""
    icons = f'<link rel="icon" type="image/png" sizes="32x32" href="{base}/brand/icon-32.png?v=2">\n<link rel="icon" type="image/png" sizes="192x192" href="{base}/brand/icon-192.png?v=2">\n<link rel="apple-touch-icon" href="{base}/brand/apple-touch-icon.png?v=2">\n<meta name="theme-color" content="#f6f3ea">\n'
    if "og:image" not in extra_head:
        extra_head = f'<meta property="og:image" content="{base}/brand/share-2.jpg">\n' + extra_head
    extra_head = '<meta name="twitter:card" content="summary_large_image">\n' + extra_head
    head = f'<title>{t}</title>\n{canon}{icons}{ADSENSE}{ANALYTICS}{SHARE_CSS}\n<meta name="description" content="{E(desc)}">\n<meta property="og:title" content="{t}">\n<meta property="og:description" content="{E(desc)}">\n{FONTS}\n{extra_head}<style>{CSS}</style>\n'
    nav = f'''<div class="top"><nav class="wrap nav" aria-label="Main">
<a class="logo" href="index.html">{LOGO_SVG}<span>{E(SITE["name"])}</span></a>
<div class="navr"><a class="sharebtn homebtn" href="index.html"{' aria-current="page"' if active=="games" else ""}>{HOME_ICON}<span>Home</span></a>
<button class="sharebtn" type="button" {share}>{SHARE_ICON}<span>Share</span></button></div>
</nav></div>'''
    foot = f'''<footer><div class="wrap"><span>© 2026 {E(SITE["owner"])}.<br>Free games, no downloads.</span>
<ul><li><a href="about.html">About</a></li><li><a href="privacy.html">Privacy</a></li></ul></div></footer>'''
    content = f"{nav}\n<main>{body}</main>\n{foot}\n{SHARE_JS}"
    if not full:  # fragment for the claude.ai preview, which supplies its own document shell
        return head + content
    return f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n{head}</head>\n<body>\n{content}\n</body>\n</html>\n'

def card(g):
    cls = "tag " + g["genre"].lower()
    return f'''<a class="card" href="{g["slug"]}.html" data-slug="{E(g["slug"])}" data-added="{E(g["added"])}" data-genre="{E(g["genre"])}" aria-label="{E(g["name"])}, {E(g["genre"])} game" title="{E(g["name"])}">
<img class="thumb" src="img/{g["slug"]}.jpg" alt="{E(g["name"])}" loading="lazy" width="640" height="640">
<div class="body"><span class="{cls}">{E(g["genre"])}</span></div></a>'''

def home(full=True):
    genres = sorted({g["genre"] for g in GAMES})
    chips = '<button class="chip" type="button" data-f="all" aria-pressed="true">All games</button>' + "".join(
        f'<button class="chip" type="button" data-f="{E(x)}" aria-pressed="false">{E(x)}</button>' for x in genres)
    also = ""
    if SITE.get("also"):
        a = SITE["also"]
        also = f'<div class="also"><p>{E(a["text"])}</p><a class="btn small" href="{E(a["url"])}" rel="noopener">{E(a["cta"])}</a></div>'
    body = f'''<div class="wrap">
<div class="homehead"><h1>{E(SITE["headline"])}</h1><p>{E(SITE["intro"])}</p></div>
<div class="chips" role="group" aria-label="Filter games">{chips}</div>
<section class="row" id="row-new" hidden><h2 class="sec">New This Week</h2><div class="strip"></div></section>
<section class="row" id="row-all" hidden><h2 class="sec">All-Time Favorites</h2><div class="strip"></div></section>
<section class="row" id="row-recent" hidden><h2 class="sec">Recent Favorites</h2><div class="strip"></div></section>
<section class="row" id="row-picks" hidden><h2 class="sec">Our Picks</h2><div class="strip"></div></section>
{"".join(f'<section class="row" id="row-genre-{E(x.lower())}" hidden><h2 class="sec">{E(x)} Games</h2><div class="strip"></div></section>' for x in genres)}
<section class="row" id="row-rest"><h2 class="sec" hidden>More Games</h2><div class="grid" id="grid">{"".join(card(g) for g in sorted(GAMES, key=lambda g: g["name"].lower()))}</div></section>
{also}
</div>
<script>
/* Home rows. Without JavaScript (or before the counts load) every game shows A to Z in the grid.
   New This Week: up to 8 games added in the last 7 days, newest first. They skip the favorites rows that week,
   so brand-new games get a fair spotlight and older games compete on play counts.
   All-Time Favorites: most plays ever. Recent Favorites: most plays in the last 30 days, not already above.
   Our Picks: the site's picks list. Then one row per genre. More Games: anything left, A to Z. Each game appears once. */
(()=>{{
  const ROW_MAX=8,NEW_DAYS=7;let filter="all";
  const grid=document.getElementById("grid"),cards=new Map([...grid.children].map(c=>[c.dataset.slug,c]));
  const taken=new Set(),rows={{}};
  ["new","all","recent","picks"].forEach(k=>rows[k]=document.getElementById("row-"+k));
  const GENRES={json.dumps(genres)};GENRES.forEach(x=>rows["genre-"+x.toLowerCase()]=document.getElementById("row-genre-"+x.toLowerCase()));
  const PICKS={json.dumps(SITE.get("picks",[]))};
  const restHead=document.querySelector("#row-rest h2");
  function fill(k,slugs){{const strip=rows[k].querySelector(".strip");
    slugs.forEach(s=>{{taken.add(s);strip.appendChild(cards.get(s))}});
    if(slugs.length){{rows[k].dataset.on="1";rows[k].hidden=false}}}}
  const t=new Date(),today=new Date(t.getFullYear(),t.getMonth(),t.getDate());
  const age=s=>{{const [y,m,d]=(cards.get(s).dataset.added||"1970-01-01").split("-").map(Number);return (today-new Date(y,m-1,d))/864e5}};
  fill("new",[...cards.keys()].filter(s=>age(s)<NEW_DAYS).sort((a,b)=>age(a)-age(b)).slice(0,ROW_MAX));
  // the rest of the rows: Our Picks, then one row per genre (A to Z), each game once; filled now and again once the counts arrive
  function fillRest(){{
    fill("picks",PICKS.filter(s=>cards.has(s)&&!taken.has(s)));
    GENRES.forEach(x=>fill("genre-"+x.toLowerCase(),[...cards.keys()].filter(s=>!taken.has(s)&&cards.get(s).dataset.genre===x).sort((a,b)=>cards.get(a).title.localeCompare(cards.get(b).title))));
  }}
  fillRest();applyFilter();
  fetch("/api/rank").then(r=>r.ok?r.json():null).catch(()=>null).then(d=>{{
    if(!d)return;
    // favorites take their games back out of the picks and genre rows
    ["picks",...GENRES.map(x=>"genre-"+x.toLowerCase())].forEach(k=>{{const r=rows[k];r.querySelectorAll(".card").forEach(c=>{{taken.delete(c.dataset.slug);grid.appendChild(c)}});delete r.dataset.on;r.hidden=true}});
    const pick=list=>(list||[]).map(x=>x.slug).filter(s=>cards.has(s)&&!taken.has(s)).slice(0,ROW_MAX);
    fill("all",pick(d.allTime));fill("recent",pick(d.recent));fillRest();applyFilter();
  }});
  function applyFilter(){{
    cards.forEach(c=>{{c.hidden=!(filter==="all"||c.dataset.genre===filter)}});
    Object.values(rows).forEach(r=>{{if(r.dataset.on)r.hidden=!r.querySelector(".card:not([hidden])")}});
    restHead.hidden=!Object.values(rows).some(r=>r.dataset.on)||!grid.querySelector(".card:not([hidden])");
  }}
  document.querySelectorAll(".chip").forEach(b=>b.addEventListener("click",()=>{{
    filter=b.dataset.f;document.querySelectorAll(".chip").forEach(x=>x.setAttribute("aria-pressed",String(x===b)));applyFilter();
  }}));
}})();
</script>'''
    return page(f'{SITE["name"]}: free family-friendly games', SITE["description"], body, "games", full, canonical="", extra_head='<style>[hidden]{display:none!important}</style>\n')

def detail(g):
    others = [o for o in GAMES if o["slug"] != g["slug"]]
    if g.get("related"):  # optional: games to list first under "More games"
        first = [o for s in g["related"] for o in others if o["slug"] == s]
        others = first + [o for o in others if o not in first]
    ld = {"@context": "https://schema.org", "@type": "VideoGame", "name": g["name"], "description": g["lead"],
          "genre": g["genre"], "gamePlatform": ["Web browser", "Mobile web"], "playMode": "SinglePlayer",
          "applicationCategory": "Game", "operatingSystem": "Any", "isAccessibleForFree": True,
          "publisher": {"@type": "Organization", "name": SITE["owner"]}}
    li = lambda xs: "".join(f"<li>{E(x)}</li>" for x in xs)
    play = E(g["play_url"]) if g.get("play_url") else f'play/{g["slug"]}.html'
    ext = ' rel="noopener" data-count' if g.get("play_url") else ""
    controls = f'<section class="panel"><h2>Controls</h2><ul>{li(g["controls"])}</ul></section>' if g.get("controls") else ""
    about = f'<section class="panel about"><h2>About {E(g["name"])}</h2>{"".join(f"<p>{E(x)}</p>" for x in g["about"])}</section>' if g.get("about") else ""
    body = f'''<div class="wrap">
<div class="crumbs"><a href="index.html">All games</a> / {E(g["genre"])}</div>
<div class="hero">
  <div class="cover"><img src="img/{g["slug"]}.jpg" alt="{E(g["name"])} gameplay" width="640" height="640"><a class="btn" href="{play}"{ext}>Play now</a></div>
  <div class="info">
    <span class="tag {g["genre"].lower()}">{E(g["genre"])}</span>
    <h1>{E(g["name"])}</h1>
    <p class="lead">{E(g["lead"])}</p>
    <ul class="facts">{li(g["facts"])}</ul>
    <div><a class="btn" href="{play}"{ext}>Play {E(g["name"])}</a></div>
  </div>
</div>
<!-- Ad slot: paste an AdSense display unit here once the site is approved -->
<div class="cols">
  <section class="panel"><h2>How to play</h2><ol>{li(g["how"])}</ol></section>
  {controls}
  <section class="panel"><h2>{E(g.get("tips_title", "Tips"))}</h2><ul>{li(g["tips"])}</ul></section>
</div>
{about}
<section><h2 class="sec">More games</h2><div class="grid">{"".join(card(o) for o in others)}</div></section>
</div>
<script type="application/ld+json">{json.dumps(ld)}</script>
{count_js(g["slug"], False) if g.get("play_url") else ""}'''
    return page(g.get("title") or f'{g["name"]}: play free online | {SITE["name"]}', g["meta"], body, "games", canonical=g["slug"], share=game_share(g),
                extra_head=(f'<meta property="og:image" content="{SITE["url"].rstrip("/")}/img/{g["slug"]}.jpg">\n' if SITE.get("url") else ""))

def about():
    body = f'''<div class="wrap prose">
<h1>About {E(SITE["name"])}</h1>
<p>{E(SITE["name"])} is a small collection of free browser games made by {E(SITE["owner"])}, an independent studio. Every game is drawn to look like a page from a kid\'s sketchbook: pencil lines on paper, with a little coloured pencil where it counts. They are the sister games of our Beach Day Arcade, built to be quick to pick up and clean enough for the whole family.</p>
<h2>What you can expect</h2>
<ul><li>Games that run in your browser on a phone, tablet or computer, with nothing to install.</li>
<li>No accounts or sign-ups. Your progress and best scores are saved on your own device.</li>
<li>No violence, no mature content and no chat with strangers.</li>
<li>New games added regularly.</li></ul>
<h2>Contact</h2>
<p>{E(SITE["contact_text"])}</p>
</div>'''
    return page(f'About | {SITE["name"]}', f'About {SITE["name"]}, a collection of free, family-friendly browser games.', body, "about", canonical="about")

def privacy():
    body = f'''<div class="wrap prose">
<h1>Privacy policy</h1>
<p><strong>Last updated:</strong> {E(SITE["policy_date"])}</p>
<p>This policy explains what information {E(SITE["name"])} ("we") collects when you visit this site and play our games.</p>
<h2>Information stored on your device</h2>
<p>Our games save settings and progress, such as your best score, current level and sound preference, in your browser's local storage. This information stays on your device. We do not receive it, and you can clear it at any time by clearing your browser's site data.</p>
<h2>Accounts</h2>
<p>You do not need an account to play, and we do not ask for your name, email address or other personal details to use the games.</p>
<h2>Advertising and analytics</h2>
<p>We may show ads provided by Google AdSense or by game-platform partners to keep the games free. These providers may use cookies or similar technologies to serve and measure ads. Google's use of advertising cookies enables it and its partners to serve ads based on visits to this and other sites. You can manage personalized advertising at <a href="https://www.google.com/settings/ads" rel="noopener">google.com/settings/ads</a>, and you can learn how Google uses information at <a href="https://policies.google.com/technologies/partner-sites" rel="noopener">policies.google.com/technologies/partner-sites</a>. We may also use basic, aggregated analytics to understand which games people enjoy.</p>
<h2>Children</h2>
<p>Our games are made for general audiences, including families. We do not knowingly collect personal information from children under 13. If you believe a child has provided personal information to us, please contact us and we will delete it.</p>
<h2>Changes</h2>
<p>We may update this policy from time to time. The date at the top shows when it last changed.</p>
<h2>Contact</h2>
<p>{E(SITE["contact_text"])}</p>
</div>'''
    return page(f'Privacy policy | {SITE["name"]}', f'How {SITE["name"]} handles your information.', body, canonical="privacy")

LOGO_SVG = '<svg viewBox="0 0 40 40" aria-hidden="true" fill="none" stroke="#2e2e33" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 32l3-9L27 7l6 6-16 16z"/><path d="M11 23l6 6"/><path d="M27 7l6 6"/><path d="M8 32l9-3"/><path d="M24 10l6 6" stroke-width="1.6"/></svg>'
HOME_ICON = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 9.5V20h5v-5.5h3V20h5V9.5"/></svg>'
SHARE_ICON = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="M7.5 7.5 12 3l4.5 4.5"/><path d="M5 12v6.5A2.5 2.5 0 0 0 7.5 21h9a2.5 2.5 0 0 0 2.5-2.5V12"/></svg>'
SHARE_CSS = """<style>
.bda-sheet{position:fixed;inset:0;z-index:9999;display:flex;align-items:flex-end;justify-content:center;background:rgba(46,46,51,.45);padding:16px;font-family:"Patrick Hand","Comic Sans MS",cursive}
@media (min-width:600px){.bda-sheet{align-items:center}}
.bda-sheet[hidden]{display:none!important}
.bda-card{width:100%;max-width:380px;background:#f6f3ea;color:#2e2e33;border:2px solid #2e2e33;border-radius:255px 15px 225px 15px/15px 225px 15px 255px;padding:18px 16px 14px;box-shadow:4px 4px 0 #55555c}
.bda-card h2{margin:0 0 4px;font:400 1.3rem/1.2 "Gloria Hallelujah","Comic Sans MS",cursive;color:#2e2e33}
.bda-card .u{margin:0 0 12px;font-size:.9rem;color:#7a7a80;overflow-wrap:anywhere}
.bda-opts{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}
.bda-opts a,.bda-opts button{appearance:none;border:0;background:none;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:6px;color:#2e2e33;text-decoration:none;font:400 .85rem "Patrick Hand","Comic Sans MS",cursive;padding:4px 0;border-radius:12px}
.bda-opts i{display:grid;place-items:center;width:46px;height:46px;border-radius:50%;border:2px solid #2e2e33;font:800 1.05rem system-ui,sans-serif;font-style:normal;color:#fff}
.bda-opts a:focus-visible,.bda-opts button:focus-visible,.bda-x:focus-visible{outline:3px solid #2e2e33;outline-offset:2px}
.bda-x{appearance:none;border:2px solid #2e2e33;margin-top:12px;width:100%;padding:8px;border-radius:15px 255px 15px 225px/225px 15px 255px 15px;background:#f6f3ea;color:#2e2e33;font:400 1.05rem "Patrick Hand","Comic Sans MS",cursive;cursor:pointer}
.bda-toast{position:fixed;left:50%;bottom:28px;transform:translateX(-50%);z-index:10000;background:#2e2e33;color:#f6f3ea;font:400 1rem "Patrick Hand","Comic Sans MS",cursive;padding:10px 16px;border-radius:12px;box-shadow:0 8px 20px rgba(0,0,0,.3)}
.bda-toast[hidden]{display:none!important}
</style>"""
SHARE_JS = """<script>
(()=>{
  let sheet,toastEl,tt;
  const enc=encodeURIComponent;
  function toast(msg){if(!toastEl){toastEl=document.createElement('div');toastEl.className='bda-toast';toastEl.setAttribute('role','status');document.body.appendChild(toastEl)}
    toastEl.textContent=msg;toastEl.hidden=false;clearTimeout(tt);tt=setTimeout(()=>toastEl.hidden=true,2200)}
  async function copy(url){try{await navigator.clipboard.writeText(url);toast('Link copied')}catch(e){
    const ta=document.createElement('textarea');ta.value=url;ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();
    let ok=false;try{ok=document.execCommand('copy')}catch(_){}ta.remove();toast(ok?'Link copied':'Copy this link: '+url)}}
  function openSheet(d){
    if(!sheet){sheet=document.createElement('div');sheet.className='bda-sheet';sheet.hidden=true;sheet.setAttribute('role','dialog');sheet.setAttribute('aria-modal','true');sheet.setAttribute('aria-label','Share');
      sheet.addEventListener('click',e=>{if(e.target===sheet)sheet.hidden=true});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&sheet)sheet.hidden=true});document.body.appendChild(sheet)}
    const msg=d.text+' '+d.url;
    sheet.innerHTML='<div class="bda-card"><h2></h2><p class="u"></p><div class="bda-opts">'+
      '<button type="button" data-a="copy"><i style="background:#0fa3b8">&#128279;</i>Copy link</button>'+
      '<a href="https://www.facebook.com/sharer/sharer.php?u='+enc(d.url)+'" target="_blank" rel="noopener"><i style="background:#1877f2">f</i>Facebook</a>'+
      '<a href="https://twitter.com/intent/tweet?text='+enc(d.text)+'&url='+enc(d.url)+'" target="_blank" rel="noopener"><i style="background:#111">X</i>X</a>'+
      '<a href="https://wa.me/?text='+enc(msg)+'" target="_blank" rel="noopener"><i style="background:#25d366">W</i>WhatsApp</a>'+
      '<a href="mailto:?subject='+enc(d.title)+'&body='+enc(msg)+'"><i style="background:#ff6f59">@</i>Email</a>'+
      '</div><button type="button" class="bda-x">Close</button></div>';
    sheet.querySelector('h2').textContent='Share '+d.title;sheet.querySelector('.u').textContent=d.url;
    sheet.querySelector('[data-a=copy]').onclick=()=>{copy(d.url);sheet.hidden=true};
    sheet.querySelector('.bda-x').onclick=()=>sheet.hidden=true;
    sheet.hidden=false;sheet.querySelector('[data-a=copy]').focus();
  }
  async function share(el){
    const d={url:el.dataset.shareUrl,title:el.dataset.shareTitle,text:el.dataset.shareText};
    try{if(window.va)window.va('event',{name:'Share',data:{page:d.title}})}catch(e){}
    const touch=matchMedia('(pointer:coarse)').matches;
    if(navigator.share&&touch){try{await navigator.share({title:d.title,text:d.text,url:d.url});return}catch(e){if(e&&e.name==='AbortError')return}}
    openSheet(d);
  }
  document.addEventListener('click',e=>{const el=e.target.closest('[data-share-url]');if(el){e.preventDefault();share(el)}});
})();
</script>"""

SCORE_SHARE = """<style>
.bda-scorebtn{appearance:none;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;margin:12px auto 0;padding:9px 18px 9px 14px;border:2px solid #2e2e33;border-radius:255px 15px 225px 15px/15px 225px 15px 255px;font:400 1.15rem/1 "Patrick Hand","Comic Sans MS",cursive;
  background:#f3e6b0;color:#2e2e33;box-shadow:3px 3px 0 #55555c;position:relative;transition:transform .12s}
.bda-scorebtn:active{transform:translate(2px,2px);box-shadow:1px 1px 0 #55555c}
.bda-scorebtn svg{width:18px;height:18px;flex:none}
.bda-scorebtn:focus-visible{outline:3px solid #2e2e33;outline-offset:3px}
.bda-scorebtn.float{position:fixed;left:50%;bottom:max(18px,env(safe-area-inset-bottom));transform:translateX(-50%);z-index:9000;margin:0}
.bda-scorebtn.float:active{transform:translate(-50%,2px)}
.bda-sc{position:fixed;inset:0;z-index:10001;display:grid;place-items:center;padding:16px;background:rgba(46,46,51,.5);font-family:"Patrick Hand","Comic Sans MS",cursive;overflow:auto}
.bda-sc[hidden]{display:none!important}
.bda-sc .in{width:100%;max-width:400px;background:#f6f3ea;border:2px solid #2e2e33;border-radius:255px 15px 225px 15px/15px 225px 15px 255px;padding:14px;box-shadow:4px 4px 0 #55555c;text-align:center}
.bda-sc img{display:block;width:100%;height:auto;border:2px solid #2e2e33;border-radius:12px;background:#f6f3ea;aspect-ratio:1}
.bda-sc .row{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px}
.bda-sc .row button,.bda-sc .row a{appearance:none;border:2px solid #2e2e33;cursor:pointer;border-radius:15px 255px 15px 225px/225px 15px 255px 15px;padding:9px 6px;font:400 1rem "Patrick Hand","Comic Sans MS",cursive;text-decoration:none;display:flex;align-items:center;justify-content:center;color:#2e2e33;background:#f6f3ea}
.bda-sc .go{background:#f3e6b0;box-shadow:2px 2px 0 #55555c}
.bda-sc .alt{background:#f6f3ea}
.bda-sc .x{appearance:none;border:0;margin-top:10px;width:100%;padding:9px;background:none;color:#7a7a80;font:400 1rem "Patrick Hand","Comic Sans MS",cursive;cursor:pointer}
.bda-sc button:focus-visible,.bda-sc a:focus-visible{outline:3px solid #2e2e33;outline-offset:2px}
</style>
<script>
/* Share-my-score card. A game calls BDA.shareScore({score, line, into, after, lead}) when a game ends:
   score = the number to brag about, line = optional extra like "Level 5" or "Advanced",
   into = the game-over card (element or selector) to put the button in, after = where in it; without into the button floats.
   lead replaces "I scored" (e.g. "I reached" with score "Level 12"). */
(()=>{
  const G=window.BDA_GAME||{},nf=n=>typeof n==='number'?n.toLocaleString('en-US'):String(n);
  const ICON='<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="M7.5 7.5 12 3l4.5 4.5"/><path d="M5 12v6.5A2.5 2.5 0 0 0 7.5 21h9a2.5 2.5 0 0 0 2.5-2.5V12"/></svg>';
  let floatBtn=null,sheet=null,cur=null;
  const load=src=>new Promise(r=>{const i=new Image();i.onload=()=>r(i);i.onerror=()=>r(null);i.src=src});
  function rr(c,x,y,w,h,r){c.beginPath();c.moveTo(x+r,y);c.arcTo(x+w,y,x+w,y+h,r);c.arcTo(x+w,y+h,x,y+h,r);c.arcTo(x,y+h,x,y,r);c.arcTo(x,y,x+w,y,r);c.closePath()}
  function fitText(c,t,max,size,weight,fam){let s=size;do{c.font=weight+' '+s+'px '+fam;s-=2}while(c.measureText(t).width>max&&s>18);return c.font}
  async function makeCard(d){
    const F='"Gloria Hallelujah","Comic Sans MS",cursive',F2='"Patrick Hand","Comic Sans MS",cursive',INK='#2e2e33',PAPER='#f6f3ea';
    try{await Promise.all([document.fonts.load('120px "Gloria Hallelujah"'),document.fonts.load('40px "Patrick Hand"')])}catch(e){}
    const cover=await load('../img/'+G.slug+'.jpg');
    const S=1080,cv=document.createElement('canvas');cv.width=cv.height=S;const c=cv.getContext('2d');
    c.fillStyle=PAPER;c.fillRect(0,0,S,S);
    // faint pencil grain and a doodled frame
    c.fillStyle='rgba(46,46,51,.035)';for(let i=0;i<1400;i++){const x=(i*197)%S,y=(i*331+i*i)%S;c.fillRect(x,y,2,2)}
    c.strokeStyle=INK;c.lineWidth=5;c.lineJoin='round';c.beginPath();for(let i=0;i<=80;i++){const t=i/80,p=t*4,k=Math.floor(p),f=p-k,w=12*Math.sin(i*1.7);
      const pts=[[40,40],[S-40,40],[S-40,S-40],[40,S-40],[40,40]];const a=pts[k],b=pts[k+1]||pts[4];c.lineTo(a[0]+(b[0]-a[0])*f+(k%2?w:0),a[1]+(b[1]-a[1])*f+(k%2?0:w))}c.stroke();
    // site name, hand lettered
    c.textAlign='center';c.textBaseline='alphabetic';c.fillStyle=INK;c.font='62px '+F;c.fillText((G.site||'Sketchpad Arcade').toUpperCase(),S/2,120);
    // cover art in a pencil frame
    const cs=470,cx=(S-cs)/2,cy=162;
    c.save();rr(c,cx,cy,cs,cs,26);c.clip();if(cover)c.drawImage(cover,cx,cy,cs,cs);c.restore();
    c.lineWidth=6;c.strokeStyle=INK;rr(c,cx,cy,cs,cs,26);c.stroke();
    // "I scored" + the big number
    c.font='54px '+F2;c.fillStyle='#55555c';c.fillText(d.lead||'I scored',S/2,712);
    const big=nf(d.score);fitText(c,big,S-120,150,400,F);
    c.fillStyle=INK;c.fillText(big,S/2,852);
    c.lineWidth=4;c.strokeStyle='#c99a1a';c.beginPath();c.moveTo(S/2-c.measureText(big).width/2-10,872);c.quadraticCurveTo(S/2,886,S/2+c.measureText(big).width/2+10,870);c.stroke();
    const line=(d.line?d.line+' · ':'')+'in '+(G.name||'');
    fitText(c,line,S-140,46,400,F2);c.fillStyle=INK;c.fillText(line,S/2,930);
    // challenge + link, in a wobbly box
    const pill='Can you beat me? '+(G.short||'sketchpadarcade.com');fitText(c,pill,S-200,38,400,F2);
    const pw=c.measureText(pill).width+72,ph=72,px=(S-pw)/2,py=962;
    c.fillStyle='#f3e6b0';rr(c,px,py,pw,ph,30);c.fill();c.lineWidth=4;c.strokeStyle=INK;c.stroke();
    c.fillStyle=INK;c.fillText(pill,S/2,py+49);
    return new Promise(r=>cv.toBlob(b=>r(b),'image/png'));
  }
  function message(d){return (d.lead||'I scored')+' '+nf(d.score)+(d.line?' ('+d.line+')':'')+' in '+G.name+' on '+(G.site||'Sketchpad Arcade')+'! Can you beat me?'}
  async function open(d){
    try{if(window.va)window.va('event',{name:'Share score',data:{game:G.slug}})}catch(e){}
    if(!sheet){sheet=document.createElement('div');sheet.className='bda-sc';sheet.hidden=true;sheet.setAttribute('role','dialog');sheet.setAttribute('aria-modal','true');sheet.setAttribute('aria-label','Share your score');
      sheet.addEventListener('click',e=>{if(e.target===sheet)close()});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&sheet&&!sheet.hidden)close()});document.body.appendChild(sheet)}
    sheet.innerHTML='<div class="in"><img alt="Your score card"><div class="row"><button type="button" class="go" data-a="share">Share</button><a class="alt" data-a="save" download>Save image</a><button type="button" class="alt" data-a="copy">Copy link</button></div><button type="button" class="x">Close</button></div>';
    sheet.hidden=false;
    const blob=await makeCard(d);const url=URL.createObjectURL(blob);
    const img=sheet.querySelector('img');img.src=url;img.alt='Score card: '+message(d);
    const file=new File([blob],(G.slug||'score')+'-score.png',{type:'image/png'});
    const save=sheet.querySelector('[data-a=save]');save.href=url;save.download=file.name;
    const text=message(d);
    sheet.querySelector('[data-a=share]').onclick=async()=>{
      try{if(navigator.canShare&&navigator.canShare({files:[file]})){await navigator.share({files:[file],title:G.name,text:text+' '+G.url});return}
        if(navigator.share){await navigator.share({title:G.name,text,url:G.url});return}}catch(e){if(e&&e.name==='AbortError')return}
      copyText(text+' '+G.url,'Message and link copied')};
    sheet.querySelector('[data-a=copy]').onclick=()=>copyText(G.url,'Link copied');
    sheet.querySelector('.x').onclick=close;
    sheet.querySelector('[data-a=share]').focus();
  }
  function close(){if(sheet)sheet.hidden=true}
  async function copyText(t,msg){let ok=false;try{await navigator.clipboard.writeText(t);ok=true}catch(e){const ta=document.createElement('textarea');ta.value=t;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{ok=document.execCommand('copy')}catch(_){}ta.remove()}
    const b=sheet&&sheet.querySelector('[data-a=copy]');if(b){const o=b.textContent;b.textContent=ok?'Copied!':'Copy failed';setTimeout(()=>b.textContent=o,1500)}}
  function button(d){const b=document.createElement('button');b.type='button';b.className='bda-scorebtn';b.innerHTML=ICON+'<span>Share my score</span>';
    b.addEventListener('click',e=>{e.stopPropagation();open(d)});return b}
  window.BDA=window.BDA||{};
  window.BDA.shareScore=function(d){
    let host=d&&d.into;if(typeof host==='string')host=document.querySelector(host);
    if(host)host.querySelectorAll('.bda-scorebtn').forEach(x=>x.remove());
    if(!d||d.score==null||d.score===''||(typeof d.score==='number'&&!(d.score>0)))return;
    cur=d;
    if(host){const b=button(d);
      const after=d.after&&host.querySelector(d.after);if(after)after.insertAdjacentElement('afterend',b);else host.appendChild(b);return b}
    // no card given: a floating button that goes away on the next tap anywhere else
    if(floatBtn)floatBtn.remove();floatBtn=button(d);floatBtn.classList.add('float');document.body.appendChild(floatBtn);
    const fb=floatBtn;setTimeout(()=>document.addEventListener('pointerdown',function h(e){if(!fb.contains(e.target)&&!(sheet&&sheet.contains(e.target))){fb.remove();document.removeEventListener('pointerdown',h,true)}},true),400);
    return fb};
  window.BDA.hideScore=function(){if(floatBtn){floatBtn.remove();floatBtn=null}};
})();
</script>"""
FIT_TITLE_JS = """<script>
(()=>{const h=document.querySelector('.sa-head h1');if(!h)return;let base=0;
function fit(){h.style.fontSize='';base=parseFloat(getComputedStyle(h).fontSize);let fs=base;
  while(h.scrollWidth>h.clientWidth+1&&fs>14){fs-=1;h.style.fontSize=fs+'px'}}
fit();addEventListener('resize',fit);if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fit);})();
</script>"""

def count_js(slug, on_load):
    """Counts a play: once per game per browser per day, so refreshes don't inflate the ranking.
    on_load=True counts when the play page opens; False counts clicks on [data-count] links
    (for games hosted on their own domain, like Gull Run: Evo)."""
    fn = ("(()=>{const s=%s;function count(){if(window.name==='bda-reel')return;try{const k='bda-played-'+s,d=new Date().toISOString().slice(0,10);"
          "if(localStorage.getItem(k)===d)return;localStorage.setItem(k,d)}catch(e){}"
          "try{fetch('/api/play?game='+encodeURIComponent(s),{method:'POST',keepalive:true}).catch(()=>{})}catch(e){}}" % json.dumps(slug))
    fn += "count();" if on_load else "document.querySelectorAll('[data-count]').forEach(a=>a.addEventListener('click',count));"
    return "<script>" + fn + "})();</script>"

def share_attrs(url, title, text):
    return f'data-share-url="{E(url)}" data-share-title="{E(title)}" data-share-text="{E(text)}"'

def site_share():
    return share_attrs(SITE.get('url', '').rstrip('/') + '/', SITE['name'], f'{SITE["name"]}: free, family-friendly games drawn like a kid\'s sketchbook, right in your browser.')

def game_share(g):
    base = SITE.get("url", "").rstrip("/")
    return share_attrs(f'{base}/{g["slug"]}', g["name"], f'Play {g["name"]} free on {SITE["name"]}! {g["tagline"]}')

BACK_CSS = '<style>.sa-share{flex:none;display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;padding:0;border-radius:255px 15px 225px 15px/15px 225px 15px 255px;cursor:pointer;background:#f3e6b0;color:#2e2e33;border:2px solid #2e2e33;box-shadow:2px 2px 0 #55555c}.sa-share:active{transform:translate(2px,2px);box-shadow:none}.sa-share svg{width:18px;height:18px}.sa-share:focus-visible,.sa-back:focus-visible{outline:3px solid #2e2e33;outline-offset:2px}.sa-head{min-width:0}.sa-head h1{min-width:0;white-space:nowrap;overflow:hidden}.sa-back{flex:none;display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:15px 255px 15px 225px/225px 15px 255px 15px;border:2px solid #2e2e33;background:#f6f3ea;color:#2e2e33;font:400 22px/1 "Patrick Hand","Comic Sans MS",cursive;text-decoration:none;box-shadow:2px 2px 0 #55555c}.sa-head{display:flex;align-items:center;gap:8px;min-width:0}</style>'

def desktop_css(g):
    """Desktop only (mouse + wide window): the game becomes a full-height 9:16 stage in the middle of the screen,
    and the sides show the game's own cover art, softly blurred. Phones and tablets never match this, so mobile is untouched."""
    img = f'../img/{g["slug"]}.jpg'
    return ("<style>@media (hover:hover) and (pointer:fine) and (min-aspect-ratio:3/4) and (min-width:700px){"
        "html{background:#e9e5d8!important;height:100%;overflow:hidden}"
        f"html::before{{content:'';position:fixed;inset:-60px;z-index:-1;background:#e9e5d8 url({img}) center/cover no-repeat;filter:blur(30px) opacity(.5)}}"
        "body{width:min(100vw,calc(100vh*9/16));width:min(100vw,calc(100dvh*9/16));height:100vh;height:100dvh;margin:0 auto!important;position:relative;overflow:hidden;"
        "transform:translateZ(0);box-shadow:0 0 0 2px #2e2e33,8px 8px 0 #55555c}"
        "body>.app,body>.wrap,body>#app{max-width:none!important}"
        "}</style>")

def play_page(g):
    s = (ROOT / "src" / "games" / f'{g["slug"]}.html').read_text()
    s = s.replace("</head>", BACK_CSS + "\n" + SHARE_CSS + "\n" + desktop_css(g) + "\n" + ANALYTICS + "</head>", 1)
    s = re.sub(r"<h1([^>]*)>(.*?)</h1>", lambda m: f'<div class="sa-head"><a class="sa-back" href="../{g["slug"]}.html" aria-label="Back to {E(SITE["name"])}">&#8249;</a><h1{m.group(1)}>{m.group(2)}</h1><button class="sa-share" type="button" aria-label="Share {E(g["name"])}" {game_share(g)}>{SHARE_ICON}</button></div>', s, count=1)
    base = SITE.get("url", "https://www.sketchpadarcade.com").rstrip("/")
    host = re.sub(r"^https?://(www\.)?", "", base)
    game = json.dumps({"slug": g["slug"], "name": g["name"], "site": SITE["name"], "url": f'{base}/{g["slug"]}', "short": f'{host}/{g["slug"]}'})
    s = s.replace("</body>", f"<script>window.BDA_GAME={game};</script>\n" + count_js(g["slug"], True) + "\n" + SHARE_JS + "\n" + SCORE_SHARE + "\n" + FIT_TITLE_JS + "\n</body>", 1)
    s = s.replace("<title>", f'<meta name="robots" content="noindex">\n<title>', 1)
    return s

def build():
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT / "play").mkdir(parents=True); (OUT / "img").mkdir()
    shutil.copytree(ROOT / "src" / "brand", OUT / "brand")
    if (ROOT / "src" / "assets").exists():  # per-game art, served at /assets/<slug>/...
        shutil.copytree(ROOT / "src" / "assets", OUT / "assets")
    shutil.copy(ROOT / "src" / "brand" / "icon-32.png", OUT / "favicon.png")
    (OUT / "index.html").write_text(home())
    (OUT / "about.html").write_text(about())
    (OUT / "privacy.html").write_text(privacy())
    for g in GAMES:
        (OUT / f'{g["slug"]}.html').write_text(detail(g))
        if not g.get("play_url"):  # games hosted on their own domain link out instead
            (OUT / "play" / f'{g["slug"]}.html').write_text(play_page(g))
        shutil.copy(ROOT / "src" / "img" / f'{g["slug"]}.jpg', OUT / "img" / f'{g["slug"]}.jpg')
    (OUT / "vercel.json").write_text(json.dumps({"cleanUrls": True}, indent=2) + "\n")
    url = SITE.get("url", "").rstrip("/")
    if url:
        pages = ["", "about", "privacy"] + [g["slug"] for g in GAMES]
        (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
            "".join(f"  <url><loc>{url}/{p}</loc></url>\n" for p in pages) + "</urlset>\n")
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {url}/sitemap.xml\n")
    else:
        (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    # the play counter only accepts games that are on the site
    (ROOT / "api" / "_slugs.js").write_text("// Written by build.py. Games the play counter accepts.\nexport const SLUGS = " + json.dumps([g["slug"] for g in GAMES]) + ";\n")
    print("built", len(GAMES), "games into", OUT)

if __name__ == "__main__":
    build()
