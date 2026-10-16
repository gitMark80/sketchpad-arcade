#!/usr/bin/env python3
"""Pencil Putt art, drawn in code to match Mark's coloured-pencil sprite sheets
(bold sketchy ink outlines, dense back-and-forth coloured-pencil scribble fills,
darker scribble on the shaded side, big friendly faces).

School-desk mini golf: rulers for walls, pink-eraser corner posts, crumpled paper
balls for rocks, a bouncy playground ball, a walking eraser instead of the crab,
a pinwheel instead of the umbrella, a crayon gate, standing pencils instead of
tiki torches, a sticky-note tee, pencil-shaving traps, blue-ink water.

    python3 tools/pencil-putt-art.py [names...] [--sheet out.png]

Writes src/assets/pencil-putt/<name>.webp with the same names (and roughly the
same shapes and anchors) as the art it replaces, so the game code is unchanged.
Drawn with <canvas> in headless Chromium at 2x, downscaled with Pillow.
"""
import base64, io, os, sys
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'src', 'assets', 'pencil-putt')
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', '/opt/pw-browsers')

# name: (width, height, opaque texture?)
SIZES = {
    'ball': (256, 256, 0), 'cup': (380, 380, 0), 'flag': (441, 342, 0), 'tee': (360, 303, 0),
    'wall': (520, 118, 0), 'cap': (300, 177, 0), 'rock': (360, 360, 0), 'bball': (390, 390, 0),
    'bsq': (390, 264, 0), 'crabA': (360, 345, 0), 'crabB': (360, 345, 0), 'dizzy': (390, 303, 0),
    'umb': (368, 368, 0), 'surf': (180, 348, 0), 'tiki': (168, 396, 0), 'star': (256, 256, 0),
    'shell': (240, 220, 0), 'splash': (400, 362, 0), 'puff': (360, 354, 0), 'confetti': (400, 394, 0),
    'sandtrap': (512, 512, 1), 'water': (512, 512, 1), 'tide': (512, 512, 1), 'slope': (512, 512, 1),
    'beach': (700, 1244, 1),
}

JS = r"""
const INK='#232327';
let seed=7;function R(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return (seed>>>0)/4294967296}
const rr=(a,b)=>a+(b-a)*R(), pick=a=>a[Math.floor(R()*a.length)];
const TAU=Math.PI*2;
function hex(c){c=c.replace('#','');return[0,2,4].map(i=>parseInt(c.substr(i,2),16))}
function mix(c,d,t){const A=hex(c),B=hex(d);return'#'+A.map((v,i)=>Math.round(v+(B[i]-v)*t).toString(16).padStart(2,'0')).join('')}
const dark=(c,t)=>mix(c,'#1c1c22',t), light=(c,t)=>mix(c,'#ffffff',t);
let ctx,U=1; // U = stroke unit (px at the drawing size)

/* ---------- shapes as point lists ---------- */
function circ(cx,cy,rx,ry,n,rot){ry=ry||rx;n=n||72;rot=rot||0;const P=[];for(let i=0;i<n;i++){const a=i/n*TAU,x=Math.cos(a)*rx,y=Math.sin(a)*ry;P.push([cx+x*Math.cos(rot)-y*Math.sin(rot),cy+x*Math.sin(rot)+y*Math.cos(rot)])}return P}
function dens(pts,closed,step){step=step||8;const P=[];const n=pts.length;for(let i=0;i<(closed?n:n-1);i++){const a=pts[i],b=pts[(i+1)%n],l=Math.hypot(b[0]-a[0],b[1]-a[1]),k=Math.max(1,Math.round(l/step));for(let j=0;j<k;j++)P.push([a[0]+(b[0]-a[0])*j/k,a[1]+(b[1]-a[1])*j/k])}if(!closed)P.push(pts[n-1]);return P}
function rrect(x,y,w,h,r,step){const P=[],n=8;const c=[[x+w-r,y+r,-Math.PI/2],[x+w-r,y+h-r,0],[x+r,y+h-r,Math.PI/2],[x+r,y+r,Math.PI]];
  for(const[cx,cy,a0]of c)for(let i=0;i<=n;i++){const a=a0+i/n*Math.PI/2;P.push([cx+Math.cos(a)*r,cy+Math.sin(a)*r])}return dens(P,true,step||8)}
function blob(cx,cy,r,amp,n,lobes){n=n||60;const ph=rr(0,6);const P=[];for(let i=0;i<n;i++){const a=i/n*TAU;let q=r*(1+amp*Math.sin(a*lobes+ph)+amp*.5*Math.sin(a*(lobes+3)+ph*2));P.push([cx+Math.cos(a)*q,cy+Math.sin(a)*q])}return P}
function jit(P,a){const ph=rr(0,6.3),ph2=rr(0,6.3),f=rr(.18,.32);return P.map(([x,y],i)=>[x+a*Math.sin(i*f+ph)+rr(-a,a)*.3,y+a*Math.cos(i*f*1.3+ph2)+rr(-a,a)*.3])}
function path(P,closed){const p=new Path2D(),n=P.length;const m=(a,b)=>[(a[0]+b[0])/2,(a[1]+b[1])/2];
  if(closed){const s=m(P[n-1],P[0]);p.moveTo(s[0],s[1]);for(let i=0;i<n;i++){const q=m(P[i],P[(i+1)%n]);p.quadraticCurveTo(P[i][0],P[i][1],q[0],q[1])}p.closePath()}
  else{p.moveTo(P[0][0],P[0][1]);for(let i=1;i<n-1;i++){const q=m(P[i],P[i+1]);p.quadraticCurveTo(P[i][0],P[i][1],q[0],q[1])}p.lineTo(P[n-1][0],P[n-1][1])}return p}
function bbox(P){let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(const[x,y]of P){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y)}return{x0,y0,x1,y1,w:x1-x0,h:y1-y0,cx:(x0+x1)/2,cy:(y0+y1)/2}}

/* ---------- pencil work ---------- */
// a back-and-forth run of coloured-pencil strokes
function run(x,y,ang,len,n,gap,w,col,al){ctx.strokeStyle=col;ctx.globalAlpha=al;ctx.lineWidth=w;ctx.lineCap=ctx.lineJoin='round';
  const c=Math.cos(ang),s=Math.sin(ang),px=-s,py=c;let X=x-c*len/2,Y=y-s*len/2,d=1;ctx.beginPath();ctx.moveTo(X,Y);
  for(let i=0;i<n;i++){const L=len*rr(.75,1.12);const g=gap*rr(.6,1.4);X+=c*L*d+px*g;Y+=s*L*d+py*g;ctx.lineTo(X+rr(-.5,.5)*w,Y+rr(-.5,.5)*w);d=-d}ctx.stroke();ctx.globalAlpha=1}
// fill a shape with coloured pencil: pale wash, dense scribble, darker scribble on the shaded (lower right) side
function pencil(P,col,o){o=o||{};const b=bbox(P),p=path(P,true);ctx.save();ctx.clip(p);
  ctx.fillStyle=light(col,o.wash==null?.6:o.wash);ctx.fill(p);
  const w=(o.w||1.25)*U,gap=w*(o.gap||1.25),cell=Math.max(12*U,Math.min(b.w,b.h)*.32),ang=o.ang==null?-1.0:o.ang;
  const dens=o.dens==null?1:o.dens;
  for(let pass=0;pass<2;pass++)for(let y=b.y0-cell*.5;y<b.y1+cell*.5;y+=cell*.55/dens)for(let x=b.x0-cell*.5;x<b.x1+cell*.5;x+=cell*.55/dens){
    run(x+rr(-cell,cell)*.3,y+rr(-cell,cell)*.3,ang+rr(-.25,.25)+(pass?rr(-.4,.4):0),cell*rr(.9,1.4),Math.round(cell/gap*rr(.5,.9)),gap,w*rr(.8,1.25),
      pick([col,col,light(col,.12),dark(col,.08)]),rr(.32,.58))}
  if(o.shade!==0){const sh=o.shade==null?1:o.shade,lx=o.lx==null?.7:o.lx,ly=o.ly==null?.7:o.ly;
    for(let y=b.y0;y<b.y1;y+=cell*.45)for(let x=b.x0;x<b.x1;x+=cell*.45){
      const d=((x-b.cx)/b.w*lx+(y-b.cy)/b.h*ly);if(d<.06+rr(0,.2))continue;
      run(x,y,ang+.9+rr(-.3,.3),cell*rr(.6,1),Math.round(cell/gap*.5),gap*1.1,w,dark(col,.3),rr(.25,.45)*sh)}}
  if(o.hi!==0){ // a few paper-white streaks on the lit side, like a pencil skipping
    ctx.globalCompositeOperation='destination-out';
    for(let i=0;i<(o.hi||3);i++){const x=b.x0+b.w*rr(.18,.42),y=b.y0+b.h*rr(.18,.4);run(x,y,ang+rr(-.2,.2),Math.min(b.w,b.h)*rr(.08,.16),3,w*1.5,w*1.4,'#000',.28)}
    ctx.globalCompositeOperation='source-over'}
  ctx.restore()}
// sketchy ink outline: a bold line and a lighter wandering second pass
function ink(P,closed,w,col){w=(w||3)*U;ctx.lineJoin=ctx.lineCap='round';ctx.strokeStyle=col||INK;
  ctx.globalAlpha=.95;ctx.lineWidth=w;ctx.stroke(path(jit(P,w*.12),closed));
  ctx.globalAlpha=.5;ctx.lineWidth=w*.42;ctx.stroke(path(jit(P,w*.45),closed));
  ctx.globalAlpha=.35;ctx.lineWidth=w*.3;ctx.stroke(path(jit(P,w*.6),closed));ctx.globalAlpha=1}
function line(pts,w,col,al){ink(dens(pts,false,6),false,w,col);}
function shape(P,col,o,w){pencil(P,col,o);ink(P,true,w||3)}
function graphite(P,o){pencil(P,'#9a9aa0',Object.assign({wash:.9,dens:.45,w:1,shade:.9,hi:0},o||{}))}
function eye(x,y,r,look,shut){
  if(shut){line([[x-r,y],[x,y-r*.5],[x+r,y]],2.4);return}
  const P=circ(x,y,r*.82,r,40);ctx.fillStyle='#fff';ctx.fill(path(P,true));ink(P,true,2.4);
  ctx.fillStyle=INK;ctx.beginPath();ctx.ellipse(x+(look?look[0]:0)*r*.3,y+(look?look[1]:.15)*r*.35,r*.48,r*.58,0,0,TAU);ctx.fill();
  ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(x+(look?look[0]:0)*r*.3-r*.18,y-r*.2,r*.17,0,TAU);ctx.fill()}
function swirl(x,y,r){const P=[];for(let i=0;i<60;i++){const a=i/60*TAU*2.4,q=r*(1-i/60*.9);P.push([x+Math.cos(a)*q,y+Math.sin(a)*q])}
  const C=circ(x,y,r*1.05,r*1.05,40);ctx.fillStyle='#fff';ctx.fill(path(C,true));ink(C,true,2.2);ink(P,false,2)}
function smile(x,y,w,h,open){if(open){const P=[[x-w/2,y],[x-w*.25,y+h*.85],[x,y+h],[x+w*.25,y+h*.85],[x+w/2,y]];const Q=dens(P,true,4);
    ctx.fillStyle='#7a2633';ctx.fill(path(Q,true));ctx.save();ctx.clip(path(Q,true));ctx.fillStyle='#e8768a';ctx.beginPath();ctx.ellipse(x,y+h,w*.28,h*.42,0,0,TAU);ctx.fill();ctx.restore();ink(Q,true,2.4);return}
  line([[x-w/2,y],[x-w*.2,y+h*.75],[x+w*.2,y+h*.75],[x+w/2,y]],2.6)}
function blush(x,y,r,col){ctx.save();ctx.globalAlpha=.55;run(x,y,-.6,r*1.6,5,r*.35,1.5*U,col||'#f08aa0',.6);ctx.restore()}
// draw something on a seamless tile: every item is drawn again shifted by the tile size
function tile(W,H,items){for(const it of items)for(const dx of[-W,0,W])for(const dy of[-H,0,H]){const b=it.r||0;
    if(it.x+dx<-b-20||it.x+dx>W+b+20||it.y+dy<-b-20||it.y+dy>H+b+20)continue;seed=it.s;ctx.save();ctx.translate(it.x+dx,it.y+dy);it.f();ctx.restore()}}

/* ---------- the art ---------- */
const COL={red:'#e23b3b',orange:'#f08a24',yellow:'#f6c81e',green:'#3fae4a',blue:'#2f86d6',purple:'#8a4fc6',pink:'#ee6fa3',tan:'#d9a35b',wood:'#e7b866'};
const ART={
ball(W,H){const P=circ(128,128,108,108,80);pencil(P,'#d4d4da',{wash:.94,dens:.22,w:1,shade:1.1,hi:0});
  ctx.save();ctx.clip(path(P,true));for(let i=0;i<34;i++){const a=rr(0,TAU),q=Math.sqrt(R())*96,x=128+Math.cos(a)*q,y=128+Math.sin(a)*q;const r=rr(5,7.5)*(1-q/190);
    ctx.globalAlpha=.4;ctx.strokeStyle='#5d5d66';ctx.lineWidth=2.4;ctx.beginPath();ctx.arc(x,y,r,0,TAU);ctx.stroke()}ctx.restore();ctx.globalAlpha=1;
  ink(P,true,6)},
cup(W,H){const O=circ(190,190,176,172,90);pencil(O,'#f3efe2',{wash:.2,dens:.35,w:1.1,shade:.8,hi:0});
  const I=circ(190,198,132,126,80);pencil(I,'#3a3a44',{wash:.05,dens:1.3,w:1.6,shade:1.5,hi:0,ang:-.6});
  ctx.save();ctx.clip(path(I,true));ctx.fillStyle='rgba(20,20,25,.55)';ctx.beginPath();ctx.ellipse(190,150,150,70,0,0,TAU);ctx.fill();ctx.restore();
  ink(O,true,5);ink(I,true,6)},
flag(W,H){const px=111;
  // pennant (orange, numbered by the game) with a little star doodle
  const F=[];for(let i=0;i<=12;i++){const u=i/12;F.push([px+6+u*312,40+u*130+Math.sin(u*3.2)*10])}
  for(let i=12;i>=0;i--){const u=i/12;F.push([px+6+u*312,300-u*130+Math.sin(u*3.2+.6)*8])}
  shape(F,COL.orange,{wash:.45,ang:-.8},5);
  // pole and knob
  const pole=rrect(px-8,22,16,322,8,8);shape(pole,'#c9a36a',{wash:.5,dens:.6,hi:0},4);
  const k=circ(px,22,17,17,30);shape(k,COL.yellow,{wash:.4,hi:1},4)},
tee(W,H){ // a yellow sticky note with a curled corner and the tee spot in the middle
  ctx.save();ctx.translate(180,152);ctx.rotate(-.04);ctx.translate(-180,-152);
  const N=[[30,22],[332,16],[338,250],[296,288],[26,284]];const P=dens(N,true,10);
  ctx.fillStyle='rgba(35,35,40,.18)';ctx.fill(path(P.map(([x,y])=>[x+8,y+8]),true));
  shape(P,COL.yellow,{wash:.42},5);
  const C=dens([[338,250],[296,288],[302,246]],true,6);shape(C,'#e2a514',{wash:.25,shade:0,hi:0},4);
  // a strip of tape across the top
  const T=dens([[130,6],[232,4],[236,40],[128,44]],true,8);ctx.save();ctx.globalAlpha=.75;pencil(T,'#d8e6ee',{wash:.5,dens:.4,shade:0,hi:0});ctx.restore();ink(T,true,2.4,'#5b6a74');
  const S=circ(180,152,30,30,36);shape(S,'#ffffff',{wash:.9,dens:.2,hi:0},4);
  ctx.restore()},
wall(W,H){ // a wooden ruler, open at both ends so it tiles along a wall
  const top=12,bot=106,P=[[-20,top],[W+20,top],[W+20,bot],[-20,bot]];pencil(dens(P,true,12),COL.wood,{wash:.45,ang:-.15,dens:1.1,lx:0,ly:1.2,hi:0});
  ctx.save();for(let i=0;i<=40;i++){const x=i*W/40;const L=i%10===0?40:i%5===0?28:16;line([[x,top+2],[x+rr(-1,1),top+2+L]],i%5===0?2.2:1.6)}
  ctx.restore();
  ink(dens([[-20,top],[W+20,top]],false,10),false,5);ink(dens([[-20,bot],[W+20,bot]],false,10),false,5)},
cap(W,H){ // pink eraser block where two rulers meet
  ctx.fillStyle='rgba(35,35,40,.2)';ctx.fill(path(rrect(30,40,262,130,30),true));
  const S=rrect(14,40,272,122,30);shape(S,dark(COL.pink,.15),{wash:.35,hi:0},5);
  const T=rrect(14,14,272,112,28);shape(T,COL.pink,{wash:.4,hi:3},5);
  line([[60,60],[110,52]],2);line([[200,96],[240,90]],2)},
rock(W,H){ // crumpled paper ball
  const P=blob(180,180,150,.07,70,7);pencil(P,'#c6c3b8',{wash:.88,dens:.5,w:1.1,shade:1.3,hi:0});
  ctx.save();ctx.clip(path(P,true));
  for(let i=0;i<9;i++){const a=rr(0,TAU),x=180+Math.cos(a)*rr(10,90),y=180+Math.sin(a)*rr(10,90),pts=[[x,y]];let ang=rr(0,TAU);
    for(let k=0;k<4;k++){ang+=rr(-1.1,1.1);const L=rr(22,48);pts.push([pts[k][0]+Math.cos(ang)*L,pts[k][1]+Math.sin(ang)*L])}
    ink(dens(pts,false,6),false,2.4,'#4a4a52')}
  // lined-paper lines showing on the crumple
  ctx.globalAlpha=.5;for(let y=60;y<330;y+=34){ink(dens([[20,y+rr(-6,6)],[120,y+rr(-12,12)],[240,y+rr(-12,12)],[340,y+rr(-6,6)]],false,10),false,1.6,'#6a9bd1')}ctx.globalAlpha=1;
  ctx.restore();ink(P,true,6)},
bball(W,H){ // red playground ball with a yellow band and a white star
  const c=195,r=180,P=circ(c,c,r,r,96);pencil(P,COL.red,{wash:.38,dens:1.1});
  ctx.save();ctx.clip(path(P,true));const B=[];for(let i=0;i<=20;i++){const u=i/20;B.push([c-r-10+u*(2*r+20),c-70+Math.sin(u*Math.PI)*-40])}
  for(let i=20;i>=0;i--){const u=i/20;B.push([c-r-10+u*(2*r+20),c+10+Math.sin(u*Math.PI)*-40])}
  pencil(B,COL.yellow,{wash:.35,shade:.6});ink(B,true,4);ctx.restore();
  const S=[];for(let i=0;i<10;i++){const a=i/10*TAU-Math.PI/2,q=i%2?26:58;S.push([c+Math.cos(a)*q,c+60+Math.sin(a)*q])}
  shape(dens(S,true,6),'#ffffff',{wash:.9,dens:.25,hi:0,shade:.4},4);
  ink(P,true,7)},
bsq(W,H){ // the ball squashed flat when something hits it
  ctx.save();ctx.translate(195,132);ctx.scale(1.02,.66);ctx.translate(-195,-195);ART.bball(390,390);ctx.restore();
  for(const s of[-1,1])for(const k of[-1,0,1])line([[195+s*188,132+k*40],[195+s*(204+(k?0:8)),132+k*52]],3)},
crabA(W,H){eraser(0,false)},crabB(W,H){eraser(1,false)},
dizzy(W,H){ctx.translate(15,-20);ctx.rotate(.05);eraser(2,true);ctx.setTransform(2,0,0,2,0,0);
  for(const[x,y,s]of[[60,40,24],[330,46,20],[200,20,18]]){const S=[];for(let i=0;i<10;i++){const a=i/10*TAU-Math.PI/2,q=i%2?s*.42:s;S.push([x+Math.cos(a)*q,y+Math.sin(a)*q])}shape(dens(S,true,4),COL.yellow,{wash:.3,shade:0,hi:0},2.6)}},
umb(W,H){ // pinwheel seen from above; the blade tips line up with the spinner's four arms
  const c=184,r=170,cols=[COL.red,COL.yellow,COL.blue,COL.green];
  for(let k=0;k<4;k++){const a=.35+k*TAU/4,tip=[c+Math.cos(a)*r,c+Math.sin(a)*r],side=[c+Math.cos(a+TAU/8)*r*.72,c+Math.sin(a+TAU/8)*r*.72],
    back=[c+Math.cos(a-TAU/4)*r*.33,c+Math.sin(a-TAU/4)*r*.33];
    const P=dens([[c,c],tip,side],true,8);const Q=dens([[c,c],back,tip],true,8);
    shape(Q,dark(cols[k],.12),{wash:.35,shade:.8},4.5);shape(P,cols[k],{wash:.4},4.5)}
  const h=circ(c,c,28,28,30);shape(h,'#f2f2f2',{wash:.7,dens:.4,hi:0},4);ctx.fillStyle=INK;ctx.beginPath();ctx.arc(c,c,8,0,TAU);ctx.fill()},
surf(W,H){ // a blue crayon standing up (the game turns it on its side)
  const x0=24,x1=156;const tip=dens([[x0+14,92],[90,10],[x1-14,92]],true,8);shape(tip,COL.blue,{wash:.35},4.5);
  const body=rrect(x0,84,x1-x0,252,14);shape(body,COL.blue,{wash:.4},5);
  const lab=dens([[x0,140],[x1,140],[x1,276],[x0,276]],true,10);shape(lab,'#bfe0ff',{wash:.55,dens:.6,shade:.5,hi:0},4);
  for(const y of[112,124,296,308])line([[x0+6,y],[x1-6,y]],2.2);
  const zz=[];for(let i=0;i<=10;i++)zz.push([90+(i%2?22:-22),156+i*11.2]);ink(zz,false,4,dark(COL.blue,.3))},
tiki(W,H){ // a yellow pencil standing on its eraser (anchored at the bottom middle)
  const cx=84,x0=40,x1=128;ctx.fillStyle='rgba(35,35,40,.2)';ctx.beginPath();ctx.ellipse(cx+8,384,62,12,0,0,TAU);ctx.fill();
  const er=rrect(x0,318,x1-x0,66,16);shape(er,COL.pink,{wash:.38},4.5);
  const fe=dens([[x0-3,288],[x1+3,288],[x1+3,326],[x0-3,326]],true,8);shape(fe,'#b8bcc4',{wash:.6,dens:.6,hi:2},4.5);
  line([[x0,300],[x1,300]],2);line([[x0,313],[x1,313]],2);
  const body=dens([[x0,92],[x1,92],[x1,290],[x0,290]],true,10);shape(body,COL.yellow,{wash:.35},5);
  line([[cx-14,100],[cx-14,282]],2.2);line([[cx+14,100],[cx+14,282]],2.2);
  const wood=dens([[x0,96],[cx,14],[x1,96]],true,8);shape(wood,'#f3d7a6',{wash:.5,dens:.6,hi:0},4.5);
  const lead=dens([[cx-17,46],[cx,12],[cx+17,46]],true,4);shape(lead,'#45454d',{wash:.1,shade:0,hi:0},4)},
star(W,H){const S=[];for(let i=0;i<10;i++){const a=i/10*TAU-Math.PI/2,q=i%2?50:112;S.push([128+Math.cos(a)*q,136+Math.sin(a)*q])}
  shape(dens(S,true,8),COL.yellow,{wash:.32},6);eye(108,128,12,[0,.2]);eye(148,128,12,[0,.2]);smile(128,150,30,12)},
shell(W,H){ // a purple paper clip lying on the paper
  ctx.translate(120,110);ctx.rotate(-.5);
  const loop=[[-80,-18],[60,-18],[80,0],[60,18],[-60,18],[-70,8],[-60,-2],[40,-2]];
  const P=[];const q=(x,y)=>P.push([x,y]);
  for(let i=0;i<=16;i++){const a=-Math.PI/2+i/16*Math.PI;q(70+Math.cos(a)*30,Math.sin(a)*30)}
  for(let i=0;i<=16;i++){const a=Math.PI/2+i/16*Math.PI;q(-78+Math.cos(a)*22,-8+Math.sin(a)*22)}
  for(let i=0;i<=16;i++){const a=-Math.PI/2+i/16*Math.PI;q(50+Math.cos(a)*14,Math.sin(a)*14)}
  q(-30,14);
  ctx.lineCap=ctx.lineJoin='round';ctx.strokeStyle=INK;ctx.lineWidth=26;ctx.stroke(path(P,false));
  ctx.strokeStyle=COL.purple;ctx.lineWidth=15;ctx.stroke(path(P,false));ctx.strokeStyle=light(COL.purple,.55);ctx.lineWidth=5;ctx.stroke(path(P.map(([x,y])=>[x-2,y-3]),false))},
splash(W,H){ // blue ink splash ring
  const c=[200,181];for(let i=0;i<14;i++){const a=i/14*TAU+rr(-.2,.2),q=rr(120,165),r=rr(9,20);const D=circ(c[0]+Math.cos(a)*q,c[1]+Math.sin(a)*q*.9,r,r*rr(.8,1),24);shape(D,COL.blue,{wash:.35,shade:0,hi:0},3)}
  const O=blob(c[0],c[1],112,.13,80,9);const I=circ(c[0],c[1],62,56,60);
  ctx.save();const p=path(O,true);p.addPath(path(I.slice().reverse(),true));ctx.clip(p,'evenodd');pencil(O,COL.blue,{wash:.35});ctx.restore();ink(O,true,4.5);ink(I,true,3.5,dark(COL.blue,.35))},
puff(W,H){ // a puff of pencil shavings
  for(let i=0;i<16;i++){const a=i/16*TAU+rr(-.2,.2),q=rr(70,150),x=180+Math.cos(a)*q,y=177+Math.sin(a)*q;shaving(x,y,rr(18,30),rr(0,TAU),pick([COL.yellow,COL.red,COL.blue,COL.green,COL.yellow]))}
  ctx.fillStyle='rgba(70,70,78,.5)';for(let i=0;i<60;i++){const a=rr(0,TAU),q=rr(40,170);ctx.beginPath();ctx.arc(180+Math.cos(a)*q,177+Math.sin(a)*q,rr(1.5,4),0,TAU);ctx.fill()}},
confetti(W,H){const cs=[COL.red,COL.yellow,COL.blue,COL.green,COL.purple,COL.pink,COL.orange];
  for(let i=0;i<34;i++){const a=rr(0,TAU),q=rr(30,180),x=200+Math.cos(a)*q,y=197+Math.sin(a)*q;ctx.save();ctx.translate(x,y);ctx.rotate(rr(0,TAU));const c=pick(cs),k=i%3;
    if(k===0)shape(dens([[-14,-7],[14,-7],[14,7],[-14,7]],true,5),c,{wash:.3,shade:0,hi:0},2.6);
    else if(k===1)shape(circ(0,0,9,9,16),c,{wash:.3,shade:0,hi:0},2.6);
    else{ctx.strokeStyle=INK;ctx.lineWidth=9;ctx.lineCap='round';const S=[[-16,0],[-8,-8],[0,0],[8,8],[16,0]];ctx.stroke(path(S,false));ctx.strokeStyle=c;ctx.lineWidth=4.5;ctx.stroke(path(S,false))}ctx.restore()}},
sandtrap(W,H){ // pencil shavings and graphite dust on pale wood-coloured paper
  ctx.fillStyle='#f1e4c8';ctx.fillRect(0,0,W,H);
  const items=[];for(let i=0;i<46;i++){const s=Math.floor(rr(1,1e9));items.push({x:rr(0,W),y:rr(0,H),r:60,s,f(){run(0,0,-.9+rr(-.3,.3),rr(60,110),9,3,1.4,pick(['#d9b77e','#e2c58f','#cfa76a']),.4)}})}
  for(let i=0;i<34;i++){const s=Math.floor(rr(1,1e9)),c=pick([COL.yellow,COL.yellow,COL.red,COL.blue,COL.green,COL.orange]);items.push({x:rr(0,W),y:rr(0,H),r:40,s,f(){shaving(0,0,rr(14,22),rr(0,TAU),c)}})}
  for(let i=0;i<120;i++){const s=Math.floor(rr(1,1e9));items.push({x:rr(0,W),y:rr(0,H),r:6,s,f(){ctx.fillStyle='rgba(60,60,68,.45)';ctx.beginPath();ctx.arc(0,0,rr(1.2,3),0,TAU);ctx.fill()}})}
  tile(W,H,items)},
water(W,H){ // blue ink puddle: blue coloured-pencil scribble with ripple strokes
  ctx.fillStyle=light(COL.blue,.62);ctx.fillRect(0,0,W,H);const items=[];
  for(let i=0;i<70;i++){const s=Math.floor(rr(1,1e9));items.push({x:rr(0,W),y:rr(0,H),r:80,s,f(){run(0,0,-.35+rr(-.2,.2),rr(70,120),12,3.2,2,pick([COL.blue,light(COL.blue,.15),dark(COL.blue,.1)]),.35)}})}
  for(let i=0;i<16;i++){const s=Math.floor(rr(1,1e9));items.push({x:rr(0,W),y:rr(0,H),r:60,s,f(){const P=[];for(let k=0;k<=8;k++)P.push([-50+k*12.5,Math.sin(k*1.1)*7]);ink(P,false,3,dark(COL.blue,.35))}})}
  tile(W,H,items)},
tide(W,H){ // fast stream: pale blue with chunky arrows pointing right
  ctx.fillStyle=light(COL.blue,.72);ctx.fillRect(0,0,W,H);const items=[];
  for(let i=0;i<50;i++){const s=Math.floor(rr(1,1e9));items.push({x:rr(0,W),y:rr(0,H),r:80,s,f(){run(0,0,-.3+rr(-.2,.2),rr(70,110),10,3.4,1.8,pick([COL.blue,light(COL.blue,.2)]),.25)}})}
  for(let r=0;r<4;r++)for(let c=0;c<4;c++){const s=Math.floor(rr(1,1e9));items.push({x:c*128+(r%2)*64+30,y:r*128+64,r:70,s,f(){
    const A=dens([[-44,-12],[8,-12],[8,-30],[46,0],[8,30],[8,12],[-44,12]],true,6);shape(A,COL.blue,{wash:.4,shade:.4,hi:0},3.4)}})}
  tile(W,H,items)},
slope(W,H){ // drawn with 'multiply' over the green: white paper with dark-green chevrons pointing uphill
  ctx.fillStyle='#ffffff';ctx.fillRect(0,0,W,H);const items=[];
  for(let r=0;r<4;r++)for(let c=0;c<4;c++){const s=Math.floor(rr(1,1e9));items.push({x:c*128+(r%2)*64+64,y:r*128+64,r:70,s,f(){
    ink(dens([[-40,22],[0,-18],[40,22]],false,6),false,6,'#2f6d38')}})}
  for(let i=0;i<40;i++){const s=Math.floor(rr(1,1e9));items.push({x:rr(0,W),y:rr(0,H),r:60,s,f(){run(0,0,-1+rr(-.2,.2),rr(50,80),8,4,1.4,'#7fae84',.22)}})}
  tile(W,H,items)},
beach(W,H){ // the desk page behind the course: grid paper with coloured doodles around the edges
  ctx.fillStyle='#f7f3e8';ctx.fillRect(0,0,W,H);
  ctx.strokeStyle='rgba(120,160,200,.32)';ctx.lineWidth=1.6;for(let x=10;x<W;x+=36){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke()}for(let y=10;y<H;y+=36){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke()}
  ctx.save();ctx.globalAlpha=.7;
  const spots=[[60,90],[640,70],[40,330],[665,300],[50,600],[650,560],[45,850],[660,830],[60,1120],[640,1150],[350,40],[350,1210],[200,1180],[500,60],[520,1190],[180,50]];
  const kinds=['pencil','star','clip','heart','crayon','spiral','eraser','cloud','star','pencil','heart','crayon','spiral','cloud','clip','eraser'];
  spots.forEach(([x,y],i)=>{ctx.save();ctx.translate(x,y);ctx.rotate(rr(-.6,.6));doodle(kinds[i]);ctx.restore()});
  ctx.restore();
  ctx.fillStyle='rgba(60,60,68,.35)';for(let i=0;i<140;i++){const e=R()<.5;const x=e?rr(0,W):pick([rr(0,110),rr(W-110,W)]),y=e?pick([rr(0,140),rr(H-140,H)]):rr(0,H);ctx.beginPath();ctx.arc(x,y,rr(1,2.6),0,TAU);ctx.fill()}}
};
function shaving(x,y,r,a,col){ctx.save();ctx.translate(x,y);ctx.rotate(a);
  const P=[];for(let i=0;i<=20;i++){const t=i/20*Math.PI*1.25;P.push([Math.cos(t)*r,Math.sin(t)*r*.8])}for(let i=20;i>=0;i--){const t=i/20*Math.PI*1.25;P.push([Math.cos(t)*r*.45,Math.sin(t)*r*.35])}
  pencil(P,'#e9c99a',{wash:.3,dens:.7,w:1,shade:.6,hi:0});const E=[];for(let i=0;i<=20;i++){const t=i/20*Math.PI*1.25;E.push([Math.cos(t)*r,Math.sin(t)*r*.8])}
  ctx.lineCap='round';ctx.strokeStyle=col;ctx.lineWidth=r*.28;ctx.stroke(path(E,false));ink(P,true,2.2);ctx.restore()}
function eraser(frame,dz){ // a walking pink eraser seen from the front (two leg poses), or dizzy
  const col=COL.pink;
  ctx.fillStyle='rgba(35,35,40,.18)';ctx.beginPath();ctx.ellipse(180,318,140,18,0,0,TAU);ctx.fill();
  // legs and sneakers
  // legs and sneakers: frame 0 lifts the left foot, frame 1 the right one
  const legs=[[130,frame===0?-16:0,frame===0?-6:6],[230,frame===1?-16:0,frame===1?6:-6]];
  for(const[x,up,s]of legs){line([[x,250],[x+s,292+up]],7);const sh=circ(x+s+(x<180?-10:10),302+up,26,15,26,up?(x<180?-.25:.25):0);shape(sh,'#3b3b44',{wash:.15,shade:0,hi:1},3.5)}
  const top=dens([[78,64],[284,44],[330,82],[124,104]],true,10);const front=dens([[78,64],[124,104],[124,258],[60,232]],true,10);const face=dens([[124,104],[330,82],[322,240],[124,258]],true,10);
  shape(top,light(col,.12),{wash:.42,shade:.5},5.5);shape(front,dark(col,.18),{wash:.32},5.5);shape(face,col,{wash:.4},5.5);
  // eraser crumbs
  if(frame!==2)for(const[x,y]of[[338,250],[352,236],[362,256]]){const c=circ(x,y,5,5,10);shape(c,col,{wash:.3,shade:0,hi:0},2)}
  if(dz){swirl(185,150,26);swirl(265,145,26);line([[180,214],[200,204],[220,216],[240,204],[260,214]],3.5)}
  else{eye(186,148,27,[frame?.3:-.2,.2]);eye(262,144,27,[frame?.3:-.2,.2]);smile(224,192,62,30,true);blush(160,198,12);blush(296,190,12)}}
const DOODLE={
 pencil(){const b=dens([[-60,-12],[40,-12],[40,12],[-60,12]],true,8);shape(b,COL.yellow,{wash:.4},3.5);shape(dens([[40,-12],[72,0],[40,12]],true,6),'#f3d7a6',{wash:.4,shade:0,hi:0},3);
   shape(dens([[62,-4],[72,0],[62,4]],true,3),'#45454d',{shade:0,hi:0},2);shape(rrect(-82,-12,24,24,6,6),COL.pink,{wash:.4,hi:0},3.5)},
 star(){const S=[];for(let i=0;i<10;i++){const a=i/10*TAU-Math.PI/2,q=i%2?14:34;S.push([Math.cos(a)*q,Math.sin(a)*q])}shape(dens(S,true,5),COL.yellow,{wash:.35,hi:0},3)},
 clip(){ctx.lineCap='round';const P=[];for(let i=0;i<=12;i++){const a=-Math.PI/2+i/12*Math.PI;P.push([36+Math.cos(a)*14,Math.sin(a)*14])}for(let i=0;i<=12;i++){const a=Math.PI/2+i/12*Math.PI;P.push([-36+Math.cos(a)*10,-4+Math.sin(a)*10])}P.push([26,6]);
   ctx.strokeStyle=INK;ctx.lineWidth=11;ctx.stroke(path(P,false));ctx.strokeStyle=COL.blue;ctx.lineWidth=6;ctx.stroke(path(P,false))},
 heart(){const P=[];for(let i=0;i<50;i++){const t=i/50*TAU;P.push([16*Math.pow(Math.sin(t),3)*1.7,-(13*Math.cos(t)-5*Math.cos(2*t)-2*Math.cos(3*t)-Math.cos(4*t))*1.7])}shape(P,COL.red,{wash:.4,hi:0},3)},
 crayon(){shape(rrect(-54,-13,96,26,8),COL.green,{wash:.4,hi:0},3.5);shape(dens([[42,-10],[66,0],[42,10]],true,5),COL.green,{wash:.3,shade:0,hi:0},3);line([[-40,-13],[-40,13]],2);line([[28,-13],[28,13]],2)},
 spiral(){const P=[];for(let i=0;i<70;i++){const a=i/70*TAU*3,q=2+i*.45;P.push([Math.cos(a)*q,Math.sin(a)*q])}ink(P,false,3,COL.purple)},
 eraser(){shape(rrect(-34,-18,68,36,8),COL.pink,{wash:.4,hi:0},3.5)},
 cloud(){const P=[];for(let i=0;i<60;i++){const a=i/60*TAU;const q=1+.18*Math.abs(Math.sin(a*3));P.push([Math.cos(a)*42*q,Math.sin(a)*22*q])}shape(P,'#bcdcf5',{wash:.6,dens:.5,shade:.4,hi:0},3)}
};
function doodle(k){DOODLE[k]()}
window.render=(name,W,H,s)=>{const c=document.createElement('canvas');c.width=W*2;c.height=H*2;ctx=c.getContext('2d');ctx.setTransform(2,0,0,2,0,0);
  seed=s||(name.split('').reduce((a,ch)=>a*31+ch.charCodeAt(0),7)>>>0)||7;U=1;ART[name](W,H);return c.toDataURL('image/png')};
"""

def main():
    args = sys.argv[1:]
    sheet = None
    if '--sheet' in args:
        i = args.index('--sheet'); sheet = args[i + 1]; del args[i:i + 2]
    names = args or list(SIZES)
    os.makedirs(OUT, exist_ok=True)
    made = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        pg.set_content('<html><body></body></html>')
        pg.add_script_tag(content=JS)
        for n in names:
            W, H, opaque = SIZES[n]
            url = pg.evaluate('([n,W,H])=>render(n,W,H)', [n, W, H])
            im = Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert('RGBA')
            im = im.resize((W, H), Image.LANCZOS)
            if opaque:
                bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg
            im.save(os.path.join(OUT, n + '.webp'), 'WEBP', quality=90, method=6)
            made.append((n, im))
        b.close()
    print('wrote', ', '.join(n for n, _ in made))
    if sheet:
        cell = 240; cols = 6; rows = (len(made) + cols - 1) // cols
        S = Image.new('RGB', (cols * cell, rows * cell), (200, 200, 200))
        for i, (n, im) in enumerate(made):
            t = im.copy(); t.thumbnail((cell - 12, cell - 12))
            bg = Image.new('RGBA', t.size, (255, 255, 255, 255)); bg.alpha_composite(t)
            S.paste(bg.convert('RGB'), ((i % cols) * cell + 6, (i // cols) * cell + 6))
        S.save(sheet)


if __name__ == '__main__':
    main()
