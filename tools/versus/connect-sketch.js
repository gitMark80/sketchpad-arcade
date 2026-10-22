INFO.scoreIsRounds=true;
/* Connect Sketch: 7 columns x 6 rows, counters drop to the lowest space. Four in a row wins.
   Player 0 is blue, player 1 pink. Easy bot mostly random; Medium wins, blocks and avoids handing over a win;
   Hard searches ahead (negamax with alpha-beta). Board index = row*7+col, row 0 at the top. */
const W=7,H=6,NS='http://www.w3.org/2000/svg';
const $=id=>document.getElementById(id);
const mk=(t,a,p)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);if(p)p.appendChild(e);return e};
const CX=c=>c*100+50,CY=r=>r*100+50;
/* every line of four: list of [i,i,i,i] */
const LINES=[];for(let r=0;r<H;r++)for(let c=0;c<W;c++)for(const[dr,dc]of[[0,1],[1,0],[1,1],[1,-1]]){const er=r+3*dr,ec=c+3*dc;if(er<0||er>=H||ec<0||ec>=W)continue;LINES.push([0,1,2,3].map(k=>(r+k*dr)*W+c+k*dc))}
const LINES_AT=[...Array(W*H)].map(()=>[]);LINES.forEach(l=>l.forEach(i=>LINES_AT[i].push(l)));
let B=Array(W*H).fill(-1),last=-1,winL=null,hover=3;
// ---------- drawing ----------
/* Mark's hand-drawn art: the frame (holes see-through) sits over the counters, so counters drop in behind it */
const ART='../assets/connect-sketch/',PIECE=[ART+'blue.webp',ART+'pink.webp'];
[...PIECE,ART+'frame.webp',ART+'sparkle.webp',ART+'mascot.webp'].forEach(u=>{const i=new Image();i.src=u});
/* little pencil mascot on the start and end cards */
['start','over'].forEach(id=>{const o=$(id),h=o&&o.querySelector('h2');if(!h)return;const m=document.createElement('img');m.className='c4deco';m.src=ART+'mascot.webp';m.alt='';h.before(m)});
function disc(p,x,y,cls){const g=mk('g',{class:'pc '+(cls||'')});const inner=mk('g',{},g);
  mk('image',{href:PIECE[p],x:x-43,y:y-43,width:86,height:86},inner);return g}
const colsG=$('cols');
const colEls=[...Array(W)].map((_,c)=>{const e=mk('rect',{class:'col',x:c*100,y:-130,width:100,height:850,tabindex:0,role:'button','aria-label':'Column '+(c+1)},colsG);
  e.addEventListener('click',()=>tap(c));e.addEventListener('pointerenter',()=>{hover=c;ghost()});
  e.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();tap(c)}});e.addEventListener('focus',()=>{hover=c;ghost()});return e});
$('c4svg').addEventListener('pointerleave',()=>{$('ghost').setAttribute('opacity',0)});
function ghost(){const g=$('ghost');g.innerHTML='';if(!S.canPlay()||colTop(B,hover)<0||!matchMedia('(hover:hover)').matches){g.setAttribute('opacity',0);return}
  g.appendChild(disc(S.turn,CX(hover),-82));g.setAttribute('opacity',.45)}
addEventListener('keydown',e=>{if(!S.active||e.ctrlKey||e.metaKey||e.altKey)return;if(document.querySelector('.over:not([hidden])'))return;
  if(/^[1-7]$/.test(e.key)){tap(+e.key-1);return}
  if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();hover=Math.max(0,Math.min(W-1,hover+(e.key==='ArrowLeft'?-1:1)));colEls[hover].focus()}});
function colTop(b,c){for(let r=H-1;r>=0;r--)if(b[r*W+c]<0)return r;return -1}
function drawPiece(i,p,anim){const r=Math.floor(i/W),c=i%W;const g=disc(p,CX(c),CY(r),anim?'drop':'');
  if(anim){g.style.setProperty('--d',(-(r+1)*100-50)+'px');g.style.setProperty('--t',(0.18+0.05*r).toFixed(2)+'s')}
  g.dataset.i=i;$('pieces').appendChild(g)}
function markLast(){document.querySelectorAll('#pieces .dot').forEach(d=>d.remove());if(last<0)return;
  const r=Math.floor(last/W),c=last%W;mk('circle',{class:'dot',cx:CX(c),cy:CY(r),r:7},$('pieces').querySelector(`[data-i="${last}"]>g`)||$('pieces'))}
function drawWin(l,p){const g=$('win');g.innerHTML='';const[a,,,d]=l;const x1=CX(a%W),y1=CY(Math.floor(a/W)),x2=CX(d%W),y2=CY(Math.floor(d/W));
  const ex=(x2-x1)*.12,ey=(y2-y1)*.12;l.forEach(i=>mk("circle",{cx:CX(i%W),cy:CY(Math.floor(i/W)),r:38},g));
  mk('path',{d:`M${x1-ex} ${y1-ey} L${x2+ex} ${y2+ey}`,stroke:S.col(p)},g);
  l.forEach((i,k)=>{const im=mk('image',{href:ART+'sparkle.webp',x:CX(i%W)+4,y:CY(Math.floor(i/W))-62,width:58,height:49},g);im.style.animationDelay=(.55+k*.1)+'s'})}
function lineAt(b,i){const p=b[i];for(const l of LINES_AT[i])if(l.every(k=>b[k]===p))return l;return null}
function updateLabels(){colEls.forEach((e,c)=>{const n=H-1-colTop(B,c);e.setAttribute('aria-label',`Column ${c+1}: `+(colTop(B,c)<0?'full':n+' counter'+(n===1?'':'s')))})}
// ---------- play ----------
function drop(c){const p=S.turn,r=colTop(B,c);const i=r*W+c;B[i]=p;last=i;drawPiece(i,p,true);markLast();updateLabels();
  S.sfx(S.isBot()?'bot':'tap');$('ghost').setAttribute('opacity',0);
  const l=lineAt(B,i);
  if(l){winL=l;drawWin(l,p);S.end(p,'Four in a row!');return}
  if(B.every(v=>v>=0)){S.end(-1,'The page is full and nobody got four in a row.');return}
  S.setTurn(1-p);ghost()}
function tap(c){if(!S.canPlay()||colTop(B,c)<0)return;drop(c)}
// ---------- bots ----------
const ORDER=[3,2,4,1,5,0,6];
function legal(b){return ORDER.filter(c=>b[c]<0)}
function wins(b,c,p){const r=colTop(b,c);if(r<0)return false;const i=r*W+c;b[i]=p;const w=!!lineAt(b,i);b[i]=-1;return w}
function winningCol(b,p){for(const c of ORDER)if(wins(b,c,p))return c;return -1}
/* safe = after I play c, the opponent can't win straight away */
function safe(b,c,me){const r=colTop(b,c);const i=r*W+c;b[i]=me;const bad=winningCol(b,1-me)>=0;b[i]=-1;return !bad}
const LW=[0,1,4,32];
function evalBoard(b,me){let s=0;for(const l of LINES){let m=0,o=0;for(const k of l){if(b[k]===me)m++;else if(b[k]>=0)o++}
    if(m&&!o)s+=LW[m];else if(o&&!m)s-=LW[o]}
  for(let r=0;r<H;r++){const v=b[r*W+3];if(v===me)s+=3;else if(v>=0)s-=3}return s}
/* iterative deepening with a time budget, so slow phones stay snappy */
let nodes=0,deadline=0,stop=false;
function negamax(b,depth,alpha,beta,p){if((++nodes&511)===0&&performance.now()>deadline)stop=true;if(stop)return 0;
  const moves=legal(b);if(!moves.length)return 0;
  for(const c of moves)if(wins(b,c,p))return 10000+depth;
  if(depth===0)return evalBoard(b,p);
  let best=-1e9;
  for(const c of moves){const r=colTop(b,c),i=r*W+c;b[i]=p;const v=-negamax(b,depth-1,-beta,-alpha,1-p);b[i]=-1;
    if(v>best)best=v;if(v>alpha)alpha=v;if(alpha>=beta)break}
  return best}
function hardMove(b,me){const t0=performance.now();const ws=winningCol(b,me);if(ws>=0)return ws;const bl=winningCol(b,1-me);if(bl>=0)return bl;
  const moves=legal(b);const ok=moves.filter(c=>safe(b,c,me));const pool=ok.length?ok:moves;
  deadline=t0+120;stop=false;let choice=pool[0];
  for(let depth=2;depth<=9;depth++){let bestV=-1e9,best=pool[0];
    for(const c of pool){const r=colTop(b,c),i=r*W+c;b[i]=me;const v=-negamax(b,depth-1,-1e9,1e9,1-me);b[i]=-1;if(stop)break;if(v>bestV){bestV=v;best=c}}
    if(stop)break;choice=best;GAME.lastDepth=depth;if(bestV>=9000)break}
  GAME.lastMs=performance.now()-t0;return choice}
function mediumMove(b,me){const ws=winningCol(b,me);if(ws>=0)return ws;const bl=winningCol(b,1-me);if(bl>=0)return bl;
  const moves=legal(b);const ok=moves.filter(c=>safe(b,c,me));const pool=ok.length?ok:moves;
  if(Math.random()<.5){let bv=-1e9,bc=pool[0];for(const c of pool){const r=colTop(b,c),i=r*W+c;b[i]=me;const v=evalBoard(b,me);b[i]=-1;if(v>bv){bv=v;bc=c}}return bc}
  return S.pick(pool)}
function easyMove(b,me){const moves=legal(b);if(Math.random()<.5){const ws=winningCol(b,me);if(ws>=0)return ws}
  if(Math.random()<.25){const bl=winningCol(b,1-me);if(bl>=0)return bl}
  /* lean a little toward the middle so it isn't silly */
  return Math.random()<.4?S.pick(moves.slice(0,3)):S.pick(moves)}
function pickMove(diff,b,me){return diff==='hard'?hardMove(b,me):diff==='medium'?mediumMove(b,me):easyMove(b,me)}
const GAME={
  save:()=>({B:B.slice(),last,win:winL}),
  load(st){const nb=st.B||[];if(!nb.some(v=>v>=0)&&B.some(v=>v>=0))GAME.reset();
    nb.forEach((v,i)=>{if(v>=0&&B[i]!==v){B[i]=v;drawPiece(i,v,true)}});
    last=st.last==null?-1:st.last;markLast();updateLabels();
    if(st.win&&!winL){winL=st.win;drawWin(winL,B[winL[0]])}ghost()},
  reset(){B.fill(-1);last=-1;winL=null;$('pieces').innerHTML='';$('win').innerHTML='';updateLabels();ghost()},
  render(){ghost()},
  botMove(){drop(pickMove(S.diff,B,S.turn))},
  /* for tests */
  _pick:pickMove,_lineAt:lineAt,_top:colTop};
updateLabels();
