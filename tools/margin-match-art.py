#!/usr/bin/env python3
"""Draws Margin Match's art in coloured pencil and writes it to src/assets/margin-match/:

  icons.webp     4x4 sheet of the 16 tile kinds (same order as NAMES in src/games/margin-match.html)
  tile.webp      the paper tile face the icons sit on
  tray.webp      the 7-slot tray, drawn as a giant pencil (slot holes match the .slot CSS percentages)
  notebook.webp  page background: faint ruled notebook lines, a red margin line and doodles in the corners

Style: dark ink outlines, a pale wash of colour inside and bright coloured-pencil cross-hatching on top
(two diagonal sets, the second a shade darker). Drawn with <canvas> in headless Chromium, saved with Pillow.
Usage: python3 tools/margin-match-art.py [--sheet out.png]   (--sheet also writes a labelled preview of every kind)
"""
import base64, io, os, sys
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'src', 'assets', 'margin-match')

JS = r"""
const OUT='#1f1f22';
const C={red:'#e0453a',orange:'#f08a24',yellow:'#f2c230',green:'#4caf50',blue:'#3a7bd5',purple:'#8e5bc9',pink:'#e86aa6',teal:'#2fa7a0',brown:'#9b6a3c',skin:'#f2c9a5',
  grey:'#8d95a0',ink:'#3a3a44',sky:'#4fb0e6',lime:'#8cc63f',white:'#c9c4b8'};
function hx(h){return[parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)]}
function mix(h,k){const a=hx(h),b=[250,248,241];return'rgb('+a.map((v,i)=>Math.round(b[i]+(v-b[i])*k)).join(',')+')'}
function dark(h,k){return'rgb('+hx(h).map(v=>Math.round(v*(1-(k==null?.25:k)))).join(',')+')'}
let SP=5.4,HL=2.1,OL=5.6;
const BOOST={0:1.14,3:1.06,6:1.06,7:1.16,12:1.12};
// pale wash + two sets of diagonal pencil lines (second set darker) clipped to the path, then the ink outline
function pf(c,path,col,o){
  o=o||{};const sp=o.sp||SP;
  c.save();c.beginPath();path(c);c.fillStyle=mix(col,o.wash==null?.32:o.wash);c.fill(o.rule||'nonzero');c.clip(o.rule||'nonzero');
  c.lineCap='round';c.lineWidth=o.hl||HL;c.globalAlpha=o.a==null?1:o.a;
  const j=(i)=>Math.sin(i*12.9898)*0.6;
  c.strokeStyle=col;c.beginPath();for(let s=-110,i=0;s<110;s+=sp,i++){c.moveTo(s+j(i),105);c.lineTo(s+110+j(i+3),-5)}c.stroke();
  c.strokeStyle=o.col2||dark(col);c.beginPath();for(let s=sp*.4,i=0;s<220;s+=sp*1.3,i++){c.moveTo(s+j(i),105);c.lineTo(s-110+j(i+5),-5)}c.stroke();
  c.restore();
  if(o.ol!==0){c.beginPath();path(c);c.strokeStyle=OUT;c.lineWidth=o.ol||OL;c.lineJoin='round';c.lineCap='round';c.stroke()}
}
function line(c,pts,w,col){c.beginPath();pts.forEach((p,i)=>i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]));c.lineWidth=w;c.strokeStyle=col||OUT;c.lineCap='round';c.lineJoin='round';c.stroke()}
function face(c,x,y,s){c.fillStyle=OUT;c.beginPath();c.arc(x-s*.42,y-s*.12,s*.15,0,7);c.arc(x+s*.42,y-s*.12,s*.15,0,7);c.fill();
  c.beginPath();c.arc(x,y+s*.05,s*.36,.35,Math.PI-.35);c.lineWidth=s*.13;c.strokeStyle=OUT;c.lineCap='round';c.stroke()}
function rot(c,a,f){c.save();c.translate(50,50);c.rotate(a);c.translate(-50,-50);f();c.restore()}
function star(c,x,y,r,rr){for(let i=0;i<10;i++){const a=-Math.PI/2+i*Math.PI/5,q=i%2?r*(rr||.5):r;c.lineTo(x+Math.cos(a)*q,y+Math.sin(a)*q)}c.closePath()}
function rr(c,x,y,w,h,r){c.roundRect(x,y,w,h,r)}

const ICONS=[
 // 0 pencil (orange)
 c=>rot(c,-.72,()=>{
   pf(c,p=>rr(p,10,38,12,24,[6,0,0,6]),C.pink);
   pf(c,p=>p.rect(21,37,8,26),C.grey,{sp:3.6});
   pf(c,p=>p.rect(29,37,43,26),C.orange);
   line(c,[[30,46],[71,46]],1.6,dark(C.orange,.35));line(c,[[30,54],[71,54]],1.6,dark(C.orange,.35));
   pf(c,p=>{p.moveTo(72,37);p.lineTo(92,50);p.lineTo(72,63);p.closePath()},C.skin,{wash:.6});
   pf(c,p=>{p.moveTo(85.5,46);p.lineTo(92,50);p.lineTo(85.5,54);p.closePath()},C.orange,{ol:3});
   c.save();c.translate(50,50);c.rotate(.72);face(c,0,0,12);c.restore();
 }),
 // 1 smiling star (yellow)
 c=>{pf(c,p=>star(p,50,53,42,.5),C.yellow,{col2:'#d99a12'});face(c,50,55,15)},
 // 2 scissors (blue handles, grey blades)
 c=>{
   pf(c,p=>{p.moveTo(45,60);p.lineTo(66,8);p.quadraticCurveTo(71,9,70,14);p.lineTo(56,62);p.closePath()},C.grey,{sp:4});
   pf(c,p=>{p.moveTo(55,60);p.lineTo(34,8);p.quadraticCurveTo(29,9,30,14);p.lineTo(44,62);p.closePath()},C.grey,{sp:4});
   pf(c,p=>{p.arc(33,75,16,0,7);p.moveTo(42,75);p.arc(33,75,8,0,7,true)},C.blue,{rule:'evenodd'});
   pf(c,p=>{p.arc(67,75,16,0,7);p.moveTo(76,75);p.arc(67,75,8,0,7,true)},C.blue,{rule:'evenodd'});
   c.beginPath();c.arc(50,47,4.5,0,7);c.fillStyle=mix(C.grey,.5);c.fill();c.lineWidth=3;c.strokeStyle=OUT;c.stroke();
 },
 // 3 paperclip (silver)
 c=>rot(c,.35,()=>{
   const path=p=>{p.moveTo(42,34);p.lineTo(42,70);p.arc(51,70,9,Math.PI,0,true);p.lineTo(60,22);p.arc(48,22,12,0,Math.PI,true);p.lineTo(36,76);p.arc(52,76,16,Math.PI,0,true);p.lineTo(68,30)};
   c.beginPath();path(c);c.lineWidth=13;c.strokeStyle=OUT;c.lineCap='round';c.lineJoin='round';c.stroke();
   c.beginPath();path(c);c.lineWidth=6.5;c.strokeStyle=mix(C.grey,.75);c.stroke();
   c.save();c.translate(1,1);c.beginPath();path(c);c.lineWidth=2;c.strokeStyle=dark(C.grey,.15);c.setLineDash([3,3]);c.stroke();c.restore();
 }),
 // 4 eraser (pink)
 c=>rot(c,-.28,()=>{
   pf(c,p=>{p.moveTo(14,40);p.lineTo(26,28);p.lineTo(90,28);p.lineTo(78,40);p.closePath()},C.pink,{wash:.18,a:.6});
   pf(c,p=>{p.moveTo(78,40);p.lineTo(90,28);p.lineTo(90,58);p.lineTo(78,72);p.closePath()},C.pink,{wash:.5});
   pf(c,p=>rr(p,14,40,64,32,3),C.pink);
   face(c,46,57,13);
 }),
 // 5 ruler (wood brown)
 c=>rot(c,-.62,()=>{
   pf(c,p=>rr(p,4,36,92,28,4),C.brown,{wash:.28});
   for(let i=0;i<=16;i++){const x=10+i*5;line(c,[[x,36],[x,36+(i%4?7:i%2?10:13)]],2)}
   c.beginPath();c.arc(88,55,3,0,7);c.lineWidth=2.4;c.strokeStyle=OUT;c.stroke();
 }),
 // 6 crayon (purple)
 c=>rot(c,.72,()=>{
   pf(c,p=>rr(p,10,37,14,26,[5,0,0,5]),C.purple,{wash:.45});
   pf(c,p=>p.rect(24,37,46,26),C.purple,{wash:.12,a:.55});
   c.save();c.beginPath();c.rect(24,37,46,26);c.clip();
   for(const x of[28,62]){pf(c,p=>{p.moveTo(x,37);p.lineTo(x+6,37);p.lineTo(x+6,63);p.lineTo(x,63);p.closePath()},C.purple,{ol:2.2})}c.restore();
   c.beginPath();c.rect(24,37,46,26);c.lineWidth=OL;c.strokeStyle=OUT;c.stroke();
   pf(c,p=>{p.moveTo(70,39);p.lineTo(86,45);p.quadraticCurveTo(91,50,86,55);p.lineTo(70,61);p.closePath()},C.purple,{wash:.5});
   c.save();c.translate(47,50);c.rotate(-.72);face(c,0,0,11);c.restore();
 }),
 // 7 paintbrush (teal handle, red paint)
 c=>rot(c,-.78,()=>{
   pf(c,p=>{p.moveTo(6,45);p.quadraticCurveTo(3,50,6,55);p.lineTo(52,60);p.lineTo(52,40);p.closePath()},C.teal);
   pf(c,p=>p.rect(52,39,14,22),C.grey,{sp:3.6});
   line(c,[[57,39],[57,61]],1.6);line(c,[[61,39],[61,61]],1.6);
   pf(c,p=>{p.moveTo(66,39);p.quadraticCurveTo(86,36,97,50);p.quadraticCurveTo(86,64,66,61);p.closePath()},C.red);
 }),
 // 8 heart (red)
 c=>{pf(c,p=>{p.moveTo(50,88);p.bezierCurveTo(20,66,6,50,8,32);p.bezierCurveTo(10,14,34,8,50,28);p.bezierCurveTo(66,8,90,14,92,32);p.bezierCurveTo(94,50,80,66,50,88);p.closePath()},C.red);
   c.beginPath();c.arc(30,32,10,3.6,4.6);c.lineWidth=3.2;c.strokeStyle=OUT;c.stroke()},
 // 9 rainbow (all colours)
 c=>{
   const cols=[C.red,C.orange,C.yellow,C.green,C.blue],R0=45,w=6.4;
   cols.forEach((col,i)=>{const r1=R0-i*w,r2=r1-w;pf(c,p=>{p.arc(50,70,r1,Math.PI,0);p.arc(50,70,r2,0,Math.PI,true);p.closePath()},col,{sp:3.6,hl:1.6,ol:2.6,wash:.45})});
   const cloud=(x)=>pf(c,p=>{p.arc(x-8,74,8,Math.PI*.5,Math.PI*1.5);p.arc(x,66,10,Math.PI,Math.PI*2);p.arc(x+9,74,8,Math.PI*1.5,Math.PI*.5);p.closePath()},C.sky,{wash:.08,a:.45});
   cloud(20);cloud(80);
 },
 // 10 notebook (green)
 c=>{
   pf(c,p=>rr(p,22,12,62,78,6),C.green);
   pf(c,p=>rr(p,38,26,36,16,3),C.white,{wash:.0,a:0,ol:3});
   line(c,[[43,32],[69,32]],1.8);line(c,[[43,37],[62,37]],1.8);
   for(let i=0;i<6;i++){const y=20+i*12.5;c.beginPath();c.ellipse(22,y,7,3.4,0,0,7);c.lineWidth=7.5;c.strokeStyle=OUT;c.stroke();c.lineWidth=3.6;c.strokeStyle=mix(C.grey,.6);c.stroke()}
   c.save();c.translate(56,66);face(c,0,0,14);c.restore();
 },
 // 11 music notes (ink)
 c=>{
   pf(c,p=>{p.moveTo(36,24);p.lineTo(82,12);p.lineTo(82,24);p.lineTo(36,36);p.closePath()},C.ink,{wash:.7,col2:'#16161a'});
   pf(c,p=>p.rect(32,30,6,46),C.ink,{wash:.7,ol:3.6});pf(c,p=>p.rect(78,18,6,46),C.ink,{wash:.7,ol:3.6});
   pf(c,p=>p.ellipse(26,78,13,10,-.4,0,7),C.ink,{wash:.7,col2:'#16161a'});
   pf(c,p=>p.ellipse(72,66,13,10,-.4,0,7),C.ink,{wash:.7,col2:'#16161a'});
   c.beginPath();c.arc(22,75,4,3.4,4.6);c.arc(68,63,4,3.4,4.6);c.lineWidth=2.4;c.strokeStyle='#f4f1e8';c.stroke();
 },
 // 12 rocket (white body, red nose and fins)
 c=>rot(c,.62,()=>{
   pf(c,p=>{p.moveTo(43,82);p.lineTo(50,98);p.lineTo(57,82);p.closePath()},C.orange,{col2:C.yellow});
   pf(c,p=>{p.moveTo(36,60);p.lineTo(24,84);p.lineTo(38,80);p.closePath()},C.red);
   pf(c,p=>{p.moveTo(64,60);p.lineTo(76,84);p.lineTo(62,80);p.closePath()},C.red);
   pf(c,p=>{p.moveTo(50,4);p.bezierCurveTo(70,20,66,60,62,84);p.lineTo(38,84);p.bezierCurveTo(34,60,30,20,50,4);p.closePath()},C.white,{wash:.0,a:.35});
   pf(c,p=>{p.moveTo(50,4);p.bezierCurveTo(58,10,62,18,63.5,26);p.lineTo(36.5,26);p.bezierCurveTo(38,18,42,10,50,4);p.closePath()},C.red);
   pf(c,p=>p.arc(50,46,9,0,7),C.sky,{wash:.4});
 }),
 // 13 cloud (sky blue)
 c=>{pf(c,p=>{p.moveTo(18,74);p.arc(20,58,16,Math.PI*.6,Math.PI*1.45);p.arc(42,40,20,Math.PI*1.1,Math.PI*1.85);p.arc(68,44,17,Math.PI*1.3,Math.PI*1.95);p.arc(80,60,14,Math.PI*1.5,Math.PI*.45);p.closePath()},C.sky);
   face(c,50,60,15)},
 // 14 lightning bolt (yellow + orange)
 c=>{pf(c,p=>{p.moveTo(60,4);p.lineTo(20,54);p.lineTo(46,54);p.lineTo(34,96);p.lineTo(82,38);p.lineTo(54,38);p.lineTo(70,4);p.closePath()},C.yellow,{col2:C.orange})},
 // 15 balloon (lime)
 c=>{line(c,[[52,76],[46,84],[56,90],[48,98]],2.6);
   pf(c,p=>{p.moveTo(52,72);p.lineTo(46,80);p.lineTo(58,80);p.closePath()},C.lime,{ol:3.4});
   pf(c,p=>p.ellipse(52,40,28,34,0,0,7),C.lime,{col2:'#5f9a22'});
   c.beginPath();c.arc(44,30,14,3.5,4.4);c.lineWidth=3.2;c.strokeStyle=OUT;c.stroke()},
];
const NAMES=['pencil','star','scissors','paperclip','eraser','ruler','crayon','paintbrush','heart','rainbow','notebook','music note','rocket','cloud','lightning bolt','balloon'];

function iconSheet(cell){
  const cv=document.createElement('canvas');cv.width=cv.height=cell*4;const c=cv.getContext('2d');
  ICONS.forEach((f,i)=>{c.save();c.translate((i%4)*cell,Math.floor(i/4)*cell);c.scale(cell/100,cell/100);
    const k=.96*(BOOST[i]||1);c.translate(50,50);c.scale(k,k);c.translate(-50,-50);f(c);c.restore()});
  return cv.toDataURL('image/png');
}
// the paper tile face: rounded square on a darker paper edge, outlined in ink
function tile(w,h){
  const cv=document.createElement('canvas');cv.width=w;cv.height=h;const c=cv.getContext('2d');const k=w/240;c.scale(k,k);
  const lw=5;
  c.beginPath();c.roundRect(4,14,232,214,34);c.fillStyle='#ddd8cb';c.fill();
  c.save();c.clip();c.strokeStyle='rgba(60,60,66,.35)';c.lineWidth=2;c.beginPath();for(let s=-240;s<240;s+=9){c.moveTo(s,230);c.lineTo(s+240,-10)}c.stroke();c.restore();
  c.beginPath();c.roundRect(4,14,232,214,34);c.lineWidth=lw;c.strokeStyle=OUT;c.stroke();
  c.beginPath();c.roundRect(4,4,232,206,34);c.fillStyle='#fbf9f3';c.fill();c.lineWidth=lw;c.stroke();
  c.beginPath();c.roundRect(16,14,208,186,26);c.lineWidth=1.6;c.strokeStyle='rgba(60,60,66,.25)';c.stroke();
  return cv.toDataURL('image/png');
}
// the 7-slot tray as a giant yellow pencil lying on its side. Slot boxes match the CSS (left %, width 10.37%, top 17.1%, height 55.1%).
function tray(W,H){
  const cv=document.createElement('canvas');cv.width=W;cv.height=H;const c=cv.getContext('2d');
  c.scale(W/1000,H/190);
  const top=8,bot=166;SP=12;HL=3.2;OL=6;
  c.fillStyle='rgba(46,46,51,.18)';c.beginPath();c.ellipse(500,176,480,10,0,0,7);c.fill();
  pf(c,p=>rr(p,6,top+6,44,bot-top-12,[26,0,0,26]),C.pink);
  pf(c,p=>p.rect(48,top+2,26,bot-top-4),C.grey,{sp:8});
  for(const x of[56,66])line(c,[[x,top+4],[x,bot-4]],3);
  pf(c,p=>p.rect(74,top,846,bot-top),C.yellow,{col2:'#d99a12',wash:.35});
  line(c,[[76,top+(bot-top)*.2],[918,top+(bot-top)*.2]],3,'#c58a10');line(c,[[76,top+(bot-top)*.86],[918,top+(bot-top)*.86]],3,'#c58a10');
  pf(c,p=>{p.moveTo(920,top);p.lineTo(994,(top+bot)/2);p.lineTo(920,bot);p.closePath()},C.skin,{wash:.55});
  pf(c,p=>{p.moveTo(970,(top+bot)/2-14);p.lineTo(994,(top+bot)/2);p.lineTo(970,(top+bot)/2+14);p.closePath()},'#55555c',{ol:5});
  const L=[8.85,20.79,32.79,44.69,56.63,68.53,80.43];
  for(const l of L){const x=l*10,y=190*.171,w=103.7,h=190*.551;
    c.beginPath();c.roundRect(x-3,y-3,w+6,h+6,14);c.fillStyle='#efebe0';c.fill();
    c.save();c.clip();c.strokeStyle='rgba(60,60,66,.3)';c.lineWidth=2;c.beginPath();for(let s=-120;s<120;s+=8){c.moveTo(x+s,y+h);c.lineTo(x+s+h,y)}c.stroke();
    c.beginPath();c.rect(x,y+14,w,h);c.fillStyle='#f7f4ec';c.fill();c.restore();
    c.beginPath();c.roundRect(x-3,y-3,w+6,h+6,14);c.lineWidth=5;c.strokeStyle=OUT;c.stroke()}
  SP=5.4;HL=2.1;OL=5.6;
  return cv.toDataURL('image/png');
}
// page background: ruled notebook paper with a red margin line and a few coloured doodles in the corners (transparent paper)
function page(W,H){
  const cv=document.createElement('canvas');cv.width=W;cv.height=H;const c=cv.getContext('2d');
  c.strokeStyle='rgba(58,123,213,.16)';c.lineWidth=2;for(let y=60;y<H;y+=44){c.beginPath();c.moveTo(0,y);c.lineTo(W,y);c.stroke()}
  c.strokeStyle='rgba(224,69,58,.32)';c.lineWidth=2.5;for(const x of[96,101]){c.beginPath();c.moveTo(x,0);c.lineTo(x,H);c.stroke()}
  const d=(x,y,s,a,f)=>{c.save();c.globalAlpha=.55;c.translate(x,y);c.rotate(a);c.scale(s/100,s/100);c.translate(-50,-50);f(c);c.restore()};
  SP=7;HL=2.4;OL=5;
  d(40,150,64,-.3,ICONS[1]);d(40,330,52,.2,ICONS[8]);d(680,210,60,.2,ICONS[13]);d(670,420,56,-.2,ICONS[14]);
  d(42,1000,58,.3,ICONS[12]);d(675,1060,60,-.1,ICONS[15]);d(45,1180,54,-.2,ICONS[11]);d(670,1215,52,.25,ICONS[9]);
  // a pencil swirl and some dashes
  c.save();c.globalAlpha=.45;c.strokeStyle=OUT;c.lineWidth=3;c.lineCap='round';c.beginPath();for(let i=0;i<120;i++){const a=i*.16,r=2+i*.22;c.lineTo(670+Math.cos(a)*r,640+Math.sin(a)*r)}c.stroke();
  c.beginPath();c.moveTo(20,640);c.quadraticCurveTo(40,620,60,640);c.quadraticCurveTo(80,660,100,640);c.stroke();c.restore();
  SP=5.4;HL=2.1;OL=5.6;
  return cv.toDataURL('image/png');
}
function preview(){
  const cell=200,cv=document.createElement('canvas');cv.width=cell*4;cv.height=cell*4+40;const c=cv.getContext('2d');
  c.fillStyle='#f6f3ea';c.fillRect(0,0,cv.width,cv.height);
  ICONS.forEach((f,i)=>{c.save();c.translate((i%4)*cell+10,Math.floor(i/4)*cell+10);c.scale(1.8,1.8);f(c);c.restore();
    c.fillStyle=OUT;c.font='18px sans-serif';c.textAlign='center';c.fillText(i+' '+NAMES[i],(i%4)*cell+cell/2,Math.floor(i/4)*cell+cell-4)});
  return cv.toDataURL('image/png');
}
"""

def png(data_url):
    return Image.open(io.BytesIO(base64.b64decode(data_url.split(',', 1)[1]))).convert('RGBA')

def main():
    sheet = sys.argv[sys.argv.index('--sheet') + 1] if '--sheet' in sys.argv else None
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        pg.set_content('<html><body></body></html>')
        pg.add_script_tag(content=JS)
        icons = png(pg.evaluate('iconSheet(256)'))
        tile = png(pg.evaluate('tile(480,464)'))
        tray = png(pg.evaluate('tray(1967,374)')).resize((1000, 190), Image.LANCZOS)
        page = png(pg.evaluate('page(720,1280)'))
        prev = png(pg.evaluate('preview()')) if sheet else None
        b.close()
    icons.save(os.path.join(OUT, 'icons.webp'), quality=90, method=6)
    tile.save(os.path.join(OUT, 'tile.webp'), quality=90, method=6)
    tray.save(os.path.join(OUT, 'tray.webp'), quality=90, method=6)
    page.save(os.path.join(OUT, 'notebook.webp'), quality=88, method=6)
    if prev: prev.save(sheet)
    print('wrote icons.webp tile.webp tray.webp notebook.webp')

if __name__ == '__main__':
    main()
