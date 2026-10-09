#!/usr/bin/env python3
"""Draws the shared classroom icon set (and the scene art around it) for No. 2 Pencil and Drop Swap.

The icons use the same coloured-pencil style as tools/margin-match-art.py (dark ink outline, pale wash, two sets of
diagonal pencil hatching, the second a shade darker) and reuse several of its drawings (pencil, scissors, paperclip,
eraser, ruler, crayon, paintbrush, notebook, star). Each icon also has a plain graphite version: same drawing, every
colour turned to pencil grey, a lighter and thinner outline, softer hatching.

Writes
  src/assets/no-2-pencil/icons-color.webp     6x4 sheet of the 24 icons in colour (order = NAMES below)
  src/assets/no-2-pencil/icons-graphite.webp  the same sheet in plain graphite
  src/assets/no-2-pencil/notebook.webp        page background: ruled notebook paper with faint graphite doodles
  src/assets/drop-swap/<piece>.webp           the six match-3 pieces, the scissors and palette specials, the scribble goal chip
  src/assets/drop-swap/room-*.webp            "My Classroom" background and the nine decorations
Drawn with <canvas> in headless Chromium (Playwright), saved with Pillow; numpy trims sprite margins.
Usage: python3 tools/classroom-icons-art.py [--sheet out.png] [--scene out.png]
"""
import base64, io, os, sys
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_N2 = os.path.join(ROOT, 'src', 'assets', 'no-2-pencil')
OUT_DS = os.path.join(ROOT, 'src', 'assets', 'drop-swap')

JS = r"""
const OUT0='#1f1f22',OUTG='#4e4e55';let OUT=OUT0,MODE='c';
const C={red:'#e0453a',orange:'#f08a24',yellow:'#f2c230',lime:'#8bc34a',green:'#4caf50',teal:'#2fa7a0',sky:'#4fb3e8',blue:'#3a7bd5',
  purple:'#8e5bc9',pink:'#e86aa6',brown:'#9b6a3c',grey:'#9aa0a6',skin:'#f2c9a5',white:'#c9c4b8',ink:'#3a3a44',gold:'#d99a12',paper:'#fbf9f3'};
function rgb(h){if(Array.isArray(h))return h;if(h[0]==='#')return[parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)];
  return h.match(/[\d.]+/g).slice(0,3).map(Number)}
// S(): colour to CSS, turned into pencil grey in graphite mode
function S(h){let a=rgb(h);if(MODE==='g'){const l=.299*a[0]+.587*a[1]+.114*a[2],g=Math.round(70+l*.72);a=[g-2,g-1,g+3]}return'rgb('+a.map(Math.round).join(',')+')'}
function mixA(h,k){const a=rgb(h),b=[250,248,241];return a.map((v,i)=>b[i]+(v-b[i])*k)}
function darkA(h,k){return rgb(h).map(v=>v*(1-(k==null?.25:k)))}
let SP=5.4,HL=2.1,OL=5.6,HB={x0:-80,y0:-80,x1:180,y1:180};
const j=(i)=>Math.sin(i*12.9898)*0.6;
// pale wash + two sets of diagonal pencil lines (second set darker) clipped to the path, then the outline
function pf(c,path,col,o){
  o=o||{};const sp=o.sp||SP,g=MODE==='g';
  c.save();c.beginPath();path(c);c.fillStyle=S(mixA(col,o.wash==null?.32:o.wash));c.fill(o.rule||'nonzero');c.clip(o.rule||'nonzero');
  c.lineCap='round';c.lineWidth=(o.hl||HL)*(g?.8:1);c.globalAlpha=(o.a==null?1:o.a)*(g?.7:1);
  const {x0,y0,x1,y1}=HB,hh=y1-y0;
  c.strokeStyle=S(col);c.beginPath();for(let s=x0-hh,i=0;s<x1;s+=sp,i++){c.moveTo(s+j(i),y1);c.lineTo(s+hh+j(i+3),y0)}c.stroke();
  if(!g||o.both){c.strokeStyle=S(o.col2||darkA(col));c.beginPath();for(let s=x0+sp*.4,i=0;s<x1+hh;s+=sp*1.3,i++){c.moveTo(s+j(i),y1);c.lineTo(s-hh+j(i+5),y0)}c.stroke()}
  c.restore();
  if(o.ol!==0){c.beginPath();path(c);c.strokeStyle=OUT;c.lineWidth=(o.ol||OL)*(g?.6:1);c.lineJoin='round';c.lineCap='round';c.stroke()}
}
function line(c,pts,w,col){c.beginPath();pts.forEach((p,i)=>i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]));c.lineWidth=w*(MODE==='g'&&!col?.65:1);c.strokeStyle=col?S(col):OUT;c.lineCap='round';c.lineJoin='round';c.stroke()}
function dot(c,x,y,r,col){c.beginPath();c.arc(x,y,r,0,7);c.fillStyle=col?S(col):OUT;c.fill()}
function face(c,x,y,s){c.fillStyle=OUT;c.beginPath();c.arc(x-s*.42,y-s*.12,s*.15,0,7);c.arc(x+s*.42,y-s*.12,s*.15,0,7);c.fill();
  c.beginPath();c.arc(x,y+s*.05,s*.36,.35,Math.PI-.35);c.lineWidth=s*.13;c.strokeStyle=OUT;c.lineCap='round';c.stroke()}
function rot(c,a,f,cx,cy){cx=cx??50;cy=cy??50;c.save();c.translate(cx,cy);c.rotate(a);c.translate(-cx,-cy);f();c.restore()}
function star(c,x,y,r,rr){for(let i=0;i<10;i++){const a=-Math.PI/2+i*Math.PI/5,q=i%2?r*(rr||.5):r;c.lineTo(x+Math.cos(a)*q,y+Math.sin(a)*q)}c.closePath()}
function rr(c,x,y,w,h,r){c.roundRect(x,y,w,h,r)}
function ring(c,x,y,r,w,col){c.beginPath();c.arc(x,y,r,0,7);c.lineWidth=w;c.strokeStyle=OUT;c.stroke();c.lineWidth=w*.45;c.strokeStyle=S(col);c.stroke()}
// tiny stroke font for chalk writing and banner letters (10 x 14 box)
const GL={A:[[[0,14],[5,0],[10,14]],[[2,8],[8,8]]],B:[[[0,14],[0,0],[6,0],[9,2],[9,5],[6,7],[0,7]],[[6,7],[10,9],[10,12],[7,14],[0,14]]],
  C:[[[10,2],[7,0],[3,0],[0,4],[0,10],[3,14],[7,14],[10,12]]],D:[[[0,0],[0,14],[5,14],[9,11],[10,7],[9,3],[5,0],[0,0]]],
  E:[[[10,0],[0,0],[0,14],[10,14]],[[0,7],[7,7]]],F:[[[10,0],[0,0],[0,14]],[[0,7],[7,7]]],G:[[[10,2],[7,0],[3,0],[0,4],[0,10],[3,14],[8,14],[10,11],[10,8],[6,8]]],
  '1':[[[2,3],[5,0],[5,14]],[[2,14],[8,14]]],'2':[[[0,3],[2,0],[8,0],[10,3],[9,6],[0,14],[10,14]]],
  '3':[[[0,1],[8,0],[10,3],[7,6],[3,7],[7,7],[10,10],[9,13],[6,14],[0,13]]],'4':[[[7,14],[7,0],[0,10],[10,10]]],
  '+':[[[5,3],[5,11]],[[1,7],[9,7]]],'=':[[[1,5],[9,5]],[[1,9],[9,9]]]};
function write(c,s,x,y,h,w,col){const k=h/14;let cx=x;for(const ch of s){const g=GL[ch];if(g)g.forEach(pl=>line(c,pl.map(p=>[cx+p[0]*k,y+p[1]*k]),w,col));cx+=k*14}}

const ICONS=[
 // 0 pencil (yellow, the classic No. 2)
 c=>rot(c,-.72,()=>{
   pf(c,p=>rr(p,10,38,12,24,[6,0,0,6]),C.pink);
   pf(c,p=>p.rect(21,37,8,26),C.grey,{sp:3.6});
   pf(c,p=>p.rect(29,37,43,26),C.yellow,{col2:C.gold,wash:.4});
   line(c,[[30,46],[71,46]],1.6,darkA(C.yellow,.35));line(c,[[30,54],[71,54]],1.6,darkA(C.yellow,.35));
   pf(c,p=>{p.moveTo(72,37);p.lineTo(92,50);p.lineTo(72,63);p.closePath()},C.skin,{wash:.6});
   pf(c,p=>{p.moveTo(85.5,46);p.lineTo(92,50);p.lineTo(85.5,54);p.closePath()},C.ink,{ol:3});
   c.save();c.translate(50,50);c.rotate(.72);face(c,0,0,12);c.restore();
 }),
 // 1 apple (red)
 c=>{
   pf(c,p=>{p.moveTo(46,32);p.quadraticCurveTo(46,18,53,7);p.lineTo(59,9);p.quadraticCurveTo(53,20,54,32);p.closePath()},C.brown,{ol:3.6});
   pf(c,p=>{p.moveTo(50,30);p.bezierCurveTo(36,16,6,20,9,52);p.bezierCurveTo(11,80,32,98,50,89);p.bezierCurveTo(68,98,89,80,91,52);p.bezierCurveTo(94,20,64,16,50,30);p.closePath()},C.red);
   pf(c,p=>{p.moveTo(56,21);p.quadraticCurveTo(68,3,88,10);p.quadraticCurveTo(76,30,56,21);p.closePath()},C.green,{ol:3.6});
   line(c,[[60,19],[78,12]],1.8);
   c.beginPath();c.arc(32,50,15,3.4,4.4);c.lineWidth=3.4;c.strokeStyle=OUT;c.lineCap='round';c.stroke();
 },
 // 2 book (blue, closed, red bookmark)
 c=>{
   pf(c,p=>{p.moveTo(60,84);p.lineTo(69,84);p.lineTo(69,98);p.lineTo(64.5,93);p.lineTo(60,98);p.closePath()},C.red,{ol:3});
   pf(c,p=>rr(p,22,15,64,78,[2,7,7,2]),C.white,{wash:0,a:0,ol:4});
   for(let y=22;y<90;y+=5)line(c,[[79,y],[84,y]],1.3);
   pf(c,p=>rr(p,12,8,66,80,[5,6,6,5]),C.blue);
   pf(c,p=>rr(p,12,8,13,80,[5,0,0,5]),C.blue,{wash:.55,col2:darkA(C.blue,.45),ol:4});
   pf(c,p=>rr(p,34,22,34,18,3),C.white,{wash:0,a:0,ol:3});
   line(c,[[39,28],[63,28]],2);line(c,[[39,34],[56,34]],2);
 },
 // 3 backpack (green)
 c=>{
   c.beginPath();c.moveTo(39,26);c.bezierCurveTo(38,4,62,4,61,26);c.lineWidth=MODE==='g'?6:10;c.strokeStyle=OUT;c.lineCap='round';c.stroke();
   c.lineWidth=4;c.strokeStyle=S(darkA(C.green,.3));c.stroke();
   pf(c,p=>rr(p,16,20,68,76,[28,28,10,10]),C.green);
   c.beginPath();c.moveTo(20,46);c.quadraticCurveTo(50,56,80,46);c.lineWidth=MODE==='g'?2.2:3.4;c.strokeStyle=OUT;c.stroke();
   pf(c,p=>rr(p,27,60,46,28,8),C.green,{wash:.55,col2:darkA(C.green,.45),ol:4});
   line(c,[[31,68],[69,68]],2.2);pf(c,p=>rr(p,60,66,6,10,2),C.grey,{ol:2.2});
   pf(c,p=>rr(p,44,40,12,12,3),C.yellow,{ol:3});
 },
 // 4 crayon (purple)
 c=>rot(c,.72,()=>{
   pf(c,p=>rr(p,10,37,14,26,[5,0,0,5]),C.purple,{wash:.45});
   pf(c,p=>p.rect(24,37,46,26),C.purple,{wash:.12,a:.55});
   c.save();c.beginPath();c.rect(24,37,46,26);c.clip();
   for(const x of[28,62]){pf(c,p=>{p.moveTo(x,37);p.lineTo(x+6,37);p.lineTo(x+6,63);p.lineTo(x,63);p.closePath()},C.purple,{ol:2.2})}c.restore();
   c.beginPath();c.rect(24,37,46,26);c.lineWidth=OL*(MODE==='g'?.6:1);c.strokeStyle=OUT;c.stroke();
   pf(c,p=>{p.moveTo(70,39);p.lineTo(86,45);p.quadraticCurveTo(91,50,86,55);p.lineTo(70,61);p.closePath()},C.purple,{wash:.5});
   c.save();c.translate(47,50);c.rotate(-.72);face(c,0,0,11);c.restore();
 }),
 // 5 gold-star sticker (orange)
 c=>{pf(c,p=>star(p,50,53,44,.5),C.orange,{col2:'#c9650f'});face(c,50,55,15)},
 // 6 scissors (blue handles, grey blades)
 c=>{
   pf(c,p=>{p.moveTo(45,60);p.lineTo(66,8);p.quadraticCurveTo(71,9,70,14);p.lineTo(56,62);p.closePath()},C.grey,{sp:4});
   pf(c,p=>{p.moveTo(55,60);p.lineTo(34,8);p.quadraticCurveTo(29,9,30,14);p.lineTo(44,62);p.closePath()},C.grey,{sp:4});
   pf(c,p=>{p.arc(33,75,16,0,7);p.moveTo(42,75);p.arc(33,75,8,0,7,true)},C.blue,{rule:'evenodd'});
   pf(c,p=>{p.arc(67,75,16,0,7);p.moveTo(76,75);p.arc(67,75,8,0,7,true)},C.blue,{rule:'evenodd'});
   c.beginPath();c.arc(50,47,4.5,0,7);c.fillStyle=S(mixA(C.grey,.5));c.fill();c.lineWidth=3;c.strokeStyle=OUT;c.stroke();
 },
 // 7 paperclip (silver)
 c=>rot(c,.35,()=>{
   const path=p=>{p.moveTo(42,34);p.lineTo(42,70);p.arc(51,70,9,Math.PI,0,true);p.lineTo(60,22);p.arc(48,22,12,0,Math.PI,true);p.lineTo(36,76);p.arc(52,76,16,Math.PI,0,true);p.lineTo(68,30)};
   c.beginPath();path(c);c.lineWidth=MODE==='g'?11:13;c.strokeStyle=OUT;c.lineCap='round';c.lineJoin='round';c.stroke();
   c.beginPath();path(c);c.lineWidth=MODE==='g'?7:6.5;c.strokeStyle=S(mixA(C.grey,.75));c.stroke();
   c.save();c.translate(1,1);c.beginPath();path(c);c.lineWidth=2;c.strokeStyle=S(darkA(C.grey,.15));c.setLineDash([3,3]);c.stroke();c.restore();
 }),
 // 8 eraser (pink)
 c=>rot(c,-.28,()=>{
   pf(c,p=>{p.moveTo(14,40);p.lineTo(26,28);p.lineTo(90,28);p.lineTo(78,40);p.closePath()},C.pink,{wash:.18,a:.6});
   pf(c,p=>{p.moveTo(78,40);p.lineTo(90,28);p.lineTo(90,58);p.lineTo(78,72);p.closePath()},C.pink,{wash:.5});
   pf(c,p=>rr(p,14,40,64,32,3),C.pink);
   face(c,46,57,13);
 }),
 // 9 ruler (wood brown)
 c=>rot(c,-.62,()=>{
   pf(c,p=>rr(p,4,36,92,28,4),C.brown,{wash:.28});
   for(let i=0;i<=16;i++){const x=10+i*5;line(c,[[x,36],[x,36+(i%4?7:i%2?10:13)]],2)}
   c.beginPath();c.arc(88,55,3,0,7);c.lineWidth=2.4;c.strokeStyle=OUT;c.stroke();
 }),
 // 10 paintbrush (teal handle, red paint)
 c=>rot(c,-.78,()=>{
   pf(c,p=>{p.moveTo(6,45);p.quadraticCurveTo(3,50,6,55);p.lineTo(52,60);p.lineTo(52,40);p.closePath()},C.teal);
   pf(c,p=>p.rect(52,39,14,22),C.grey,{sp:3.6});
   line(c,[[57,39],[57,61]],1.6);line(c,[[61,39],[61,61]],1.6);
   pf(c,p=>{p.moveTo(66,39);p.quadraticCurveTo(86,36,97,50);p.quadraticCurveTo(86,64,66,61);p.closePath()},C.red);
 }),
 // 11 spiral notebook (lime)
 c=>{
   pf(c,p=>rr(p,22,10,64,82,6),C.lime,{col2:'#5f9a22'});
   pf(c,p=>rr(p,38,24,38,17,3),C.white,{wash:0,a:0,ol:3});
   line(c,[[43,30],[70,30]],1.8);line(c,[[43,35.5],[63,35.5]],1.8);
   for(let i=0;i<6;i++){const y=19+i*13;c.beginPath();c.ellipse(22,y,7,3.4,0,0,7);c.lineWidth=MODE==='g'?5.5:7.5;c.strokeStyle=OUT;c.stroke();c.lineWidth=3.6;c.strokeStyle=S(mixA(C.grey,.6));c.stroke()}
   c.save();c.translate(57,65);face(c,0,0,14);c.restore();
 },
 // 12 globe on a stand (sky sea, green land)
 c=>{
   pf(c,p=>p.ellipse(50,91,22,6.5,0,0,7),C.brown,{ol:4});
   pf(c,p=>p.rect(45.5,76,9,15),C.brown,{ol:3.6});
   pf(c,p=>p.arc(47,42,32,0,7),C.sky,{col2:darkA(C.sky,.3)});
   c.save();c.beginPath();c.arc(47,42,32,0,7);c.clip();
   pf(c,p=>{p.moveTo(22,20);p.bezierCurveTo(32,8,50,16,45,28);p.bezierCurveTo(41,38,52,44,43,54);p.bezierCurveTo(35,63,24,52,26,42);p.bezierCurveTo(17,37,15,27,22,20);p.closePath()},C.green,{ol:2.8});
   pf(c,p=>{p.moveTo(58,40);p.bezierCurveTo(70,32,84,42,79,55);p.bezierCurveTo(75,68,62,74,57,63);p.bezierCurveTo(53,54,51,46,58,40);p.closePath()},C.green,{ol:2.8});
   pf(c,p=>{p.moveTo(56,14);p.bezierCurveTo(64,8,74,14,70,22);p.bezierCurveTo(66,28,56,24,56,14);p.closePath()},C.green,{ol:2.8});
   c.restore();
   c.beginPath();c.arc(47,42,32,0,7);c.lineWidth=OL*(MODE==='g'?.6:1);c.strokeStyle=OUT;c.stroke();
   c.beginPath();c.arc(48,42,39,-Math.PI*.42,Math.PI*.5);c.lineWidth=MODE==='g'?6:8.5;c.strokeStyle=OUT;c.lineCap='round';c.stroke();c.lineWidth=3.4;c.strokeStyle=S(C.grey);c.stroke();
 },
 // 13 chalkboard (green board, wood frame, chalk ABC)
 c=>{
   pf(c,p=>rr(p,5,14,90,64,5),C.brown);
   pf(c,p=>rr(p,13,22,74,48,2),C.green,{col2:darkA(C.green,.45),wash:.62,ol:3.2});
   write(c,'ABC',20,30,22,3.4,'#fbf9f3');
   line(c,[[20,62],[80,62]],2,'#fbf9f3');
   pf(c,p=>rr(p,9,78,82,7,2),C.brown,{ol:3.4});
   pf(c,p=>rr(p,60,72.5,16,6,2),C.white,{wash:0,a:0,ol:2.6});
 },
 // 14 calculator (teal)
 c=>{
   pf(c,p=>rr(p,20,5,60,90,10),C.teal);
   pf(c,p=>rr(p,28,13,44,20,3),C.lime,{wash:.4,a:.45,ol:3.2});
   write(c,'123',38,17,12,2.4);
   for(let r=0;r<4;r++)for(let k=0;k<3;k++){const x=29+k*15,y=41+r*12.6,last=r===3&&k===2;
     pf(c,p=>rr(p,x,y,12,9,2.5),last?C.orange:C.white,last?{ol:2.4}:{wash:0,a:0,ol:2.4})}
 },
 // 15 school bus (yellow)
 c=>{
   pf(c,p=>{p.moveTo(5,74);p.lineTo(5,34);p.quadraticCurveTo(5,25,14,25);p.lineTo(78,25);p.quadraticCurveTo(87,25,89,34);p.lineTo(95,52);p.lineTo(95,74);p.closePath()},C.yellow,{col2:C.gold,wash:.4});
   for(let i=0;i<4;i++)pf(c,p=>rr(p,11+i*16,32,12,14,2),C.sky,{wash:.3,a:.45,ol:3});
   pf(c,p=>{p.moveTo(77,32);p.lineTo(85,32);p.lineTo(90,49);p.lineTo(77,49);p.closePath()},C.sky,{wash:.3,a:.45,ol:3});
   line(c,[[5,58],[95,58]],2.8);line(c,[[5,63],[95,63]],2.8);
   pf(c,p=>rr(p,88,64,6,5,1),C.red,{ol:2.2});
   for(const x of[25,74]){pf(c,p=>p.arc(x,76,11,0,7),C.ink,{wash:.55,col2:'#16161a'});dot(c,x,76,3.8,'#e8e4da')}
 },
 // 16 alarm clock (red)
 c=>{
   line(c,[[30,80],[21,94]],7);line(c,[[70,80],[79,94]],7);
   line(c,[[50,8],[50,22]],4);dot(c,50,8,4.5);
   pf(c,p=>{p.arc(25,24,13,Math.PI*.95,Math.PI*2.05);p.closePath()},C.red,{wash:.5});
   pf(c,p=>{p.arc(75,24,13,Math.PI*.95,Math.PI*2.05);p.closePath()},C.red,{wash:.5});
   pf(c,p=>p.arc(50,56,34,0,7),C.red);
   pf(c,p=>p.arc(50,56,24,0,7),C.white,{wash:0,a:0,ol:3.4});
   for(let i=0;i<12;i++){const a=i*Math.PI/6,r1=i%3?20:17;line(c,[[50+Math.cos(a)*r1,56+Math.sin(a)*r1],[50+Math.cos(a)*22,56+Math.sin(a)*22]],i%3?1.6:2.6)}
   line(c,[[50,56],[50,40]],3.6);line(c,[[50,56],[61,63]],3.6);dot(c,50,56,3.4);
 },
 // 17 lunchbox (orange, dome lid)
 c=>{
   c.beginPath();c.roundRect(35,12,30,22,9);c.lineWidth=MODE==='g'?6:9;c.strokeStyle=OUT;c.stroke();c.lineWidth=4;c.strokeStyle=S(C.grey);c.stroke();
   pf(c,p=>{p.moveTo(10,88);p.lineTo(10,46);p.quadraticCurveTo(10,26,50,26);p.quadraticCurveTo(90,26,90,46);p.lineTo(90,88);p.quadraticCurveTo(90,93,85,93);p.lineTo(15,93);p.quadraticCurveTo(10,93,10,88);p.closePath()},C.orange,{col2:'#c9650f'});
   line(c,[[10,50],[90,50]],3.2);
   pf(c,p=>rr(p,44,43,12,14,3),C.grey,{ol:3});
   pf(c,p=>{p.moveTo(50,86);p.bezierCurveTo(36,76,34,64,42,62);p.bezierCurveTo(46,61,49,63,50,67);p.bezierCurveTo(51,63,54,61,58,62);p.bezierCurveTo(66,64,64,76,50,86);p.closePath()},C.red,{ol:3});
 },
 // 18 paint palette (wood, five paint blobs)
 c=>{
   pf(c,p=>{p.moveTo(50,10);p.bezierCurveTo(80,8,97,30,93,52);p.bezierCurveTo(89,70,72,64,67,74);p.bezierCurveTo(61,86,66,93,47,93);p.bezierCurveTo(19,93,5,72,7,50);p.bezierCurveTo(9,25,27,10,50,10);p.closePath();
     p.moveTo(42,73);p.arc(35,73,7,0,7,true)},C.brown,{rule:'evenodd',wash:.4});
   [[27,47,C.purple],[33,28,C.red],[54,22,C.yellow],[74,29,C.blue],[80,48,C.green]].forEach(([x,y,col])=>pf(c,p=>p.ellipse(x,y,8.5,7.5,.3,0,7),col,{wash:.55,ol:3}));
 },
 // 19 pencil cup (purple, three pencils)
 c=>{
   const pen=(x,a,col)=>{c.save();c.translate(x,62);c.rotate(a);
     pf(c,p=>p.rect(-5.5,-50,11,48),col,{ol:3.2});
     pf(c,p=>{p.moveTo(-5.5,-50);p.lineTo(0,-63);p.lineTo(5.5,-50);p.closePath()},C.skin,{wash:.6,ol:3.2});
     pf(c,p=>{p.moveTo(-2,-58.5);p.lineTo(0,-63);p.lineTo(2,-58.5);p.closePath()},col,{ol:2});c.restore()};
   pen(38,-.28,C.yellow);pen(51,.02,C.red);pen(62,.3,C.blue);
   pf(c,p=>{p.moveTo(24,46);p.lineTo(76,46);p.lineTo(71,91);p.quadraticCurveTo(70,95,66,95);p.lineTo(34,95);p.quadraticCurveTo(30,95,29,91);p.closePath()},C.purple);
   line(c,[[27,56],[73,56]],2.4);
   pf(c,p=>star(p,50,75,10,.5),C.yellow,{ol:2.6});
 },
 // 20 sticky note (pink, folded corner, pinned)
 c=>rot(c,-.1,()=>{
   pf(c,p=>{p.moveTo(13,15);p.lineTo(87,15);p.lineTo(87,68);p.lineTo(68,87);p.lineTo(13,87);p.closePath()},C.pink);
   pf(c,p=>{p.moveTo(87,68);p.lineTo(68,87);p.lineTo(71,71);p.closePath()},C.pink,{wash:.65,col2:darkA(C.pink,.4),ol:3.6});
   const wig=(y,x1)=>{const pts=[];for(let x=24;x<=x1;x+=3)pts.push([x,y+Math.sin(x*.9)*1.6]);line(c,pts,2.6)};
   wig(36,72);wig(49,66);wig(62,56);
   dot(c,50,15,7.5);dot(c,50,15,4.5,C.red);
 }),
 // 21 magnifying glass (sky lens, brown handle)
 c=>{
   pf(c,p=>{p.moveTo(59,70);p.lineTo(70,59);p.lineTo(94,83);p.quadraticCurveTo(96,93,84,94);p.closePath()},C.brown);
   pf(c,p=>{p.moveTo(56,66);p.lineTo(66,56);p.lineTo(73,63);p.lineTo(63,73);p.closePath()},C.grey,{ol:3.4});
   pf(c,p=>p.arc(40,40,24,0,7),C.sky,{wash:.35,a:.5,ol:0});
   pf(c,p=>{p.arc(40,40,32,0,7);p.moveTo(64,40);p.arc(40,40,24,0,7,true)},C.grey,{rule:'evenodd'});
   c.beginPath();c.arc(40,40,15,3.5,4.5);c.lineWidth=4;c.strokeStyle='#fbf9f3';c.lineCap='round';c.stroke();
 },
 // 22 ABC block (lime front, yellow top, sky side)
 c=>{
   pf(c,p=>{p.moveTo(12,30);p.lineTo(34,12);p.lineTo(88,12);p.lineTo(66,30);p.closePath()},C.yellow,{wash:.45});
   pf(c,p=>{p.moveTo(66,30);p.lineTo(88,12);p.lineTo(88,68);p.lineTo(66,90);p.closePath()},C.sky,{wash:.45});
   pf(c,p=>rr(p,12,30,54,60,2),C.lime,{col2:'#5f9a22'});
   write(c,'A',26,40,40,6.5);
 },
 // 23 trophy (gold)
 c=>{
   for(const x of[22,78])pf(c,p=>{p.arc(x,30,13,0,7);p.moveTo(x+7,30);p.arc(x,30,7,0,7,true)},C.yellow,{rule:'evenodd',col2:C.gold});
   pf(c,p=>{p.moveTo(21,10);p.lineTo(79,10);p.bezierCurveTo(79,44,65,58,50,58);p.bezierCurveTo(35,58,21,44,21,10);p.closePath()},C.yellow,{col2:C.gold,wash:.4});
   pf(c,p=>p.rect(44,57,12,13),C.yellow,{col2:C.gold,ol:3.6});
   pf(c,p=>rr(p,31,69,38,9,2),C.yellow,{col2:C.gold,ol:4});
   pf(c,p=>rr(p,22,78,56,15,3),C.brown);
   pf(c,p=>star(p,50,31,11,.5),C.orange,{ol:2.8});
 },
];
const NAMES=['pencil','apple','book','backpack','crayon','star sticker','scissors','paperclip','eraser','ruler','paintbrush','notebook',
  'globe','chalkboard','calculator','school bus','alarm clock','lunchbox','paint palette','pencil cup','sticky note','magnifying glass','ABC block','trophy'];
const BOOST={0:1.1,4:1.08,7:1.12,9:1.04,10:1.1};

function drawIcon(c,i,mode){MODE=mode;OUT=mode==='g'?OUTG:OUT0;c.save();const k=.96*(BOOST[i]||1);c.translate(50,50);c.scale(k,k);c.translate(-50,-50);ICONS[i](c);c.restore();MODE='c';OUT=OUT0}
function iconSheet(cell,mode){
  const cv=document.createElement('canvas');cv.width=cell*6;cv.height=cell*4;const c=cv.getContext('2d');
  ICONS.forEach((f,i)=>{c.save();c.translate((i%6)*cell,Math.floor(i/6)*cell);c.scale(cell/100,cell/100);drawIcon(c,i,mode);c.restore()});
  return cv.toDataURL('image/png');
}
function one(i,px,mode){const cv=document.createElement('canvas');cv.width=cv.height=px;const c=cv.getContext('2d');c.scale(px/100,px/100);drawIcon(c,i,mode||'c');return cv.toDataURL('image/png')}
// scribble goal chip: a loopy graphite scribble
function scribble(px){const cv=document.createElement('canvas');cv.width=cv.height=px;const c=cv.getContext('2d');c.scale(px/100,px/100);
  c.lineCap='round';c.lineJoin='round';
  c.beginPath();for(let i=0;i<=140;i++){const t=i/140,a=t*Math.PI*11,x=18+t*64+Math.cos(a)*13,y=50+Math.sin(a)*24*Math.sin(t*Math.PI*.9+.2);i?c.lineTo(x,y):c.moveTo(x,y)}
  c.lineWidth=9;c.strokeStyle='#2a2a30';c.stroke();c.lineWidth=4;c.strokeStyle='#8a8a92';c.stroke();
  return cv.toDataURL('image/png')}

// ---------- notebook page background for No. 2 Pencil (graphite doodles, transparent paper) ----------
function page(W,H){
  const cv=document.createElement('canvas');cv.width=W;cv.height=H;const c=cv.getContext('2d');
  c.strokeStyle='rgba(58,123,213,.16)';c.lineWidth=2;for(let y=60;y<H;y+=44){c.beginPath();c.moveTo(0,y);c.lineTo(W,y);c.stroke()}
  c.strokeStyle='rgba(224,69,58,.3)';c.lineWidth=2.5;for(const x of[96,101]){c.beginPath();c.moveTo(x,0);c.lineTo(x,H);c.stroke()}
  for(let i=0;i<3;i++){c.beginPath();c.arc(40,260+i*380,13,0,7);c.fillStyle='rgba(46,46,51,.08)';c.fill();c.strokeStyle='rgba(46,46,51,.35)';c.lineWidth=2;c.stroke()}
  const d=(x,y,s,a,i)=>{c.save();c.globalAlpha=.5;c.translate(x,y);c.rotate(a);c.scale(s/100,s/100);c.translate(-50,-50);drawIcon(c,i,'g');c.restore()};
  d(40,120,62,-.3,1);d(675,150,64,.2,16);d(668,400,58,-.15,0);d(44,560,52,.2,5);
  d(42,920,56,.25,13);d(672,980,60,-.1,22);d(48,1190,56,-.2,15);d(668,1220,58,.25,12);
  c.save();c.globalAlpha=.4;c.strokeStyle='#2e2e33';c.lineWidth=3;c.lineCap='round';
  c.beginPath();c.moveTo(640,700);c.quadraticCurveTo(660,680,680,700);c.quadraticCurveTo(700,720,720,700);c.stroke();
  write(c,'1+2=3',20,760,24,3);c.restore();
  return cv.toDataURL('image/png');
}

// ---------- My Classroom scene (Drop Swap) ----------
function sprite(w,h,f,k){k=k||2;const cv=document.createElement('canvas');cv.width=w*k;cv.height=h*k;const c=cv.getContext('2d');c.scale(k,k);
  const o=[SP,HL,OL,HB];SP=9;HL=3;OL=6;HB={x0:-20,y0:-20,x1:w+20,y1:h+20};f(c);[SP,HL,OL,HB]=o;return cv.toDataURL('image/png')}
const ROOM={
  bg:[900,1205,c=>{
    const W=900,H=1205,FL=H*.62;
    // wall
    pf(c,p=>p.rect(-10,-10,W+20,FL+10),C.yellow,{wash:.1,a:.12,ol:0,sp:14});
    // floor boards in perspective
    pf(c,p=>p.rect(-10,FL,W+20,H-FL+10),C.brown,{wash:.22,a:.22,ol:0,sp:12});
    c.save();c.strokeStyle='rgba(110,72,40,.55)';c.lineWidth=2.4;const vx=W/2,vy=FL-520;
    for(let i=-8;i<=8;i++){const xb=W/2+i*120;const t=0;c.beginPath();c.moveTo(vx+(xb-vx)*((FL-vy)/(H-vy)),FL);c.lineTo(xb,H);c.stroke()}
    for(const y of[FL+60,FL+140,FL+250,FL+400]){c.beginPath();c.moveTo(0,y);c.lineTo(W,y);c.globalAlpha=.5;c.stroke();c.globalAlpha=1}c.restore();
    // skirting board
    pf(c,p=>p.rect(-10,FL-22,W+20,26),C.brown,{wash:.4,ol:4});
    // window, upper left
    pf(c,p=>rr(p,40,170,210,250,6),C.white,{wash:.15,a:.5,ol:6});
    pf(c,p=>p.rect(58,188,174,214),C.sky,{wash:.28,a:.35,ol:4});
    pf(c,p=>{p.moveTo(110,260);p.arc(110,262,22,Math.PI*.6,Math.PI*1.4);p.arc(140,244,28,Math.PI*1.1,Math.PI*1.9);p.arc(172,262,20,Math.PI*1.4,Math.PI*.5);p.closePath()},C.white,{wash:0,a:.2,ol:3});
    line(c,[[145,188],[145,402]],6);line(c,[[58,295],[232,295]],6);
    pf(c,p=>rr(p,28,412,234,18,4),C.white,{wash:.2,a:.4,ol:5});
    // ABC bunting along the top
    const flags='ABCDEFG',cols=[C.red,C.orange,C.yellow,C.green,C.sky,C.blue,C.purple];
    c.beginPath();for(let x=0;x<=W;x+=10)c.lineTo(x,48+Math.sin(x/W*Math.PI)*36);c.lineWidth=3;c.strokeStyle=OUT;c.stroke();
    for(let i=0;i<7;i++){const x=70+i*127,y=48+Math.sin(x/W*Math.PI)*36,w=40;
      pf(c,p=>{p.moveTo(x-w,y);p.lineTo(x+w,y);p.lineTo(x,y+92);p.closePath()},cols[i],{wash:.4,ol:4});
      write(c,flags[i],x-11,y+14,30,4.4)}
  }],
  towel:[320,120,c=>{ // reading rug: rainbow ovals
    [C.red,C.orange,C.yellow,C.lime,C.sky].forEach((col,i)=>pf(c,p=>p.ellipse(160,60,154-i*28,56-i*10.5,0,0,7),col,{wash:.4,ol:4.5}));
  }],
  umbrella:[100,100,c=>{SP=5.4;HL=2.1;OL=5.6;drawIcon(c,12,'c')}],
  castle:[260,320,c=>{ // bookshelf
    pf(c,p=>rr(p,6,6,248,308,4),C.brown,{wash:.45});
    pf(c,p=>p.rect(22,22,216,272),C.brown,{wash:.15,a:.35,ol:4});
    for(const y of[112,204])pf(c,p=>p.rect(16,y,228,12),C.brown,{wash:.45,ol:4});
    const books=[[[C.red,20,70],[C.blue,24,80],[C.yellow,18,66],[C.green,26,84],[C.purple,20,72],[C.orange,22,78],[C.teal,18,62]],
                 [[C.sky,24,74],[C.pink,20,80],[C.lime,26,70],[C.red,18,76],[C.blue,22,64]],
                 [[C.green,24,78],[C.yellow,20,70],[C.purple,26,82],[C.orange,22,68],[C.sky,20,76],[C.red,24,72]]];
    const bases=[110,202,292];
    books.forEach((row,ri)=>{let x=26;row.forEach(([col,w,h],bi)=>{const b=bases[ri];
      if(ri===1&&bi===4){rot(c,-.35,()=>pf(c,p=>p.rect(x,b-h,w,h),col,{ol:4}),x+w,b);x+=w+30;return}
      pf(c,p=>p.rect(x,b-h,w,h),col,{ol:4});line(c,[[x+4,b-h+12],[x+w-4,b-h+12]],2);x+=w+2})});
  }],
  palm:[200,320,c=>{ // potted plant
    const leaf=(x,y,a,l,col)=>{c.save();c.translate(x,y);c.rotate(a);pf(c,p=>{p.moveTo(0,0);p.quadraticCurveTo(l*.35,-l*.22,l,0);p.quadraticCurveTo(l*.35,l*.22,0,0);p.closePath()},col,{ol:4});line(c,[[4,0],[l*.85,0]],2);c.restore()};
    line(c,[[100,210],[96,120]],6,C.green);line(c,[[100,210],[120,110]],6,C.green);
    leaf(100,200,-2.3,110,C.green);leaf(100,200,-.85,110,C.green);leaf(98,150,-2.0,100,C.lime);leaf(102,150,-1.1,100,C.lime);
    leaf(98,118,-1.75,96,C.green);leaf(118,110,-1.2,84,C.lime);leaf(96,124,-2.6,80,C.lime);leaf(110,170,-.4,88,C.green);
    pf(c,p=>{p.moveTo(40,210);p.lineTo(160,210);p.lineTo(146,314);p.lineTo(54,314);p.closePath()},C.orange,{col2:'#c9650f'});
    pf(c,p=>rr(p,32,200,136,26,4),C.orange,{col2:'#c9650f',wash:.45});
  }],
  hut:[440,270,c=>{ // teacher's desk (apple and books on the left, room for the trophy on the right)
    pf(c,p=>rr(p,30,100,120,160,3),C.brown,{wash:.4});
    for(const y of[112,162,212]){pf(c,p=>rr(p,42,y,96,40,3),C.brown,{wash:.25,ol:4});pf(c,p=>rr(p,78,y+16,24,8,4),C.grey,{ol:3})}
    pf(c,p=>p.rect(380,100,26,160),C.brown,{wash:.4});
    pf(c,p=>p.rect(150,100,230,96),C.brown,{wash:.25,a:.6});
    pf(c,p=>rr(p,10,70,420,32,4),C.brown,{wash:.5});
    pf(c,p=>rr(p,40,52,92,18,2),C.blue,{ol:4});pf(c,p=>rr(p,46,36,82,16,2),C.red,{ol:4});pf(c,p=>rr(p,42,22,88,14,2),C.green,{ol:4});
    c.save();c.translate(158,4);c.scale(.66,.66);SP=6;HL=2.4;OL=6;ICONS[1](c);SP=9;HL=3;OL=6;c.restore();
  }],
  hammock:[270,180,c=>{ // bean bag
    pf(c,p=>{p.moveTo(20,160);p.bezierCurveTo(0,110,30,40,90,26);p.bezierCurveTo(130,14,150,40,170,30);p.bezierCurveTo(230,6,270,90,252,160);p.quadraticCurveTo(140,186,20,160);p.closePath()},C.purple);
    c.beginPath();c.moveTo(70,70);c.quadraticCurveTo(140,110,210,64);c.lineWidth=4;c.strokeStyle=OUT;c.stroke();
    line(c,[[134,96],[128,160]],3);
  }],
  pier:[520,330,c=>{ // chalkboard on the wall
    pf(c,p=>rr(p,6,6,508,292,8),C.brown,{wash:.45});
    pf(c,p=>rr(p,26,26,468,252,3),C.green,{col2:darkA(C.green,.45),wash:.62,ol:5});
    write(c,'ABC',60,58,58,6,'#fbf9f3');write(c,'1+2=3',60,160,50,6,'#fbf9f3');
    c.save();c.strokeStyle=S('#fbf9f3');c.lineWidth=5;c.lineCap='round';c.beginPath();c.arc(390,120,46,0,7);c.stroke();
    c.beginPath();c.arc(374,108,5,0,7);c.arc(406,108,5,0,7);c.fillStyle=S('#fbf9f3');c.fill();c.beginPath();c.arc(390,124,26,.3,Math.PI-.3);c.stroke();c.restore();
    pf(c,p=>rr(p,0,296,520,18,3),C.brown,{wash:.5,ol:4.5});
    pf(c,p=>rr(p,300,282,36,14,3),C.white,{wash:0,a:0,ol:3.4});pf(c,p=>rr(p,350,284,24,12,3),C.yellow,{ol:3.4});
    pf(c,p=>rr(p,400,274,70,24,4),C.blue,{ol:4});pf(c,p=>rr(p,400,290,70,8,2),C.grey,{ol:3});
  }],
  lighthouse:[300,300,c=>{ // wall clock (hands are drawn live by the game)
    pf(c,p=>p.arc(150,150,144,0,7),C.orange,{col2:'#c9650f'});
    pf(c,p=>p.arc(150,150,112,0,7),C.white,{wash:0,a:0,ol:5});
    for(let i=0;i<12;i++){const a=i*Math.PI/6,r1=i%3?96:86;line(c,[[150+Math.cos(a)*r1,150+Math.sin(a)*r1],[150+Math.cos(a)*106,150+Math.sin(a)*106]],i%3?3:6)}
    write(c,'12',131,52,28,4.4);
  }],
  chest:[100,100,c=>{SP=5.4;HL=2.1;OL=5.6;drawIcon(c,23,'c')}],
};
function room(id){const [w,h,f]=ROOM[id];const k=id==='bg'?1:(id==='umbrella'||id==='chest')?6:2;return sprite(w,h,f,k)}

function preview(){
  const cell=150,cv=document.createElement('canvas');cv.width=cell*6*2+40;cv.height=cell*4+60;const c=cv.getContext('2d');
  c.fillStyle='#f6f3ea';c.fillRect(0,0,cv.width,cv.height);
  c.fillStyle='#1f1f22';c.font='22px sans-serif';c.fillText('graphite (untouched)',12,26);c.fillText('colour (touched)',cell*6+52,26);
  for(const [mode,ox] of [['g',10],['c',cell*6+30]])ICONS.forEach((f,i)=>{const x=ox+(i%6)*cell,y=40+Math.floor(i/6)*cell;
    c.save();c.translate(x+15,y+2);c.scale(1.2,1.2);drawIcon(c,i,mode);c.restore();
    c.fillStyle='#1f1f22';c.font='14px sans-serif';c.textAlign='center';c.fillText(i+' '+NAMES[i],x+cell/2,y+cell-6);c.textAlign='left'});
  return cv.toDataURL('image/png');
}
"""

PIECES = [(1, 'apple'), (0, 'pencil'), (2, 'book'), (3, 'backpack'), (4, 'crayon'), (5, 'star')]  # Drop Swap piece order
SPECIALS = [(6, 'scissors'), (18, 'palette')]
ROOM_FILES = {'bg': 'room-bg', 'towel': 'room-rug', 'umbrella': 'room-globe', 'castle': 'room-bookshelf', 'palm': 'room-plant',
              'hut': 'room-desk', 'hammock': 'room-beanbag', 'pier': 'room-chalkboard', 'lighthouse': 'room-clock', 'chest': 'room-trophy'}


def png(data_url):
    return Image.open(io.BytesIO(base64.b64decode(data_url.split(',', 1)[1]))).convert('RGBA')


def trim(im, pad=4):
    a = np.array(im)[:, :, 3]
    ys, xs = np.nonzero(a > 8)
    if not len(xs):
        return im
    box = (max(0, xs.min() - pad), max(0, ys.min() - pad), min(im.width, xs.max() + pad + 1), min(im.height, ys.max() + pad + 1))
    return im.crop(box)


def main():
    sheet = sys.argv[sys.argv.index('--sheet') + 1] if '--sheet' in sys.argv else None
    scene = sys.argv[sys.argv.index('--scene') + 1] if '--scene' in sys.argv else None
    os.makedirs(OUT_N2, exist_ok=True); os.makedirs(OUT_DS, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        pg.set_content('<html><body></body></html>')
        pg.add_script_tag(content=JS)
        color = png(pg.evaluate('iconSheet(192,"c")'))
        graph = png(pg.evaluate('iconSheet(192,"g")'))
        page = png(pg.evaluate('page(720,1280)'))
        pieces = {name: png(pg.evaluate(f'one({i},256)')) for i, name in PIECES + SPECIALS}
        scrib = png(pg.evaluate('scribble(128)'))
        rooms = {k: png(pg.evaluate(f'room("{k}")')) for k in ROOM_FILES}
        prev = png(pg.evaluate('preview()')) if sheet else None
        b.close()
    color.save(os.path.join(OUT_N2, 'icons-color.webp'), quality=90, method=6)
    graph.save(os.path.join(OUT_N2, 'icons-graphite.webp'), quality=90, method=6)
    page.save(os.path.join(OUT_N2, 'notebook.webp'), quality=86, method=6)
    for name, im in pieces.items():
        im.save(os.path.join(OUT_DS, name + '.webp'), quality=90, method=6)
    scrib.save(os.path.join(OUT_DS, 'scribble.webp'), quality=90, method=6)
    for k, name in ROOM_FILES.items():
        im = rooms[k]
        if k == 'bg':
            im = im.convert('RGB'); im.save(os.path.join(OUT_DS, name + '.webp'), quality=82, method=6)
        else:
            im = trim(im)
            if im.width > 640:
                im = im.resize((640, round(im.height * 640 / im.width)), Image.LANCZOS)
            im.save(os.path.join(OUT_DS, name + '.webp'), quality=88, method=6)
        print(name, im.size)
    if prev:
        prev.save(sheet)
    if scene:
        bg = rooms['bg'].convert('RGBA')
        bg.save(scene)
    print('wrote icons-color/graphite, notebook, pieces, room art')


if __name__ == '__main__':
    main()
