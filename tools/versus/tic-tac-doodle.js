INFO.scoreIsRounds=true;
/* Tic-Tac-Doodle: player 0 is blue X, player 1 is pink O. Easy bot mostly random, Medium wins/blocks, Hard never loses (minimax). */
const LINES=[[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
const CEN=i=>[50+100*(i%3),50+100*Math.floor(i/3)];
const board=document.getElementById('board');
const cells=[...Array(9)].map((_,i)=>{const b=document.createElement('button');b.className='cell';b.type='button';b.setAttribute('aria-label','Square '+(i+1));b.onclick=()=>tap(i);board.appendChild(b);return b});
let B=Array(9).fill(-1);
function winner(b){for(const l of LINES){const[a,c,d]=l;if(b[a]>=0&&b[a]===b[c]&&b[a]===b[d])return{p:b[a],l}}return b.every(v=>v>=0)?{p:-1}:null}
function mark(p){const w=()=>(Math.random()*6-3).toFixed(1);
  return p===0?`<svg class="x" viewBox="0 0 100 100"><path d="M${15+ +w()} ${15+ +w()} C40 38 62 60 ${85+ +w()} ${86+ +w()}"/><path d="M${84+ +w()} ${15+ +w()} C60 40 40 62 ${16+ +w()} ${85+ +w()}"/></svg>`
  :`<svg class="o" viewBox="0 0 100 100"><path d="M52 14 C78 12 90 34 87 54 C84 78 62 90 44 86 C22 82 11 62 15 42 C18 26 32 15 56 17"/></svg>`}
function drawMark(i,p){B[i]=p;cells[i].innerHTML=mark(p);cells[i].setAttribute('aria-label','Square '+(i+1)+': '+(p?'O':'X'))}
function winLine(w){const[a,,c]=w.l,[x1,y1]=CEN(a),[x2,y2]=CEN(c);const dx=(x2-x1)*.18,dy=(y2-y1)*.18;
  document.getElementById('winline').innerHTML=`<path stroke="${S.col(w.p)}" d="M${x1-dx} ${y1-dy} L${x2+dx} ${y2+dy}"/>`;w.l.forEach(k=>cells[k].classList.add('hot'))}
function place(i){const p=S.turn;drawMark(i,p);S.sfx(S.isBot()?'bot':'tap');
  const w=winner(B);if(w){if(w.p>=0){winLine(w);S.end(w.p,'Three in a row!')}else S.end(-1,'Nobody got three in a row.');return}
  S.setTurn(1-p)}
function tap(i){if(!S.canPlay()||B[i]>=0)return;place(i)}
function mm(b,p,me,depth){const w=winner(b);if(w)return w.p===-1?0:(w.p===me?10-depth:depth-10);let best=p===me?-99:99;
  for(let i=0;i<9;i++)if(b[i]<0){b[i]=p;const v=mm(b,1-p,me,depth+1);b[i]=-1;best=p===me?Math.max(best,v):Math.min(best,v)}return best}
function bestMoves(){const me=S.turn;let best=-99,out=[];for(let i=0;i<9;i++)if(B[i]<0){B[i]=me;const v=mm(B,1-me,me,1);B[i]=-1;if(v>best){best=v;out=[i]}else if(v===best)out.push(i)}return out}
function findLine(p){for(const l of LINES){const v=l.map(k=>B[k]);if(v.filter(x=>x===p).length===2&&v.includes(-1))return l[v.indexOf(-1)]}return -1}
const GAME={save:()=>({B:B.slice()}),
  load(st){const nb=st.B||Array(9).fill(-1);if(nb.every(v=>v<0)&&B.some(v=>v>=0))GAME.reset();nb.forEach((v,i)=>{if(v>=0&&B[i]!==v)drawMark(i,v)});const w=winner(B);if(w&&w.p>=0&&!document.getElementById('winline').innerHTML)winLine(w)},
  reset(){B.fill(-1);cells.forEach(c=>{c.innerHTML='';c.classList.remove('hot');c.setAttribute('aria-label','Square')});document.getElementById('winline').innerHTML=''},
  botMove(){const free=B.map((v,i)=>v<0?i:-1).filter(i=>i>=0);let m=-1;
    if(S.diff==='hard')m=S.pick(bestMoves());
    else if(S.diff==='medium'){m=findLine(1);if(m<0)m=findLine(0);if(m<0&&Math.random()<.5)m=S.pick(bestMoves());if(m<0)m=B[4]<0&&Math.random()<.5?4:S.pick(free)}
    else{m=Math.random()<.3?findLine(1):-1;if(m<0)m=S.pick(free)}
    place(m)}};
