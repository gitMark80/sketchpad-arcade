INFO.best='time';INFO.bestLabel='Best times';INFO.winHead='Solved!';
/*SHELL*/
/* Doodle Doku: 9x9 Sudoku. Puzzles are made on the spot and always have exactly one answer.
   Easy keeps about 40 numbers, Medium about 32, Hard as few as 25. Mistakes are counted but never end the game. */
const GIVENS={easy:40,medium:32,hard:25};
const $=id=>document.getElementById(id);
const ROW=i=>Math.floor(i/9),COL=i=>i%9,BOX=i=>Math.floor(ROW(i)/3)*3+Math.floor(COL(i)/3);
const PEERS=[...Array(81)].map((_,i)=>[...Array(81).keys()].filter(j=>j!==i&&(ROW(j)===ROW(i)||COL(j)===COL(i)||BOX(j)===BOX(i))));
function solve(g,limit){/* counts solutions up to limit; fills g with the first one found when limit===1 */
  let count=0;const a=g.slice();
  const cand=i=>{let m=0x3fe;for(const j of PEERS[i])if(a[j])m&=~(1<<a[j]);return m};
  function rec(){let best=-1,bm=0,bc=10;for(let i=0;i<81;i++)if(!a[i]){const m=cand(i);let c=0;for(let v=1;v<=9;v++)if(m>>v&1)c++;if(c<bc){bc=c;best=i;bm=m;if(c<2)break}}
    if(best<0){count++;if(limit===1)g.splice(0,81,...a);return count>=limit}
    if(!bc)return false;const vals=[];for(let v=1;v<=9;v++)if(bm>>v&1)vals.push(v);if(limit===1)P.shuffle(vals);
    for(const v of vals){a[best]=v;if(rec())return true}a[best]=0;return false}
  rec();return count}
function make(d){const sol=Array(81).fill(0);solve(sol,1);const puz=sol.slice();let n=81;
  for(const i of P.shuffle([...Array(81).keys()])){if(n<=GIVENS[d])break;const v=puz[i];puz[i]=0;if(solve(puz,2)!==1)puz[i]=v;else n--}
  return{sol,puz}}
let SOL=[],G=[],GIV=[],NOTES=[],sel=-1,notesOn=false,mistakes=0,hints=3;
const boardEl=$('board'),padEl=$('pad');
const cells=[...Array(81)].map((_,i)=>{const b=document.createElement('button');b.type='button';b.className='q';b.onclick=()=>select(i);boardEl.appendChild(b);return b});
const padBtns=[...Array(9)].map((_,k)=>{const b=document.createElement('button');b.type='button';b.innerHTML=`${k+1}<small></small>`;b.setAttribute('aria-label','Number '+(k+1));b.onclick=()=>enter(k+1);padEl.appendChild(b);return b});
$('notes').onclick=()=>{notesOn=!notesOn;$('notes').setAttribute('aria-pressed',notesOn);$('notes').textContent='✏️ Notes: '+(notesOn?'On':'Off');P.sfx('soft')};
$('erase').onclick=()=>{if(!P.active||sel<0||GIV[sel])return;G[sel]=0;NOTES[sel]=0;P.sfx('soft');paint()};
$('hint').onclick=()=>{if(!P.active||!hints)return;let i=sel>=0&&!GIV[sel]&&G[sel]!==SOL[sel]?sel:-1;
  if(i<0){const open=[...Array(81).keys()].filter(j=>G[j]!==SOL[j]);if(!open.length)return;i=P.pick(open)}
  P.go();hints--;G[i]=SOL[i];GIV[i]=1;NOTES[i]=0;clearNotes(i,SOL[i]);sel=i;$('hint').textContent='💡 Hint ('+hints+')';$('hint').disabled=!hints;P.sfx('good');paint(i);check()};
addEventListener('keydown',e=>{if(!P.active)return;if(/^[1-9]$/.test(e.key))enter(+e.key);else if(e.key==='Backspace'||e.key==='Delete'||e.key==='0')$('erase').click();
  else if(e.key==='n'||e.key==='N')$('notes').click();
  else{const mv={ArrowUp:-9,ArrowDown:9,ArrowLeft:-1,ArrowRight:1}[e.key];if(mv){e.preventDefault();select(sel<0?40:Math.min(80,Math.max(0,sel+mv)));cells[sel].focus()}}});
function select(i){if(!P.active)return;sel=i;P.sfx('soft');paint()}
function clearNotes(i,v){for(const j of PEERS[i])NOTES[j]&=~(1<<v)}
function enter(v){if(!P.active||sel<0||GIV[sel])return;P.go();
  if(notesOn){if(G[sel])return;NOTES[sel]^=(1<<v);P.sfx('soft');paint();return}
  if(G[sel]===v){return}
  G[sel]=v;NOTES[sel]=0;
  if(v!==SOL[sel]){mistakes++;P.stat(mistakes);P.sfx('bad');P.msg('That '+v+" doesn't fit there.")}else{clearNotes(sel,v);P.sfx('tap');P.msg('')}
  paint(sel);check()}
function check(){if(G.every((v,i)=>v===SOL[i])){sel=-1;paint();P.pop('Solved!');P.win(null,`Solved in ${P.fmt(P.secs)} with ${mistakes} mistake${mistakes===1?'':'s'}.`)}}
function paint(fresh){const sv=sel>=0?G[sel]:0;const counts=Array(10).fill(0);G.forEach((v,i)=>{if(v&&v===SOL[i])counts[v]++});
  cells.forEach((b,i)=>{let c='q c'+COL(i)+' r'+ROW(i);if(GIV[i])c+=' given';if(i===sel)c+=' sel';else if(sv&&G[i]===sv)c+=' same';else if(sel>=0&&PEERS[sel].includes(i))c+=' peer';
    if(G[i]&&G[i]!==SOL[i])c+=' bad';if(i===fresh)c+=' new';b.className=c;
    if(G[i])b.textContent=G[i];else if(NOTES[i]){b.innerHTML='<span class="nt">'+[1,2,3,4,5,6,7,8,9].map(v=>`<i>${NOTES[i]>>v&1?v:''}</i>`).join('')+'</span>'}else b.textContent='';
    b.setAttribute('aria-label',`Row ${ROW(i)+1} column ${COL(i)+1}: ${G[i]||'empty'}`)});
  padBtns.forEach((b,k)=>{const left=9-counts[k+1];b.querySelector('small').textContent=left||'';b.classList.toggle('done',!left)})}
const GAME={reset(d){const {sol,puz}=make(d);SOL=sol;G=puz.slice();GIV=puz.map(v=>v?1:0);NOTES=Array(81).fill(0);sel=-1;mistakes=0;hints=3;
    $('hint').textContent='💡 Hint (3)';$('hint').disabled=false;P.stat(0);paint();P.msg(G.filter(Boolean).length+' numbers to start')}};
