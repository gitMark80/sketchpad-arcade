INFO.best='low';INFO.bestLabel='Fewest guesses';INFO.winHead='Code cracked!';INFO.loseHead='Out of rows';
/*SHELL*/
/* Crayon Code: Mastermind with crayons. Black dot = right colour, right spot. Open dot = right colour, wrong spot. */
const COLS=[['Red','#c84a3a','#efc4bc'],['Orange','#d9661a','#f0c9a8'],['Yellow','#d4a51c','#f3e6b0'],['Green','#5a9a6a','#dcebdd'],['Blue','#2f6fb5','#d6e4f2'],['Purple','#6f4a9a','#e6dcef']];
const LV={easy:{slots:3,cols:4,rows:10,rep:false},medium:{slots:4,cols:6,rows:10,rep:false},hard:{slots:4,cols:6,rows:8,rep:true}};
const $=id=>document.getElementById(id);
let L,code=[],rows=[],cur=[],row=0;
const crayon=(c,w)=>`<svg viewBox="0 0 40 70"><path d="M12 22 L20 4 L28 22 Z" fill="${c[1]}" stroke="#2e2e33" stroke-width="2.5" stroke-linejoin="round"/><rect x="10" y="22" width="20" height="44" rx="3" fill="${c[1]}" stroke="#2e2e33" stroke-width="2.5"/><rect x="10" y="32" width="20" height="18" fill="${c[2]}" stroke="#2e2e33" stroke-width="2"/><path d="M13 36 L27 46 M13 42 L22 48" stroke="${c[1]}" stroke-width="1.5" opacity=".7"/></svg>`;
const fill=(el,k)=>{el.style.background=k==null?'':`radial-gradient(circle at 38% 35%,${COLS[k][2]} 0 22%,${COLS[k][1]} 60%)`;el.classList.toggle('f',k!=null)};
function score(g,c){let b=0,w=0;const gc=[],cc=[];g.forEach((v,i)=>{if(v===c[i])b++;else{gc.push(v);cc.push(c[i])}});gc.forEach(v=>{const j=cc.indexOf(v);if(j>=0){w++;cc.splice(j,1)}});return[b,w]}
function buildRows(){const R=$('rows');R.innerHTML='';rows=[...Array(L.rows)].map((_,r)=>{const el=document.createElement('div');el.className='rw';
    el.innerHTML=`<span class="n">${r+1}</span><div class="slots">${'<button type="button" class="slot" tabindex="-1"></button>'.repeat(L.slots)}</div><div class="pegs">${'<span class="peg"></span>'.repeat(L.slots)}</div>`;
    [...el.querySelectorAll('.slot')].forEach((s,i)=>s.onclick=()=>{if(r!==row||!P.active||cur[i]==null)return;cur[i]=null;P.sfx('soft');draw()});R.appendChild(el);return el})}
function buildPalette(){const pal=$('palette');pal.innerHTML='';for(let k=0;k<L.cols;k++){const b=document.createElement('button');b.type='button';b.className='cr';b.innerHTML=crayon(COLS[k]);b.setAttribute('aria-label',COLS[k][0]+' crayon');b.onclick=()=>add(k);pal.appendChild(b)}}
function draw(){rows.forEach((el,r)=>{el.classList.toggle('now',r===row&&P.active);[...el.querySelectorAll('.slot')].forEach((s,i)=>{s.tabIndex=r===row?0:-1;if(r===row){fill(s,cur[i]);s.setAttribute('aria-label','Spot '+(i+1)+': '+(cur[i]==null?'empty':COLS[cur[i]][0]))}})});
  [...$('palette').children].forEach((b,k)=>b.disabled=!P.active||(!L.rep&&cur.includes(k))||!cur.includes(null));
  $('check').disabled=!P.active||cur.includes(null);$('clear').disabled=!P.active||cur.every(v=>v==null);P.stat((Math.min(row+1,L.rows))+'/'+L.rows)}
function add(k){if(!P.active)return;const i=cur.indexOf(null);if(i<0||(!L.rep&&cur.includes(k)))return;P.go();cur[i]=k;P.sfx('tap');draw();const s=rows[row].querySelectorAll('.slot')[i];s.classList.remove('ink');void s.offsetWidth;s.classList.add('ink')}
$('clear').onclick=()=>{cur=Array(L.slots).fill(null);P.sfx('soft');draw()};
$('check').onclick=()=>{if(!P.active||cur.includes(null))return;const[b,w]=score(cur,code);const el=rows[row];el.classList.add('done');
  const pegs=[...el.querySelectorAll('.peg')];[...Array(b).fill('b'),...Array(w).fill('w')].forEach((t,i)=>{pegs[i].className='peg ink '+t;pegs[i].style.animationDelay=(i*.12)+'s'});
  el.setAttribute('aria-label',`Guess ${row+1}: ${cur.map(k=>COLS[k][0]).join(', ')}. ${b} right spot, ${w} wrong spot.`);
  if(b===L.slots){P.sfx('good');reveal();P.pop('Cracked!');P.win(row+1,`You cracked it in ${row+1} ${row?'guesses':'guess'}!`);row++;draw();return}
  P.sfx(b||w?'soft':'bad');P.msg(b+w===0?'None of those colours are in the code.':`${b} right spot${b===1?'':'s'}, ${w} right colour${w===1?'':'s'} in the wrong spot.`);
  row++;cur=Array(L.slots).fill(null);
  if(row>=L.rows){reveal();P.lose('The secret code was '+code.map(k=>COLS[k][0]).join(', ')+'.');}draw()};
function reveal(){$('secret').innerHTML=code.map(()=>'<span class="slot"></span>').join('');[...$('secret').children].forEach((s,i)=>fill(s,code[i]))}
addEventListener('keydown',e=>{if(!P.active)return;if(/^[1-6]$/.test(e.key)&&+e.key<=L.cols)add(+e.key-1);else if(e.key==='Enter')$('check').click();else if(e.key==='Backspace'){const i=cur.map(v=>v!=null).lastIndexOf(true);if(i>=0){cur[i]=null;draw()}}});
const GAME={reset(d){L=LV[d];const pool=[...Array(L.cols).keys()];code=L.rep?[...Array(L.slots)].map(()=>P.rand(L.cols)):P.shuffle(pool).slice(0,L.slots);
    row=0;cur=Array(L.slots).fill(null);$('secret').innerHTML='';buildRows();buildPalette();draw();
    P.msg(`Find the ${L.slots} secret colours`+(L.rep?' (colours can repeat)':''))}};
