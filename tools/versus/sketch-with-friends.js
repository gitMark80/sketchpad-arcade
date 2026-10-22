/* Sketch with Friends: a two-player crossword tile game on an 11x11 sketchbook board.
   Our own board layout, letter points and tile counts (70 tiles, no blanks). Words come from the kid-safe list in
   /assets/sketch-with-friends/words.txt (made by tools/sketch-with-friends-words.py). The bot builds every legal move
   with a letter tree (anchor squares + cross-checks) and picks a weak, middling or best one for Easy, Medium, Hard.
   Racks are private: pass & play hands the phone over between turns. Online, both racks and the bag are in the saved
   game (fine for a friendly game; a curious kid could peek with browser tools). */
INFO.botDelay=700;INFO.endDelay=1600;
const N=11,CEN=60;
const VAL={a:1,b:4,c:4,d:2,e:1,f:4,g:3,h:3,i:1,j:9,k:5,l:2,m:4,n:2,o:1,p:4,q:10,r:1,s:1,t:1,u:2,v:5,w:4,x:8,y:3,z:10};
/* 70 tiles: the 11x11 board fills up fast, so fewer tiles than a big board would use */
const COUNT={a:5,b:2,c:2,d:3,e:8,f:1,g:2,h:2,i:6,j:1,k:1,l:3,m:2,n:3,o:5,p:2,q:1,r:4,s:4,t:4,u:3,v:1,w:1,x:1,y:2,z:1};
/* premium squares: one eighth of the board, mirrored to the rest */
const QUAD={'0,0':'tl','0,3':'tw','0,5':'dl','1,1':'dw','1,4':'dl','2,2':'tl','2,5':'dl','3,3':'dw','4,4':'dl','5,5':'st'};
const PREM=[...Array(N*N)].map((_,i)=>{const r=Math.floor(i/N),c=i%N,a=Math.min(r,N-1-r),b=Math.min(c,N-1-c);return QUAD[Math.min(a,b)+','+Math.max(a,b)]||''});
const LABEL={dl:'DL',tl:'TL',dw:'DW',tw:'TW',st:'★'};
const LM_=i=>PREM[i]==='dl'?2:PREM[i]==='tl'?3:1, WM_=i=>PREM[i]==='dw'||PREM[i]==='st'?2:PREM[i]==='tw'?3:1;
const row=i=>Math.floor(i/N),col=i=>i%N;
const $w=id=>document.getElementById(id);
let B=Array(N*N).fill(''),O=Array(N*N).fill(-1),R=[[],[]],BAG=[],LAST=[],LM=null,PASSES=0;
let pend=[],sel=-1,swapMode=false,swapSel=new Set(),handoff=false,passArm=0;
/* ---------- words ---------- */
let WORDS=null,WLIST=null,T=null;
fetch('../assets/sketch-with-friends/words.txt').then(r=>r.text()).then(txt=>{const out=[];let prev='';
  for(const ln of txt.split('\n')){if(!ln)continue;const k=ln.charCodeAt(0)-48,w=prev.slice(0,k)+ln.slice(1);out.push(w);prev=w}
  WLIST=out;WORDS=new Set(out);render()}).catch(()=>{WLIST=[];WORDS=new Set();render()});
const isWord=w=>!!WORDS&&WORDS.has(w);
function trie(){if(T)return T;const first=[0],cnt=[0],end=[0],ech=[],eto=[];const words=WLIST;
  const st=[[0,0,words.length,0]];
  while(st.length){let[nd,lo,hi,d]=st.pop();if(lo<hi&&words[lo].length===d){end[nd]=1;lo++}
    const g=[];let i=lo;while(i<hi){const ch=words[i].charCodeAt(d);let j=i+1;while(j<hi&&words[j].charCodeAt(d)===ch)j++;g.push([ch-97,i,j]);i=j}
    first[nd]=ech.length;cnt[nd]=g.length;g.forEach(([ch])=>{ech.push(ch);eto.push(0)});
    g.forEach(([ch,a,b],k)=>{const c=first.length;first.push(0);cnt.push(0);end.push(0);eto[first[nd]+k]=c;st.push([c,a,b,d+1])})}
  T={first:Int32Array.from(first),cnt:Uint8Array.from(cnt),end:Uint8Array.from(end),ech:Uint8Array.from(ech),eto:Int32Array.from(eto)};return T}
function child(nd,ch){const f=T.first[nd],n=T.cnt[nd];for(let k=f;k<f+n;k++)if(T.ech[k]===ch)return T.eto[k];return -1}
/* ---------- rules ---------- */
function stepOK(i,d,back){/* is the square one step along d (or back) still on the same line? */const j=back?i-d:i+d;if(j<0||j>=N*N)return false;return d===N||row(j)===row(i)}
function wordAt(g,i,d){let s=i;while(stepOK(s,d,true)&&g[s-d])s-=d;let w='',cells=[],k=s;while(true){w+=g[k];cells.push(k);if(!stepOK(k,d)||!g[k+d])break;k+=d}return{w,cells}}
function evaluate(pl,board){board=board||B;if(!pl.length)return{ok:false,err:''};
  const rs=new Set(pl.map(p=>row(p.i))),cs=new Set(pl.map(p=>col(p.i)));
  if(rs.size>1&&cs.size>1)return{ok:false,err:'Put your tiles in one straight line.',bad:true};
  const g=board.slice();pl.forEach(p=>g[p.i]=p.l);const nw=new Set(pl.map(p=>p.i)),empty=board.every(x=>!x);
  let d;if(pl.length>1)d=rs.size===1?1:N;else{const i=pl[0].i;d=(stepOK(i,1,true)&&g[i-1])||(stepOK(i,1)&&g[i+1])?1:N}
  const idx=pl.map(p=>p.i).sort((a,b)=>a-b);for(let k=idx[0];k<=idx[idx.length-1];k+=d)if(!g[k])return{ok:false,err:'No gaps between your tiles.',bad:true};
  if(empty){if(!nw.has(CEN))return{ok:false,err:'Your first word must cover the ★ in the middle.',bad:true}}
  else if(!pl.some(p=>[-1,1,-N,N].some(o=>{const j=p.i+o;return j>=0&&j<N*N&&(Math.abs(o)===N||row(j)===row(p.i))&&board[j]})))return{ok:false,err:'Join your word onto the words on the board.',bad:true};
  const words=[];const main=wordAt(g,idx[0],d);if(main.w.length>1)words.push(main);
  pl.forEach(p=>{const x=wordAt(g,p.i,d===1?N:1);if(x.w.length>1)words.push(x)});
  if(!words.length)return{ok:false,err:'Make a word of at least 2 letters.',bad:true};
  let total=0;words.forEach(x=>{let s=0,m=1;x.cells.forEach(k=>{const v=VAL[g[k]];if(nw.has(k)){s+=v*LM_(k);m*=WM_(k)}else s+=v});x.score=s*m;total+=x.score});
  if(pl.length===7)total+=35;
  const main1=words[0].w;
  if(!WORDS)return{ok:false,err:'Loading the word list…',words,score:total,main:main1};
  const bad=words.find(x=>!isWord(x.w));
  if(bad)return{ok:false,err:`“${bad.w.toUpperCase()}” isn't in our word list.`,words,score:total,main:main1,notword:true};
  return{ok:true,words,score:total,main:main1,bingo:pl.length===7}}
/* ---------- turns ---------- */
function shuffle(a){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}
function draw(p){while(R[p].length<7&&BAG.length)R[p].push(BAG.pop())}
const rackVal=p=>R[p].reduce((s,l)=>s+VAL[l],0);
const nm=p=>S.names()[p];
function nextTurn(){pend=[];sel=-1;swapMode=false;swapSel.clear();const n=1-S.turn;
  if(S.mode==='friend'){handoff=true;S.setTurn(n);S.pass(nm(n),()=>{handoff=false;render()})}else S.setTurn(n)}
function finishOut(p){const o=1-p,left=rackVal(o);S.scores[o]-=left;S.scores[p]+=left;
  const[a,b]=S.scores;S.end(a>b?0:b>a?1:-1,`${nm(p)} used every tile${left?` and took ${left} points from the tiles left over`:''}. Final score ${a} to ${b}.`)}
function finishPasses(){S.scores[0]-=rackVal(0);S.scores[1]-=rackVal(1);const[a,b]=S.scores;
  S.end(a>b?0:b>a?1:-1,`Four turns in a row with no word, so the game is over. Leftover tiles were taken off. Final score ${a} to ${b}.`)}
function commit(pl,ev){const p=S.turn;pl.forEach(x=>{B[x.i]=x.l;O[x.i]=p;const j=R[p].indexOf(x.l);if(j>=0)R[p].splice(j,1)});
  draw(p);LAST=pl.map(x=>x.i);LM={p,t:`played ${ev.main.toUpperCase()} for ${ev.score}`};PASSES=0;pend=[];sel=-1;
  S.addScore(p,ev.score);S.sfx('score');S.pop(ev.bingo?'All 7! +'+ev.score:'+'+ev.score,S.col(p));if(ev.bingo)cheer();
  if(!R[p].length&&!BAG.length){render();finishOut(p);return}nextTurn()}
function doSwap(p,letters){letters.forEach(l=>{const j=R[p].indexOf(l);R[p].splice(j,1)});BAG.push(...letters);shuffle(BAG);draw(p);
  LM={p,t:`swapped ${letters.length} tile${letters.length>1?'s':''}`};PASSES++;S.sfx('tap');if(PASSES>=4){render();finishPasses();return}nextTurn()}
function doPass(p){LM={p,t:'passed'};PASSES++;S.sfx('miss');if(PASSES>=4){render();finishPasses();return}nextTurn()}
/* ---------- your moves ---------- */
const mine=()=>S.canPlay()&&!handoff;
function rackOf(){return R[S.viewer()]||[]}
function place(i,j){if(!mine()||B[i]||pend.some(p=>p.i===i)||j<0||pend.some(p=>p.ri===j))return;const l=rackOf()[j];if(!l)return;pend.push({i,ri:j,l});sel=-1;S.sfx('tap');render()}
function cellTap(i){if(!mine())return;const k=pend.findIndex(p=>p.i===i);if(k>=0){pend.splice(k,1);S.sfx('tap');render();return}
  if(swapMode)return;if(sel>=0)place(i,sel)}
function rackTap(j){if(!mine())return;if(swapMode){swapSel.has(j)?swapSel.delete(j):swapSel.add(j);S.sfx('tap');render();return}
  if(pend.some(p=>p.ri===j))return;sel=sel===j?-1:j;S.sfx('tap');render()}
$w('wMix').onclick=()=>{if(!mine())return;if(pend.length){pend=[];sel=-1}else{const r=rackOf();shuffle(r);sel=-1}S.sfx('tap');render()};
$w('wSwap').onclick=()=>{if(!mine())return;pend=[];sel=-1;swapMode=!swapMode;swapSel.clear();S.sfx('tap');render()};
$w('wPass').onclick=()=>{if(!mine())return;if(!passArm){passArm=setTimeout(()=>{passArm=0;render()},2500);render();return}clearTimeout(passArm);passArm=0;doPass(S.turn)};
$w('wPlay').onclick=()=>{if(!mine())return;const p=S.turn;
  if(swapMode){if(!swapSel.size)return;const r=rackOf();doSwap(p,[...swapSel].map(j=>r[j]));return}
  const ev=evaluate(pend);if(!ev.ok){S.sfx('miss');S.pop(ev.notword?'Not a word':'Oops!','#d9661a');render();return}commit(pend.slice(),ev)};
/* drag a rack tile onto the board */
let drag=null,justDragged=false;
function cellAt(x,y){const el=document.elementFromPoint(x,y);const c=el&&el.closest&&el.closest('.sq');return c?+c.dataset.i:-1}
function dragStart(e,j){if(!mine()||swapMode||pend.some(p=>p.ri===j))return;drag={j,x:e.clientX,y:e.clientY,on:false,el:null,over:-1};try{e.target.setPointerCapture(e.pointerId)}catch(_){}}
addEventListener('pointermove',e=>{if(!drag)return;if(!drag.on){if(Math.hypot(e.clientX-drag.x,e.clientY-drag.y)<7)return;drag.on=true;drag.el=document.createElement('div');drag.el.className='ghost';drag.el.textContent=rackOf()[drag.j];document.body.appendChild(drag.el)}
  drag.el.style.left=e.clientX+'px';drag.el.style.top=e.clientY+'px';const i=cellAt(e.clientX,e.clientY-26);if(i!==drag.over){if(drag.over>=0)cells[drag.over].classList.remove('drop');drag.over=i;if(i>=0&&!B[i])cells[i].classList.add('drop')}});
function dragEnd(e){if(!drag)return;const d=drag;drag=null;if(!d.on)return;justDragged=true;setTimeout(()=>justDragged=false,0);d.el.remove();if(d.over>=0){cells[d.over].classList.remove('drop');place(d.over,d.j)}}
addEventListener('pointerup',dragEnd);addEventListener('pointercancel',()=>{if(drag&&drag.el)drag.el.remove();if(drag&&drag.over>=0)cells[drag.over].classList.remove('drop');drag=null});
/* ---------- drawing ---------- */
const boardEl=$w('board');
const cells=[...Array(N*N)].map((_,i)=>{const b=document.createElement('button');b.type='button';b.className='sq '+PREM[i];b.dataset.i=i;b.onclick=()=>cellTap(i);boardEl.appendChild(b);return b});
/* Mark's hand-drawn art (src/assets/sketch-with-friends/) */
const ART='../assets/sketch-with-friends/';
['tile','tileglow','dl','tl','dw','tw','start','rack','bag','mascot'].forEach(n=>{const im=new Image();im.src=ART+n+'.webp'});
function cheer(){const st=document.getElementById('stage');if(!st)return;const m=document.createElement('img');m.className='cheer';m.src=ART+'mascot.webp';m.alt='';st.appendChild(m);setTimeout(()=>m.remove(),1800)}
const tileHTML=(l,cls)=>`<span class="tile ${cls}">${l}<i>${VAL[l]}</i></span>`;
function render(){const ev=pend.length?evaluate(pend):null,badSet=ev&&!ev.ok?new Set(pend.map(p=>p.i)):null,last=new Set(LAST);
  cells.forEach((c,i)=>{const p=pend.find(x=>x.i===i);let h='';
    if(B[i])h=tileHTML(B[i],'o'+O[i]+(last.has(i)?' last':''));else if(p)h=tileHTML(p.l,'pend'+(badSet?' bad':''));else h=LABEL[PREM[i]]||'';
    if(c._h!==h){c.innerHTML=h;c._h=h}
    c.setAttribute('aria-label',`Row ${row(i)+1} column ${col(i)+1}: `+(B[i]||(p&&p.l)||(PREM[i]?LABEL[PREM[i]]:'empty')))});
  const rk=$w('rack'),v=S.viewer(),hide=handoff||(S.mode==='bot'&&v!==0)||v<0;rk.classList.toggle('hide',hide);
  const r=R[v]||[];rk.innerHTML='';
  if(hide&&S.active){rk.innerHTML='<span class="note">Tiles hidden</span>'}
  else r.forEach((l,j)=>{const b=document.createElement('button');b.type='button';b.className='rk'+(sel===j?' sel':'')+(swapSel.has(j)?' swap':'')+(pend.some(p=>p.ri===j)?' gone':'');
    b.innerHTML=l+'<i>'+VAL[l]+'</i>';b.setAttribute('aria-label','Tile '+l.toUpperCase()+', '+VAL[l]+' points');
    b.onclick=()=>{if(!justDragged)rackTap(j)};b.addEventListener('pointerdown',e=>dragStart(e,j));rk.appendChild(b)});
  const line=$w('wline');
  if(swapMode)line.textContent='Tap the tiles to swap, then tap Swap.';
  else if(ev){if(ev.ok)line.innerHTML=`<b>${ev.main}</b> <span class="ok">✓ ${ev.score} point${ev.score===1?'':'s'}</span>`+(ev.words.length>1?` <span>(${ev.words.length} words)</span>`:'');
    else if(ev.words)line.innerHTML=`<b>${ev.main}</b> <span class="no">✗ ${ev.err}</span>`;else line.innerHTML=`<span class="no">${ev.err}</span>`}
  else{const t=LM?`${nm(LM.p)} ${LM.t}`:(S.active?'First word must cover the ★':'');line.textContent=t+(S.active&&t?' · ':'');
    if(S.active){const bg=document.createElement('span');bg.className='bagc';bg.innerHTML='<img src="'+ART+'bag.webp" alt="">';bg.append('Bag: '+BAG.length);line.appendChild(bg)}}
  const can=mine();$w('wMix').textContent=pend.length?'↩ Recall':'🔀 Shuffle';$w('wMix').disabled=!can;
  $w('wSwap').textContent=swapMode?'✕ Cancel':'♻ Swap';$w('wSwap').disabled=!can||(!swapMode&&!BAG.length);
  $w('wPass').textContent=passArm?'Sure?':'Pass';$w('wPass').disabled=!can||swapMode;
  $w('wPlay').textContent=swapMode?'Swap '+swapSel.size:'Play';$w('wPlay').disabled=!can||(swapMode?!swapSel.size||swapSel.size>BAG.length:!pend.length)}
/* ---------- bot ---------- */
function allMoves(rackLetters,board,cap){board=board||B;cap=cap||5000;trie();const cnt=Array(26).fill(0);rackLetters.forEach(l=>cnt[l.charCodeAt(0)-97]++);
  const empty=board.every(x=>!x),out=[],seen=new Set();
  for(const d of[1,N]){const pd=d===1?N:1;
    for(let line=0;line<N;line++){const at=pos=>d===1?line*N+pos:pos*N+line;const L=[...Array(N)].map((_,p)=>board[at(p)]);
      /* cross-checks: letters allowed in each empty square by the words running the other way */
      const cross=Array(N).fill(0x3ffffff),anchor=Array(N).fill(false);
      for(let p=0;p<N;p++){const i=at(p);if(L[p])continue;
        const nb=[-pd,pd].some(o=>{const j=i+o;return j>=0&&j<N*N&&(pd===N||row(j)===row(i))&&board[j]});
        const ln=[-d,d].some(o=>{const j=i+o;return j>=0&&j<N*N&&(d===N||row(j)===row(i))&&board[j]});
        anchor[p]=empty?i===CEN:(nb||ln);
        if(nb){let m=0;const g=board.slice();for(let c=0;c<26;c++){g[i]=String.fromCharCode(97+c);if(isWord(wordAt(g,i,pd).w))m|=1<<c}cross[p]=m}}
      for(let a=0;a<N;a++){if(!anchor[a]||out.length>=cap)continue;
        const ext=(nd,pos,placed)=>{if(out.length>=cap)return;
          if((pos>=N||!L[pos])&&T.end[nd]&&pos>a){const key=placed.map(x=>at(x[0])+':'+x[1]).join('|');if(!seen.has(key)){seen.add(key);out.push(placed.map(([p,c])=>({i:at(p),l:String.fromCharCode(97+c)})))}}
          if(pos>=N)return;
          if(!L[pos]){const f=T.first[nd],n=T.cnt[nd];for(let k=f;k<f+n;k++){const c=T.ech[k];if(cnt[c]&&(cross[pos]>>c&1)){cnt[c]--;ext(T.eto[k],pos+1,placed.concat([[pos,c]]));cnt[c]++}}}
          else{const c=child(nd,L[pos].charCodeAt(0)-97);if(c>=0)ext(c,pos+1,placed)}};
        if(a>0&&L[a-1]){let s=a-1;while(s>0&&L[s-1])s--;let nd=0;for(let k=s;k<a&&nd>=0;k++)nd=child(nd,L[k].charCodeAt(0)-97);if(nd>=0)ext(nd,a,[])}
        else{let lim=0;for(let k=a-1;k>=0&&!L[k]&&!anchor[k];k--)lim++;lim=Math.min(lim,6);
          const left=(nd,part)=>{/* part = letters placed before the anchor, ending at a-1 */
            ext(nd,a,part.map((c,k)=>[a-part.length+k,c]));
            if(part.length>=lim)return;const f=T.first[nd],n=T.cnt[nd];
            for(let k=f;k<f+n;k++){const c=T.ech[k];if(cnt[c]){cnt[c]--;left(T.eto[k],part.concat([c]));cnt[c]++}}};
          left(0,[])}}}}
  return out}
function scoredMoves(rackLetters,board){const ms=allMoves(rackLetters,board);const res=[];for(const m of ms){const ev=evaluate(m,board);if(ev.ok)res.push({m,ev})}res.sort((a,b)=>b.ev.score-a.ev.score);return res}
function botPick(list){if(!list.length)return null;if(S.diff==='hard')return list[0];
  if(S.diff==='medium'){const top=list[0].ev.score,mid=list.filter(x=>x.ev.score<=top*.75&&x.ev.score>=top*.35);return mid.length?S.pick(mid):list[Math.floor(list.length/2)]}
  const short=list.filter(x=>x.ev.main.length<=4),pool=(short.length?short:list);return pool[Math.floor(pool.length*(.5+Math.random()*.5))]||pool[pool.length-1]}
const GAME={
  reset(){B=Array(N*N).fill('');O=Array(N*N).fill(-1);BAG=[];for(const l in COUNT)for(let k=0;k<COUNT[l];k++)BAG.push(l);shuffle(BAG);R=[[],[]];draw(0);draw(1);
    LAST=[];LM=null;PASSES=0;pend=[];sel=-1;swapMode=false;swapSel.clear();handoff=false;render()},
  begin(st){if(S.mode==='bot'&&WLIST&&!T)setTimeout(trie,60);if(S.mode==='friend'){handoff=true;S.setTurn(st);S.pass(nm(st),()=>{handoff=false;render()})}else S.setTurn(st)},
  render,
  save(){return{b:B.map(x=>x||'.').join(''),o:O.map(x=>x<0?'.':x).join(''),r:[R[0].join(''),R[1].join('')],g:BAG.join(''),l:LAST,m:LM,p:PASSES}},
  load(st){if(!st||!st.b){render();return}B=[...st.b].map(x=>x==='.'?'':x);O=[...st.o].map(x=>x==='.'?-1:+x);R=[[...(st.r[0]||'')],[...(st.r[1]||'')]];BAG=[...(st.g||'')];
    LAST=st.l||[];LM=st.m||null;PASSES=st.p||0;pend=[];sel=-1;swapMode=false;swapSel.clear();handoff=false;render()},
  botMove(){const p=S.turn,t0=performance.now();const list=scoredMoves(R[p]);GAME.lastBotMs=Math.round(performance.now()-t0);const mv=botPick(list);
    if(mv){commit(mv.m,mv.ev);return}
    if(BAG.length){const r=R[p].slice().sort((a,b)=>VAL[b]-VAL[a]);doSwap(p,r.slice(0,Math.min(BAG.length,4)));return}
    doPass(p)},
  evaluate,scoredMoves};
