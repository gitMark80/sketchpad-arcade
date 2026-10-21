/* Invite a friend: play by text, taking turns whenever. Only switched on when the site has a Supabase project
   (window.SA_ONLINE = {url, key}, written by build.py) and the game hasn't opted out (INFO.online === false).
   A game that supports it defines GAME.save() -> plain object and GAME.load(obj) (redraw to match, no sounds).
   The inviter is seat 0 (blue) and moves first; the friend who opens the link is seat 1 (pink).
   No accounts: this device has one random secret id (kept in localStorage); the server only keeps its hash. */
const ON=(()=>{
  const $=id=>document.getElementById(id);
  const CFG=window.SA_ONLINE,ok=!!(CFG&&CFG.url&&CFG.key&&INFO.online!==false&&GAME.save&&GAME.load);
  const ON={ok,code:null,seat:-1,version:0,status:null,applying:false,pollT:0,since:0};
  if(!ok){const b=$('vsInvite');if(b)b.remove();return ON}
  // ---------- device id and this device's game list ----------
  function id(){let t='';try{t=localStorage.getItem('sa-online-id')||''}catch(e){}
    if(t.length<20){const a=new Uint8Array(18);crypto.getRandomValues(a);t=[...a].map(x=>x.toString(16).padStart(2,'0')).join('');try{localStorage.setItem('sa-online-id',t)}catch(e){}}return t}
  function remember(code,seat){try{let l=JSON.parse(localStorage.getItem('sa-online-games')||'[]');l=l.filter(x=>x.code!==code);
    l.unshift({code,game:INFO.slug,name:INFO.name,seat,t:Date.now()});localStorage.setItem('sa-online-games',JSON.stringify(l.slice(0,30)))}catch(e){}}
  // ---------- server ----------
  async function rpc(fn,args){const h={'Content-Type':'application/json',apikey:CFG.key};if(/^eyJ/.test(CFG.key))h.Authorization='Bearer '+CFG.key;
    const r=await fetch(CFG.url.replace(/\/$/,'')+'/rest/v1/rpc/'+fn,{method:'POST',headers:h,body:JSON.stringify(args)});
    const j=await r.json().catch(()=>null);if(!r.ok)throw new Error((j&&(j.message||j.hint))||('Error '+r.status));return j}
  const link=code=>{const base=(window.BDA_GAME&&BDA_GAME.url)||location.origin+'/'+INFO.slug;return base+'?game='+code};
  // ---------- names, turns ----------
  const me=()=>ON.seat,them=()=>1-ON.seat;
  ON.names=()=>ON.seat===1?['Friend','You']:['You','Friend'];
  ON.turnText=()=>{if(S.turn===me())return '✏️ Your turn'+(INFO.turnHint?INFO.turnHint(S.turn):'');
    return ON.status==='waiting'?'📲 Waiting for your friend to open the link':'⏳ Waiting for your friend…'};
  // ---------- applying a saved game ----------
  function apply(g,fresh){ON.version=g.version;ON.status=g.status;ON.code=g.code;const st=g.state||{};
    ON.applying=true;try{
      if(fresh){S.active=true;S.scores=[0,0];S.show(null);GAME.reset()}
      GAME.load(st.g||{});S.scores=(st.scores||[0,0]).slice();
      if(g.status==='done'){if(S.active){S.turn=g.turn;S.end(g.winner,st.msg||'')}}
      else{S.active=true;S.setTurn(g.turn)}
      S.hud();bar()}finally{ON.applying=false}
    poll()}
  // ---------- saving my move ----------
  ON.push=async(turn,done,winner,msg)=>{if(ON.applying)return;S.busy=true;bar('Sending…');
    const state={g:GAME.save(),scores:S.scores,msg:msg||''};
    try{const g=await rpc('vs_move',{p_code:ON.code,p_token:id(),p_version:ON.version,p_state:state,p_turn:turn,p_status:done?'done':'playing',p_winner:done?winner:null});
      ON.version=g.version;ON.status=g.status;S.busy=false;remember(ON.code,ON.seat);
      if(!done){S.status(ON.turnText(),turn);bar(null,true)}else bar();poll()}
    catch(e){S.busy=false;bar("Couldn't send that move. Getting the latest game…");sync(true)}};
  // ---------- checking for the other player's move ----------
  async function sync(force){if(!ON.code)return;try{const g=await rpc('vs_get',{p_code:ON.code});if(!g)return;
      if(force||g.version!==ON.version||g.status!==ON.status){const was=ON.version;apply(g);if(g.version!==was&&!force)S.sfx('bot')}}catch(e){}}
  function poll(){clearTimeout(ON.pollT);if(!ON.code||ON.status==='done'||S.turn===me()&&ON.status!=='waiting'||document.hidden)return;
    if(!ON.since)ON.since=Date.now();const quiet=Date.now()-ON.since;ON.pollT=setTimeout(async()=>{await sync();poll()},quiet<120000?3000:quiet<600000?8000:20000)}
  document.addEventListener('visibilitychange',()=>{if(!document.hidden&&ON.code){ON.since=Date.now();sync()}});
  addEventListener('focus',()=>{if(ON.code)sync()});
  // ---------- the share strip under the board ----------
  function bar(text,nudge){let el=$('onbar');if(!el)return;
    if(!ON.code||S.mode!=='online'){el.hidden=true;return}el.hidden=false;
    const myTurn=S.turn===me()&&ON.status!=='done';
    $('onText').textContent=text||(ON.status==='done'?'Game over · code '+ON.code:ON.status==='waiting'?'Send your friend the link · code '+ON.code:(myTurn?'Your move · code ':"Friend's move · code ")+ON.code);
    $('onShare').textContent=nudge||(!myTurn&&ON.status!=='done')?'📲 Tell your friend':'📲 Share link';
    $('onShare').hidden=ON.status==='done'}
  async function share(){const url=link(ON.code);const text=ON.status==='waiting'?`Play ${INFO.name} with me on ${(window.BDA_GAME&&BDA_GAME.site)||'Sketchpad Arcade'}!`:`Your turn in ${INFO.name}!`;
    try{if(navigator.share){await navigator.share({title:INFO.name,text,url});return}}catch(e){if(e&&e.name==='AbortError')return}
    try{await navigator.clipboard.writeText(text+' '+url);S.pop('Link copied!')}catch(e){prompt('Copy this link:',url)}}
  // ---------- starting and joining ----------
  async function create(){S.mode='online';S.sfx('tap');S.show(null);S.status('Making your game…');
    try{S.scores=[0,0];GAME.reset();const st={g:GAME.save(),scores:[0,0],msg:''};
      const g=await rpc('vs_create',{p_game:INFO.slug,p_state:st,p_token:id()});ON.seat=0;remember(g.code,0);
      history.replaceState(null,'',location.pathname+'?game='+g.code);ON.since=Date.now();apply(g,true);showInvite()}
    catch(e){S.status("Couldn't start an online game. Check your connection.");S.show('start')}}
  function showInvite(){$('invLink').textContent=link(ON.code).replace(/^https?:\/\//,'');S.show('invite')}
  async function join(code){S.mode='online';S.show(null);S.status('Opening your game…');
    try{const g=await rpc('vs_join',{p_code:code,p_token:id()});
      if(!g){S.status('That game link has expired.');history.replaceState(null,'',location.pathname);S.show('start');return}
      if(g.game!==INFO.slug){location.replace('/play/'+g.game+'?game='+g.code);return}
      if(g.seat<0){S.mode=null;S.status('That game already has two players.');history.replaceState(null,'',location.pathname);S.show('start');return}
      ON.seat=g.seat;remember(g.code,g.seat);ON.since=Date.now();apply(g,true);
      if(g.status!=='done'&&g.seat===1&&g.version===0)S.pop("You're pink!",S.col(1))}
    catch(e){S.status("Couldn't open that game. Check your connection and try again.");S.mode=null;S.show('start')}}
  ON.leave=()=>{ON.code=null;ON.status=null;clearTimeout(ON.pollT);history.replaceState(null,'',location.pathname);bar()};
  $('vsInvite').onclick=create;
  $('onShare').onclick=share;$('invShare').onclick=share;
  $('invGo').onclick=()=>{S.sfx('tap');S.show(null)};
  $('again').addEventListener('click',e=>{if(S.mode==='online'){e.stopImmediatePropagation();create()}},true);
  ON.start=()=>{const m=location.search.match(/[?&]game=([A-Za-z0-9]{4,10})/);if(m){join(m[1].toUpperCase());return true}return false};
  return ON;
})();
