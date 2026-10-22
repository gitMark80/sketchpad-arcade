/* Sketchers: checkers (English draughts) on an 8x8 sketchbook page.
   Player 0 = blue, starts at the bottom and moves up. Player 1 = pink, starts at the top and moves down.
   Jumps are compulsory and a whole multi-jump is one turn; a man that reaches the far row is crowned and stops.
   Score = pieces captured. 40 moves in a row with no capture or crowning = draw.
   Bots: Easy random legal move, Medium shallow search, Hard alpha-beta with iterative deepening. */
INFO.botDelay=550;
const EMPTY=0,BM=1,BK=2,PM=3,PK=4,DRAW_AT=40;
const own=v=>v===0?-1:v<=2?0:1, isK=v=>v===BK||v===PK;
const RC=i=>[i>>3,i&7];
const $q=id=>document.getElementById(id);
const sqEl=$q('sqs'),pcEl=$q('pcs');
let B=new Int8Array(64),PID=new Int32Array(64),pieces={},nextId=1,qm=0,last=[],sel=-1,cands=null,path=[],anim=false;
function initial(){const b=new Int8Array(64);for(let i=0;i<64;i++){const[r,c]=RC(i);if((r+c)%2!==1)continue;if(r<3)b[i]=PM;else if(r>4)b[i]=BM}return b}
const START=initial();
// ---------- rules ----------
function dirsOf(v){return v===BM?[[-1,-1],[-1,1]]:v===PM?[[1,-1],[1,1]]:[[-1,-1],[-1,1],[1,-1],[1,1]]}
function crownRow(v){return v===BM?0:v===PM?7:-1}
function genMoves(b,p){const caps=[],steps=[];
  for(let i=0;i<64;i++){const v=b[i];if(own(v)!==p)continue;
    const before=caps.length;b[i]=EMPTY;jumps(b,i,v,[i],[],caps);b[i]=v;
    if(caps.length===before&&!caps.length){const[r,c]=RC(i);for(const[dr,dc]of dirsOf(v)){const nr=r+dr,nc=c+dc;if(nr<0||nr>7||nc<0||nc>7)continue;const t=nr*8+nc;if(b[t]===EMPTY)steps.push({path:[i,t],caps:[]})}}}
  return caps.length?caps:steps}
function jumps(b,at,v,pathSoFar,capSoFar,out){const[r,c]=RC(at);let any=false;
  for(const[dr,dc]of dirsOf(v)){const mr=r+dr,mc=c+dc,lr=r+2*dr,lc=c+2*dc;if(lr<0||lr>7||lc<0||lc>7)continue;
    const m=mr*8+mc,l=lr*8+lc;if(own(b[m])!==1-own(v)||capSoFar.includes(m)||b[l]!==EMPTY)continue;
    any=true;const np=pathSoFar.concat(l),nc=capSoFar.concat(m);
    if(!isK(v)&&lr===crownRow(v))out.push({path:np,caps:nc});else jumps(b,l,v,np,nc,out)}
  if(!any&&capSoFar.length)out.push({path:pathSoFar,caps:capSoFar})}
function apply(b,m){const f=m.path[0],t=m.path[m.path.length-1];let v=b[f];b[f]=EMPTY;for(const c of m.caps)b[c]=EMPTY;
  let crowned=false;if(!isK(v)&&(t>>3)===crownRow(v)){v=v===BM?BK:PK;crowned=true}b[t]=v;return crowned}
// ---------- search ----------
function evalFor(b,p){let s=0;for(let i=0;i<64;i++){const v=b[i];if(!v)continue;const[r,c]=RC(i);let x;
    if(isK(v))x=175;else{x=100+(v===BM?7-r:r)*5;if((v===BM&&r===7)||(v===PM&&r===0))x+=10}
    if(r>=3&&r<=4&&c>=2&&c<=5)x+=4;s+=own(v)===p?x:-x}return s}
function matOnly(b,p){let s=0;for(let i=0;i<64;i++){const v=b[i];if(!v)continue;const x=isK(v)?150:100;s+=own(v)===p?x:-x}return s}
let deadline=0,timedOut=false;
function negamax(b,p,depth,a,be,ev,ply){if(Date.now()>deadline){timedOut=true;return 0}
  const ms=genMoves(b,p);if(!ms.length)return -100000+ply;
  if(depth<=0&&!ms[0].caps.length)return ev(b,p);
  if(depth<=-6)return ev(b,p);
  let best=-Infinity;for(const m of ms){const nb=b.slice();apply(nb,m);const v=-negamax(nb,1-p,depth-1,-be,-a,ev,ply+1);
    if(v>best)best=v;if(v>a)a=v;if(a>=be)break}return best}
function searchBest(b,p,maxDepth,ms,ev,limit){deadline=Date.now()+limit;let bestMoves=ms.slice(),order=ms.slice();
  for(let d=1;d<=maxDepth;d++){timedOut=false;let scored=[];
    for(const m of order){const nb=b.slice();apply(nb,m);const v=-negamax(nb,1-p,d-1,-Infinity,Infinity,ev,1);if(timedOut)break;scored.push([v,m])}
    if(timedOut)break;scored.sort((x,y)=>y[0]-x[0]);order=scored.map(x=>x[1]);const top=scored[0][0];bestMoves=scored.filter(x=>x[0]===top).map(x=>x[1]);if(Math.abs(top)>90000)break}
  return S.pick(bestMoves)}
function chooseBot(b,p){const ms=genMoves(b,p);if(ms.length===1)return ms[0];
  if(S.diff==='easy')return S.pick(ms);
  if(S.diff==='medium')return Math.random()<.15?S.pick(ms):searchBest(b,p,3,ms,matOnly,200);
  return searchBest(b,p,10,ms,evalFor,350)}
// ---------- drawing ----------
/* Mark's hand-drawn art: pieces, kings, crown, capture puff and board squares. Each square gets one of four
   rotated/flipped copies of the square drawing so the board doesn't look stamped. Falls back to CSS if art fails. */
const ART_DIR='../assets/sketchers/',ART={ok:false};
(()=>{const names=['blue','pink','blueking','pinkking','crown','puff','dark','light'];let left=names.length,bad=false;const img={};
  names.forEach(n=>{const im=new Image();im.onload=()=>{if(--left===0&&!bad)ready()};im.onerror=()=>{bad=true};im.src=ART_DIR+n+'.webp';img[n]=im});
  function variants(im){const out=[];for(let k=0;k<4;k++){const c=document.createElement('canvas');const s=Math.max(im.naturalWidth,im.naturalHeight);c.width=c.height=s;const x=c.getContext('2d');
      x.translate(s/2,s/2);x.rotate(k*Math.PI/2);if(k&1)x.scale(-1,1);x.drawImage(im,-s/2,-s/2,s,s);out.push('url('+c.toDataURL('image/webp',.85)+')')}return out}
  function ready(){let dv,lv;try{dv=variants(img.dark);lv=variants(img.light)}catch(e){dv=[`url(${ART_DIR}dark.webp)`];lv=[`url(${ART_DIR}light.webp)`]}
    sqs.forEach((b,i)=>{const d=((i>>3)+(i&7))%2,h=(i*7+(i>>3)*3)%4;b.style.setProperty('--art',(d?dv:lv)[h%(d?dv:lv).length])});
    ART.ok=true;document.getElementById('board').classList.add('art')}})();
const flip=()=>S.mode==='online'&&S.viewer()===1;
function pos(i){let[r,c]=RC(i);if(flip()){r=7-r;c=7-c}return{left:(c*12.5)+'%',top:(r*12.5)+'%'}}
const CROWN='<svg viewBox="0 0 40 40"><path d="M8 28 L6 13 L14 20 L20 9 L26 20 L34 13 L32 28 Z" fill="#f3e6b0" stroke="#2e2e33" stroke-width="3" stroke-linejoin="round"/><path d="M9 32 L31 32" stroke="#2e2e33" stroke-width="3" stroke-linecap="round"/><circle cx="20" cy="8" r="2.5" fill="#c99a1a"/></svg>';
const SCRIBBLE='<svg class="scr" viewBox="0 0 40 40"><path d="M6 12 L34 8 L8 20 L33 17 L7 29 L32 27 L10 35"/></svg>';
function makePiece(i){const v=B[i],id=nextId++;const el=document.createElement('div');el.className='pc p'+own(v)+(isK(v)?' k':'');el.innerHTML='<i>'+(isK(v)?CROWN:'')+'</i>';
  Object.assign(el.style,pos(i));pcEl.appendChild(el);pieces[id]=el;PID[i]=id}
const sqs=[...Array(64)].map((_,i)=>{const b=document.createElement('button');b.type='button';b.className='sq'+(((i>>3)+(i&7))%2?' d':'');b.tabIndex=((i>>3)+(i&7))%2?0:-1;
  b.onclick=()=>tap(i);sqEl.appendChild(b);return b});
function layoutSquares(){const f=flip();for(let i=0;i<64;i++){const d=f?63-i:i;sqEl.appendChild(sqs[d])}}
function fullRender(){pcEl.innerHTML='';pieces={};PID.fill(0);for(let i=0;i<64;i++)if(B[i])makePiece(i);layoutSquares();marks()}
function label(i){const[r,c]=RC(i);const v=B[i];return 'Row '+(8-r)+' column '+(c+1)+(v?(': '+(own(v)?'pink':'blue')+(isK(v)?' king':' piece')):'')}
function marks(){const myTurn=S.canPlay()&&!anim;const ms=myTurn?genMoves(B,S.turn):[];const must=ms.length&&ms[0].caps.length&&sel<0&&!path.length;
  for(let i=0;i<64;i++){const s=sqs[i];s.classList.toggle('last',last.includes(i));s.classList.toggle('sel',i===sel);s.classList.remove('dest','cap');s.setAttribute('aria-label',label(i))}
  Object.values(pieces).forEach(el=>el.classList.remove('up','must'));
  if(sel>=0&&PID[sel]&&pieces[PID[sel]])pieces[PID[sel]].classList.add('up');
  if(cands){const k=path.length||1;cands.forEach(m=>{const t=m.path[k];if(t!=null){sqs[t].classList.add('dest');if(m.caps.length)sqs[t].classList.add('cap')}})}
  if(must)ms.forEach(m=>{const el=pieces[PID[m.path[0]]];if(el)el.classList.add('must')})}
// ---------- moving ----------
function hop(a,b,capSq){const id=PID[a];const el=pieces[id];PID[b]=id;PID[a]=0;B[b]=B[a];B[a]=EMPTY;if(el)Object.assign(el.style,pos(b));
  if(capSq!=null&&B[capSq]){const cid=PID[capSq];const ce=pieces[cid];B[capSq]=EMPTY;PID[capSq]=0;delete pieces[cid];
    if(ce){ce.insertAdjacentHTML('beforeend',ART.ok?'<img class="puff" alt="" src="'+ART_DIR+'puff.webp">':SCRIBBLE);ce.classList.add('gone');setTimeout(()=>ce.remove(),700)}}}
function mid(a,b){const[r1,c1]=RC(a),[r2,c2]=RC(b);return Math.abs(r1-r2)===2?((r1+r2)/2)*8+(c1+c2)/2:null}
function finish(m){const p=S.turn,t=m.path[m.path.length-1];let crowned=false;const v=B[t];
  if(!isK(v)&&(t>>3)===crownRow(v)){B[t]=v===BM?BK:PK;crowned=true;const el=pieces[PID[t]];if(el){el.classList.add('k');el.querySelector('i').innerHTML=CROWN;if(ART.ok){const c=document.createElement('img');c.className='cpop';c.alt='';c.src=ART_DIR+'crown.webp';el.appendChild(c);setTimeout(()=>c.remove(),1200)}}S.pop('Crowned!',S.col(p));S.sfx('score')}
  qm=(m.caps.length||crowned)?0:qm+1;last=m.path.slice();sel=-1;cands=null;path=[];
  const opp=1-p,oppMoves=genMoves(B,opp);let left=0;for(let i=0;i<64;i++)if(own(B[i])===opp)left++;
  if(!left){marks();S.end(p,'Every piece captured!');return}
  if(!oppMoves.length){marks();S.end(p,"No moves left for "+(S.names()[opp]==='You'?'you':S.names()[opp])+'.');return}
  if(qm>=DRAW_AT){marks();S.end(-1,DRAW_AT+' moves with no captures. Call it a draw!');return}
  S.setTurn(opp);marks()}
function doHop(m,k,cb){const a=m.path[k],b=m.path[k+1];const c=mid(a,b);hop(a,b,c);
  if(c!=null){S.addScore(S.turn,1);S.sfx('score')}else S.sfx(S.isBot()?'bot':'tap');anim=true;marks();setTimeout(()=>{anim=false;cb()},300)}
function tap(i){if(!S.canPlay()||anim)return;const p=S.turn;
  if(path.length){// in the middle of a multi-jump: only the next landing squares
    const nx=cands.filter(m=>m.path[path.length]===i);if(!nx.length){S.sfx('miss');return}step(nx,i);return}
  const all=genMoves(B,p);
  if(own(B[i])===p){const mine=all.filter(m=>m.path[0]===i);if(!mine.length){S.sfx('miss');if(all.length&&all[0].caps.length)S.pop('You must jump!',S.col(p));return}
    sel=i;cands=mine;S.sfx('tap');marks();return}
  if(sel>=0&&cands){const nx=cands.filter(m=>m.path[1]===i);if(nx.length){path=[sel];step(nx,i)}}}
function step(nx,to){const k=path.length-1;const m0=nx[0];path.push(to);cands=nx;
  doHop(m0,k,()=>{sel=to;const done=nx.find(m=>m.path.length===path.length);if(done&&nx.length===1){finish(done);return}
    if(done&&nx.every(m=>m.path.length===path.length)){finish(done);return}marks()})}
function botPlay(m){let k=0;const next=()=>{if(k>=m.path.length-1){finish(m);return}doHop(m,k++,next)};next()}
// ---------- game hooks ----------
const GAME={
  save:()=>({B:Array.from(B),last:last.slice(),qm}),
  load(st){const nb=st.B&&st.B.length===64?Int8Array.from(st.B):START.slice();
    if(nb.every((v,i)=>v===START[i])&&!B.every((v,i)=>v===START[i]))GAME.reset();
    const changed=!nb.every((v,i)=>v===B[i]);B=nb;last=st.last||[];qm=st.qm||0;sel=-1;cands=null;path=[];if(changed||!pcEl.children.length)fullRender();else marks()},
  reset(){B=START.slice();qm=0;last=[];sel=-1;cands=null;path=[];anim=false;fullRender()},
  render(){marks();if(sqEl.firstChild!==sqs[flip()?63:0])fullRender()},
  botMove(){botPlay(chooseBot(B,S.turn))}};
addEventListener('keydown',e=>{if(e.key==='Escape'&&!path.length){sel=-1;cands=null;marks()}});
