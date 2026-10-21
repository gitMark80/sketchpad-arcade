INFO.best='time';INFO.bestLabel='Best times';INFO.winHead='Page saved!';INFO.loseHead='Splat!';INFO.endDelay=1300;
/*SHELL*/
/* Blot Sweeper: Minesweeper with ink blots. First tap is always safe (and opens an area). */
const LV={easy:[8,8,10],medium:[9,11,18],hard:[10,13,30]};
const bEl=document.getElementById('board');
let C=0,R=0,M=0,blot=[],open=[],flag=[],cnt=[],cells=[],placed=false,mode='dig',left=0;
const FLAG='<svg viewBox="0 0 40 40"><path d="M13 35 L13 6" stroke="#2e2e33" stroke-width="3.5" stroke-linecap="round"/><path d="M14 7 C22 4 26 12 33 9 L32 21 C25 24 21 16 14 19 Z" fill="#f0c9a8" stroke="#d9661a" stroke-width="2.5" stroke-linejoin="round"/><path d="M7 35 L20 35" stroke="#2e2e33" stroke-width="3" stroke-linecap="round"/></svg>';
const BLOT='<svg viewBox="0 0 40 40"><path d="M20 6 C25 6 26 11 30 10 C35 9 35 15 32 18 C36 21 35 27 30 27 C31 32 26 35 22 32 C18 36 12 34 13 29 C7 30 5 24 9 21 C5 17 8 11 13 13 C13 8 16 6 20 6 Z" fill="#2e2e33"/><circle cx="34" cy="31" r="2.5" fill="#2e2e33"/><circle cx="6" cy="10" r="2" fill="#2e2e33"/><path d="M15 15 C17 13 19 13 20 14" stroke="#f6f3ea" stroke-width="2" fill="none" stroke-linecap="round" opacity=".7"/></svg>';
document.querySelectorAll('.md').forEach(b=>b.onclick=()=>{mode=b.dataset.m;document.querySelectorAll('.md').forEach(x=>{x.classList.toggle('on',x===b);x.setAttribute('aria-checked',x===b)});P.sfx('soft')});
const nbrs=i=>{const x=i%C,y=Math.floor(i/C),o=[];for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){if(!dx&&!dy)continue;const a=x+dx,b=y+dy;if(a>=0&&b>=0&&a<C&&b<R)o.push(b*C+a)}return o};
function place(safe){const ban=new Set([safe,...nbrs(safe)]);const pool=[...Array(C*R).keys()].filter(i=>!ban.has(i));P.shuffle(pool).slice(0,M).forEach(i=>blot[i]=1);
  for(let i=0;i<C*R;i++)cnt[i]=nbrs(i).filter(j=>blot[j]).length;placed=true}
function stat(){P.stat(M-flag.filter(Boolean).length)}
function paint(i){const k=cells[i];let cls='k';let h='';
  if(open[i]){cls+=' open';if(blot[i])h=BLOT;else if(cnt[i]){h=cnt[i];cls+=' n'+cnt[i]}}else if(flag[i])h=FLAG;
  k.className=cls;k.innerHTML=h;k.setAttribute('aria-label',`Row ${Math.floor(i/C)+1} column ${i%C+1}: `+(open[i]?(blot[i]?'blot':cnt[i]?cnt[i]:'empty'):flag[i]?'flagged':'covered'))}
function reveal(i){const st=[i];let n=0;while(st.length){const j=st.pop();if(open[j]||flag[j])continue;open[j]=1;n++;left--;paint(j);cells[j].classList.add('opn');if(!cnt[j]&&!blot[j])nbrs(j).forEach(k=>{if(!open[k])st.push(k)})}return n}
function lose(i){open[i]=1;paint(i);cells[i].classList.add('boom');
  blot.forEach((b,j)=>{if(b&&!flag[j]){open[j]=1;paint(j)}if(!b&&flag[j])cells[j].classList.add('wrongflag')});cells[i].classList.add('boom');P.lose('You uncovered an ink blot. Try again!')}
function checkWin(){if(left===0){blot.forEach((b,j)=>{if(b&&!flag[j]){flag[j]=1;paint(j)}});stat();P.pop('Clean page!');P.win(null,'Every clean square uncovered in '+P.fmt(P.secs)+'.')}}
function act(i,asFlag){if(!P.active)return;
  if(asFlag){if(open[i])return;flag[i]=flag[i]?0:1;paint(i);stat();P.sfx('flag');return}
  if(flag[i])return;
  if(open[i]){/* chord */if(!cnt[i])return;const ns=nbrs(i);if(ns.filter(j=>flag[j]).length!==cnt[i])return;let hit=-1;ns.forEach(j=>{if(!open[j]&&!flag[j]){if(blot[j])hit=j;else reveal(j)}});
    if(hit>=0){lose(hit);return}P.sfx('soft');checkWin();return}
  if(!placed){place(i);P.msg('')}P.go();
  if(blot[i]){lose(i);return}
  const n=reveal(i);P.sfx(n>3?'good':'tap');checkWin()}
const GAME={reset(d){[C,R,M]=LV[d];bEl.style.setProperty('--cols',C);bEl.style.setProperty('--rows',R);
    bEl.style.setProperty('--bw',`calc((100dvh - 260px) * ${C/R})`);
    blot=Array(C*R).fill(0);open=Array(C*R).fill(0);flag=Array(C*R).fill(0);cnt=Array(C*R).fill(0);placed=false;left=C*R-M;
    bEl.innerHTML='';cells=[...Array(C*R)].map((_,i)=>{const b=document.createElement('button');b.type='button';b.className='k';
      let hold=0,held=false;
      b.addEventListener('pointerdown',e=>{held=false;clearTimeout(hold);hold=setTimeout(()=>{held=true;act(i,true);if(navigator.vibrate)try{navigator.vibrate(15)}catch(e){}},420)});
      ['pointerup','pointerleave','pointercancel'].forEach(t=>b.addEventListener(t,()=>clearTimeout(hold)));
      b.addEventListener('click',e=>{if(held){held=false;return}act(i,mode==='flag')});
      b.addEventListener('contextmenu',e=>{e.preventDefault();if(!held)act(i,true);held=false});
      bEl.appendChild(b);return b});
    cells.forEach((_,i)=>paint(i));stat();P.msg('Tap any square to start. Your first tap is safe.')}};
