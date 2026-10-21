/* Sketchpad Arcade one-player puzzle shell: Easy / Medium / Hard picker, timer, best results per level (saved
   on this device), sound and the start / end / help cards. A game defines GAME = {reset(diff)} and calls
   P.go() on the first move, P.stat(text), P.win(value, msg) and P.lose(msg). INFO.best is 'time' (lower
   is better), 'low' (fewer is better) or 'high'. */
const P=(()=>{
  const $=id=>document.getElementById(id);
  const KEY='sa-solo-'+INFO.slug;
  let save={diff:'easy',best:{},played:0,won:0};
  try{const v=JSON.parse(localStorage.getItem(KEY)||'null');if(v)save=Object.assign(save,v)}catch(e){}
  let sound=true;try{sound=localStorage.getItem('sa-sound')!=='off'}catch(e){}
  const P={diff:save.diff,active:false,t0:0,secs:0,timer:0,started:false};
  function persist(){try{localStorage.setItem(KEY,JSON.stringify(save))}catch(e){}}
  P.rand=n=>Math.floor(Math.random()*n);
  P.pick=a=>a[Math.floor(Math.random()*a.length)];
  P.shuffle=a=>{for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a};
  let ac=null;
  function tone(f,d,type,vol,slide){if(!sound)return;try{ac=ac||new (window.AudioContext||window.webkitAudioContext)();if(ac.state==='suspended')ac.resume();
    const o=ac.createOscillator(),g=ac.createGain(),t=ac.currentTime;o.type=type||'triangle';o.frequency.setValueAtTime(f,t);if(slide)o.frequency.exponentialRampToValueAtTime(slide,t+d);
    g.gain.setValueAtTime(vol||.12,t);g.gain.exponentialRampToValueAtTime(.001,t+d);o.connect(g).connect(ac.destination);o.start(t);o.stop(t+d+.02)}catch(e){}}
  P.sfx=k=>{if(k==='tap')tone(520,.07,'triangle',.09);else if(k==='soft')tone(420,.05,'triangle',.06);
    else if(k==='good'){tone(660,.1);setTimeout(()=>tone(880,.14),90)}
    else if(k==='bad')tone(260,.25,'sine',.1,150);
    else if(k==='flag')tone(700,.06,'square',.05);
    else if(k==='win'){[523,659,784,1047].forEach((f,i)=>setTimeout(()=>tone(f,.18),i*110))}
    else if(k==='lose'){[440,370,311].forEach((f,i)=>setTimeout(()=>tone(f,.22,'sine'),i*140))}};
  function sndLabel(){$('snd').textContent=(sound?'🔊':'🔇')+' Sound: '+(sound?'On':'Off')}
  $('snd').onclick=()=>{sound=!sound;try{localStorage.setItem('sa-sound',sound?'on':'off')}catch(e){}sndLabel()};sndLabel();
  P.pop=(t,col)=>{const d=document.createElement('div');d.className='pop';d.textContent=t;if(col)d.style.color=col;$('stage').appendChild(d);setTimeout(()=>d.remove(),1000)};
  P.msg=t=>{$('msg').textContent=t||''};
  P.stat=v=>{$('st1').textContent=v};
  const fmt=s=>INFO.best==='time'?Math.floor(s/60)+':'+String(s%60).padStart(2,'0'):String(s);
  P.fmt=fmt;
  function bestText(){const b=save.best[P.diff];return b==null?'–':fmt(b)}
  function tick(){P.secs=Math.floor((Date.now()-P.t0)/1000);$('time').textContent=fmt0(P.secs)}
  const fmt0=s=>Math.floor(s/60)+':'+String(s%60).padStart(2,'0');
  P.go=()=>{if(P.started||!P.active)return;P.started=true;P.t0=Date.now();clearInterval(P.timer);P.timer=setInterval(tick,500)};
  function stop(){clearInterval(P.timer);if(P.started)tick()}
  const LV={easy:'Easy',medium:'Medium',hard:'Hard'};
  function hud(){$('lvl').textContent=LV[P.diff];$('best').textContent=bestText();$('time').textContent='0:00'}
  function show(id){['start','over','help'].forEach(x=>{$(x).hidden=x!==id})}
  P.show=show;
  P.newGame=()=>{clearInterval(P.timer);P.started=false;P.secs=0;P.active=true;show(null);hud();P.msg('');GAME.reset(P.diff)};
  function done(won,value,head,msg){if(!P.active)return;P.active=false;stop();save.played++;let nb=false;
    if(won){save.won++;const v=INFO.best==='time'?P.secs:value;const o=save.best[P.diff];
      if(v!=null&&(o==null||(INFO.best==='high'?v>o:v<o))){save.best[P.diff]=v;nb=o!=null||true}}
    persist();$('best').textContent=bestText();P.sfx(won?'win':'lose');
    setTimeout(()=>{$('overH').textContent=head;$('overMsg').textContent=msg||'';
      $('overRec').textContent=won?(nb?'New best on '+LV[P.diff]+'! ':'')+'Best on '+LV[P.diff]+': '+bestText():'';show('over')},INFO.endDelay||1000)}
  P.win=(value,msg,head)=>done(true,value,head||INFO.winHead||'You did it!',msg);
  P.lose=(msg,head)=>done(false,null,head||INFO.loseHead||'Oh no!',msg);
  P.setBest=(v)=>{/* for 'high' games that keep a running score (streaks) */const o=save.best[P.diff];if(o==null||v>o){save.best[P.diff]=v;persist();$('best').textContent=bestText()}};
  function pickDiff(d){P.diff=d;save.diff=d;persist();P.sfx('tap');P.newGame()}
  document.querySelectorAll('[data-diff]').forEach(b=>b.onclick=()=>pickDiff(b.dataset.diff));
  $('again').onclick=()=>{P.sfx('tap');P.newGame()};
  $('overLvl').onclick=$('lvlb').onclick=()=>{P.active=false;clearInterval(P.timer);startRec();show('start')};
  $('newg').onclick=()=>{if(!$('start').hidden)return;P.newGame()};
  $('helpb').onclick=()=>{P.wasOpen=['start','over'].find(x=>!$(x).hidden)||null;show('help')};
  $('helpClose').onclick=()=>show(P.wasOpen);
  function startRec(){const b=save.best,f=k=>b[k]==null?'–':fmt(b[k]);$('startRec').textContent=(b.easy!=null||b.medium!=null||b.hard!=null)?(INFO.bestLabel||'Your best')+': Easy '+f('easy')+' · Medium '+f('medium')+' · Hard '+f('hard'):''}
  P.boot=()=>{startRec();hud();GAME.reset(P.diff);P.active=false;show('start')};
  return P;
})();
