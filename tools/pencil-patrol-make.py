#!/usr/bin/env python3
"""Makes src/games/pencil-patrol.html, the Sketchpad Arcade twin of Beach Day Arcade's Pearl Patrol.

Pearl Patrol is fully code-drawn (no image assets), so this script takes the original page and rewrites
the look and the words: Stubby the pencil scuttles across notebook pages collecting pencil dots while four
giggly erasers try to rub him out. Gameplay, sounds, save data and layout are untouched.

Usage: python3 tools/pencil-patrol-make.py <path to pearl-patrol.html>
"""
import re, sys
from pathlib import Path

SRC = Path(sys.argv[1]).read_text()
OUT = Path(__file__).resolve().parent.parent / "src/games/pencil-patrol.html"
s = SRC

def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, f"expected {count} of {old[:60]!r}, found {n}"
    s = s.replace(old, new)

def between(start, end, new):
    """Replace everything from `start` up to (not including) `end`."""
    global s
    a = s.index(start); b = s.index(end, a)
    s = s[:a] + new + s[b:]

# ---------------------------------------------------------------- head + CSS
rep('<title>Pearl Patrol</title>', '<title>Pencil Patrol</title>')
rep('family=Baloo+2:wght@700;800&family=Nunito:wght@600;800&display=swap', 'family=Gloria+Hallelujah&family=Patrick+Hand&display=swap')

CSS = r'''<style>
/* Pencil Patrol: the Sketchpad Arcade twin of Pearl Patrol. Layout: one portrait column. Title row, HUD card
   (level, score, best + pencils and dots bar), the notebook-page maze, then a dock with pause, the d-pad and sound.
   Everything is drawn in code: ink outlines with bright coloured-pencil hatching on cream paper. */
:root{
  --paper:#f6f3ea; --paper-2:#efeadd; --ink:#2e2e33; --pencil:#55555c; --muted:#7a7a80; --faint:#c9c6bc;
  --yellow:#c99a1a; --yellow-wash:#f3e6b0; --orange:#d9661a; --blue:#2f6fb5; --blue-wash:#d6e4f2;
  --green:#5a9a6a; --green-wash:#dcebdd; --purple:#6f4a9a; --purple-wash:#e6dcef; --pink:#c45a8a; --pink-wash:#f0d5e2;
  --display:"Gloria Hallelujah","Comic Sans MS","Chalkboard SE",cursive;
  --body:"Patrick Hand","Comic Sans MS","Chalkboard SE",cursive;
  --wob:255px 15px 225px 15px/15px 225px 15px 255px;
  --wob2:15px 255px 15px 225px/225px 15px 255px 15px;
  color-scheme:light;
}
html,body{height:100%;overflow:hidden;overscroll-behavior:none}
body{margin:0;font-family:var(--body);color:var(--ink);overflow:hidden;background-color:var(--paper);
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 .3 0 0 0 0 .3 0 0 0 0 .3 0 0 0 .07 0'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)'/%3E%3C/svg%3E");
  -webkit-tap-highlight-color:transparent;-webkit-user-select:none;user-select:none;touch-action:manipulation}
button{font-family:inherit;color:inherit;cursor:pointer}
.app{height:100%;max-width:520px;margin:0 auto;padding-inline:16px;padding-block:10px 12px;display:flex;flex-direction:column;gap:8px}
.top{display:flex;align-items:center;justify-content:space-between;gap:10px}
.brand{flex:1;min-width:0;font-family:var(--display);font-weight:400;font-size:clamp(1.05rem,6.2vw,1.6rem);line-height:1;margin:0;letter-spacing:.04em;text-transform:uppercase;white-space:nowrap;
  color:var(--ink);transform:rotate(-1.5deg);transform-origin:left center;overflow:hidden;text-overflow:ellipsis}
.iconbtn{appearance:none;border:2px solid var(--ink);background:var(--paper);color:var(--ink);font:400 1rem var(--body);min-height:44px;
  border-radius:var(--wob2);padding:8px 12px;box-shadow:2px 2px 0 var(--pencil);display:inline-flex;align-items:center;justify-content:center;gap:6px;white-space:nowrap;flex:none}
.iconbtn svg{width:18px;height:18px;flex:none}
.iconbtn:focus-visible,.gold:focus-visible,.alt:focus-visible,.pad button:focus-visible{outline:3px solid var(--blue);outline-offset:2px}
.iconbtn:active{transform:translate(2px,2px);box-shadow:none}
.iconbtn[aria-pressed="true"].tog{background:var(--yellow-wash)}
.hud{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:6px 12px;background:var(--paper);border:2px solid var(--ink);border-radius:var(--wob);padding:8px 14px 10px;box-shadow:3px 3px 0 var(--pencil)}
.stat{display:flex;flex-direction:column;gap:3px;min-width:0}
.stat small{font-size:.8rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-family:var(--body)}
.stat b{font-family:var(--display);font-weight:400;font-size:1.45rem;line-height:1;font-variant-numeric:tabular-nums}
.stat.mid{align-items:center}
.stat.mid b{font-size:1.7rem;color:var(--orange)}
.stat.end{align-items:flex-end}
.stat b.pop{animation:pop .25s}
@keyframes pop{50%{transform:scale(1.18)}}
.row2{grid-column:1/-1;display:flex;align-items:center;gap:10px}
.lives{display:flex;gap:2px;flex:none;min-width:70px}
.lives svg{width:22px;height:22px}
.lives svg.gone{opacity:.18;filter:grayscale(1)}
.lives svg.new{animation:pop .5s 2}
.prog{flex:1;position:relative;height:18px;border-radius:9px;background:var(--paper);border:2px solid var(--ink);overflow:hidden}
.prog i{position:absolute;left:0;top:0;bottom:0;width:0;transition:width .3s;
  background:repeating-linear-gradient(135deg,var(--yellow) 0 2px,var(--yellow-wash) 2px 6px)}
.prog span{position:relative;display:block;text-align:center;font:400 .85rem/14px var(--body);color:var(--ink);white-space:nowrap;text-shadow:0 0 3px var(--paper),0 0 2px var(--paper)}
.field{flex:1000 1 0;min-height:0;position:relative;border:2px solid var(--ink);border-radius:var(--wob);overflow:hidden;box-shadow:3px 3px 0 var(--pencil);background:var(--paper);touch-action:none}
#cv{display:block;width:100%;height:100%;touch-action:none}
.banner{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) scale(.8) rotate(-2deg);font:400 2.1rem/1.05 var(--display);color:var(--ink);text-shadow:0 0 6px var(--paper),0 0 12px var(--paper),2px 2px 0 var(--paper);
  opacity:0;transition:opacity .25s,transform .3s;pointer-events:none;white-space:nowrap;text-align:center;z-index:2}
.banner.show{opacity:1;transform:translate(-50%,-50%) scale(1) rotate(-2deg)}
.banner small{display:block;font:400 1.05rem/1.25 var(--body);margin-top:6px;white-space:normal;width:min(300px,80vw);margin-inline:auto}
.dock{flex:1 0 auto;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;--pw:56px;--ph:48px}
.dock.nopad{display:flex;justify-content:space-between}
.dock .side{display:flex;gap:8px}
.dock .side.r{justify-content:flex-end}
.dock:not(.nopad) .side.r{flex-direction:column;align-items:flex-end}
.dock:not(.nopad) .side.r .iconbtn{width:48px}
.pad{display:grid;grid-template-columns:repeat(3,var(--pw));grid-template-rows:repeat(2,var(--ph));gap:6px}
.pad button{appearance:none;border:2px solid var(--ink);border-radius:var(--wob2);background:var(--paper);box-shadow:3px 3px 0 var(--pencil);display:grid;place-items:center;color:var(--ink);touch-action:none;padding:0}
.pad button svg{width:24px;height:24px}
.pad button.on,.pad button:active{transform:translate(2px,2px);box-shadow:1px 1px 0 var(--pencil);background:var(--yellow-wash)}
.pad .u{grid-column:2;grid-row:1}.pad .l{grid-column:1;grid-row:2}.pad .d{grid-column:2;grid-row:2}.pad .r{grid-column:3;grid-row:2}
.overlay{position:fixed;inset:0;background:rgba(246,243,234,.55);display:grid;place-items:center;padding:16px;z-index:10;overflow:auto}
.card{position:relative;overflow:hidden;background:var(--paper);border:2px solid var(--ink);border-radius:var(--wob);padding:18px 18px 16px;width:100%;max-width:370px;text-align:center;box-shadow:4px 4px 0 var(--pencil);
  max-height:calc(100% - 8px);overflow-y:auto;animation:rise .35s cubic-bezier(.2,1.4,.4,1)}
.card>*{position:relative}
@keyframes rise{from{transform:translateY(24px) scale(.94);opacity:0}}
.card h2{font:400 2.1rem/1.05 var(--display);margin:0;color:var(--ink);text-transform:uppercase;letter-spacing:.03em;transform:rotate(-1.5deg);text-wrap:balance}
.card p{margin:6px 0 0;color:var(--muted);line-height:1.4;font-size:1.05rem}
#mini{width:240px;height:96px;display:block;margin:0 auto 2px}
.rules{list-style:none;padding:0;margin:10px 0 0;display:grid;gap:6px;text-align:left;font-size:1rem;color:var(--ink);line-height:1.3}
.rules li{display:grid;grid-template-columns:22px 1fr;gap:8px;align-items:start}
.rules b{display:grid;place-items:center;width:22px;height:22px;border-radius:var(--wob2);background:var(--paper);border:2px solid var(--ink);color:var(--ink);font:400 .85rem var(--display)}
.rules u{text-decoration:underline wavy var(--purple);color:var(--purple)}
.jl{display:flex;justify-content:center;gap:6px;flex-wrap:wrap;margin-top:8px}
.jl span{display:inline-flex;align-items:center;gap:5px;background:var(--paper);border:1.5px solid var(--ink);border-radius:var(--wob2);padding:3px 9px 3px 5px;font:400 .85rem/1.2 var(--body);color:var(--ink)}
.jl i{width:14px;height:11px;border-radius:3px;flex:none;border:1.5px solid var(--ink);background-image:repeating-linear-gradient(135deg,var(--c) 0 1.5px,transparent 1.5px 4px);background-color:var(--w)}
.big{font:400 3rem/1 var(--display);color:var(--ink);margin:6px 0 0;font-variant-numeric:tabular-nums}
.newbest{display:inline-block;background:var(--yellow-wash);border:2px solid var(--ink);border-radius:var(--wob2);color:var(--ink);font-size:.9rem;padding:3px 10px;margin-bottom:6px;transform:rotate(-2deg)}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0 0}
.stats div{background:var(--paper);border:2px dashed var(--faint);border-radius:var(--wob);padding:8px 4px}
.stats b{display:block;font:400 1.35rem/1.1 var(--display);color:var(--ink);font-variant-numeric:tabular-nums}
.stats span{font-size:.85rem;color:var(--muted)}
.gold{position:relative;appearance:none;border:2px solid var(--ink);width:100%;margin-top:14px;border-radius:var(--wob2);padding:12px 18px;min-height:56px;font:400 2rem/1 var(--display);letter-spacing:.05em;text-transform:uppercase;color:var(--ink);
  background:var(--yellow-wash);box-shadow:4px 4px 0 var(--pencil);transition:transform .1s}
.gold:active{transform:translate(3px,3px);box-shadow:1px 1px 0 var(--pencil)}
.gold.sm{font-size:1.45rem}
.bestline{margin-top:10px;font-size:1rem;color:var(--muted)}
.keys{margin-top:8px;font-size:.9rem;color:var(--muted);line-height:1.35}
.keys kbd{display:inline-block;min-width:22px;padding:1px 5px;border-radius:5px;background:var(--paper);border:1.5px solid var(--ink);box-shadow:1px 1px 0 var(--pencil);font:400 .85rem var(--body);color:var(--ink)}
@media (pointer:coarse){.keys{display:none}}
@media (prefers-reduced-motion:reduce){.card{animation:none}.banner{transition:none}}
@media (max-height:740px){.hud{padding:6px 12px 8px}.stat b{font-size:1.25rem}.stat.mid b{font-size:1.45rem}}
@media (max-height:700px){#mini{height:76px;width:190px}.rules{font-size:.9rem;gap:4px}.card h2{font-size:1.8rem}.gold{min-height:50px;font-size:1.6rem;padding:9px}}
@media (max-width:370px){.iconbtn{font-size:.9rem;padding:8px 9px}}
</style>
'''
between('<style>\n/* Layout: one portrait column.', '</head>', CSS)

# ---------------------------------------------------------------- HTML
rep('<h1 class="brand">Pearl Patrol</h1>', '<h1 class="brand">Pencil Patrol</h1>')
rep('aria-label="Shells left"', 'aria-label="Pencils left"')
rep('<span id="progTxt">0 pearls left</span>', '<span id="progTxt">0 dots left</span>')
rep('aria-label="A coral reef maze seen from above. Guide Shelly the hermit crab to collect every pearl while the jellyfish drift around."',
    'aria-label="A maze drawn on a notebook page. Guide Stubby the pencil to collect every dot while the erasers wander around."')

# ---------------------------------------------------------------- script: words, colours, data
rep("const KEY='bda-pearl-patrol-';", "const KEY='spa-pencil-patrol-';\nconst PAPER='#f6f3ea',INK='#2e2e33',GRAPH='#55555c',PENCIL='rgba(46,46,51,.55)';\nconst C={yellow:'#e0b020',yellowW:'#f6e7a8',orange:'#e8742a',orangeW:'#f5cfae',blue:'#3a7fd0',blueW:'#d4e3f5',green:'#5fae72',greenW:'#dcefdf',purple:'#7a4fb0',purpleW:'#e6daf2',pink:'#e06aa0',pinkW:'#f6d6e5',red:'#d8473c',redW:'#f3c9c4',teal:'#3d9aa8',tealW:'#d2ecef',brown:'#a06a3a',brownW:'#e8d2bd'};")
rep("/* ---------- the reefs: left halves, mirrored into 19 x 21 mazes ---------- */", "/* ---------- the pages: left halves, mirrored into 19 x 21 mazes ---------- */")
between("const THEMES=[", "const SPAWN=", """const THEMES=[
  {name:'Blue Pencil Page',wall:C.blue,lt:C.blueW,fill:'#eaf0f8'},
  {name:'Green Crayon Page',wall:C.green,lt:C.greenW,fill:'#eaf3ec'},
  {name:'Orange Marker Page',wall:C.orange,lt:C.orangeW,fill:'#f8ede3'},
  {name:'Purple Pencil Page',wall:C.purple,lt:C.purpleW,fill:'#f0eaf6'}];
""")
rep("// cells: 0 open, 1 pearl, 2 starfish, 3 wall, 4 door, 5 nest", "// cells: 0 open, 1 dot, 2 gold star, 3 wall, 4 door, 5 pencil case")
rep("const TREATS=[{k:'coconut',n:'Coconut',p:100},{k:'icepop',n:'Ice pop',p:300},{k:'melon',n:'Watermelon',p:500},{k:'coconut',n:'Coconut',p:700},{k:'icepop',n:'Ice pop',p:1000},{k:'melon',n:'Watermelon',p:2000}];",
    "const TREATS=[{k:'apple',n:'Apple',p:100},{k:'glue',n:'Glue stick',p:300},{k:'crayon',n:'Crayon',p:500},{k:'apple',n:'Apple',p:700},{k:'glue',n:'Glue stick',p:1000},{k:'crayon',n:'Crayon',p:2000}];")
between("const JDEF=[", "function resetActors(){", """const JDEF=[
  {name:'Pinky',col:C.pink,wash:C.pinkW,corner:[W-2,-3],kind:'chase'},
  {name:'Smudge',col:C.purple,wash:C.purpleW,corner:[1,-3],kind:'ambush'},
  {name:'Zigzag',col:C.green,wash:C.greenW,corner:[W-1,H+1],kind:'zig'},
  {name:'Dozer',col:C.orange,wash:C.orangeW,corner:[0,H+1],kind:'shy'}];

""")
rep("J=JDEF.map((d,i)=>({i,name:d.name,col:d.col,corner:d.corner,", "J=JDEF.map((d,i)=>({i,name:d.name,col:d.col,wash:d.wash,corner:d.corner,")
rep("const J_SPEED=L=>", "const J_SPEED=L=>")  # untouched; sanity
rep("// eat whatever is under Shelly's middle", "// eat whatever is under Stubby's middle")
# particles: no white on paper
rep("col:k%2?'#fff6d0':'#ffffff',spark:true})}}", "col:k%2?C.yellow:GRAPH,spark:true})}}")
rep("col:k%2?'#ffd34d':'#fff3b0',spark:true})}", "col:k%2?C.yellow:C.orange,spark:true})}")
rep("col:k%2?'#ffffff':'#ffe27a',star:true,g:60})}", "col:k%2?C.yellow:C.pink,star:true,g:60})}")
rep("col:['#ff7aa8','#ffe27a','#7ee0ff'][k%3],spark:true})}", "col:[C.pink,C.yellow,C.blue][k%3],spark:true})}")
rep("col:['#ff6f91','#ffe27a','#7ee0ff','#b47cff','#3fd96b'][k%5],g:300,conf:true,rot:Math.random()*6})}", "col:[C.pink,C.yellow,C.blue,C.purple,C.green][k%5],g:300,conf:true,rot:Math.random()*6})}")
rep("banner('Extra shell!','',1200)", "banner('Extra pencil!','',1200)")
rep("banner('Reef cleared!','',1800)", "banner('Page cleared!','',1800)")
rep("// Bloop hurries near the end", "// Pinky hurries near the end")
# no bubbles drifting (nothing is under water any more)
rep("bubbles=[];for(let k=0;k<(RM?5:14);k++)bubbles.push({x:rnd(0,cw),y:rnd(0,ch),r:rnd(1.5,4.5),sp:rnd(10,26),w:rnd(0,6)});", "bubbles=[];")

# ---------------------------------------------------------------- the maze picture
between("function buildMaze(){", "/* ---------- drawing: characters ---------- */", r"""function buildMaze(){
  if(!grid||cs<2)return;
  const mw=W*cs,mh=H*cs,th=theme;
  // the page: cream paper with a faint pencil dot in some open cells
  let g;[floorC,g]=mk(cw,ch);
  g.fillStyle=PAPER;g.fillRect(0,0,cw,ch);
  for(let y=0;y<H;y++)for(let x=0;x<W;x++){const c=grid[y*W+x];if(c===3||c===5||c===4)continue;const h=hash(x+maze*7,y);
    if(h<.08){const px=ox+(x+.2+h*4)*cs,py=oy+(y+.85)*cs;g.strokeStyle=PENCIL;g.lineWidth=1;g.beginPath();g.moveTo(px-cs*.12,py);g.lineTo(px+cs*.12,py-cs*.04);g.stroke()}}
  // the maze walls: coloured-pencil hatching inside a wobbly ink outline, with a pencil shadow
  let w;[wallC,w]=mk(mw,mh);
  const ol=Math.max(1.5,cs*.09); // the outline is a grown ink fill under the body, so overlapping cells still make one clean edge
  w.fillStyle='rgba(46,46,51,.2)';wallPath(w,ol,cs*.12);w.fill();
  w.fillStyle=INK;wallPath(w,ol,0);w.fill();
  w.fillStyle=th.fill;wallPath(w,0,0);w.fill();
  w.save();wallPath(w,0,0);w.clip();w.strokeStyle=th.wall;w.globalAlpha=.8;w.lineWidth=1.3;w.beginPath();
  const gap=Math.max(5,cs*.34),cA=Math.cos(-.7),sA=Math.sin(-.7),L=mw+mh;
  for(let d=-L;d<=L;d+=gap){w.moveTo(mw/2-cA*L-sA*d,mh/2-sA*L+cA*d);w.lineTo(mw/2+cA*L-sA*d,mh/2+sA*L+cA*d)}w.stroke();
  w.globalAlpha=.5;w.lineWidth=1;w.beginPath();const cB=Math.cos(.75),sB=Math.sin(.75);
  for(let d=-L;d<=L;d+=gap*1.6){w.moveTo(mw/2-cB*L-sB*d,mh/2-sB*L+cB*d);w.lineTo(mw/2+cB*L-sB*d,mh/2+sB*L+cB*d)}w.stroke();
  w.globalAlpha=1;w.restore();
  // the pencil case the erasers live in: a tin box with a lid line and a little latch
  const nx=7.5*cs,ny=8.5*cs,nw=4*cs,nh=2*cs;
  w.fillStyle=C.yellowW;rrect(w,nx-cs*.1,ny+cs*.05,nw+cs*.2,nh+cs*.5,cs*.3);w.fill();
  w.save();rrect(w,nx-cs*.1,ny+cs*.05,nw+cs*.2,nh+cs*.5,cs*.3);w.clip();w.strokeStyle=C.yellow;w.globalAlpha=.7;w.lineWidth=1.2;w.beginPath();
  for(let d=-nh*2;d<=nw+nh;d+=Math.max(4,cs*.3)){w.moveTo(nx+d,ny-cs*.2);w.lineTo(nx+d+nh*1.4,ny+nh+cs*.8)}w.stroke();w.restore();
  w.strokeStyle=INK;w.lineWidth=Math.max(1.5,cs*.08);rrect(w,nx-cs*.1,ny+cs*.05,nw+cs*.2,nh+cs*.5,cs*.3);w.stroke();
  w.lineWidth=Math.max(1,cs*.05);w.beginPath();w.moveTo(nx-cs*.1,ny+cs*.55);w.lineTo(nx+nw+cs*.1,ny+cs*.55);w.stroke();
  w.fillStyle=PAPER;rrect(w,nx+nw/2-cs*.25,ny+cs*.38,cs*.5,cs*.34,cs*.08);w.fill();w.stroke();
  const dx0=8.6*cs,dy0=8.5*cs;w.fillStyle=C.pinkW;rrect(w,dx0,dy0-cs*.1,cs*.8,cs*.22,cs*.06);w.fill();w.strokeStyle=C.pink;w.lineWidth=Math.max(1,cs*.05);w.setLineDash([cs*.12,cs*.1]);w.stroke();w.setLineDash([]);
  // flash copy for level clear
  let f;[wallFlashC,f]=mk(mw,mh);f.drawImage(wallC,0,0,mw,mh);f.globalCompositeOperation='source-atop';f.fillStyle='rgba(246,243,234,.7)';f.fillRect(0,0,mw,mh);
  // dot sprite: a little pencil dot with a tiny shine gap
  const ps=Math.max(4,cs*.62);let p;[pearlSpr,p]=mk(ps*2,ps*2);
  const pr=cs*.13;p.fillStyle=INK;p.beginPath();p.arc(ps,ps,pr,0,7);p.fill();
  p.strokeStyle=GRAPH;p.lineWidth=Math.max(1,pr*.5);p.globalAlpha=.6;p.beginPath();p.arc(ps,ps,pr*1.25,-2.2,-.6);p.stroke();
}

""")

# ---------------------------------------------------------------- characters
between("/* ---------- drawing: characters ---------- */", "/* ---------- drawing: the scene ---------- */", r"""/* ---------- drawing helpers: ink outlines, coloured-pencil hatching ---------- */
function hatch(g,pathFn,line,wash,gap=5,ang=-.7,alpha=.85){g.save();g.beginPath();pathFn(g);g.clip();
  g.fillStyle=wash;g.fillRect(-400,-400,800,800);
  g.strokeStyle=line;g.globalAlpha=alpha;g.lineWidth=1.2;g.beginPath();const c=Math.cos(ang),s=Math.sin(ang);
  for(let d=-200;d<=200;d+=gap){g.moveTo(-c*240-s*d,-s*240+c*d);g.lineTo(c*240-s*d,s*240+c*d)}g.stroke();g.restore()}
function outline(g,pathFn,w=2){g.beginPath();pathFn(g);g.strokeStyle=INK;g.lineWidth=w;g.lineJoin='round';g.lineCap='round';g.stroke()}
function cRect(g,x,y,w,h,r){rrect(g,x-w/2,y-h/2,w,h,r)}

/* ---------- drawing: characters ---------- */
function eye(g,x,y,r,lx,ly,o){
  o=o||{};
  if(o.happy){g.strokeStyle=INK;g.lineWidth=Math.max(1,r*.38);g.lineCap='round';g.beginPath();g.arc(x,y+r*.25,r*.6,Math.PI+.35,-.35);g.stroke();return}
  g.fillStyle=PAPER;g.beginPath();g.arc(x,y,r,0,7);g.fill();g.strokeStyle=INK;g.lineWidth=Math.max(.9,r*.18);g.stroke();
  const pr=r*(o.small?.32:.55),m=r-pr-r*.08;
  g.fillStyle=INK;g.beginPath();g.arc(x+lx*m,y+ly*m,pr,0,7);g.fill();
  g.fillStyle=PAPER;g.beginPath();g.arc(x+lx*m-pr*.35,y+ly*m-pr*.4,pr*.3,0,7);g.fill();
}
/* Stubby: a short yellow No. 2 pencil scuttling on three little legs, point first */
function drawShelly(g,x,y,r,face,lx,ly,ph,o){
  o=o||{};g.save();g.translate(x,y);if(o.rot)g.rotate(o.rot);if(o.scale)g.scale(o.scale,o.scale);g.scale(1.25,1.25);
  g.fillStyle='rgba(46,46,51,.18)';g.beginPath();g.ellipse(0,r*.78,r*.95,r*.26,0,0,7);g.fill();
  const bob=o.still?0:Math.abs(Math.sin(ph))*r*.08;g.translate(0,-bob);
  g.scale(face,1);g.lineJoin='round';g.lineCap='round';
  const ol=Math.max(1.3,r*.1),bh=r*.62,bw=r*1.1,x0=-r*.75; // body: from x0 to x0+bw, tip beyond
  // little legs
  g.strokeStyle=INK;g.lineWidth=Math.max(1.2,r*.1);g.beginPath();
  for(let k=0;k<3;k++){const lx0=x0+r*.18+k*r*.38,sw=o.still?0:Math.sin(ph*2+k*1.7)*r*.12;g.moveTo(lx0,r*.3);g.lineTo(lx0+r*.08+sw,r*.68);g.lineTo(lx0+r*.22+sw,r*.68)}g.stroke();
  // eraser (back), ferrule, body, wood tip, graphite point
  const chomp=o.still?0:Math.max(o.chomp||0,0);
  hatch(g,c=>cRect(c,x0+r*.12,r*.02,r*.26,bh*.9,r*.06),C.pink,C.pinkW,3.5,-.8);outline(g,c=>cRect(c,x0+r*.12,r*.02,r*.26,bh*.9,r*.06),ol);
  hatch(g,c=>cRect(c,x0+r*.3,r*.02,r*.14,bh,r*.03),GRAPH,'#e8e6df',3,-.8,.5);outline(g,c=>cRect(c,x0+r*.3,r*.02,r*.14,bh,r*.03),ol);
  const body=c=>{c.rect(x0+r*.37,r*.02-bh/2,bw-r*.37,bh)};
  hatch(g,body,C.yellow,C.yellowW,Math.max(3,r*.16),-.8);outline(g,body,ol);
  g.strokeStyle=INK;g.lineWidth=Math.max(.8,r*.05);g.beginPath();g.moveTo(x0+r*.37,r*.02-bh*.17);g.lineTo(x0+bw,r*.02-bh*.17);g.moveTo(x0+r*.37,r*.02+bh*.17);g.lineTo(x0+bw,r*.02+bh*.17);g.stroke();
  const tipL=r*.55*(1-chomp*.25),tx=x0+bw;
  const wood=c=>{c.moveTo(tx,r*.02-bh/2);c.lineTo(tx+tipL,r*.02);c.lineTo(tx,r*.02+bh/2);c.closePath()};
  hatch(g,wood,C.brown,C.brownW,3,.9,.6);outline(g,wood,ol);
  g.fillStyle=INK;g.beginPath();g.moveTo(tx+tipL*.62,r*.02-bh*.19);g.lineTo(tx+tipL+r*.02,r*.02);g.lineTo(tx+tipL*.62,r*.02+bh*.19);g.closePath();g.fill();
  // eyes on the body (un-flip so pupils look the right way)
  g.scale(face,1);
  const e1x=face*(x0+r*.62),e2x=face*(x0+r*.98),ey0=-r*.1,er=r*.17;
  if(o.dizzy){for(const ex0 of [e1x,e2x]){g.strokeStyle=INK;g.lineWidth=Math.max(1,r*.07);g.fillStyle=PAPER;g.beginPath();g.arc(ex0,ey0,er,0,7);g.fill();g.stroke();
      g.beginPath();for(let t=0;t<=1;t+=.1){const a=t*9+ph*3,rr=er*.8*t;g.lineTo(ex0+Math.cos(a)*rr,ey0+Math.sin(a)*rr)}g.stroke()}}
  else{eye(g,e1x,ey0,er,lx,ly);eye(g,e2x,ey0,er,lx,ly)}
  g.scale(face,1);
  // smile + blush
  g.fillStyle='rgba(224,106,160,.45)';g.beginPath();g.ellipse(x0+r*1.08,r*.16,r*.09,r*.05,0,0,7);g.fill();
  g.strokeStyle=INK;g.lineWidth=Math.max(1,r*.07);g.beginPath();
  if(o.dizzy){g.ellipse(x0+r*.8,r*.18,r*.07,r*.09,0,0,7)}else g.arc(x0+r*.8,r*.1,r*.11+chomp*r*.05,.3,Math.PI-.3);g.stroke();
  g.restore();
}
/* an eraser: a tilted block with crumbs trailing below; goes pale and wobbly when frightened */
function drawJelly(g,x,y,r,col,lx,ly,ph,o){
  o=o||{};g.save();g.translate(x,y);
  const fr=o.fr,flash=o.flash,home=o.home,j=o.j;
  const line=fr?(flash?C.pink:'#8a9bb5'):col,wash=fr?(flash?C.pinkW:'#e6ebf2'):(j?j.wash:'#eee');
  if(home)g.globalAlpha=.75;
  if(!o.noShadow){g.fillStyle='rgba(46,46,51,.16)';g.beginPath();g.ellipse(0,r*1.02,r*.8,r*.2,0,0,7);g.fill()}
  const wob=Math.sin(ph)*(fr?.1:.05),bob=Math.sin(ph*.8)*r*.08;
  g.translate(0,bob-r*.1);g.scale(1+wob,1-wob);if(home)g.scale(.82,.82);g.rotate(Math.sin(ph*.7)*.08);
  // crumbs below
  g.fillStyle=line;g.globalAlpha*= .8;for(let k=0;k<4;k++){const cx=(k-1.5)*r*.45+Math.sin(ph*1.6+k)*r*.12,cy=r*.85+Math.abs(Math.sin(ph+k*1.3))*r*.25;g.beginPath();g.ellipse(cx,cy,r*.1,r*.07,k,0,7);g.fill()}
  g.globalAlpha=home?.75:1;
  // the block
  const blk=c=>cRect(c,0,0,r*1.9,r*1.45,r*.28);
  hatch(g,blk,line,wash,Math.max(3,r*.2),-.75);
  g.strokeStyle=line;g.globalAlpha*=.55;g.lineWidth=Math.max(1,r*.06);g.beginPath();g.moveTo(-r*.95,-r*.2);g.lineTo(r*.95,-r*.2);g.stroke();g.globalAlpha=home?.75:1;
  outline(g,blk,Math.max(1.5,r*.11));
  // face
  const jx=Math.sin(ph*2.3)*.12,jy=Math.cos(ph*1.9)*.12;
  if(home){eye(g,-r*.33,-r*.02,r*.24,0,0,{happy:true});eye(g,r*.33,-r*.02,r*.24,0,0,{happy:true});
    g.fillStyle=INK;g.beginPath();g.arc(0,r*.22,r*.16,0,Math.PI);g.closePath();g.fill()}
  else if(fr){eye(g,-r*.32,-r*.05,r*.22,jx*3,jy*3,{small:true});eye(g,r*.32,-r*.05,r*.22,-jx*3,jy*3,{small:true});
    g.strokeStyle=INK;g.lineWidth=Math.max(1,r*.08);g.beginPath();for(let k=0;k<=6;k++)g.lineTo(-r*.3+k*r*.1,r*.3+(k%2?-1:1)*r*.05);g.stroke()}
  else{eye(g,-r*.32,-r*.05,r*.27,clamp(lx+jx,-1,1),clamp(ly+jy,-1,1));eye(g,r*.34,-r*.07,r*.3,clamp(lx-jx,-1,1),clamp(ly+jy,-1,1));
    g.strokeStyle=INK;g.lineWidth=Math.max(1,r*.08);g.lineCap='round';g.beginPath();g.arc(0,r*.24,r*.14,.3,Math.PI-.3);g.stroke()}
  g.fillStyle='rgba(224,106,160,.4)';g.beginPath();g.ellipse(-r*.64,r*.22,r*.12,r*.07,0,0,7);g.ellipse(r*.66,r*.22,r*.12,r*.07,0,0,7);g.fill();
  g.restore();g.globalAlpha=1;
}
/* a gold star sticker */
function drawStarfish(g,x,y,r,ph){
  g.save();g.translate(x,y);g.rotate(Math.sin(ph)*.15);const s=1+Math.sin(ph*2)*.08;g.scale(s,s);
  g.strokeStyle=C.yellow;g.lineWidth=1;g.globalAlpha=.5;for(let k=0;k<8;k++){const a=k*Math.PI/4+ph*.3;g.beginPath();g.moveTo(Math.cos(a)*r*1.25,Math.sin(a)*r*1.25);g.lineTo(Math.cos(a)*r*1.6,Math.sin(a)*r*1.6);g.stroke()}g.globalAlpha=1;
  const st=c=>starPath(c,r,.5);
  hatch(g,st,C.yellow,C.yellowW,3,-.8);outline(g,st,Math.max(1.3,r*.12));
  g.fillStyle=INK;g.beginPath();g.arc(-r*.16,-r*.02,r*.08,0,7);g.arc(r*.16,-r*.02,r*.08,0,7);g.fill();
  g.strokeStyle=INK;g.lineWidth=Math.max(1,r*.07);g.lineCap='round';g.beginPath();g.arc(0,r*.08,r*.1,.3,Math.PI-.3);g.stroke();
  g.restore();
}
/* bonus treats: an apple for the teacher, a glue stick and a crayon */
function drawTreat(g,k,x,y,r,ph){
  g.save();g.translate(x,y+Math.sin(ph)*r*.1);g.lineJoin='round';g.lineCap='round';
  g.fillStyle='rgba(46,46,51,.16)';g.beginPath();g.ellipse(0,r*.95,r*.7,r*.18,0,0,7);g.fill();
  const ol=Math.max(1.3,r*.1);
  if(k==='apple'){
    const ap=c=>{c.moveTo(0,-r*.45);c.bezierCurveTo(-r*.3,-r*.95,-r*1.05,-r*.55,-r*.85,r*.1);c.bezierCurveTo(-r*.7,r*.7,-r*.25,r*.95,0,r*.75);c.bezierCurveTo(r*.25,r*.95,r*.7,r*.7,r*.85,r*.1);c.bezierCurveTo(r*1.05,-r*.55,r*.3,-r*.95,0,-r*.45);c.closePath()};
    hatch(g,ap,C.red,C.redW,3.5,-.8);outline(g,ap,ol);
    g.strokeStyle=INK;g.lineWidth=ol;g.beginPath();g.moveTo(0,-r*.5);g.quadraticCurveTo(r*.05,-r*.9,r*.2,-r*1.05);g.stroke();
    const lf=c=>{c.moveTo(r*.08,-r*.72);c.quadraticCurveTo(r*.45,-r*1.15,r*.75,-r*.8);c.quadraticCurveTo(r*.4,-r*.6,r*.08,-r*.72);c.closePath()};
    hatch(g,lf,C.green,C.greenW,3,.9);outline(g,lf,Math.max(1,r*.07));
  }else if(k==='glue'){
    const cap=c=>cRect(c,0,-r*.55,r*.7,r*.6,r*.1),tube=c=>cRect(c,0,r*.3,r*.78,r*1.2,r*.12);
    hatch(g,tube,C.blue,C.blueW,3.5,-.8);outline(g,tube,ol);
    hatch(g,cap,C.purple,C.purpleW,3,-.8);outline(g,cap,ol);
    g.fillStyle=PAPER;cRect(g,0,r*.35,r*.5,r*.45,r*.06);g.fill();g.strokeStyle=INK;g.lineWidth=Math.max(1,r*.06);g.stroke();
    g.fillStyle=INK;g.font=`${Math.max(5,r*.32)}px "Patrick Hand","Comic Sans MS",cursive`;g.textAlign='center';g.textBaseline='middle';g.fillText('GLUE',0,r*.36);
  }else{
    g.rotate(-.45);
    const stick=c=>cRect(c,0,r*.15,r*.55,r*1.5,r*.05),tip=c=>{c.moveTo(-r*.27,-r*.6);c.lineTo(-r*.12,-r*1);c.lineTo(r*.12,-r*1);c.lineTo(r*.27,-r*.6);c.closePath()};
    hatch(g,stick,C.green,C.greenW,3,-.8,.5);outline(g,stick,ol);
    hatch(g,tip,C.green,C.greenW,3,-.8);outline(g,tip,ol);
    g.strokeStyle=INK;g.lineWidth=Math.max(1,r*.06);g.beginPath();g.moveTo(-r*.27,-r*.35);g.lineTo(r*.27,-r*.35);g.moveTo(-r*.27,r*.65);g.lineTo(r*.27,r*.65);g.stroke();
    g.strokeStyle=C.green;g.lineWidth=Math.max(1,r*.05);g.beginPath();g.moveTo(-r*.1,-r*.2);g.lineTo(-r*.1,r*.5);g.stroke();
  }
  g.restore();
}

""")

# ---------------------------------------------------------------- scene drawing
rep("""function textOut(s,x,y,size,fill='#fff',stroke='#0b4a63'){ctx.save();ctx.font=`800 ${size}px "Baloo 2","Arial Rounded MT Bold",sans-serif`;""",
    """function textOut(s,x,y,size,fill=INK,stroke=PAPER){ctx.save();ctx.font=`${size}px "Gloria Hallelujah","Comic Sans MS",cursive`;""")
rep("""  if(floorC)ctx.drawImage(floorC,0,0,cw,ch);else{ctx.fillStyle='#1a8fae';ctx.fillRect(0,0,cw,ch)}
  // drifting light ripples
  if(!RM){ctx.save();ctx.globalCompositeOperation='lighter';ctx.fillStyle='rgba(255,255,255,.035)';
    for(let k=0;k<7;k++){const x=(hash(k,9)*cw+T*10*(k%2?1:-1))%(cw+120)-60,y=hash(k,7)*ch+Math.sin(T*.5+k)*20;ctx.beginPath();ctx.ellipse(x,y,70+k*8,24+k*3,.4,0,7);ctx.fill()}ctx.restore()}
""", """  if(floorC)ctx.drawImage(floorC,0,0,cw,ch);else{ctx.fillStyle=PAPER;ctx.fillRect(0,0,cw,ch)}
""")
rep("  // pearls and starfish\n", "  // dots and gold stars\n")
rep("""      if(tw>.93&&!RM){const s=cs*.22*(tw-.93)/.07;ctx.fillStyle='#fff';ctx.beginPath();""", """      if(tw>.93&&!RM){const s=cs*.22*(tw-.93)/.07;ctx.fillStyle=C.yellow;ctx.beginPath();""")
rep("    const opts={fr:j.fr,flash:fl,home:j.mode==='home'||j.mode==='enter'};", "    const opts={fr:j.fr,flash:fl,home:j.mode==='home'||j.mode==='enter',j};")
rep("parts.push({x:tx(jx)+rnd(-6,6),y:ty(jy)+rnd(-6,6),vx:0,vy:-20,life:.4,max:.4,r:1.6,col:'#ffffff',spark:true});", "parts.push({x:tx(jx)+rnd(-6,6),y:ty(jy)+rnd(-6,6),vx:0,vy:-20,life:.4,max:.4,r:1.6,col:GRAPH,spark:true});")
rep("ctx.fillStyle='#ffe27a';ctx.strokeStyle='#c98a0a';ctx.lineWidth=1;starPath(ctx,cs*.16,.45);ctx.fill();ctx.stroke();ctx.restore()}}", "ctx.fillStyle=C.yellowW;ctx.strokeStyle=INK;ctx.lineWidth=1.2;starPath(ctx,cs*.16,.45);ctx.fill();ctx.stroke();ctx.restore()}}")
rep("""  // bubbles drifting up
  for(const b of bubbles){ctx.strokeStyle='rgba(255,255,255,.55)';ctx.lineWidth=1.2;ctx.fillStyle='rgba(220,250,255,.12)';ctx.beginPath();ctx.arc(b.x,b.y,b.r,0,7);ctx.fill();ctx.stroke();
    ctx.fillStyle='rgba(255,255,255,.8)';ctx.beginPath();ctx.arc(b.x-b.r*.35,b.y-b.r*.35,b.r*.25,0,7);ctx.fill()}
""", "")
rep("if(p.ring){const u=1-a;ctx.strokeStyle='rgba(255,255,255,.9)';", "if(p.ring){const u=1-a;ctx.strokeStyle=C.yellow;")
rep("textOut(f.s,f.x,f.y,f.size,f.gold?'#ffe27a':'#fff',f.gold?'#8a4b00':'#0b4a63')", "textOut(f.s,f.x,f.y,f.size,f.gold?C.yellow:INK,PAPER)")
rep("textOut(TOUCH?'Swipe to scuttle!':'Arrow keys to scuttle!'", "textOut(TOUCH?'Swipe to scribble!':'Arrow keys to scribble!'")

# ---------------------------------------------------------------- HUD + cards
between("const SHELL='", "let shownScore=-1", """const SHELL='<svg viewBox="0 0 24 24" aria-hidden="true"><g transform="rotate(-35 12 12)"><rect x="3" y="9" width="4" height="6" rx="1" fill="#f6d6e5" stroke="#2e2e33" stroke-width="1.4"/><rect x="7" y="9" width="2.5" height="6" fill="#e8e6df" stroke="#2e2e33" stroke-width="1.2"/><rect x="9.5" y="9" width="8" height="6" fill="#f6e7a8" stroke="#2e2e33" stroke-width="1.4"/><path d="M10.5 10.5h6M10.5 13.5h6" stroke="#e0b020" stroke-width="1"/><path d="M17.5 9l4.5 3-4.5 3Z" fill="#e8d2bd" stroke="#2e2e33" stroke-width="1.4" stroke-linejoin="round"/><path d="M20.3 11.1 22 12l-1.7.9Z" fill="#2e2e33"/></g></svg>';
""")
rep("$('lives').setAttribute('aria-label',lives+(lives===1?' shell':' shells')+' left')}", "$('lives').setAttribute('aria-label',lives+(lives===1?' pencil':' pencils')+' left')}")
rep("$('progTxt').textContent=pearlsLeft+(pearlsLeft===1?' pearl left':' pearls left');", "$('progTxt').textContent=pearlsLeft+(pearlsLeft===1?' dot left':' dots left');")
rep("""const JL=`<div class="jl">${JDEF.map((d,i)=>`<span><i style="background:${d.col}"></i>${d.name} ${['follows you','heads you off','zigzags','is shy'][i]}</span>`).join('')}</div>`;""",
    """const JL=`<div class="jl">${JDEF.map((d,i)=>`<span><i style="--c:${d.col};--w:${d.wash}"></i>${d.name} ${['follows you','heads you off','zigzags','is shy'][i]}</span>`).join('')}</div>`;""")
between("const RULES=`<ul class=\"rules\">", "function startCard(){", """const RULES=`<ul class="rules">
  <li><b>1</b><span>Swipe on the page (or use the arrow pad) to guide Stubby the pencil. On a computer, use the arrow keys or WASD.</span></li>
  <li><b>2</b><span>Collect every pencil dot to clear the page. Turn early and Stubby takes the next opening.</span></li>
  <li><b>3</b><span>Bump into an <u>eraser</u> and Stubby gets rubbed dizzy and loses a pencil. You have 3 pencils.</span></li>
  <li><b>4</b><span>Grab a gold star sticker and the erasers go pale and wobbly. Bonk them for 200, 400, 800, 1600!</span></li></ul>${JL}
  <p class="keys">Keys: <kbd>&larr;</kbd><kbd>&uarr;</kbd><kbd>&rarr;</kbd><kbd>&darr;</kbd> or <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> move, <kbd>P</kbd> pause, <kbd>M</kbd> sound.</p>`;
""")
rep("<h2>Pearl Patrol</h2>", "<h2>Pencil Patrol</h2>")
rep("<h2>Tickled out!</h2><p>The jellies giggled Shelly out of shells on level ${level}.</p>", "<h2>Rubbed out!</h2><p>The erasers scrubbed Stubby off the page on level ${level}.</p>")
rep("<div><b>${eatenTotal}</b><span>pearls</span></div><div><b>${boopsTotal}</b><span>jellies booped</span></div>", "<div><b>${eatenTotal}</b><span>dots</span></div><div><b>${boopsTotal}</b><span>erasers bonked</span></div>")
between("function drawMini(){", "/* ---------- input ---------- */", r"""function drawMini(){
  const c=$('mini');if(!c)return;const r=c.getBoundingClientRect(),d=Math.min(2.5,devicePixelRatio||1);c.width=Math.round(r.width*d);c.height=Math.round(r.height*d);
  const g=c.getContext('2d'),k=r.width/240;g.scale(d*k,d*k);
  // a strip of page with two hatched walls, dots, a star, Stubby and an eraser
  g.fillStyle=PAPER;rrect(g,2,4,236,90,10);g.fill();
  for(const y of [8,78]){const bar=c2=>{c2.rect(10,y,220,12)};hatch(g,bar,C.blue,'#eaf0f8',5,-.7,.8);outline(g,bar,2)}
  g.fillStyle=INK;for(let x=86;x<=150;x+=16){g.beginPath();g.arc(x,50,3,0,7);g.fill()}
  drawStarfish(g,170,50,10,0);
  drawShelly(g,54,50,18,1,1,0,0,{still:true,chomp:.6});
  drawJelly(g,210,48,15,JDEF[0].col,-1,0,1,{noShadow:true,j:JDEF[0]});
}

""")

# ---------------------------------------------------------------- aria / tests
rep("jellies:J.map(j=>", "jellies:J.map(j=>")  # untouched; keeps the test hook shape

# nothing sea-coloured may remain
for bad in ['#0b4a63','#123a44','#1a8fae','#ff6a4d','#ffb3d1','#fffaf0','#fff','#ffffff','Baloo','Nunito','Shelly the hermit','jellyfish','pearl ']:
    assert bad not in s, f"leftover {bad!r}"
OUT.write_text(s)
print("wrote", OUT, len(s), "bytes")
