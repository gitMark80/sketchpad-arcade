/* Sketchpad Arcade two-player shell: Play vs Friend (pass & play) or Play vs Bot (Easy / Medium / Hard),
   turn banner, scores, round tally, sound, and the player's record against the bot (saved on this device).
   A game defines GAME = {reset(), botMove(), render?()} and calls S.setTurn(), S.addScore(), S.end(). */
const S=(()=>{
  const $=id=>document.getElementById(id);
  const KEY='sa-vs-'+INFO.slug;
  let save={wins:{easy:0,medium:0,hard:0},losses:{easy:0,medium:0,hard:0},streak:0,best:0,mode:null,diff:'easy'};
  try{const v=JSON.parse(localStorage.getItem(KEY)||'null');if(v)save=Object.assign(save,v)}catch(e){}
  let sound=true;try{sound=localStorage.getItem('sa-sound')!=='off'}catch(e){}
  const S={mode:save.mode,diff:save.diff,turn:0,first:0,scores:[0,0],rounds:[0,0],active:false,busy:false,botTimer:0};
  function persist(){try{localStorage.setItem(KEY,JSON.stringify(save))}catch(e){}}
  const online=()=>S.mode==='online'&&typeof ON!=='undefined';
  S.names=()=>online()?ON.names():S.mode==='bot'?['You','Bot']:['Player 1','Player 2'];
  S.isBot=()=>S.mode==='bot'&&S.turn===1;
  S.canPlay=()=>S.active&&!S.busy&&!S.isBot()&&!(online()&&S.turn!==ON.seat);
  S.rand=n=>Math.floor(Math.random()*n);
  S.pick=a=>a[Math.floor(Math.random()*a.length)];
  /* chance the bot plays its best move instead of a random-ish one */
  S.skill=()=>({easy:.25,medium:.7,hard:1})[S.diff];
  // ---------- sound ----------
  let ac=null;
  function tone(f,d,type,vol,slide){if(!sound)return;try{ac=ac||new (window.AudioContext||window.webkitAudioContext)();if(ac.state==='suspended')ac.resume();
    const o=ac.createOscillator(),g=ac.createGain(),t=ac.currentTime;o.type=type||'triangle';o.frequency.setValueAtTime(f,t);if(slide)o.frequency.exponentialRampToValueAtTime(slide,t+d);
    g.gain.setValueAtTime(vol||.12,t);g.gain.exponentialRampToValueAtTime(.001,t+d);o.connect(g).connect(ac.destination);o.start(t);o.stop(t+d+.02)}catch(e){}}
  S.sfx=k=>{if(k==='tap')tone(520,.08,'triangle',.1);else if(k==='bot')tone(380,.08,'triangle',.08);
    else if(k==='score'){tone(660,.1);setTimeout(()=>tone(880,.14),90)}
    else if(k==='miss')tone(300,.25,'sine',.1,160);
    else if(k==='win'){[523,659,784,1047].forEach((f,i)=>setTimeout(()=>tone(f,.18),i*110))}
    else if(k==='lose'){[440,370,311].forEach((f,i)=>setTimeout(()=>tone(f,.22,'sine'),i*140))}
    else if(k==='draw'){tone(500,.15);setTimeout(()=>tone(500,.15),160)}};
  function sndLabel(){$('snd').textContent=(sound?'🔊':'🔇')+' Sound: '+(sound?'On':'Off')}
  $('snd').onclick=()=>{sound=!sound;try{localStorage.setItem('sa-sound',sound?'on':'off')}catch(e){}sndLabel()};sndLabel();
  // ---------- HUD ----------
  S.pop=(t,col)=>{const d=document.createElement('div');d.className='pop';d.textContent=t;if(col)d.style.color=col;$('stage').appendChild(d);setTimeout(()=>d.remove(),1000)};
  S.col=p=>p===0?'#2f6fb5':'#c45a8a';
  S.wash=p=>p===0?'#d6e4f2':'#f0d5e2';
  S.hud=()=>{const n=S.names();$('n0').textContent=n[0];$('n1').textContent=n[1];const sc=INFO.scoreIsRounds?S.rounds:S.scores;$('s0').textContent=sc[0];$('s1').textContent=sc[1];
    $('p0').classList.toggle('on',S.active&&S.turn===0);$('p1').classList.toggle('on',S.active&&S.turn===1);
    $('tally').textContent='Rounds won: '+n[0]+' '+S.rounds[0]+' · '+n[1]+' '+S.rounds[1];$('tally').hidden=online()};
  S.status=(t,who)=>{const e=$('turn');e.textContent=t;e.className='turn'+(who===0||who===1?' t'+who:'')};
  S.turnText=()=>{if(online())return ON.turnText();const n=S.names();if(S.isBot())return '🤖 Bot is thinking…';return '✏️ '+(S.mode==='bot'?'Your':n[S.turn]+"'s")+' turn'+(INFO.turnHint?INFO.turnHint(S.turn):'')};
  S.addScore=(p,n)=>{S.scores[p]+=n;S.hud()};
  S.setTurn=(t,quiet)=>{S.turn=t;S.hud();if(!S.active)return;if(online()&&!ON.applying)ON.push(t,false);S.status(S.turnText(),t);if(GAME.render)GAME.render();
    clearTimeout(S.botTimer);if(S.isBot()){S.busy=true;S.botTimer=setTimeout(()=>{S.busy=false;if(S.active&&S.isBot())GAME.botMove()},INFO.botDelay||650)}};
  // ---------- rounds ----------
  function show(id){['start','diff','over','help','pass','invite'].forEach(x=>{const e=$(x);if(e)e.hidden=x!==id})}
  S.show=show;
  S.newRound=()=>{clearTimeout(S.botTimer);S.busy=false;S.scores=[0,0];S.active=true;show(null);GAME.reset();const st=S.first;S.first^=1;if(GAME.begin)GAME.begin(st);else S.setTurn(st);};
  S.end=(winner,msg)=>{if(!S.active)return;S.active=false;clearTimeout(S.botTimer);if(online()&&!ON.applying)ON.push(S.turn,true,winner,msg);S.hud();const n=S.names();let head;
    if(winner===0||winner===1){S.rounds[winner]++;head=S.mode==='bot'||online()?(n[winner]==='You'?'You win!':n[winner]+' wins'):n[winner]+' wins!'}else head="It's a draw";
    if(S.mode==='bot'){const d=S.diff;if(winner===0){save.wins[d]++;save.streak++;save.best=Math.max(save.best,save.streak)}else{if(winner===1)save.losses[d]++;if(winner===1)save.streak=0}persist()}
    S.sfx(winner===-1?'draw':((S.mode==='bot'||online())&&n[winner]!=='You'?'lose':'win'));
    S.status(head,winner);S.hud();if(GAME.render)GAME.render();
    setTimeout(()=>{$('overH').textContent=head;$('overMsg').textContent=msg||'';$('overRec').textContent=S.mode==='bot'?record():'';$('overRec').hidden=S.mode!=='bot';$('again').textContent='Play again';show('over')},INFO.endDelay||1100)};
  function record(){const w=save.wins,d=S.diff;return 'Your wins vs Bot — Easy '+w.easy+' · Medium '+w.medium+' · Hard '+w.hard+(save.best?' · Best streak '+save.best:'')}
  function startRec(){const w=save.wins;const any=w.easy+w.medium+w.hard;$('startRec').textContent=any?record():'Beat the bot to start your record.'}
  function pickMode(m){S.mode=m;save.mode=m;persist();S.rounds=[0,0];S.first=0;if(m==='bot'){show('diff')}else{S.newRound()}}
  $('vsFriend').onclick=()=>{S.sfx('tap');pickMode('friend')};
  $('vsBot').onclick=()=>{S.sfx('tap');pickMode('bot')};
  document.querySelectorAll('[data-diff]').forEach(b=>b.onclick=()=>{S.sfx('tap');S.diff=b.dataset.diff;save.diff=S.diff;persist();S.rounds=[0,0];S.first=0;S.newRound()});
  $('diffBack').onclick=()=>show('start');
  $('again').onclick=()=>{S.sfx('tap');S.newRound()};
  $('overMode').onclick=$('modeb').onclick=()=>{if(online())ON.leave();S.mode=null;S.active=false;clearTimeout(S.botTimer);startRec();S.status('Pick who to play against');show('start')};
  $('newr').onclick=()=>{if(!S.mode||online()){if(online())ON.leave();S.mode=null;S.active=false;startRec();S.status('Pick who to play against');show('start');return}S.newRound()};
  $('helpb').onclick=()=>{S.wasOpen=['start','diff','over','pass','invite'].find(x=>$(x)&&!$(x).hidden)||null;show('help')};
  $('helpClose').onclick=()=>show(S.wasOpen);
  S.pass=(name,cb)=>{$('passH').textContent='Pass to '+name;$('passGo').textContent="I'm "+name+' — go!';show('pass');$('passGo').onclick=()=>{S.sfx('tap');show(null);cb()}};
  // ---------- boot ----------
  S.boot=()=>{startRec();S.hud();S.status('Pick who to play against');GAME.reset();if(GAME.render)GAME.render();show('start');if(typeof ON!=='undefined'&&ON.ok)ON.start()};
  return S;
})();
