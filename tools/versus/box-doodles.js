/* Box Doodles: 6x6 dots, 25 boxes (so there's never a tie). Closing a box scores it and you draw again.
   Easy bot: often misses boxes. Medium: takes boxes, avoids drawing third sides. Hard: same, and when it has to give boxes away it gives the fewest. */
const NB=5,SP=100,NS='http://www.w3.org/2000/svg';
const E_=[];// edges: {x1,y1,x2,y2,boxes:[...]}
for(let r=0;r<=NB;r++)for(let c=0;c<NB;c++)E_.push({x1:c,y1:r,x2:c+1,y2:r,b:[r>0?(r-1)*NB+c:-1,r<NB?r*NB+c:-1].filter(v=>v>=0)});
for(let r=0;r<NB;r++)for(let c=0;c<=NB;c++)E_.push({x1:c,y1:r,x2:c,y2:r+1,b:[c>0?r*NB+c-1:-1,c<NB?r*NB+c:-1].filter(v=>v>=0)});
const BOX_E=[...Array(NB*NB)].map(()=>[]);E_.forEach((e,i)=>e.b.forEach(b=>BOX_E[b].push(i)));
let ED=Array(E_.length).fill(-1),BX=Array(NB*NB).fill(-1),last=-1;
const g=id=>document.getElementById(id),mk=(t,a)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);return e};
for(let r=0;r<=NB;r++)for(let c=0;c<=NB;c++)g('dotsg').appendChild(mk('circle',{class:'dot',cx:c*SP,cy:r*SP,r:9}));
const hits=E_.map((e,i)=>{const h=mk('line',{class:'hit',x1:e.x1*SP,y1:e.y1*SP,x2:e.x2*SP,y2:e.y2*SP,tabindex:0,role:'button','aria-label':'Line '+(i+1)});
  const gh=mk('line',{class:'ghost',x1:e.x1*SP+14*(e.x2-e.x1),y1:e.y1*SP+14*(e.y2-e.y1),x2:e.x2*SP-14*(e.x2-e.x1),y2:e.y2*SP-14*(e.y2-e.y1)});
  h.addEventListener('click',()=>tap(i));h.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();tap(i)}});g('hits').append(h,gh);return[h,gh]});
const sides=(ed,b)=>BOX_E[b].filter(i=>ed[i]>=0).length;
function closes(ed,i){return E_[i].b.filter(b=>sides(ed,b)===3).length}
function draw(){g('edges').innerHTML='';ED.forEach((p,i)=>{if(p<0)return;const e=E_[i];const w=()=>(Math.random()*3-1.5);
    g('edges').appendChild(mk('path',{class:'edge e'+p+(i===last?' last new':''),d:`M${e.x1*SP+w()} ${e.y1*SP+w()} Q${(e.x1+e.x2)*SP/2+w()*2} ${(e.y1+e.y2)*SP/2+w()*2} ${e.x2*SP+w()} ${e.y2*SP+w()}`}));
    hits[i][0].style.display='none';hits[i][1].style.display='none'})}
function claim(b,p){BX[b]=p;const r=Math.floor(b/NB),c=b%NB;const grp=mk('g',{class:'box'});
  grp.appendChild(mk('rect',{x:c*SP+6,y:r*SP+6,width:SP-12,height:SP-12,fill:`url(#h${p})`,rx:6}));
  const t=mk('text',{x:c*SP+SP/2,y:r*SP+SP/2});t.textContent=S.mode==='friend'?(p?'2':'1'):S.names()[p][0];grp.appendChild(t);g('boxes').appendChild(grp)}
function play(i){const p=S.turn;const got=E_[i].b.filter(b=>sides(ED,b)===3);ED[i]=p;last=i;draw();got.forEach(b=>claim(b,p));
  if(got.length){S.addScore(p,got.length);S.sfx('score')}else S.sfx(S.isBot()?'bot':'tap');
  if(BX.every(v=>v>=0)){const[a,b]=S.scores;S.end(a>b?0:1,`${a} boxes to ${b}.`);return}
  S.setTurn(got.length?p:1-p)}
function tap(i){if(!S.canPlay()||ED[i]>=0)return;play(i)}
const free=()=>ED.map((v,i)=>v<0?i:-1).filter(i=>i>=0);
const safe=i=>E_[i].b.every(b=>sides(ED,b)<2);
/* boxes the opponent could grab in a row after we draw edge i (greedy chain count) */
function giveaway(i){const ed=ED.slice();ed[i]=9;let n=0,go=true;while(go){go=false;for(let j=0;j<ed.length;j++)if(ed[j]<0&&closes(ed,j)){n+=closes(ed,j);ed[j]=9;go=true}}return n}
const GAME={save:()=>({E:ED.slice(),B:BX.slice(),last}),
  load(st){const e=st.E||[];if(!e.some(v=>v>=0)&&ED.some(v=>v>=0))GAME.reset();ED=e.length?e.slice():ED;last=st.last==null?-1:st.last;draw();(st.B||[]).forEach((p,b)=>{if(p>=0&&BX[b]<0)claim(b,p)})},
  reset(){ED.fill(-1);BX.fill(-1);last=-1;g('boxes').innerHTML='';g('edges').innerHTML='';hits.forEach(([h,gh])=>{h.style.display='';gh.style.display=''})},
  botMove(){const f=free();const cl=f.filter(i=>closes(ED,i));const sf=f.filter(safe);let m;
    if(S.diff==='easy'){m=cl.length&&Math.random()<.5?S.pick(cl):S.pick(f)}
    else if(S.diff==='medium'){m=cl.length&&Math.random()<.85?S.pick(cl):sf.length&&Math.random()<.8?S.pick(sf):S.pick(f)}
    else{if(cl.length)m=S.pick(cl);else if(sf.length)m=S.pick(sf);else{let lo=99;f.forEach(i=>{const k=giveaway(i);if(k<lo){lo=k;m=i}})}}
    play(m)}};
