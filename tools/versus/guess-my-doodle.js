/* Guess My Doodle: draw-and-guess for two, played together (co-op). Each drawing: the drawer picks one of three
   words, draws it, and sends it; the guesser watches it redraw line by line and spells the word with letter tiles.
   A right guess scores the word's points for both players. The guesser then draws next. Ten drawings make a game.
   Saved game (for online play): {round, drawer, phase:'pick'|'guess', offers, used, cur:{word,tier,by,d}, hist} where
   d is the drawing: [[colour, size, gap, base64 points]...], each point being x, y (0-255) and a time step (10 ms). */
INFO.noBot=true;INFO.endDelay=1600;
const GD_WORDS=[
 /* easy: 10 points */
 ['cat','dog','sun','moon','star','tree','fish','bird','house','car','ball','apple','hat','cake','boat','duck','frog','pig','cow','egg',
  'cup','book','bed','door','key','kite','sock','shoe','hand','eye','nose','ear','smile','heart','cloud','rain','snow','flower','leaf','grass',
  'bus','train','bike','lamp','clock','chair','table','bear','bee','ant','snail','worm','mouse','owl','sheep','horse','lion','banana','pear','grape',
  'carrot','cookie','pizza','donut','candy','bread','cheese','milk','juice','pie','box','bell','drum','gift','hill','road','sand','wave','shell','crab',
  'boot','glove','bag','pen','pencil','brush','fork','spoon','bowl','plate','phone','robot','ghost','crown','ring','bone','nest','web','spider','balloon',
  'candle','window','fence','flag','tent','rocket','planet','sock','mitten','scarf','bat','sled','ice','fire','lemon','corn','teeth','foot','tail','wing'],
 /* medium: 20 points */
 ['rainbow','snowman','pumpkin','dragon','castle','pirate','penguin','giraffe','turtle','rabbit','monkey','zebra','octopus','whale','shark','dolphin','unicorn','robot','camera','guitar',
  'piano','trumpet','ladder','bridge','island','mountain','river','beach','garden','bucket','shovel','umbrella','sunglasses','backpack','crayon','scissors','teapot','toaster','popcorn','sandwich',
  'burger','hotdog','icecream','cupcake','pancake','pretzel','cherry','pineapple','broccoli','mushroom','cactus','sunflower','tornado','lightning','comet','astronaut','alien','spaceship','airplane','helicopter',
  'tractor','firetruck','sailboat','submarine','skateboard','bicycle','scooter','swing','slide','sandcastle','treasure','compass','magnet','battery','lightbulb','toothbrush','bathtub','pillow','blanket','mirror',
  'hammer','wrench','paintbrush','easel','puzzle','kitebird','butterfly','ladybug','caterpillar','dinosaur','hedgehog','squirrel','peacock','flamingo','koala','panda','kangaroo','elephant','crocodile','jellyfish'],
 /* hard: 30 points */
 ['volcano','lighthouse','waterfall','windmill','igloo','pyramid','skyscraper','fireworks','telescope','microscope','parachute','hourglass','snowflake','constellation','eclipse','rollercoaster','carousel','ferriswheel','hammock','campfire',
  'thunderstorm','avalanche','glacier','desert','jungle','canyon','oasis','iceberg','treehouse','birthday','wedding','picnic','parade','circus','museum','library','farmhouse','barn','scarecrow','haystack',
  'lawnmower','wheelbarrow','birdhouse','fountain','sprinkler','raincoat','backflip','cartwheel','juggler','magician','detective','scientist','gardener','chef','firefighter','mermaid','wizard','knight','princess','superhero',
  'yoyo','trampoline','hopscotch','snowball','sledding','surfing','skiing','fishing','camping','bowling','yawning','sneezing','sleeping','dancing','singing','shadow','echo','rainstorm','starfish','seahorse']];
GD_WORDS[0]=[...new Set(GD_WORDS[0])].filter(w=>w.length<=10);GD_WORDS[1]=[...new Set(GD_WORDS[1])].filter(w=>w.length<=10&&w!=='kitebird'&&!GD_WORDS[0].includes(w));
GD_WORDS[2]=[...new Set(GD_WORDS[2])].filter(w=>w.length<=10);
const GD_PTS=[10,20,30],GD_TOTAL=10,GD_MAXPTS=3000;
const GD_COLS=[['Black','#2e2e33'],['Red','#c84a3a'],['Orange','#d9661a'],['Yellow','#d4a51c'],['Green','#5a9a6a'],['Blue','#2f6fb5'],['Purple','#6f4a9a']];
const $g=id=>document.getElementById(id);
const stars=t=>'★'.repeat(t+1);
let G=null,draft=null,penCol=0,penSize=0,handing=false,viewKey='',replayT=0,guessFill=[],tilesNow=[],resolving=false;
function fresh(first){return{round:0,drawer:first||0,phase:'pick',offers:offers([]),used:[],cur:null,hist:[]}}
function offers(used){return GD_WORDS.map(list=>{const pool=list.filter(w=>!used.includes(w));return S.pick(pool.length?pool:list)})}
// ---------- drawing data: encode / decode ----------
const b64e=bytes=>{let s='';for(let i=0;i<bytes.length;i+=8192)s+=String.fromCharCode.apply(null,bytes.slice(i,i+8192));return btoa(s)};
const b64d=str=>{const s=atob(str),a=new Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);return a};
function encode(strokes){return strokes.map(st=>{const b=[];st.p.forEach(([x,y,dt])=>b.push(x,y,Math.min(255,Math.round(dt/10))));return[st.c,st.s,Math.min(200,Math.round(st.gap/10)),b64e(b)]})}
function decode(d){return(d||[]).map(([c,s,gap,str])=>{const b=b64d(str),p=[];for(let i=0;i+2<b.length;i+=3)p.push([b[i],b[i+1],b[i+2]*10]);return{c,s,gap:gap*10,p}})}
const npts=strokes=>strokes.reduce((n,s)=>n+s.p.length,0);
// ---------- canvas ----------
const cv=$g('cv'),ctx=cv.getContext('2d');let CW=300;
function sizeCanvas(){const wrap=$g('cvWrap');if(wrap.hidden)return;const gd=$g('gd'),stage=$g('stage');
  let used=0;[...gd.children].forEach(el=>{if(el!==wrap&&!el.hidden)used+=el.getBoundingClientRect().height+8});
  const avail=Math.max(160,Math.min(stage.clientWidth,stage.clientHeight-used-6,520));CW=Math.floor(avail);
  wrap.style.width=wrap.style.height=CW+'px';const dpr=Math.min(3,window.devicePixelRatio||1);
  if(cv.width!==Math.round(CW*dpr)){cv.width=cv.height=Math.round(CW*dpr)}
  ctx.setTransform(cv.width/256,0,0,cv.height/256,0,0)}
function pen(st){ctx.strokeStyle=ctx.fillStyle=GD_COLS[st.c][1];ctx.lineWidth=st.s?7.5:2.6;ctx.lineCap='round';ctx.lineJoin='round';ctx.globalAlpha=.92}
function drawSeg(st,i){const p=st.p;pen(st);if(i===0){ctx.beginPath();ctx.arc(p[0][0],p[0][1],ctx.lineWidth/2,0,7);ctx.fill();return}
  const a=p[i-1],b=p[i];ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.stroke()}
function clearCv(){ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,cv.width,cv.height);ctx.restore()}
function drawAll(strokes){clearCv();strokes.forEach(st=>{for(let i=0;i<st.p.length;i++)drawSeg(st,i)})}
function stopReplay(){cancelAnimationFrame(replayT);replayT=0}
function replay(strokes,done){stopReplay();clearCv();const events=[];let t=0;
  strokes.forEach((st,si)=>{t+=Math.min(st.gap,600);st.p.forEach((pt,i)=>{t+=i?Math.min(pt[2],250):0;events.push([t,si,i])})});
  const speed=Math.max(1.4,t/8000);let k=0;const t0=performance.now();
  const step=now=>{const el=(now-t0)*speed;while(k<events.length&&events[k][0]<=el){const[,si,i]=events[k];drawSeg(strokes[si],i);k++}
    if(k<events.length)replayT=requestAnimationFrame(step);else{replayT=0;if(done)done()}};replayT=requestAnimationFrame(step)}
// ---------- recording the drawer's strokes ----------
let live=null,lastT=0,lastUp=0;
function cvPt(e){const r=cv.getBoundingClientRect();return[Math.max(0,Math.min(255,Math.round((e.clientX-r.left)/r.width*255))),Math.max(0,Math.min(255,Math.round((e.clientY-r.top)/r.height*255)))]}
cv.addEventListener('pointerdown',e=>{if(!draft||!S.canPlay())return;e.preventDefault();if(npts(draft)>=GD_MAXPTS){S.pop('Page full!');return}
  cv.setPointerCapture(e.pointerId);const now=performance.now(),[x,y]=cvPt(e);
  live={c:penCol,s:penSize,gap:draft.length?Math.min(2000,now-lastUp):0,p:[[x,y,0]]};lastT=now;draft.push(live);drawSeg(live,0);tools()});
cv.addEventListener('pointermove',e=>{if(!live)return;const evs=e.getCoalescedEvents?e.getCoalescedEvents():[e];
  for(const ev of (evs.length?evs:[e])){const[x,y]=cvPt(ev),l=live.p[live.p.length-1];if(Math.abs(x-l[0])+Math.abs(y-l[1])<2)continue;
    if(npts(draft)>=GD_MAXPTS){endStroke();S.pop('Page full!');return}const now=performance.now();live.p.push([x,y,now-lastT]);lastT=now;drawSeg(live,live.p.length-1)}});
function endStroke(){if(!live)return;live=null;lastUp=performance.now();tools()}
['pointerup','pointercancel','lostpointercapture'].forEach(t=>cv.addEventListener(t,endStroke));
// ---------- drawing tools ----------
const pal=$g('pal');GD_COLS.forEach(([n,c],i)=>{const b=document.createElement('button');b.type='button';b.style.background=c;b.setAttribute('aria-label',n+' pencil');b.setAttribute('role','radio');
  b.onclick=()=>{penCol=i;S.sfx('tap');tools()};pal.appendChild(b)});
$g('sizeB').onclick=()=>{penSize^=1;S.sfx('tap');tools()};
$g('undoB').onclick=()=>{if(!draft||!draft.length)return;draft.pop();drawAll(draft);S.sfx('tap');tools()};
$g('clearB').onclick=()=>{if(!draft||!draft.length)return;draft=[];clearCv();S.sfx('miss');tools()};
$g('sendB').onclick=()=>{if(!draft||!draft.length||!S.canPlay())return;send()};
function tools(){[...pal.children].forEach((b,i)=>{b.classList.toggle('on',i===penCol);b.setAttribute('aria-checked',i===penCol)});
  $g('sizeB').textContent=penSize?'🖍 Thick':'✏️ Thin';const has=!!(draft&&draft.length);$g('undoB').disabled=$g('clearB').disabled=$g('sendB').disabled=!has}
// ---------- turns ----------
function pickWord(t){if(!S.canPlay()||G.phase!=='pick')return;S.sfx('tap');G.cur={word:G.offers[t],tier:t,by:S.turn,d:null};G.phase='draw';draft=[];viewKey='';render()}
function send(){const me=S.turn,other=1-me;G.cur.d=encode(draft);G.phase='guess';draft=null;S.sfx('score');
  if(S.mode==='friend'){handing=true;viewKey='';render();S.status('Pass to '+S.names()[other],other);S.pass(S.names()[other],()=>{handing=false;viewKey='';S.setTurn(other)})}
  else S.setTurn(other)}
function finishGuess(solved){if(resolving)return;resolving=true;S.busy=true;const c=G.cur,pts=solved?GD_PTS[c.tier]:0;
  if(solved){S.addScore(0,pts);S.addScore(1,pts);S.sfx('score');S.pop('Got it! +'+pts,S.col(S.turn))}else S.sfx('miss');
  G.hist.push({word:c.word,tier:c.tier,by:c.by,ok:solved,pts});G.used.push(c.word);G.round++;
  setTimeout(()=>{resolving=false;S.busy=false;stopReplay();
    if(G.round>=GD_TOTAL){G.phase='pick';G.cur=c;S.end(-1,summary());return}
    G.drawer=S.turn;G.phase='pick';G.offers=offers(G.used);G.cur=null;viewKey='';S.setTurn(S.turn)},solved?1500:2200)}
function summary(){const got=G.hist.filter(h=>h.ok),best=got.sort((a,b)=>b.pts-a.pts)[0];
  return `You guessed ${G.hist.filter(h=>h.ok).length} of ${GD_TOTAL} drawings.`+(best?` Best: ${best.word.toUpperCase()} (+${best.pts}).`:'')}
// ---------- guessing ----------
function setupGuess(){const w=G.cur.word.toUpperCase(),abc='ABCDEFGHIJKLMNOPRSTUWY';const L=w.split('');
  while(L.length<12)L.push(abc[S.rand(abc.length)]);
  tilesNow=L.map((ch,i)=>({ch,id:i})).sort(()=>Math.random()-.5);guessFill=Array(w.length).fill(null);drawGuess()}
function drawGuess(state){const w=G.cur.word.toUpperCase();const sl=$g('slots');sl.className='slots'+(state?' '+state:'');sl.innerHTML='';
  guessFill.forEach((tid,i)=>{const b=document.createElement('button');b.type='button';
    const ch=state==='reveal'||state==='good'?w[i]:tid==null?'':tilesNow.find(t=>t.id===tid).ch;b.textContent=ch;if(ch)b.className='f';
    b.setAttribute('aria-label','Letter '+(i+1)+': '+(ch||'blank'));b.onclick=()=>{if(state||tid==null||!S.canPlay())return;guessFill[i]=null;S.sfx('tap');drawGuess()};sl.appendChild(b)});
  const tl=$g('tiles');tl.innerHTML='';tilesNow.forEach(t=>{const b=document.createElement('button');b.type='button';b.textContent=t.ch;b.setAttribute('aria-label','Tile '+t.ch);
    if(guessFill.includes(t.id))b.className='used';b.onclick=()=>tapTile(t.id);tl.appendChild(b)})}
function tapTile(id){if(!S.canPlay()||resolving||guessFill.includes(id))return;const i=guessFill.indexOf(null);if(i<0)return;guessFill[i]=id;S.sfx('tap');drawGuess();
  if(!guessFill.includes(null)){const g=guessFill.map(x=>tilesNow.find(t=>t.id===x).ch).join('');
    if(g===G.cur.word.toUpperCase()){drawGuess('good');stopReplay();drawAll(decode(G.cur.d));finishGuess(true)}
    else{S.sfx('miss');const sl=$g('slots');sl.classList.remove('bad');void sl.offsetWidth;sl.classList.add('bad')}}}
$g('replayB').onclick=()=>{if(G&&G.cur&&G.cur.d){S.sfx('tap');replay(decode(G.cur.d))}};
$g('skipB').onclick=()=>{if(!S.canPlay()||resolving||G.phase!=='guess')return;drawGuess('reveal');stopReplay();drawAll(decode(G.cur.d));finishGuess(false)};
addEventListener('keydown',e=>{if(!G||G.phase!=='guess'||!S.canPlay()||e.ctrlKey||e.metaKey)return;const k=e.key.toUpperCase();
  if(e.key==='Backspace'){const i=guessFill.map(x=>x!=null).lastIndexOf(true);if(i>=0){guessFill[i]=null;drawGuess()}return}
  if(/^[A-Z]$/.test(k)){const t=tilesNow.find(t=>t.ch===k&&!guessFill.includes(t.id));if(t)tapTile(t.id)}});
// ---------- screens ----------
function show(ids){['pick','cvWrap','drawTools','guessBox','waitBox'].forEach(id=>$g(id).hidden=!ids.includes(id))}
function msg(t){const m=$g('cvMsg');m.hidden=!t;m.textContent=t||''}
function lastLine(){const h=G.hist[G.hist.length-1];if(!h)return'';const n=S.names();const who=h.by===S.viewer()?'your':(S.mode==='online'?"your friend's":n[h.by]+"'s");
  return h.ok?`✅ ${who[0].toUpperCase()+who.slice(1)} ${h.word.toUpperCase()} was guessed! +${h.pts}`:`🙈 ${who[0].toUpperCase()+who.slice(1)} ${h.word.toUpperCase()} was skipped.`}
function render(){if(!G)return;const n=S.names(),me=S.viewer(),myTurn=S.active&&S.turn===me,num=Math.min(G.round+1,GD_TOTAL);
  const key=[S.active,S.turn,me,G.phase,G.round,handing,S.mode].join('|');if(key===viewKey){sizeCanvas();return}viewKey=key;stopReplay();
  const head=$g('gdHead');
  if(!S.active&&G.hist.length>=GD_TOTAL){head.innerHTML=`Game over · <b>${G.hist.filter(h=>h.ok).length} of ${GD_TOTAL}</b> guessed`;show(['cvWrap','waitBox']);msg('');sizeCanvas();
    const c=G.cur||{};if(c.d)drawAll(decode(c.d));else clearCv();$g('waitBox').textContent=lastLine();return}
  if(!S.active){head.textContent='';show([]);return}
  if(handing){head.innerHTML=`Drawing <b>${num}</b> of ${GD_TOTAL}`;show(['cvWrap']);sizeCanvas();clearCv();msg('Sent! Pass the phone so they can guess.');return}
  if(!myTurn){/* online: the other player is acting */
    head.innerHTML=`Drawing <b>${num}</b> of ${GD_TOTAL}`;show(['cvWrap','waitBox']);sizeCanvas();const wb=$g('waitBox');
    if(G.phase==='guess'&&G.cur&&G.cur.by===me){drawAll(decode(G.cur.d));msg('');wb.innerHTML=`Your friend is guessing your <b>${G.cur.word.toUpperCase()}</b> ${stars(G.cur.tier)}`}
    else{clearCv();const h=G.hist[G.hist.length-1];msg(G.round===0&&S.mode==='online'&&typeof ON!=='undefined'&&ON.status==='waiting'?'Waiting for your friend to join…':'✏️ Your friend is picking a word to draw…');
      wb.textContent=lastLine()}
    return}
  if(G.phase==='pick'){head.innerHTML=`Drawing <b>${num}</b> of ${GD_TOTAL} · ${S.mode==='online'?'your':n[S.turn]+"'s"} turn to draw`;show(['pick']);msg('');
    const pk=$g('pick');pk.innerHTML='';const p=document.createElement('p');p.textContent='Pick a word to draw:';pk.appendChild(p);
    G.offers.forEach((w,t)=>{const b=document.createElement('button');b.type='button';b.className='t'+t;b.innerHTML=`<span></span><span class="stars">${stars(t)}</span><small>+${GD_PTS[t]}</small>`;
      b.firstChild.textContent=w;b.onclick=()=>pickWord(t);pk.appendChild(b)});
    const ll=lastLine();if(ll){const q=document.createElement('p');q.className='last';q.textContent=ll;pk.appendChild(q)}return}
  if(G.phase==='draw'){head.innerHTML=`Draw <b>${G.cur.word.toUpperCase()}</b> <span class="stars">${stars(G.cur.tier)}</span> · no letters!`;show(['cvWrap','drawTools']);msg('');tools();sizeCanvas();drawAll(draft||[]);return}
  if(G.phase==='guess'){head.innerHTML=`Drawing <b>${num}</b> of ${GD_TOTAL} · guess the word <span class="stars">${stars(G.cur.tier)}</span>`;show(['cvWrap','guessBox']);msg('');setupGuess();sizeCanvas();replay(decode(G.cur.d))}}
addEventListener('resize',()=>{if(!G)return;sizeCanvas();if(G.phase==='draw'&&draft)drawAll(draft);else if(G.cur&&G.cur.d&&!replayT)drawAll(decode(G.cur.d))});
const GAME={
  reset(){stopReplay();G=fresh(0);draft=null;handing=false;resolving=false;viewKey=''},
  begin(st){G=fresh(st);viewKey='';S.setTurn(st)},
  render,
  endHead:()=>'Team score: '+S.scores[0]+'!',
  save(){const s=JSON.parse(JSON.stringify(G));if(s.phase==='draw'){s.phase='pick';s.cur=null}return s},
  load(st){stopReplay();resolving=false;handing=false;draft=null;viewKey='';
    G=Object.assign(fresh(0),JSON.parse(JSON.stringify(st||{})));if(!G.offers||G.offers.length!==3)G.offers=offers(G.used||[]);if(G.phase==='draw')G.phase='pick'},
  botMove(){}
};
