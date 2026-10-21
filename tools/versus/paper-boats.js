/* Paper Boats (8x8, boats of 4, 3, 3 and 2). One shot a turn. Players hide boats with Shuffle, then Ready.
   vs Friend: the game asks to pass the phone between turns. Bots: Easy shoots about at random,
   Medium hunts around its hits, Hard also works out where boats can still fit. */
INFO.botDelay=800;INFO.endDelay=1500;
const W=8,LENS=[4,3,3,2],NAMES={4:'Big boat',3:'Boat',2:'Little boat'};
const $=id=>document.getElementById(id);
let fleets=[[],[]],shots=[[],[]],phase='setup',setupP=0,viewer=0,lastShot=[-1,-1];
function randFleet(){for(;;){const occ=new Set(),out=[];let ok=true;
  for(const L of LENS){let placed=false;for(let t=0;t<200&&!placed;t++){const v=Math.random()<.5,x=S.rand(v?W:W-L+1),y=S.rand(v?W-L+1:W);
      const cells=[...Array(L)].map((_,k)=>(y+(v?k:0))*W+x+(v?0:k));
      /* keep a gap round each boat so they never touch */
      if(cells.some(c=>{const cx=c%W,cy=Math.floor(c/W);for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const nx=cx+dx,ny=cy+dy;if(nx>=0&&ny>=0&&nx<W&&ny<W&&occ.has(ny*W+nx))return true}return false}))continue;
      cells.forEach(c=>occ.add(c));out.push({len:L,v,cells,sunk:false});placed=true}
    if(!placed){ok=false;break}}if(ok)return out}}
function cellsOf(el){if(!el.children.length)for(let i=0;i<W*W;i++){const b=document.createElement('button');b.type='button';b.className='c';b.dataset.i=i;el.appendChild(b)}return[...el.children]}
const tgtC=cellsOf($('tgt')),ownC=cellsOf($('own'));
tgtC.forEach(b=>b.onclick=()=>tap(+b.dataset.i));
function boatAt(f,i){return f.find(b=>b.cells.includes(i))}
function paint(cells,fleet,shotsOn,showBoats){cells.forEach((b,i)=>{const sh=shotsOn[i]||0,bt=boatAt(fleet,i);let cls='c';
    if(bt&&(showBoats||bt.sunk)){cls+=' boat'+(bt.v?' v':'')+(bt.cells[0]===i?' s':'')+(bt.cells[bt.len-1]===i?' e':'')+(bt.sunk?' sunk':'')}
    if(sh){cls+=' shot '+(sh===2?'hit':'miss')}b.className=cls;b.innerHTML=sh===2?'<i>✕</i>':sh===1?'<i></i>':'';
    b.setAttribute('aria-label',`Row ${Math.floor(i/W)+1} column ${i%W+1}`+(sh===2?': hit':sh===1?': splash':''))})}
function fleetList(f){$('fleetList').innerHTML=f.map(b=>`<li class="${b.sunk?'gone':''}"><span class="bt">${'<span></span>'.repeat(b.len)}</span>${NAMES[b.len]}</li>`).join('')}
function render(){
  if(phase==='setup'){const p=setupP;$('capT').textContent=(S.mode==='bot'?'Your':S.names()[p]+"'s")+' page: hide your boats';paint(tgtC,fleets[p],[],true);
    $('tgt').classList.remove('aim');$('setupBar').hidden=false;$('lower').hidden=true;return}
  $('setupBar').hidden=true;$('lower').hidden=false;const me=viewer,op=1-me;
  $('capT').textContent=S.mode==='bot'?"Bot's page: tap to fire":(S.names()[op]+"'s page");
  paint(tgtC,fleets[op],shots[me],!S.active);paint(ownC,fleets[me],shots[op],true);
  $('tgt').classList.toggle('aim',S.canPlay());fleetList(fleets[op]);
  const[lp,li]=lastShot;if(li>=0){const c=(lp===me?tgtC:ownC)[li];c.classList.add('just','new')}}
function setupDone(){if(S.mode==='bot'){fleets[1]=randFleet();phase='play';viewer=0;S.setTurn(S.startP);return}
  if(setupP===0){setupP=1;fleets[1]=randFleet();S.pass(S.names()[1],()=>{render();S.status('✏️ '+S.names()[1]+': hide your boats',1)});S.status('Pass to '+S.names()[1],1);return}
  phase='play';viewer=S.startP;S.pass(S.names()[S.startP],()=>S.setTurn(S.startP))}
$('shuffle').onclick=()=>{if(phase!=='setup')return;fleets[setupP]=randFleet();S.sfx('tap');render()};
$('ready').onclick=()=>{if(phase!=='setup'||!S.active)return;S.sfx('score');setupDone()};
function fire(i){const p=S.turn,op=1-p;const bt=boatAt(fleets[op],i);shots[p][i]=bt?2:1;lastShot=[p,i];let sunk=false;
  if(bt&&bt.cells.every(c=>shots[p][c]===2)){bt.sunk=true;sunk=true}
  render();
  if(bt){S.sfx('score');if(sunk){S.addScore(p,1);S.pop(NAMES[bt.len]+' found!',S.col(p))}else S.pop('Hit!',S.col(p))}else{S.sfx('miss');S.pop('Splash',S.col(p))}
  if(fleets[op].every(b=>b.sunk)){const n=shots[p].filter(Boolean).length;S.end(p,`All four boats found in ${n} shots.`);return}
  if(S.mode==='bot'){S.setTurn(op);return}
  S.busy=true;setTimeout(()=>{S.busy=false;if(!S.active)return;viewer=op;S.status('Pass to '+S.names()[op],op);S.pass(S.names()[op],()=>{lastShot=[-1,-1];S.setTurn(op)})},1100)}
function tap(i){if(phase!=='play'||!S.canPlay()||shots[S.turn][i])return;fire(i)}
/* ---------- bots ---------- */
const nb=i=>{const x=i%W,y=Math.floor(i/W);return[[x-1,y],[x+1,y],[x,y-1],[x,y+1]].filter(([a,b])=>a>=0&&b>=0&&a<W&&b<W).map(([a,b])=>b*W+a)};
function openHits(sh,f){return sh.map((v,i)=>v===2&&!boatAt(f,i).sunk?i:-1).filter(i=>i>=0)}
function targetMoves(sh,hits){if(!hits.length)return[];let c=[];
  if(hits.length>1){const xs=hits.map(i=>i%W),ys=hits.map(i=>Math.floor(i/W));
    if(new Set(ys).size===1){const y=ys[0];c=[Math.min(...xs)-1,Math.max(...xs)+1].filter(x=>x>=0&&x<W).map(x=>y*W+x)}
    else if(new Set(xs).size===1){const x=xs[0];c=[Math.min(...ys)-1,Math.max(...ys)+1].filter(y=>y>=0&&y<W).map(y=>y*W+x)}
    c=c.filter(i=>!sh[i])}
  if(!c.length)hits.forEach(h=>nb(h).forEach(n=>{if(!sh[n])c.push(n)}));return c}
function density(sh,f){const score=Array(W*W).fill(0);const hits=openHits(sh,f);
  f.filter(b=>!b.sunk).forEach(b=>{const L=b.len;for(let v=0;v<2;v++)for(let y=0;y<(v?W-L+1:W);y++)for(let x=0;x<(v?W:W-L+1);x++){
    const cells=[...Array(L)].map((_,k)=>(y+(v?k:0))*W+x+(v?0:k));
    if(cells.some(c=>sh[c]===1||(sh[c]===2&&boatAt(f,c).sunk)))continue;
    const h=cells.filter(c=>sh[c]===2).length;if(hits.length&&!h)continue;const w=h?1+h*20:1;cells.forEach(c=>{if(!sh[c])score[c]+=w})}});
  let best=-1,out=[];score.forEach((s,i)=>{if(sh[i])return;if(s>best){best=s;out=[i]}else if(s===best)out.push(i)});return out}
const GAME={reset(){fleets=[randFleet(),[]];shots=[Array(W*W).fill(0),Array(W*W).fill(0)];phase='setup';setupP=0;viewer=0;lastShot=[-1,-1];render()},
  begin(st){S.startP=st;phase='setup';setupP=0;render();S.status('✏️ '+(S.mode==='bot'?'Hide your boats, then tap Ready':S.names()[0]+': hide your boats'),0);S.hud()},
  render,
  botMove(){const sh=shots[1],f=fleets[0];const free=sh.map((v,i)=>v?-1:i).filter(i=>i>=0);const hits=openHits(sh,f);let m;
    if(S.diff==='easy'){const t=targetMoves(sh,hits);m=t.length&&Math.random()<.25?S.pick(t):S.pick(free)}
    else if(S.diff==='medium'){const t=targetMoves(sh,hits);if(t.length)m=S.pick(t);else{const par=free.filter(i=>(i%W+Math.floor(i/W))%2===0);m=S.pick(par.length&&Math.random()<.7?par:free)}}
    else m=S.pick(density(sh,f));
    fire(m)}};
