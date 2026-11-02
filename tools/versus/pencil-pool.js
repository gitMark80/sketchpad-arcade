/* Pencil Pool: 8-ball on a sketchbook page. Blue (seat 0) sinks the blue balls, pink (seat 1) the pink ones,
   then the 8. Aim by dragging: the pencil cue points where your finger is, pull further from the cue ball for
   more power, let go to shoot. Fouls give the other player ball in hand (drag the cue ball anywhere).
   The bot picks its shot by trying candidate shots with the same physics; Easy adds wobble to its aim. */
INFO.botDelay=700;INFO.endDelay=1400;
INFO.turnHint=t=>{const n=left(GROUP[t]);return(n?' · '+n+' left':' · sink the 8!')+(P.bih?' · ball in hand':'')};
const $=id=>document.getElementById(id);
/* The table is Mark's drawing (assets/pencil-pool/table.webp, 376x707 in the sheet): the felt is the play area, scaled so it is TW wide. */
const ART={w:496,h:986,fx:50,fy:54,fw:395,fh:876},ASC=380/ART.fw;
const TW=380,TH=Math.round(ART.fh*ASC),R=14,RL=ART.fx*ASC,RT=ART.fy*ASC,OW=ART.w*ASC,OH=ART.h*ASC,GROUP=['b','p'];
const POCKETS=[{x:1,y:-1,r:26},{x:TW-4,y:-3,r:26},{x:-6,y:416,r:23},{x:TW+2,y:414,r:23},{x:2,y:TH-1,r:26},{x:TW-3,y:TH-5,r:26}];
const IMG={};['cue','blue','pink','eight','pencil','table'].forEach(n=>{const i=new Image();i.onload=()=>{IMG[n]=i;sprites={};bg=null;draw()};i.src='../assets/pencil-pool/'+n+'.webp'});
const IK={c:'cue',b:'blue',p:'pink','8':'eight'};
const COL={b:'#2f6fb5',p:'#c45a8a'},WASH={b:'#d6e4f2',p:'#f0d5e2'};
const PAPER='#f6f3ea',INK='#2e2e33',GRAPH='#55555c';
const MAXV=1300,DT=1/240,DECEL=190,CUSH=.72,REST=.95;
const cv=$('table');let ctx=cv.getContext('2d');
/* P = state of the table. balls: {x,y,vx,vy,k ('b','p','8','c'),in} */
const P={balls:[],moving:false,bih:false,broke:false,aim:null,drag:null,kb:{a:-Math.PI/2,p:.5,on:false},ev:null,shotBy:0,botT:0};
let view={s:1,ox:0,oy:0,land:false,w:0,h:0},bg=null,sprites={},dpr=1;
// ---------- helpers ----------
const cue=()=>P.balls.find(b=>b.k==='c');
const left=k=>P.balls.filter(b=>b.k===k&&!b.in).length;
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
function free(x,y,skip){if(x<R||y<R||x>TW-R||y>TH-R)return false;return!P.balls.some(b=>b!==skip&&!b.in&&Math.hypot(b.x-x,b.y-y)<2*R+1)}
function spot(k){/* put a ball back on the foot spot or the nearest free place up the table */
  for(let dy=0;dy<TH/2;dy+=R){for(const sx of[0,R*2,-R*2,R*4,-R*4]){const x=TW/2+sx,y=TH*.25-dy;if(free(x,y))return{x,y}}}return{x:TW/2,y:TH/2}}
// ---------- rack ----------
function rack(){const kinds=[];for(let i=0;i<7;i++)kinds.push('b','p');for(let i=kinds.length-1;i>0;i--){const j=S.rand(i+1);[kinds[i],kinds[j]]=[kinds[j],kinds[i]]}
  const balls=[],ax=TW/2,ay=TH*.25,dy=R*Math.sqrt(3)+.6;let n=0;
  for(let row=0;row<5;row++)for(let i=0;i<=row;i++){const x=ax+(i-row/2)*(2*R+.6),y=ay-row*dy;let k;
    if(row===2&&i===1)k='8';else k=kinds[n++];balls.push({x,y,vx:0,vy:0,k,in:false})}
  /* the back row's two corners should be one of each colour */
  const c1=balls[10],c2=balls[14];if(c1.k===c2.k){const o=balls.find(b=>b.k!==c1.k&&b.k!=='8'&&b!==c1&&b!==c2);if(o){const t=o.k;o.k=c2.k;c2.k=t}}
  balls.push({x:TW/2,y:TH*.75,vx:0,vy:0,k:'c',in:false});return balls}
// ---------- physics (pure: works on any ball list, so the bot can try shots) ----------
function step(balls,ev){let moving=false;
  for(const b of balls){if(b.in)continue;const sp=Math.hypot(b.vx,b.vy);if(sp<=0)continue;
    const ns=Math.max(0,sp-DECEL*DT)*(1-.12*DT);if(ns<3){b.vx=b.vy=0;continue}b.vx*=ns/sp;b.vy*=ns/sp;b.x+=b.vx*DT;b.y+=b.vy*DT;moving=true;
    /* pockets */
    for(const p of POCKETS){if(Math.hypot(b.x-p.x,b.y-p.y)<p.r){b.in=true;b.vx=b.vy=0;b.x=p.x;b.y=p.y;if(ev){ev.potted.push(b.k);if(b.k==='c')ev.cueIn=true}break}}
    if(b.in)continue;
    /* cushions, except where a pocket mouth is */
    const nearP=POCKETS.some(p=>Math.hypot(b.x-p.x,b.y-p.y)<p.r+R*1.2);
    if(!nearP){if(b.x<R){b.x=R;b.vx=-b.vx*CUSH}else if(b.x>TW-R){b.x=TW-R;b.vx=-b.vx*CUSH}
      if(b.y<R){b.y=R;b.vy=-b.vy*CUSH}else if(b.y>TH-R){b.y=TH-R;b.vy=-b.vy*CUSH}}
    else{if(b.x<-R*2||b.x>TW+R*2||b.y<-R*2||b.y>TH+R*2){b.in=true;b.vx=b.vy=0;if(ev){ev.potted.push(b.k);if(b.k==='c')ev.cueIn=true}}}}
  /* ball on ball */
  for(let i=0;i<balls.length;i++){const a=balls[i];if(a.in)continue;for(let j=i+1;j<balls.length;j++){const b=balls[j];if(b.in)continue;
    const dx=b.x-a.x,dy=b.y-a.y,d2=dx*dx+dy*dy;if(d2>=4*R*R||d2===0)continue;const d=Math.sqrt(d2),nx=dx/d,ny=dy/d,ov=(2*R-d)/2;
    a.x-=nx*ov;a.y-=ny*ov;b.x+=nx*ov;b.y+=ny*ov;const rv=(a.vx-b.vx)*nx+(a.vy-b.vy)*ny;if(rv<=0)continue;
    const imp=rv*(1+REST)/2;a.vx-=imp*nx;a.vy-=imp*ny;b.vx+=imp*nx;b.vy+=imp*ny;moving=true;
    if(ev){if(ev.first===null){const o=a.k==='c'?b:b.k==='c'?a:null;if(o)ev.first=o.k}ev.hits++;if(ev.onHit)ev.onHit(rv)}}}
  return moving}
function shootBalls(balls,dir,power){const c=balls.find(b=>b.k==='c'),v=MAXV*(.08+.92*power);c.vx=Math.cos(dir)*v;c.vy=Math.sin(dir)*v}
function simulate(dir,power){const balls=P.balls.map(b=>({...b})),ev={first:null,potted:[],cueIn:false,hits:0};shootBalls(balls,dir,power);
  for(let i=0;i<4000;i++){if(!step(balls,ev))break}return{balls,ev}}
// ---------- rules ----------
function settle(){const ev=P.ev,me=P.shotBy,my=GROUP[me],other=1-me;P.ev=null;P.moving=false;S.busy=false;
  const ownLeft=left(my),eightIn=ev.potted.includes('8');
  if(eightIn&&!P.broke){/* 8 on the break: spot it and play on */const e=P.balls.find(b=>b.k==='8');const s=spot('8');e.in=false;e.x=s.x;e.y=s.y;e.vx=e.vy=0;S.pop('8 is back!')}
  const was=P.broke;P.broke=true;
  if(ev.cueIn){const c=cue();c.in=false;c.vx=c.vy=0;const s=spot('c');c.x=TW/2;c.y=TH*.75;if(!free(c.x,c.y,c)){c.x=s.x;c.y=s.y}}
  const names=S.names();
  if(eightIn&&was){const win=ownLeft===0&&!ev.cueIn?me:other;S.scores[0]=7-left('b');S.scores[1]=7-left('p');S.hud();
    S.end(win,win===me?names[me]+' sank the 8 ball!':ev.cueIn?names[me]+' scratched on the 8.':names[me]+' sank the 8 too early.');return}
  let foul=null;
  if(ev.cueIn)foul='Scratch!';else if(ev.first===null)foul='Nothing hit!';
  else if(was&&ownLeft+ev.potted.filter(k=>k===my).length>0&&ev.first==='8')foul='Hit the 8 first!';
  else if(was&&ev.first!==my&&ev.first!=='8'&&left(my)>0)foul='Wrong ball first!';
  else if(was&&left(my)===0&&ev.first!=='8')foul='Hit the 8 first!';
  S.scores[0]=7-left('b');S.scores[1]=7-left('p');S.hud();
  const mine=ev.potted.filter(k=>k===my).length;
  if(foul){S.sfx('miss');S.pop(foul,'#d9661a');P.bih=true;S.setTurn(other)}
  else if(mine){S.sfx('score');S.pop(mine>1?mine+' down!':'Nice!');P.bih=false;S.setTurn(me)}
  else{P.bih=false;S.setTurn(other)}}
function shoot(dir,power){if(P.moving)return;P.shotBy=S.turn;P.aim=null;P.kb.on=false;P.moving=true;S.busy=true;
  P.ev={first:null,potted:[],cueIn:false,hits:0,onHit:rv=>{if(rv>120)S.sfx('tap')}};shootBalls(P.balls,dir,power);S.sfx('bot');tick(true)}
// ---------- the bot ----------
function clearPath(balls,from,to,skipA,skipB){const dx=to.x-from.x,dy=to.y-from.y,L=Math.hypot(dx,dy);if(L<1)return true;
  for(const b of balls){if(b.in||b===skipA||b===skipB)continue;const t=((b.x-from.x)*dx+(b.y-from.y)*dy)/(L*L);if(t<=0||t>=1)continue;
    const px=from.x+dx*t,py=from.y+dy*t;if(Math.hypot(b.x-px,b.y-py)<2*R-.5)return false}return true}
function botTargets(){const my=GROUP[1];return left(my)?P.balls.filter(b=>b.k===my&&!b.in):P.balls.filter(b=>b.k==='8'&&!b.in)}
function botCandidates(){const c=cue(),out=[];
  for(const b of botTargets())for(const p of POCKETS){const dpx=b.x-p.x,dpy=b.y-p.y,L=Math.hypot(dpx,dpy);if(L<R)continue;
    const g={x:b.x+dpx/L*2*R,y:b.y+dpy/L*2*R};const gd=dist(c,g);if(gd<R)continue;
    /* cut angle between the cue's path and the ball's path to the pocket */
    const cos=((g.x-c.x)/gd*(-dpx/L)+(g.y-c.y)/gd*(-dpy/L));if(cos<.2)continue;
    if(!clearPath(P.balls,c,g,c,b))continue;if(!clearPath(P.balls,b,{x:p.x,y:p.y},b,c))continue;
    const dir=Math.atan2(g.y-c.y,g.x-c.x),need=Math.min(1,(gd+L/cos)/900+.12);
    out.push({dir,power:Math.min(1,need),kind:'pot'});out.push({dir,power:Math.min(1,need+.25),kind:'pot'})}
  if(!out.length){/* no clear pot: nudge the nearest own ball gently */
    for(const b of botTargets()){if(!clearPath(P.balls,c,b,c,b))continue;out.push({dir:Math.atan2(b.y-c.y,b.x-c.x),power:Math.min(.6,dist(c,b)/700+.1),kind:'safe'})}}
  if(!out.length)for(let i=0;i<10;i++)out.push({dir:Math.random()*Math.PI*2,power:.35,kind:'rand'});
  return out}
function scoreShot(ev,my){let s=0;const otherLeftBefore=0;
  for(const k of ev.potted){if(k===my)s+=100;else if(k==='c')s-=250;else if(k==='8')s+=(left(my)===0?1000:-800);else s-=40}
  if(ev.first===null)s-=150;else if(left(my)>0&&ev.first!==my)s-=150;else if(left(my)===0&&ev.first!=='8')s-=150;
  return s+Math.random()*2}
function botPlace(){/* ball in hand: find a spot with a straight, clear shot at one of its balls */
  const c=cue();let best=null;
  for(const b of botTargets())for(const p of POCKETS){const dpx=b.x-p.x,dpy=b.y-p.y,L=Math.hypot(dpx,dpy);if(L<R)continue;
    for(const back of[110,170,240]){const x=b.x+dpx/L*back,y=b.y+dpy/L*back;if(!free(x,y,c))continue;const g={x:b.x+dpx/L*2*R,y:b.y+dpy/L*2*R};
      if(!clearPath(P.balls,{x,y},g,c,b)||!clearPath(P.balls,b,{x:p.x,y:p.y},b,c))continue;const sc=-L-back*.3;if(!best||sc>best.sc)best={x,y,sc}}}
  if(!best){for(let t=0;t<200;t++){const x=R+Math.random()*(TW-2*R),y=R+Math.random()*(TH-2*R);if(free(x,y,c)){best={x,y};break}}}
  if(best){c.x=best.x;c.y=best.y}P.bih=false}
function botMove(){if(!S.active||P.moving)return;if(P.bih)botPlace();
  const my=GROUP[1],cands=botCandidates(),skill=S.skill();let scored=cands.map(c=>({...c,sc:scoreShot(simulate(c.dir,c.power).ev,my)}));
  scored.sort((a,b)=>b.sc-a.sc);let pick=Math.random()<skill?scored[0]:S.pick(scored.slice(0,Math.min(scored.length,6)));
  const wob={easy:.045,medium:.014,hard:.003}[S.diff];pick={...pick,dir:pick.dir+(Math.random()*2-1)*wob,power:Math.min(1,Math.max(.05,pick.power+(Math.random()*2-1)*wob*3))};
  P.aim={dir:pick.dir,power:pick.power,bot:true};draw();clearTimeout(P.botT);P.botT=setTimeout(()=>{if(S.active&&S.isBot())shoot(pick.dir,pick.power)},650)}
// ---------- view: fit the table to the canvas, sideways when the stage is wide ----------
function fit(){const box=$('pool').getBoundingClientRect();const w=Math.max(120,Math.floor(box.width)),h=Math.max(120,Math.floor(box.height));dpr=Math.min(2,window.devicePixelRatio||1);
  if(cv.width!==Math.round(w*dpr)||cv.height!==Math.round(h*dpr)){cv.width=Math.round(w*dpr);cv.height=Math.round(h*dpr)}
  const land=w>h*1.05;const tw=land?OH:OW,th=land?OW:OH;const s=Math.min(w/tw,h/th);view={s,ox:(w-tw*s)/2,oy:(h-th*s)/2,land,w,h};bg=null;sprites={};draw()}
function applyT(){ctx.setTransform(dpr,0,0,dpr,0,0);if(view.land){ctx.translate(view.ox,view.oy+OW*view.s);ctx.scale(view.s,view.s);ctx.rotate(-Math.PI/2)}else{ctx.translate(view.ox,view.oy);ctx.scale(view.s,view.s)}ctx.translate(RL,RT)}
function toTable(px,py){const{s,ox,oy,land}=view;return land?{x:(oy+OW*s-py)/s-RL,y:(px-ox)/s-RT}:{x:(px-ox)/s-RL,y:(py-oy)/s-RT}}
new ResizeObserver(fit).observe($('pool'));window.addEventListener('orientationchange',()=>setTimeout(fit,200));
// ---------- drawing ----------
function hatch(x,y,w,h,col,gap,alpha){ctx.save();ctx.beginPath();ctx.rect(x,y,w,h);ctx.clip();ctx.strokeStyle=col;ctx.globalAlpha=alpha;ctx.lineWidth=1.1;ctx.beginPath();
  for(let d=-h;d<w+h;d+=gap){ctx.moveTo(x+d,y);ctx.lineTo(x+d+h,y+h)}ctx.stroke();ctx.restore()}
function wobbleRect(x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y+1);ctx.lineTo(x+w-r,y-1);ctx.quadraticCurveTo(x+w+1,y,x+w,y+r);ctx.lineTo(x+w+1,y+h-r);ctx.quadraticCurveTo(x+w,y+h+1,x+w-r,y+h);
  ctx.lineTo(x+r,y+h-1);ctx.quadraticCurveTo(x-1,y+h,x,y+h-r);ctx.lineTo(x-1,y+r);ctx.quadraticCurveTo(x,y-1,x+r,y);ctx.closePath()}
function drawTable(){/* cached: rails, felt, pockets */
  if(bg&&bg.width===cv.width&&bg.height===cv.height)return;bg=document.createElement('canvas');bg.width=cv.width;bg.height=cv.height;const c2=bg.getContext('2d');
  const paint=()=>{
    ctx.clearRect(-RL-5,-RT-5,OW+10,OH+10);
    if(IMG.table){ctx.drawImage(IMG.table,-RL,-RT,OW,OH);ctx.save();ctx.setLineDash([5,7]);ctx.strokeStyle=PAPER;ctx.globalAlpha=.55;ctx.lineWidth=1.3;ctx.beginPath();ctx.moveTo(4,TH*.75);ctx.lineTo(TW-4,TH*.75);ctx.stroke();ctx.restore();return}
    // rails: paper wood with pencil grain
    ctx.fillStyle='#e9e2cf';wobbleRect(-RL,-RT,OW,OH,16);ctx.fill();ctx.lineWidth=2.2;ctx.strokeStyle=INK;ctx.stroke();
    ctx.save();wobbleRect(-RL,-RT,OW,OH,16);ctx.clip();ctx.strokeStyle=GRAPH;ctx.globalAlpha=.35;ctx.lineWidth=1;
    for(let i=0;i<40;i++){const y=-RT+((i*97)%OH),x0=-RL+((i*53)%60);ctx.beginPath();ctx.moveTo(x0,y);ctx.bezierCurveTo(x0+90,y+4,x0+200,y-5,x0+OW,y+2);ctx.stroke()}
    ctx.restore();
    // felt: green coloured pencil
    ctx.fillStyle='#dcebdd';wobbleRect(0,0,TW,TH,6);ctx.fill();hatch(0,0,TW,TH,'#5a9a6a',7,.3);
    ctx.save();ctx.beginPath();ctx.rect(0,0,TW,TH);ctx.clip();ctx.strokeStyle='#5a9a6a';ctx.globalAlpha=.16;ctx.lineWidth=1.1;ctx.beginPath();for(let d=-TH;d<TW+TH;d+=13){ctx.moveTo(d,0);ctx.lineTo(d-TH,TH)}ctx.stroke();ctx.restore();
    ctx.lineWidth=2.2;ctx.strokeStyle=INK;wobbleRect(0,0,TW,TH,6);ctx.stroke();
    // head string and foot spot
    ctx.save();ctx.setLineDash([5,7]);ctx.strokeStyle=GRAPH;ctx.globalAlpha=.5;ctx.lineWidth=1.3;ctx.beginPath();ctx.moveTo(0,TH*.75);ctx.lineTo(TW,TH*.75);ctx.stroke();ctx.restore();
    ctx.fillStyle=GRAPH;ctx.globalAlpha=.5;ctx.beginPath();ctx.arc(TW/2,TH*.25,2.5,0,7);ctx.fill();ctx.globalAlpha=1;
    // pockets: scribbled ink holes
    for(const p of POCKETS){ctx.fillStyle='#e9e2cf';ctx.beginPath();ctx.arc(p.x,p.y,p.r+3,0,7);ctx.fill();
      ctx.fillStyle=INK;ctx.globalAlpha=.9;ctx.beginPath();ctx.ellipse(p.x,p.y,p.r-2,p.r-3.5,.4,0,7);ctx.fill();ctx.globalAlpha=1;
      ctx.strokeStyle=INK;ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(p.x+1,p.y-1,p.r-1,p.r-2,.4,0,7);ctx.stroke();
      ctx.strokeStyle=GRAPH;ctx.lineWidth=1;ctx.globalAlpha=.6;for(let i=0;i<3;i++){ctx.beginPath();ctx.ellipse(p.x-1+i,p.y+1-i,p.r-4-i*2,p.r-6-i,.3+i*.5,0,5.5);ctx.stroke()}ctx.globalAlpha=1}
  };
  // temporarily point the shared ctx at the offscreen canvas
  const real=ctx;ctx=c2;applyT();paint();ctx=real;}
function sprite(k){const key=k+'@'+(view.s*dpr).toFixed(2);if(sprites[key])return sprites[key];const sc=view.s*dpr,n=Math.ceil((R+3)*2*sc),c=document.createElement('canvas');c.width=c.height=n;const g=c.getContext('2d');
  g.translate(n/2,n/2);g.scale(sc,sc);
  if(IMG[IK[k]]){const d=2*R+2.5;g.drawImage(IMG[IK[k]],-d/2,-d/2,d,d);sprites[key]=c;return c}
  g.fillStyle=k==='8'?INK:PAPER;g.beginPath();g.ellipse(0,0,R,R*.97,.3,0,7);g.fill();
  if(k==='b'||k==='p'){g.save();g.beginPath();g.arc(0,0,R-1,0,7);g.clip();g.fillStyle=WASH[k];g.fillRect(-R,-R,2*R,2*R);g.strokeStyle=COL[k];g.globalAlpha=.75;g.lineWidth=1.3;g.beginPath();
    for(let d=-2*R;d<2*R;d+=3.2){g.moveTo(d,-R);g.lineTo(d+2*R,R)}g.stroke();g.restore()}
  if(k==='8'){g.fillStyle=PAPER;g.beginPath();g.arc(0,0,R*.55,0,7);g.fill();g.fillStyle=INK;g.font=`${R*.95}px "Patrick Hand","Comic Sans MS",cursive`;g.textAlign='center';g.textBaseline='middle';g.fillText('8',0,.5)}
  if(k==='c'){g.strokeStyle=GRAPH;g.globalAlpha=.35;g.lineWidth=1;g.beginPath();g.arc(1,1,R*.6,.2,1.6);g.stroke();g.globalAlpha=1}
  g.strokeStyle=INK;g.lineWidth=1.8;g.beginPath();g.ellipse(0,0,R,R*.97,.3,0,7);g.stroke();
  g.strokeStyle=GRAPH;g.globalAlpha=.5;g.lineWidth=1.2;g.beginPath();g.arc(-2.5,-2.5,R*.55,3.4,4.6);g.stroke();
  sprites[key]=c;return c}
function drawBall(b){const sp=sprite(b.k),w=sp.width/(view.s*dpr);ctx.fillStyle='rgba(46,46,51,.22)';ctx.beginPath();ctx.ellipse(b.x+2,b.y+3,R,R*.8,0,0,7);ctx.fill();
  if(view.land&&b.k==='8'){ctx.save();ctx.translate(b.x,b.y);ctx.rotate(Math.PI/2);ctx.drawImage(sp,-w/2,-w/2,w,w);ctx.restore()}else ctx.drawImage(sp,b.x-w/2,b.y-w/2,w,w)}
function drawPencil(c,dir,power){/* the cue is a No. 2 pencil, pulled back from the cue ball */
  const back=R+6+power*46,len=150;ctx.save();ctx.translate(c.x,c.y);ctx.rotate(dir+Math.PI);ctx.translate(back,0);
  if(IMG.pencil){const h=len*IMG.pencil.height/IMG.pencil.width;ctx.drawImage(IMG.pencil,0,-h/2,len,h);ctx.restore();return}
  // tip
  ctx.fillStyle='#e9d9b2';ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(16,-5);ctx.lineTo(16,5);ctx.closePath();ctx.fill();ctx.strokeStyle=INK;ctx.lineWidth=1.6;ctx.stroke();
  ctx.fillStyle=INK;ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(5,-1.6);ctx.lineTo(5,1.6);ctx.closePath();ctx.fill();
  // body
  ctx.fillStyle='#f3e6b0';ctx.fillRect(16,-5,len,10);hatch(16,-5,len,10,'#c99a1a',4,.5);ctx.strokeStyle=INK;ctx.lineWidth=1.6;ctx.strokeRect(16,-5,len,10);
  ctx.strokeStyle=GRAPH;ctx.globalAlpha=.5;ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(18,-1.5);ctx.lineTo(16+len,-1.5);ctx.moveTo(18,1.5);ctx.lineTo(16+len,1.5);ctx.stroke();ctx.globalAlpha=1;
  // ferrule and eraser
  ctx.fillStyle='#e4e2d8';ctx.fillRect(16+len,-5.5,10,11);ctx.strokeStyle=INK;ctx.strokeRect(16+len,-5.5,10,11);
  ctx.fillStyle='#f0d5e2';ctx.beginPath();ctx.roundRect(26+len,-5,12,10,[0,4,4,0]);ctx.fill();hatch(26+len,-5,12,10,'#c45a8a',3.5,.5);ctx.strokeStyle=INK;ctx.beginPath();ctx.roundRect(26+len,-5,12,10,[0,4,4,0]);ctx.stroke();
  ctx.fillStyle=INK;ctx.font='7px "Patrick Hand",cursive';ctx.textAlign='center';ctx.textBaseline='middle';ctx.save();ctx.translate(16+len*.55,0);if(Math.cos(dir+Math.PI-(view.land?Math.PI/2:0))<0)ctx.rotate(Math.PI);ctx.fillText('No. 2',0,0);ctx.restore();
  ctx.restore()}
function drawAim(c,dir,power){const dx=Math.cos(dir),dy=Math.sin(dir);
  /* where the cue ball first meets another ball or a cushion */
  let tMin=Infinity,hitB=null;for(const b of P.balls){if(b.in||b===c)continue;const ox=b.x-c.x,oy=b.y-c.y,p=ox*dx+oy*dy;if(p<=0)continue;const d2=ox*ox+oy*oy-p*p;if(d2>4*R*R)continue;const t=p-Math.sqrt(4*R*R-d2);if(t>0&&t<tMin){tMin=t;hitB=b}}
  const tx=dx>0?(TW-R-c.x)/dx:dx<0?(R-c.x)/dx:Infinity,ty=dy>0?(TH-R-c.y)/dy:dy<0?(R-c.y)/dy:Infinity;const tWall=Math.min(tx,ty);if(tWall<tMin){tMin=tWall;hitB=null}
  const gx=c.x+dx*tMin,gy=c.y+dy*tMin;
  ctx.save();ctx.setLineDash([6,6]);ctx.strokeStyle=INK;ctx.globalAlpha=.8;ctx.lineWidth=1.8;ctx.beginPath();ctx.moveTo(c.x+dx*R,c.y+dy*R);ctx.lineTo(gx,gy);ctx.stroke();
  ctx.setLineDash([3,4]);ctx.beginPath();ctx.arc(gx,gy,R,0,7);ctx.stroke();
  if(hitB){const nx=(hitB.x-gx)/(2*R),ny=(hitB.y-gy)/(2*R),dot=nx*dx+ny*dy,L=40+60*Math.max(0,dot);ctx.setLineDash([4,5]);ctx.strokeStyle=COL[hitB.k]||INK;ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(hitB.x,hitB.y);ctx.lineTo(hitB.x+nx*L,hitB.y+ny*L);ctx.stroke()}
  ctx.restore();
  drawPencil(c,dir,power)}
function drawPower(power){/* power bar in screen space, along the bottom (or right) edge */
  ctx.setTransform(dpr,0,0,dpr,0,0);const w=view.land?10:Math.min(160,view.w*.5),h=view.land?Math.min(160,view.h*.5):10;const x=view.land?view.w-16:(view.w-w)/2,y=view.land?(view.h-h)/2:view.h-16;
  ctx.fillStyle=PAPER;ctx.fillRect(x,y,w,h);ctx.strokeStyle=INK;ctx.lineWidth=1.5;ctx.strokeRect(x,y,w,h);
  ctx.fillStyle=power>.75?'#d9661a':'#c99a1a';if(view.land)ctx.fillRect(x+2,y+h-2-(h-4)*power,w-4,(h-4)*power);else ctx.fillRect(x+2,y+2,(w-4)*power,h-4)}
function draw(){if(!view.w)return;drawTable();ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,cv.width,cv.height);ctx.drawImage(bg,0,0);applyT();
  const c=cue();for(const b of P.balls){if(!b.in&&b.k!=='c')drawBall(b)}
  if(c&&!c.in){if(P.bih&&!P.moving&&S.canPlay()){ctx.save();ctx.setLineDash([4,4]);ctx.strokeStyle=COL[GROUP[S.turn]];ctx.lineWidth=2;const t=Date.now()/400;ctx.beginPath();ctx.arc(c.x,c.y,R+5+Math.sin(t)*2,0,7);ctx.stroke();ctx.restore()}
    drawBall(c)}
  if(!P.moving&&c&&!c.in&&S.active){
    if(P.aim&&!P.drag)drawAim(c,P.aim.dir,P.aim.power);
    else if(P.kb.on&&S.canPlay())drawAim(c,P.kb.a,P.kb.p)}
  if(P.bih&&!P.moving&&S.canPlay()){ctx.fillStyle=INK;ctx.font='15px "Patrick Hand","Comic Sans MS",cursive';ctx.textAlign='center';ctx.save();if(view.land){ctx.translate(TW/2,TH*.5);ctx.rotate(Math.PI/2);ctx.translate(-TW/2,-TH*.5)}
    ctx.strokeStyle=PAPER;ctx.lineWidth=4;ctx.strokeText('Ball in hand: drag the cue ball',TW/2,TH*.5);ctx.fillText('Ball in hand: drag the cue ball',TW/2,TH*.5);ctx.restore()}
  if(P.aim&&!P.drag&&!P.moving)drawPower(P.aim.power);else if(P.kb.on&&!P.moving&&S.canPlay())drawPower(P.kb.p);
  cv.className=P.moving||!S.canPlay()?'wait':P.bih?'hand':''}
let raf=0;function tick(go){cancelAnimationFrame(raf);const loop=()=>{if(P.moving){let mv=false;for(let i=0;i<4;i++)mv=step(P.balls,P.ev)||mv;if(!mv){settle();tick(true);return}}
  draw();if(P.moving||P.bih||P.aim||P.kb.on)raf=requestAnimationFrame(loop)};if(go||P.moving||P.bih)raf=requestAnimationFrame(loop);else draw()}
// ---------- input ----------
let ptr=null;
/* slingshot aim: pull back from the cue ball; the pencil sits under your finger and the ball goes the other way */
function aimFrom(t){const c=cue();const dx=c.x-t.x,dy=c.y-t.y,d=Math.hypot(dx,dy);if(d<4)return;P.aim={dir:Math.atan2(dy,dx),power:Math.min(1,Math.max(0,(d-R-14)/240))}}
cv.addEventListener('pointerdown',e=>{if(!S.canPlay()||P.moving||S.isBot())return;e.preventDefault();cv.setPointerCapture(e.pointerId);ptr=e.pointerId;const t=toTable(e.offsetX,e.offsetY),c=cue();P.kb.on=false;
  if(P.bih&&dist(t,c)<R*3.2){P.drag={ox:c.x-t.x,oy:c.y-t.y};P.aim=null}else{P.drag=null;aimFrom(t)}tick(true)});
cv.addEventListener('pointermove',e=>{if(ptr!==e.pointerId)return;const t=toTable(e.offsetX,e.offsetY);
  if(P.drag){const c=cue(),x=Math.min(TW-R,Math.max(R,t.x+P.drag.ox)),y=Math.min(TH-R,Math.max(R,t.y+P.drag.oy));c.x=x;c.y=y}else aimFrom(t)});
function up(e){if(ptr!==e.pointerId)return;ptr=null;const c=cue();
  if(P.drag){P.drag=null;if(!free(c.x,c.y,c)){/* slide to the nearest free spot */let best=null;for(let r=R;r<TW&&!best;r+=R/2)for(let a=0;a<6.3;a+=.5){const x=c.x+Math.cos(a)*r,y=c.y+Math.sin(a)*r;if(free(x,y,c)){best={x,y};break}}if(best){c.x=best.x;c.y=best.y}}S.sfx('tap');draw();return}
  if(P.aim){const a=P.aim;P.aim=null;if(a.power>.02&&S.canPlay())shoot(a.dir,a.power);else draw()}}
cv.addEventListener('pointerup',up);cv.addEventListener('pointercancel',up);
cv.tabIndex=0;
cv.addEventListener('keydown',e=>{if(!S.canPlay()||P.moving)return;const k=P.kb,st=e.shiftKey?.004:.02;
  if(e.key==='ArrowLeft'){k.a-=st;k.on=true}else if(e.key==='ArrowRight'){k.a+=st;k.on=true}else if(e.key==='ArrowUp'){k.p=Math.min(1,k.p+.05);k.on=true}else if(e.key==='ArrowDown'){k.p=Math.max(.05,k.p-.05);k.on=true}
  else if(e.key===' '||e.key==='Enter'){if(k.on){e.preventDefault();shoot(k.a,k.p);return}}else return;e.preventDefault();P.aim=null;tick(true)});
// ---------- game hooks for the shell ----------
const GAME={
  reset(){clearTimeout(P.botT);P.balls=rack();P.moving=false;P.bih=false;P.broke=false;P.aim=null;P.drag=null;P.kb.on=false;P.ev=null;P.kb.a=-Math.PI/2;P.kb.p=.5;tick(true)},
  render(){draw()},
  botMove,
  save(){return{balls:P.balls.map(b=>({x:Math.round(b.x*10)/10,y:Math.round(b.y*10)/10,k:b.k,in:b.in})),bih:P.bih,broke:P.broke}},
  load(st){clearTimeout(P.botT);P.balls=st.balls.map(b=>({x:b.x,y:b.y,vx:0,vy:0,k:b.k,in:!!b.in}));P.bih=!!st.bih;P.broke=!!st.broke;P.moving=false;P.aim=null;P.drag=null;P.ev=null;
    S.scores[0]=7-left('b');S.scores[1]=7-left('p');tick(true)}
};
