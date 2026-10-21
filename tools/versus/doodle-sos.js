/* Doodle SOS on a 6x6 grid. Spelling S-O-S scores a point per line and gives another turn.
   Easy bot: random with the odd point. Medium: takes points, often avoids setting you up. Hard: takes every point and never sets you up if it can help it. */
const N=6,DIRS=[[1,0],[0,1],[1,1],[1,-1]];
const boardEl=document.getElementById('board'),linesEl=document.getElementById('lines');
let G=Array(N*N).fill(''),OWN=Array(N*N).fill(-1),letter='S';
const sqs=[...Array(N*N)].map((_,i)=>{const b=document.createElement('button');b.type='button';b.className='sq';b.setAttribute('aria-label','Row '+(Math.floor(i/N)+1)+' column '+(i%N+1));b.onclick=()=>tap(i);boardEl.appendChild(b);return b});
document.querySelectorAll('.lt').forEach(b=>b.onclick=()=>{letter=b.dataset.l;document.querySelectorAll('.lt').forEach(x=>{x.classList.toggle('on',x===b);x.setAttribute('aria-checked',x===b)});S.sfx('tap')});
const at=(x,y)=>x<0||y<0||x>=N||y>=N?null:G[y*N+x];
function formed(g,i,l){const x=i%N,y=Math.floor(i/N),out=[];const A=(x,y)=>x<0||y<0||x>=N||y>=N?null:g[y*N+x];
  for(const[dx,dy]of DIRS){if(l==='O'){if(A(x-dx,y-dy)==='S'&&A(x+dx,y+dy)==='S')out.push([[x-dx,y-dy],[x+dx,y+dy]])}
    else{if(A(x+dx,y+dy)==='O'&&A(x+2*dx,y+2*dy)==='S')out.push([[x,y],[x+2*dx,y+2*dy]]);if(A(x-dx,y-dy)==='O'&&A(x-2*dx,y-2*dy)==='S')out.push([[x,y],[x-2*dx,y-2*dy]])}}return out}
function drawLine(seg,p){const c=([x,y])=>[x*100+50,y*100+50];const[a,b]=seg.map(c);const ex=(b[0]-a[0])*.14,ey=(b[1]-a[1])*.14;
  const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d',`M${a[0]-ex} ${a[1]-ey} L${b[0]+ex} ${b[1]+ey}`);path.setAttribute('stroke',S.col(p));linesEl.appendChild(path)}
function play(i,l){const p=S.turn;G[i]=l;OWN[i]=p;const s=sqs[i];s.textContent=l;s.className='sq new c'+p;s.setAttribute('aria-label',s.getAttribute('aria-label').split(':')[0]+': '+l);
  const f=formed(G,i,l);f.forEach(seg=>drawLine(seg,p));
  if(f.length){S.addScore(p,f.length);S.sfx('score');S.pop(f.length>1?'SOS ×'+f.length+'!':'SOS!',S.col(p))}else S.sfx(S.isBot()?'bot':'tap');
  if(G.every(v=>v)){const[a,b]=S.scores;S.end(a>b?0:b>a?1:-1,`Final score ${a} to ${b}.`);return}
  S.setTurn(f.length?p:1-p)}
function tap(i){if(!S.canPlay()||G[i])return;play(i,letter)}
function moves(){const m=[];G.forEach((v,i)=>{if(!v){m.push([i,'S'],[i,'O'])}});return m}
function gain(i,l){return formed(G,i,l).length}
function risk(i,l){G[i]=l;let r=0;for(let j=0;j<N*N&&r<3;j++)if(!G[j]){r=Math.max(r,formed(G,j,'S').length,formed(G,j,'O').length)}G[i]='';return r}
const GAME={reset(){G.fill('');OWN.fill(-1);sqs.forEach(s=>{s.textContent='';s.className='sq'});linesEl.innerHTML=''},
  botMove(){const all=moves();const best=Math.max(...all.map(([i,l])=>gain(i,l)));const scoring=all.filter(([i,l])=>gain(i,l)===best);
    let m;const r=Math.random();
    if(S.diff==='easy'){m=best>0&&r<.35?S.pick(scoring):S.pick(all)}
    else{const take=S.diff==='hard'||r<.8;if(best>0&&take)m=S.pick(scoring);
      else{const safe=all.filter(([i,l])=>gain(i,l)===0&&risk(i,l)===0);
        if(safe.length&&(S.diff==='hard'||Math.random()<.65))m=S.pick(safe);
        else if(S.diff==='hard'){let lo=9;all.forEach(([i,l])=>{const k=risk(i,l)-gain(i,l);if(k<lo){lo=k;m=[i,l]}})}
        else m=S.pick(all)}}
    play(m[0],m[1])}};
