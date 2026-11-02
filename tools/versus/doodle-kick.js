/* Doodle Kick: flick soccer on a sketchbook page. Five pencil-drawn players a side and one ball.
   On your turn drag one of your players back like a pool cue and let go to flick it. Everything slides,
   bounces and stops, then it's the other side's turn. Knock the ball into the far goal; first to GOALS wins.
   Player 0 = blue, defends the bottom goal and shoots up. Player 1 = pink, defends the top goal.
   The physics is a fixed-step simulation, so the same flick plays out the same way on both phones online;
   the shot itself is saved so the friend's phone replays it before snapping to the saved end positions.
   Bots try a spread of flicks on a copy of the table and keep the one that ends best (Easy adds noise and
   often picks a so-so one, Hard tries more and always keeps the best). */
INFO.botDelay=700;
INFO.turnHint=t=>(S.mode==='online'||S.mode==='bot')&&(S.canPlay()?' · flick a player':'')||'';
const W=100,H=160,GW=38,GD=11,RP=5.2,RB=3.1,RPOST=1.3,GOALS=3,DT=1/120,MAXV=160,MAXPULL=34;
const POW=4.6;                 // units of speed per unit of pull
const MP=2,MB=1,REST=.82,WALLR=.68,DRAG=.988,STOPV=1.5;
const $k=id=>document.getElementById(id);
const cv=$k('pitch'),cx=cv.getContext('2d'),wrap=$k('pitchWrap');
/* body = {x,y,vx,vy,r,m,p (owner 0/1 or -1 for the ball)} */
/* three line-ups, one per match, then round again (blue's half; pink mirrors it) */
const FORMS=[
  [[50,146],[24,120],[76,120],[36,97],[64,97]],   // 1-2-2
  [[50,146],[50,124],[28,108],[72,108],[50,92]],  // diamond
  [[50,146],[20,118],[50,126],[80,118],[50,96]]]; // 1-3-1
let fi=0,matchNo=0;
function formation(){const f=[];const add=(p,x,y)=>f.push({x,y,vx:0,vy:0,r:RP,m:MP,p,a:0});
  for(const[x,y]of FORMS[fi])add(0,x,y);
  for(const[x,y]of FORMS[fi])add(1,100-x,160-y);
  f.push({x:50,y:80,vx:0,vy:0,r:RB,m:MB,p:-1});return f}
let bodies=formation(),anim=false,replaying=false,drag=null,lastShot=null,shotId=0,settledCb=null,spark=[],goalFlash=0;
const ball=()=>bodies[10];
const flip=()=>S.mode==='online'&&S.viewer()===1;
// ---------- physics ----------
function clone(bs){return bs.map(b=>({x:b.x,y:b.y,vx:b.vx,vy:b.vy,r:b.r,m:b.m,p:b.p,a:0}))}
const POSTS=[[50-GW/2,0],[50+GW/2,0],[50-GW/2,H],[50+GW/2,H]];
/* one fixed step; returns the scoring player (0/1) when the ball crosses a goal line, -1 otherwise, or -2 if nothing moved */
function step(bs,fx){let moving=false,goal=-1;
  for(const b of bs){if(!b.vx&&!b.vy)continue;b.x+=b.vx*DT;b.y+=b.vy*DT;b.vx*=DRAG;b.vy*=DRAG;if(b.p>=0)b.a=(b.a||0)+Math.hypot(b.vx,b.vy)*DT/b.r*.55*(b.vx<0?-1:1);
    if(Math.hypot(b.vx,b.vy)<STOPV){b.vx=b.vy=0}else moving=true}
  // walls
  for(const b of bs){const inMouth=Math.abs(b.x-50)<GW/2-b.r*.2;
    if(b.x<b.r){b.x=b.r;if(b.vx<0)b.vx=-b.vx*WALLR;fx&&fx('wall',b)}else if(b.x>W-b.r){b.x=W-b.r;if(b.vx>0)b.vx=-b.vx*WALLR;fx&&fx('wall',b)}
    if(inMouth){if(b.p===-1){if(b.y<-b.r-1){goal=0}else if(b.y>H+b.r+1){goal=1}}
      // back of the net: the ball sticks, players bounce back out
      const k=b.p===-1?.3:.75;
      if(b.y<-GD+b.r){b.y=-GD+b.r;b.vy=Math.abs(b.vy)*k;fx&&fx('wall',b)}else if(b.y>H+GD-b.r){b.y=H+GD-b.r;b.vy=-Math.abs(b.vy)*k;fx&&fx('wall',b)}
      if(b.y<0||b.y>H){const l=50-GW/2+b.r,rr=50+GW/2-b.r;if(b.x<l){b.x=l;b.vx=Math.abs(b.vx)*.4}else if(b.x>rr){b.x=rr;b.vx=-Math.abs(b.vx)*.4}}}
    else{if(b.y<b.r){b.y=b.r;if(b.vy<0)b.vy=-b.vy*WALLR;fx&&fx('wall',b)}else if(b.y>H-b.r){b.y=H-b.r;if(b.vy>0)b.vy=-b.vy*WALLR;fx&&fx('wall',b)}}
    // goal posts
    for(const[px,py]of POSTS){const dx=b.x-px,dy=b.y-py,d=Math.hypot(dx,dy),min=b.r+RPOST;if(d<min&&d>0){const nx=dx/d,ny=dy/d;b.x=px+nx*min;b.y=py+ny*min;const vn=b.vx*nx+b.vy*ny;if(vn<0){b.vx-=(1+WALLR)*vn*nx;b.vy-=(1+WALLR)*vn*ny;fx&&fx('wall',b)}}}}
  // bodies
  for(let i=0;i<bs.length;i++)for(let j=i+1;j<bs.length;j++){const a=bs[i],b=bs[j];const dx=b.x-a.x,dy=b.y-a.y,min=a.r+b.r;if(Math.abs(dx)>min||Math.abs(dy)>min)continue;
    const d=Math.hypot(dx,dy);if(d>=min||d===0)continue;const nx=dx/d,ny=dy/d,over=min-d;const ma=a.m,mb=b.m,tm=ma+mb;
    a.x-=nx*over*(mb/tm);a.y-=ny*over*(mb/tm);b.x+=nx*over*(ma/tm);b.y+=ny*over*(ma/tm);
    const rvx=b.vx-a.vx,rvy=b.vy-a.vy,vn=rvx*nx+rvy*ny;if(vn>=0)continue;
    const jj=-(1+REST)*vn/(1/ma+1/mb);a.vx-=jj*nx/ma;a.vy-=jj*ny/ma;b.vx+=jj*nx/mb;b.vy+=jj*ny/mb;moving=true;
    fx&&fx(a.p===-1||b.p===-1?'ball':'hit',a,b,Math.abs(vn))}
  if(goal>=0)return goal;return moving?-1:-2}
/* run a whole shot on a copy: returns {bs, goal, steps} */
function simulate(bs,i,vx,vy,maxSteps){const c=clone(bs);c[i].vx=vx;c[i].vy=vy;let goal=-1,n=0;
  for(;n<(maxSteps||900);n++){const r=step(c);if(r>=0){goal=r;break}if(r===-2)break}return{bs:c,goal,steps:n}}
// ---------- drawing ----------
let cw=0,ch=0,sc=1,ox=0,oy=0;
function resize(){const r=wrap.getBoundingClientRect();const aw=Math.max(120,r.width),ah=Math.max(160,r.height);const ar=W/(H+2*GD+4);
  let w=aw,h=w/ar;if(h>ah){h=ah;w=h*ar}cw=Math.floor(w);ch=Math.floor(h);const dpr=Math.min(2,window.devicePixelRatio||1);
  cv.width=Math.round(cw*dpr);cv.height=Math.round(ch*dpr);cv.style.width=cw+'px';cv.style.height=ch+'px';cx.setTransform(dpr,0,0,dpr,0,0);
  sc=cw/W;ox=0;oy=(GD+2)*sc;draw()}
new ResizeObserver(resize).observe(wrap);addEventListener('resize',resize);
const toScreen=(x,y)=>flip()?[ox+(W-x)*sc,oy+(H-y)*sc]:[ox+x*sc,oy+y*sc];
const toWorld=(px,py)=>{const x=(px-ox)/sc,y=(py-oy)/sc;return flip()?[W-x,H-y]:[x,y]};
/* Mark's hand-drawn art in src/assets/doodle-kick/ (pitch, players, goalies, ball, goals, goal burst, kick lines,
   power dot). The canvas falls back to drawing everything itself until every picture has loaded. */
const ART_DIR='../assets/doodle-kick/',ART={ok:false};
(()=>{const names=['pitch','blue','pink','ball','bluegoal','pinkgoal','burst','kick','dot'];let left=names.length,bad=false;
  names.forEach(n=>{const im=new Image();im.onload=()=>{if(--left===0&&!bad){ART.ok=true;draw()}};im.onerror=()=>{bad=true};im.src=ART_DIR+n+'.webp';ART[n]=im})})();
const PITCH_M=.75;   // cream margin round the pitch picture, in pitch units
let goalPos=null,kickFx=null;
/* wobbly hand-drawn line */
function wob(x1,y1,x2,y2,a){cx.beginPath();const n=Math.max(2,Math.round(Math.hypot(x2-x1,y2-y1)/22));cx.moveTo(x1,y1);
  for(let i=1;i<=n;i++){const t=i/n;const jx=(Math.sin(i*7.3+x1+a)*.8),jy=(Math.cos(i*5.1+y1+a)*.8);cx.lineTo(x1+(x2-x1)*t+(i<n?jx:0),y1+(y2-y1)*t+(i<n?jy:0))}cx.stroke()}
function wobCircle(x,y,r){cx.beginPath();for(let i=0;i<=28;i++){const t=i/28*Math.PI*2;const rr=r*(1+Math.sin(i*2.7+x)*.025);cx.lineTo(x+Math.cos(t)*rr,y+Math.sin(t)*rr)}cx.closePath()}
function hatch(x,y,w,h,col,gap,ang){cx.save();cx.beginPath();cx.rect(x,y,w,h);cx.clip();cx.strokeStyle=col;cx.lineWidth=1;cx.lineCap='round';const L=Math.hypot(w,h);cx.translate(x+w/2,y+h/2);cx.rotate(ang);
  cx.beginPath();for(let d=-L;d<L;d+=gap){cx.moveTo(d,-L);cx.lineTo(d+L*.08,L)}cx.stroke();cx.restore()}
function pitchBg(){const ink='#2e2e33';
  cx.fillStyle='#f6f3ea';cx.fillRect(0,0,cw,ch);
  if(ART.ok){cx.drawImage(ART.pitch,ox-PITCH_M*sc,oy-PITCH_M*sc,(W+2*PITCH_M)*sc,(H+2*PITCH_M)*sc);
    for(const side of[0,1]){const top=(side===1)!==flip();const im=side===0?ART.bluegoal:ART.pinkgoal;const gw=(GW+2*RPOST+2.6)*sc,gh=gw*im.naturalHeight/im.naturalWidth;
      cx.save();cx.translate(ox+50*sc,top?oy:oy+H*sc);if(!top)cx.scale(1,-1);cx.drawImage(im,-gw/2,-gh+1.5*sc,gw,gh);cx.restore()}
    if(goalFlash>0){cx.fillStyle='rgba(243,230,176,'+(goalFlash*.35)+')';cx.fillRect(0,0,cw,ch)}return}
  // grass: coloured pencil hatching in mowed stripes
  const [fx0,fy0]=[ox,oy],fw=W*sc,fh=H*sc;const stripes=8;
  for(let i=0;i<stripes;i++){const y=fy0+fh*i/stripes,h=fh/stripes;cx.fillStyle=i%2?'#dfe9d6':'#e6eedc';cx.fillRect(fx0,y,fw,h);
    hatch(fx0,y,fw,h,i%2?'rgba(90,154,106,.28)':'rgba(90,154,106,.2)',i%2?5:6,-.9+i*.03)}
  cx.strokeStyle=ink;cx.lineWidth=2;cx.lineCap='round';cx.lineJoin='round';
  // pitch lines
  const L=(x1,y1,x2,y2)=>{const a=toScreen(x1,y1),b=toScreen(x2,y2);wob(a[0],a[1],b[0],b[1],x1+y1)};
  cx.globalAlpha=.9;
  L(.6,.6,W-.6,.6);L(W-.6,.6,W-.6,H-.6);L(W-.6,H-.6,.6,H-.6);L(.6,H-.6,.6,.6);
  L(0,H/2,W,H/2);
  const c=toScreen(50,80);wobCircle(c[0],c[1],13*sc);cx.stroke();cx.fillStyle='rgba(46,46,51,.9)';cx.beginPath();cx.arc(c[0],c[1],1.6,0,7);cx.fill();
  // boxes
  for(const side of[0,1]){const yb=side?0:H,dir=side?1:-1;const by=yb+dir*24,sy=yb+dir*9;
    L(22,yb,22,by);L(22,by,78,by);L(78,by,78,yb);L(34,yb,34,sy);L(34,sy,66,sy);L(66,sy,66,yb);
    const pen=toScreen(50,yb+dir*16);cx.beginPath();cx.arc(pen[0],pen[1],1.6,0,7);cx.fill();
    // penalty arc
    cx.beginPath();const pr=12*sc;const cc=toScreen(50,yb+dir*16);const up=(dir===1)!==flip();
    cx.arc(cc[0],cc[1],pr,up?0.72:Math.PI+0.72,up?Math.PI-0.72:2*Math.PI-0.72);cx.stroke()}
  // corner arcs
  for(const[x,y]of[[0,0],[W,0],[0,H],[W,H]]){const p=toScreen(x,y);cx.beginPath();cx.arc(p[0],p[1],4*sc,0,7);cx.stroke()}
  cx.globalAlpha=1;
  // goals (nets)
  for(const side of[0,1]){const top=(side===1)!==flip();const gx=ox+(50-GW/2)*sc,gw=GW*sc,gy=top?oy-GD*sc:oy+H*sc,gh=GD*sc;
    const owner=side;const col=owner===0?'#2f6fb5':'#c45a8a',wash=owner===0?'#d6e4f2':'#f0d5e2';
    cx.fillStyle=wash;cx.fillRect(gx,gy,gw,gh);
    cx.save();cx.beginPath();cx.rect(gx,gy,gw,gh);cx.clip();cx.strokeStyle=col;cx.globalAlpha=.55;cx.lineWidth=1;cx.beginPath();
    for(let x=gx;x<=gx+gw;x+=5)for(let y=gy;y<=gy+gh;y+=5){cx.moveTo(x,gy);cx.lineTo(x,gy+gh);cx.moveTo(gx,y);cx.lineTo(gx+gw,y)}cx.stroke();cx.restore();
    cx.strokeStyle=ink;cx.lineWidth=2.5;cx.globalAlpha=1;
    wob(gx,gy,gx,gy+gh,1);wob(gx+gw,gy,gx+gw,gy+gh,2);wob(gx,top?gy:gy+gh,gx+gw,top?gy:gy+gh,3);
    // posts
    for(const px of[gx,gx+gw]){const py=top?oy:oy+H*sc;cx.fillStyle='#f6f3ea';cx.beginPath();cx.arc(px,py,RPOST*sc+1,0,7);cx.fill();cx.stroke()}}
  if(goalFlash>0){cx.fillStyle='rgba(243,230,176,'+(goalFlash*.35)+')';cx.fillRect(0,0,cw,ch)}}
function star(x,y,r){cx.beginPath();for(let i=0;i<10;i++){const a=-Math.PI/2+i*Math.PI/5,rr=i%2?r*.45:r;cx.lineTo(x+Math.cos(a)*rr,y+Math.sin(a)*rr)}cx.closePath()}
function ring(x,y,r){cx.save();cx.strokeStyle='#2e2e33';cx.lineWidth=2;cx.setLineDash([5,5]);cx.lineDashOffset=-performance.now()/40;cx.beginPath();cx.arc(x,y,r+5,0,7);cx.stroke();cx.restore()}
function drawPiece(b,hl){const[x,y]=toScreen(b.x,b.y),r=b.r*sc;const col=b.p===0?'#2f6fb5':'#c45a8a',wash=b.p===0?'#d6e4f2':'#f0d5e2';
  // shadow
  cx.fillStyle='rgba(46,46,51,.22)';cx.beginPath();cx.arc(x+2,y+3,r,0,7);cx.fill();
  if(ART.ok){const im=ART[b.p===0?'blue':'pink'];const d=r*2.12;cx.save();cx.translate(x,y);cx.rotate(b.a||0);cx.drawImage(im,-d/2,-d/2,d,d);cx.restore();if(hl)ring(x,y,r);return}
  cx.save();wobCircle(x,y,r);cx.clip();cx.fillStyle=wash;cx.fillRect(x-r,y-r,2*r,2*r);hatch(x-r,y-r,2*r,2*r,col,3.2,b.p?.75:-.75);cx.restore();
  cx.strokeStyle='#2e2e33';cx.lineWidth=2.2;wobCircle(x,y,r);cx.stroke();
  cx.save();cx.translate(x,y);cx.rotate(b.a||0);cx.fillStyle='#f6f3ea';star(0,0,r*.5);cx.fill();cx.strokeStyle='#2e2e33';cx.lineWidth=1.4;cx.stroke();cx.restore();
  if(hl)ring(x,y,r)}
function drawBall(){const b=ball();const[x,y]=toScreen(b.x,b.y),r=b.r*sc;
  cx.fillStyle='rgba(46,46,51,.22)';cx.beginPath();cx.arc(x+1.5,y+2.5,r,0,7);cx.fill();
  if(ART.ok){const d=r*2.15;cx.save();cx.translate(x,y);cx.rotate((b.x+b.y)*.1);cx.drawImage(ART.ball,-d/2,-d/2,d,d);cx.restore();return}
  cx.fillStyle='#fbfaf5';wobCircle(x,y,r);cx.fill();cx.strokeStyle='#2e2e33';cx.lineWidth=2;cx.stroke();
  // pentagon patch and spokes
  const a0=(b.x+b.y)*.3;cx.fillStyle='#2e2e33';cx.beginPath();for(let i=0;i<5;i++){const a=a0+i*Math.PI*2/5;cx.lineTo(x+Math.cos(a)*r*.42,y+Math.sin(a)*r*.42)}cx.closePath();cx.fill();
  cx.lineWidth=1.2;cx.beginPath();for(let i=0;i<5;i++){const a=a0+i*Math.PI*2/5;cx.moveTo(x+Math.cos(a)*r*.42,y+Math.sin(a)*r*.42);cx.lineTo(x+Math.cos(a)*r*.95,y+Math.sin(a)*r*.95)}cx.stroke()}
function draw(){if(!cw)return;pitchBg();
  const mine=S.active&&S.canPlay()&&!anim&&!replaying?S.turn:-1;
  if(kickFx&&ART.ok){kickFx.t-=1/60;if(kickFx.t<=0)kickFx=null;else{const[x,y]=toScreen(kickFx.x,kickFx.y);const a=Math.atan2(kickFx.vy,kickFx.vx)+(flip()?Math.PI:0);const im=ART.kick;const w=14*sc,h=w*im.naturalHeight/im.naturalWidth;
    cx.save();cx.globalAlpha=Math.min(1,kickFx.t*2.5);cx.translate(x,y);cx.rotate(a);cx.drawImage(im,-w-RP*sc*.6,-h/2,w,h);cx.restore()}}
  bodies.forEach((b,i)=>{if(b.p>=0)drawPiece(b,b.p===mine&&(!drag||drag.i===i))});drawBall();
  if(goalFlash>0&&goalPos&&ART.ok){const[x,y]=toScreen(goalPos[0],goalPos[1]);const k=1.25-goalFlash*.5;const im=ART.burst;const w=34*sc*k,h=w*im.naturalHeight/im.naturalWidth;
    cx.save();cx.globalAlpha=Math.min(1,goalFlash*1.6);cx.drawImage(im,x-w/2,y-h/2,w,h);cx.restore()}
  // sparks
  spark=spark.filter(s=>(s.t-=1/60)>0);for(const s of spark){const[x,y]=toScreen(s.x,s.y);cx.strokeStyle='rgba(46,46,51,'+(s.t*2)+')';cx.lineWidth=1.5;cx.beginPath();for(let k=0;k<5;k++){const a=k*1.26+s.x;const rr=(1-s.t)*14+3;cx.moveTo(x+Math.cos(a)*rr*.5,y+Math.sin(a)*rr*.5);cx.lineTo(x+Math.cos(a)*rr,y+Math.sin(a)*rr)}cx.stroke()}
  // aim
  if(drag&&drag.len>0){const b=bodies[drag.i];const[x,y]=toScreen(b.x,b.y);const pw=Math.min(1,drag.len/MAXPULL);const dir=flip()?-1:1;
    const ax=-drag.dx*dir,ay=-drag.dy*dir;const al=Math.hypot(ax,ay)||1;const ux=ax/al,uy=ay/al;
    cx.save();cx.strokeStyle=ART.ok?'#f6f3ea':'#2e2e33';cx.lineWidth=2.5;cx.setLineDash([3,6]);cx.beginPath();cx.moveTo(x+ux*b.r*sc,y+uy*b.r*sc);cx.lineTo(x+ux*(b.r*sc+pw*70),y+uy*(b.r*sc+pw*70));cx.stroke();
    cx.setLineDash([]);cx.strokeStyle=ART.ok?'rgba(246,243,234,.6)':'rgba(46,46,51,.45)';cx.lineWidth=1.5;cx.beginPath();cx.moveTo(x,y);cx.lineTo(x-ux*pw*MAXPULL*sc,y-uy*pw*MAXPULL*sc);cx.stroke();
    // power meter
    const mx=x-ux*pw*MAXPULL*sc,my=y-uy*pw*MAXPULL*sc;
    if(ART.ok){const d=(9+pw*10);cx.drawImage(ART.dot,mx-d/2,my-d/2,d,d)}else{cx.fillStyle=pw>.75?'#d9661a':'#c99a1a';cx.beginPath();cx.arc(mx,my,4+pw*5,0,7);cx.fill();cx.strokeStyle='#2e2e33';cx.stroke()}cx.restore()}}
function loop(){draw();if(anim||spark.length||drag||goalFlash>0||kickFx){if(goalFlash>0)goalFlash-=.03;requestAnimationFrame(loop)}else{raf=false}}
let raf=false;function wake(){if(!raf){raf=true;requestAnimationFrame(loop)}}
// ---------- playing a shot ----------
const fx=(k,a,b,v)=>{if(k==='ball'){const bb=a.p===-1?a:b;spark.push({x:bb.x,y:bb.y,t:.5});if(v>25)S.sfx('bot')}else if(k==='hit'&&v>30)S.sfx('bot')};
let acc=0,lastT=0,steps=0;
function shoot(i,vx,vy,cb){kickFx={x:bodies[i].x,y:bodies[i].y,vx,vy,t:.55};bodies[i].vx=vx;bodies[i].vy=vy;anim=true;steps=0;settledCb=cb;lastT=performance.now();acc=0;cv.classList.add('busy');S.hud();requestAnimationFrame(tick);wake()}
function tick(t){if(!anim)return;acc+=Math.min(.05,(t-lastT)/1000);lastT=t;let res=-1;
  while(acc>=DT&&anim){acc-=DT;res=step(bodies,fx);steps++;if(res>=0||res===-2||steps>1500){anim=false;break}}
  if(!anim){bodies.forEach(b=>{b.vx=b.vy=0});cv.classList.remove('busy');const cb=settledCb;settledCb=null;if(cb)cb(res>=0?res:-1);return}
  requestAnimationFrame(tick)}
function afterShot(goal){const shooter=S.turn;lastShot.final=bodies.map(b=>[+b.x.toFixed(2),+b.y.toFixed(2)]);lastShot.goal=goal;
  if(goal>=0){scored(goal,shooter);return}
  S.setTurn(1-shooter);draw()}
function scored(goal,shooter){const own=goal!==shooter;goalPos=[ball().x,Math.max(-GD/2,Math.min(H+GD/2,ball().y))];S.busy=true;S.addScore(goal,1);goalFlash=1;wake();S.sfx('score');
  S.pop(own?'Own goal!':'GOAL!',S.col(goal));
  const n=S.names();setTimeout(()=>{S.busy=false;if(!S.active)return;
    if(S.scores[goal]>=GOALS){bodies=formation();lastShot.final=bodies.map(b=>[b.x,b.y]);S.end(goal,(n[goal]==='You'?'You':n[goal])+' scored '+GOALS+' first!');draw();return}
    bodies=formation();lastShot.final=bodies.map(b=>[b.x,b.y]);S.setTurn(1-goal);draw()},900)}
function kick(i,vx,vy){lastShot={id:++shotId,by:S.turn,i,vx:+vx.toFixed(2),vy:+vy.toFixed(2),before:bodies.map(b=>[+b.x.toFixed(2),+b.y.toFixed(2)])};
  S.sfx('tap');shoot(i,vx,vy,afterShot)}
// ---------- input ----------
function hitPiece(wx,wy){let best=-1,bd=1e9;bodies.forEach((b,i)=>{if(b.p!==S.turn)return;const d=Math.hypot(b.x-wx,b.y-wy);if(d<b.r*1.9&&d<bd){bd=d;best=i}});return best}
cv.addEventListener('pointerdown',e=>{if(!S.canPlay()||anim||replaying||drag)return;const r=cv.getBoundingClientRect();const[wx,wy]=toWorld(e.clientX-r.left,e.clientY-r.top);
  const i=hitPiece(wx,wy);if(i<0)return;drag={i,id:e.pointerId,sx:e.clientX,sy:e.clientY,dx:0,dy:0,len:0};try{cv.setPointerCapture(e.pointerId)}catch(x){}wake();e.preventDefault()});
cv.addEventListener('pointermove',e=>{if(!drag||e.pointerId!==drag.id)return;let dx=(e.clientX-drag.sx)/sc,dy=(e.clientY-drag.sy)/sc;const l=Math.hypot(dx,dy);
  if(l>MAXPULL){dx*=MAXPULL/l;dy*=MAXPULL/l}drag.dx=dx;drag.dy=dy;drag.len=Math.min(l,MAXPULL);e.preventDefault()});
function endDrag(e){if(!drag||e.pointerId!==drag.id)return;const d=drag;drag=null;if(d.len<3||!S.canPlay()||anim){draw();return}
  const dir=flip()?-1:1;let vx=-d.dx*dir*POW,vy=-d.dy*dir*POW;const l=Math.hypot(vx,vy);if(l>MAXV){vx*=MAXV/l;vy*=MAXV/l}kick(d.i,vx,vy)}
cv.addEventListener('pointerup',endDrag);cv.addEventListener('pointercancel',e=>{if(drag&&e.pointerId===drag.id){drag=null;draw()}});
// ---------- bots ----------
function goalY(p){return p===0?0:H}          // the goal player p attacks
function evaluate(res,p){const b=res.bs[10];const me=p,op=1-p;
  if(res.goal===me)return 1000-res.steps*.05;if(res.goal===op)return -1500;
  const tgt=goalY(me),ownG=goalY(op);
  let s=-Math.hypot(b.x-50,b.y-tgt)*2.2;            // closer to the goal we attack
  s+=Math.min(40,Math.hypot(b.x-50,b.y-ownG))*.6;   // and away from ours
  let nearOp=1e9,nearMe=1e9;for(const q of res.bs){if(q.p===op)nearOp=Math.min(nearOp,Math.hypot(q.x-b.x,q.y-b.y));if(q.p===me)nearMe=Math.min(nearMe,Math.hypot(q.x-b.x,q.y-b.y))}
  s+=Math.min(30,nearOp)*.9-Math.min(30,nearMe)*.35;
  // ball sitting in front of our own goal with an opponent behind it is asking for trouble
  const dangerY=Math.abs(b.y-ownG);if(dangerY<40&&Math.abs(b.x-50)<24)s-=(40-dangerY)*(nearOp<25?1.6:.6);
  return s}
function candidates(p,count){const out=[];const b=ball();const tgt=goalY(p);
  bodies.forEach((pc,i)=>{if(pc.p!==p)return;
    // flick the ball so it heads for the goal: aim this piece at the contact point behind the ball
    const toG=[50-b.x,tgt-b.y];const gl=Math.hypot(toG[0],toG[1])||1;const gx=toG[0]/gl,gy=toG[1]/gl;
    const cxp=b.x-gx*(RP+RB),cyp=b.y-gy*(RP+RB);
    const base=Math.atan2(cyp-pc.y,cxp-pc.x);const dist=Math.hypot(cxp-pc.x,cyp-pc.y);
    for(const da of[-.3,-.15,-.06,0,.06,.15,.3])for(const pw of[.45,.7,1]){out.push({i,a:base+da,v:Math.min(MAXV,MAXPULL*POW*pw*Math.min(1,.5+dist/90))})}
    // straight at the ball
    const dirB=Math.atan2(b.y-pc.y,b.x-pc.x);for(const pw of[.5,.85])out.push({i,a:dirB,v:MAXPULL*POW*pw});
    // defensive/positional flicks
    for(let k=0;k<4;k++)out.push({i,a:Math.random()*Math.PI*2,v:MAXPULL*POW*(.3+Math.random()*.6)})});
  for(let i=out.length-1;i>0;i--){const j=S.rand(i+1);[out[i],out[j]]=[out[j],out[i]]}return out.slice(0,count)}
function chooseBot(p){const n=S.diff==='easy'?40:S.diff==='medium'?90:130;const cs=candidates(p,n);
  const scored=cs.map(c=>{const vx=Math.cos(c.a)*c.v,vy=Math.sin(c.a)*c.v;return{c,s:evaluate(simulate(bodies,c.i,vx,vy,S.diff==='hard'?1100:700),p)}});
  scored.sort((x,y)=>y.s-x.s);let pick;
  if(Math.random()<S.skill())pick=scored[0];else pick=scored[Math.min(scored.length-1,1+S.rand(Math.max(1,Math.floor(scored.length*(S.diff==='easy'?.5:.25)))))];
  const c=pick.c;let a=c.a,v=c.v;if(S.diff==='easy'){a+=(Math.random()-.5)*.25;v*=.8+Math.random()*.3}else if(S.diff==='medium'){a+=(Math.random()-.5)*.08}
  return{i:c.i,vx:Math.cos(a)*v,vy:Math.sin(a)*v}}
// ---------- game hooks ----------
const GAME={
  save:()=>({P:bodies.map(b=>[+b.x.toFixed(2),+b.y.toFixed(2)]),shot:lastShot,f:fi}),
  load(st){replaying=false;drag=null;if(st.f>=0&&st.f<FORMS.length)fi=st.f;
    const setP=P=>{if(P&&P.length===11)P.forEach((q,i)=>{bodies[i].x=q[0];bodies[i].y=q[1];bodies[i].vx=bodies[i].vy=0})};
    const sh=st.shot;
    if(sh&&sh.id&&sh.by!==S.viewer()&&sh.id!==shotId&&sh.before&&sh.final){
      // replay the friend's flick, then snap to where the server says everything ended
      shotId=sh.id;lastShot=sh;anim=false;setP(sh.before);replaying=true;cv.classList.add('busy');draw();
      shoot(sh.i,sh.vx,sh.vy,goal=>{replaying=false;if(goal>=0){goalPos=[ball().x,Math.max(-GD/2,Math.min(H+GD/2,ball().y))];goalFlash=1;wake();S.sfx('score');S.pop(goal===sh.by?'GOAL!':'Own goal!',S.col(goal))}
        setTimeout(()=>{setP(sh.final);draw();S.hud();S.status(S.turnText(),S.turn)},goal>=0?700:0)});
      return}
    if(sh&&sh.id){shotId=Math.max(shotId,sh.id);lastShot=sh}
    setP(st.P);if(!st.P)bodies=formation();draw()},
  reset(){if(S.active){fi=matchNo%FORMS.length;matchNo++}else fi=0;bodies=formation();anim=false;replaying=false;drag=null;spark=[];goalFlash=0;lastShot=null;cv.classList.remove('busy');draw()},
  render(){cv.classList.toggle('wait',!S.canPlay());draw()},
  botMove(){const m=chooseBot(S.turn);kick(m.i,m.vx,m.vy)}};
resize();
