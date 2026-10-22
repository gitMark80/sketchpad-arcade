/* Shared player layer (Sketchpad Arcade twin of Beach Day Arcade's), put at the top of <head> on every play page by build.py (before the game's own script).
   1. Sound: tells the browser the game's sounds are "ambient" so they mix with an audiobook or music playing in another app
      instead of pausing it, and parks every AudioContext while the page is in the background.
   2. Progress: whatever the game saves in localStorage is mirrored to the player's profile (a name plus a 6-letter code from
      /api/profile) a few seconds after each change, and pulled back on any device that enters the same code.
   3. A small player button in the game's header opens the profile card. */
(()=>{
'use strict';
/* ---------- 1. sound that plays nicely with other apps ---------- */
try{if(navigator.audioSession)navigator.audioSession.type='ambient'}catch(e){}
const ctxs=new Set(),parked=new Set();
for(const n of ['AudioContext','webkitAudioContext']){const O=window[n];if(typeof O!=='function')continue;
  try{window[n]=new Proxy(O,{construct(T,args){const c=new T(...args);ctxs.add(c);return c}})}catch(e){}}
document.addEventListener('visibilitychange',()=>{ctxs.forEach(c=>{try{
  if(document.hidden){if(c.state==='running'){parked.add(c);c.suspend().catch(()=>{})}}
  else if(parked.has(c)){parked.delete(c);if(c.state==='suspended')c.resume().catch(()=>{})}}catch(e){}})});

/* ---------- 2. progress mirrored to a profile ---------- */
const G=()=>window.BDA_GAME||{},slug=()=>G().slug||location.pathname.split('/').pop().replace(/\.html$/,'');
const PKEY='sa.profile';
const ls={get(k){try{return localStorage.getItem(k)}catch(e){return null}},set(k,v){try{localStorage.setItem(k,v)}catch(e){}},del(k){try{localStorage.removeItem(k)}catch(e){}}};
const own=k=>typeof k==='string'&&!k.startsWith('bda.')&&!k.startsWith('bda-')&&!k.startsWith('sa.')&&!k.startsWith('sa-'); // bda-played-* is the play counter, sa-sound and sa-online-* are per-device settings, not progress
let profile=null;try{profile=JSON.parse(ls.get(PKEY)||'null')}catch(e){}
// the keys this game has ever written, so a fresh device knows what to pull
const keysKey=()=>'sa.keys.'+slug(),atKey=()=>'sa.at.'+slug();
const bootAt=Number(ls.get(atKey()))||0; // when this device last saved, as of page load (writes the game makes while starting up don't count)
function keys(){try{return new Set(JSON.parse(ls.get(keysKey())||'[]'))}catch(e){return new Set()}}
function noteKey(k){const s=keys();if(!s.has(k)){s.add(k);ls.set(keysKey(),JSON.stringify([...s]))}}
let syncT=0,syncing=false,lastPushed='',applying=false;
function touched(k){if(!own(k)||applying)return;noteKey(k);ls.set(atKey(),String(Date.now()));if(profile){clearTimeout(syncT);syncT=setTimeout(push,4000)}}
try{const P=Storage.prototype,S=P.setItem,R=P.removeItem;
  P.setItem=function(k,v){S.call(this,k,v);if(this===localStorage)touched(k)};
  P.removeItem=function(k){R.call(this,k);if(this===localStorage)touched(k)}}catch(e){}
function snapshot(){const o={};keys().forEach(k=>{const v=ls.get(k);if(v!=null)o[k]=v});return{keys:o,at:Number(ls.get(atKey()))||0}}
async function push(){if(!profile||syncing)return;const snap=snapshot();if(!Object.keys(snap.keys).length)return;
  const body=JSON.stringify({game:slug(),data:snap});if(body===lastPushed)return;syncing=true;
  try{const r=await fetch('/api/profile?code='+profile.code,{method:'PUT',headers:{'Content-Type':'application/json'},body,keepalive:true});
    if(r.status===404)setProfile(null);else if(r.ok)lastPushed=body}catch(e){}syncing=false}
function flush(){if(profile){clearTimeout(syncT);push()}}
document.addEventListener('visibilitychange',()=>{if(document.hidden)flush()});addEventListener('pagehide',flush);
// write the profile's copy of this game into localStorage, then reload so the game starts from it
function apply(d){if(!d||typeof d!=='object'||!d.keys)return false;applying=true;
  const mine=keys(),remote=d.keys;mine.forEach(k=>{if(!(k in remote))ls.del(k)});
  for(const k in remote){if(own(k)){ls.set(k,String(remote[k]));mine.add(k)}}
  ls.set(keysKey(),JSON.stringify([...mine]));ls.set(atKey(),String(d.at||Date.now()));applying=false;return true}
async function pull(){if(!profile)return;try{const r=await fetch('/api/profile?code='+profile.code);if(r.status===404){setProfile(null);return}if(!r.ok)return;
  const j=await r.json();if(j.name&&j.name!==profile.name)setProfile({code:profile.code,name:j.name});
  const d=j.games&&j.games[slug()],flag='sa.pulled.'+slug();
  if(d&&(d.at||0)>bootAt){if(sessionStorage.getItem(flag)===String(d.at))return;sessionStorage.setItem(flag,String(d.at));if(apply(d))location.reload()}
  else if(!d)push()}catch(e){}}

/* ---------- 3. the profile card ---------- */
const PERSON='<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 20.5c0-4 3.6-6.5 8-6.5s8 2.5 8 6.5"/></svg>';
const F='"Patrick Hand","Comic Sans MS","Chalkboard SE",cursive',D='"Gloria Hallelujah","Comic Sans MS","Chalkboard SE",cursive';
const WOB='255px 15px 225px 15px/15px 225px 15px 255px',WOB2='15px 255px 15px 225px/225px 15px 255px 15px';
const CSS='.sa-player{flex:none;display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;padding:0;border-radius:'+WOB2+';cursor:pointer;border:2px solid #2e2e33;background:#f6f3ea;color:#2e2e33;box-shadow:2px 2px 0 #55555c;position:relative}.sa-player svg{width:19px;height:19px}.sa-player:active{transform:translate(2px,2px);box-shadow:none}.sa-player.on{background:#dcebdd}.sa-player.on::after{content:"";position:absolute;right:-4px;top:-4px;width:12px;height:12px;border-radius:50%;background:#5a9a6a;border:2px solid #2e2e33}.sa-player:focus-visible{outline:3px solid #2e2e33;outline-offset:2px}'+
'.sa-pcover{position:fixed;inset:0;z-index:9999;display:grid;place-items:center;padding:14px;background:rgba(46,46,51,.5);font-family:'+F+';-webkit-user-select:none;user-select:none}.sa-pcover[hidden]{display:none}'+
'.sa-pcard{position:relative;background:#f6f3ea;color:#2e2e33;border:2px solid #2e2e33;border-radius:'+WOB+';padding:20px 18px 14px;width:100%;max-width:340px;text-align:center;box-shadow:4px 4px 0 #55555c;max-height:92vh;overflow:auto;box-sizing:border-box;background-image:linear-gradient(#d6e4f2 1px,transparent 1px);background-size:100% 30px;background-position:0 12px}'+
'.sa-pcard h2{margin:0;font:400 1.75rem/1.1 '+D+';text-transform:uppercase;letter-spacing:.04em;transform:rotate(-1.5deg)}.sa-pcard p{margin:8px 0 0;color:#55555c;line-height:1.35;font-size:1.05rem}.sa-pcard p b{color:#2e2e33}'+
'.sa-pfield{display:block;text-align:left;margin-top:12px}.sa-pfield span{display:block;font:400 .85rem '+D+';letter-spacing:.08em;text-transform:uppercase;color:#55555c;margin:0 0 4px 4px}'+
'.sa-pfield input{width:100%;appearance:none;border:2px solid #2e2e33;border-radius:'+WOB2+';background:#fff;padding:9px 12px;font:400 1.25rem/1.2 '+F+';color:#2e2e33;box-sizing:border-box;box-shadow:2px 2px 0 #55555c;-webkit-user-select:text;user-select:text}.sa-pfield input:focus{outline:3px solid #c99a1a;outline-offset:1px}.sa-pfield input::placeholder{color:#a9a69c}'+
'#saCodeIn{font-size:1.55rem;letter-spacing:.3em;text-align:center;text-transform:uppercase}'+
'.sa-pbtn{display:block;appearance:none;width:100%;margin-top:12px;border:2px solid #2e2e33;border-radius:'+WOB+';padding:11px 16px;min-height:48px;font:400 1.2rem/1 '+D+';color:#2e2e33;cursor:pointer;background:#d6e4f2;box-shadow:3px 3px 0 #55555c}.sa-pbtn.go{background:#f3e6b0}.sa-pbtn:active{transform:translate(2px,2px);box-shadow:1px 1px 0 #55555c}.sa-pbtn:disabled{opacity:.6}'+
'.sa-plink{appearance:none;border:0;background:none;margin-top:10px;font:400 1rem '+F+';color:#2f6fb5;text-decoration:underline;min-height:36px;cursor:pointer}'+
'.sa-por{margin-top:16px!important;padding-top:12px;border-top:2px dashed #c9c6bc}.sa-pcode{margin:10px auto 0;display:inline-block;background:#fff;border:2px dashed #2e2e33;border-radius:'+WOB2+';padding:8px 18px;font:400 2rem/1 '+D+';letter-spacing:.3em;color:#2e2e33;-webkit-user-select:text;user-select:text}'+
'.sa-pmsg{min-height:1.2em;color:#d9661a!important}';
const CARD='<div class="sa-pcard" role="dialog" aria-modal="true" aria-labelledby="saPTitle"><h2 id="saPTitle">My profile</h2>'+
'<div id="saPNew"><p>A profile keeps your levels, stars and best scores for every game here, and lets you pick up on another phone or tablet.</p>'+
'<label class="sa-pfield"><span>Your name</span><input id="saNameIn" type="text" maxlength="24" autocomplete="nickname" placeholder="e.g. Kim" enterkeyhint="done"></label>'+
'<button class="sa-pbtn go" id="saCreate" type="button">Make my profile</button></div>'+
'<div id="saPHave"><p class="sa-por">Already have a profile on another device?</p>'+
'<label class="sa-pfield"><span>Profile code</span><input id="saCodeIn" type="text" maxlength="6" autocapitalize="characters" autocomplete="off" spellcheck="false" placeholder="ABC123" enterkeyhint="go"></label>'+
'<button class="sa-pbtn" id="saLoad" type="button">Load my progress</button></div>'+
'<div id="saPMine" hidden><p>Playing as <b id="saPName"></b>. Your progress in every game saves to this profile as you play.</p>'+
'<p>To play on another device, open any game there, tap the player button and enter this code:</p><div class="sa-pcode" id="saPCode"></div>'+
'<button class="sa-pbtn" id="saSync" type="button">Save now</button>'+
'<button class="sa-plink" id="saForget" type="button">Use this device without the profile</button></div>'+
'<p class="sa-pmsg" id="saPMsg" role="status" aria-live="polite"></p><button class="sa-plink" id="saPClose" type="button">Back</button></div>';
let $=null;
function setProfile(p){profile=p;if(p)ls.set(PKEY,JSON.stringify(p));else ls.del(PKEY);lastPushed='';paint()}
function paint(){if(!$)return;const has=!!profile;$.btn.classList.toggle('on',has);$.btn.setAttribute('aria-label',has?'Profile: '+profile.name:'Player profile: save your progress');
  $.pnew.hidden=has;$.phave.hidden=has;$.mine.hidden=!has;if(has){$.name.textContent=profile.name;$.code.textContent=profile.code}}
const msg=t=>{if($)$.msg.textContent=t};
const cleanName=v=>String(v||'').replace(/\s+/g,' ').trim().slice(0,24);
function mount(){
  const head=document.querySelector('.sa-head');if(!head||document.querySelector('.sa-player'))return;
  const st=document.createElement('style');st.textContent=CSS;document.head.appendChild(st);
  const btn=document.createElement('button');btn.type='button';btn.className='sa-player';btn.innerHTML=PERSON;
  const share=head.querySelector('.sa-share');if(share)head.insertBefore(btn,share);else head.appendChild(btn);
  const cover=document.createElement('div');cover.className='sa-pcover';cover.hidden=true;cover.innerHTML=CARD;document.body.appendChild(cover);
  const q=id=>cover.querySelector('#'+id);
  $={btn,cover,pnew:q('saPNew'),phave:q('saPHave'),mine:q('saPMine'),name:q('saPName'),code:q('saPCode'),msg:q('saPMsg'),nameIn:q('saNameIn'),codeIn:q('saCodeIn'),create:q('saCreate'),load:q('saLoad')};
  const open=()=>{msg('');cover.hidden=false;if(!profile)$.nameIn.focus()},close=()=>{cover.hidden=true};
  btn.addEventListener('click',open);q('saPClose').addEventListener('click',close);cover.addEventListener('click',e=>{if(e.target===cover)close()});
  cover.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
  $.codeIn.addEventListener('input',()=>{$.codeIn.value=$.codeIn.value.toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,6)});
  $.create.addEventListener('click',async()=>{const name=cleanName($.nameIn.value);if(!name){msg('Type a name first.');$.nameIn.focus();return}
    $.create.disabled=true;msg('Making your profile…');
    try{const r=await fetch('/api/profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});if(!r.ok)throw 0;const j=await r.json();setProfile({code:j.code,name:j.name});msg('');push()}
    catch(e){msg("Couldn't reach the profile server. Check your connection and try again.")}$.create.disabled=false});
  $.load.addEventListener('click',async()=>{const code=$.codeIn.value.toUpperCase().replace(/[^A-Z0-9]/g,'');if(code.length!==6){msg('A code is 6 letters and numbers.');$.codeIn.focus();return}
    $.load.disabled=true;msg('Looking it up…');
    try{const r=await fetch('/api/profile?code='+code);if(r.status===404){msg('No profile has that code. Check it and try again.');$.load.disabled=false;return}if(!r.ok)throw 0;
      const j=await r.json();setProfile({code,name:j.name||'Player'});const d=j.games&&j.games[slug()];$.codeIn.value='';
      if(d&&apply(d)){sessionStorage.setItem('sa.pulled.'+slug(),String(d.at||0));msg('Loading your progress…');location.reload()}else{msg('');push()}}
    catch(e){msg("Couldn't reach the profile server. Check your connection and try again.")}$.load.disabled=false});
  q('saSync').addEventListener('click',async()=>{msg('Saving…');lastPushed='';await push();msg(profile?'Saved to your profile.':'That profile is gone; make a new one.')});
  q('saForget').addEventListener('click',()=>{setProfile(null);msg('');close()});
  paint();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{mount();pull()});else{mount();pull()}
window.BDA=window.BDA||{};window.BDA.player={get profile(){return profile},setProfile,push,pull,snapshot};
})();
