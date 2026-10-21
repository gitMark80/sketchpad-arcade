INFO.best='high';INFO.bestLabel='Best streaks';INFO.winHead='Doodle saved!';INFO.loseHead='Rubbed out!';INFO.endDelay=1200;
/*SHELL*/
/* Save the Doodle: a hangman-style word guess. Each wrong letter rubs out part of a pencil doodle instead of drawing a gallows.
   Streak = words saved in a row on this level (Best keeps the longest). */
const WORDS={
 easy:{Animal:['cat','dog','pig','cow','duck','frog','bear','lion','fish','goat','hen','owl','fox','bee','ant','deer','mouse','horse','sheep','zebra'],
  Food:['cake','pie','apple','pear','corn','bread','soup','milk','egg','rice','grape','lemon','pizza','candy','jam'],
  'At school':['desk','book','pen','glue','bus','bell','chalk','paper','ruler','class','lunch','map'],
  'Out and about':['park','tree','kite','sun','moon','star','rain','boat','car','bike','ship','snow','sand','hill']},
 medium:{Animal:['rabbit','turtle','monkey','parrot','puppy','kitten','giraffe','dolphin','penguin','spider','beaver','camel','donkey','hamster','lizard'],
  Food:['banana','cookie','muffin','noodle','carrot','cheese','waffle','pancake','popcorn','pickle','cherry','orange','pretzel','sandwich'],
  'At school':['pencil','eraser','crayon','sticker','teacher','recess','marker','backpack','notebook','scissors','library','homework'],
  'Things to do':['painting','dancing','singing','fishing','camping','baking','reading','drawing','skating','jumping','swimming']},
 hard:{Animal:['squirrel','kangaroo','octopus','flamingo','hedgehog','crocodile','butterfly','chameleon','porcupine','jellyfish','woodpecker','grasshopper'],
  'Around the house':['blanket','fireplace','staircase','doorbell','cupboard','toothbrush','washcloth','lampshade','refrigerator','bookshelf'],
  'Big ideas':['adventure','imagine','friendship','kindness','treasure','mystery','rainbow','celebrate','discovery','invention'],
  Places:['library','playground','museum','lighthouse','mountain','volcano','waterfall','cathedral','orchard','farmhouse']}};
const TRIES={easy:7,medium:6,hard:5};
const $=id=>document.getElementById(id);
const partsEl=[...document.querySelectorAll('#parts [data-p]')];
let word='',cat='',got=new Set(),miss=0,streak=0,lastWords=[];
const keysEl=$('keys');const keyBtn={};
'abcdefghijklmnopqrstuvwxyz'.split('').forEach(ch=>{const b=document.createElement('button');b.type='button';b.textContent=ch;b.setAttribute('aria-label','Letter '+ch.toUpperCase());b.onclick=()=>guess(ch);keysEl.appendChild(b);keyBtn[ch]=b});
addEventListener('keydown',e=>{if(e.ctrlKey||e.metaKey||e.altKey)return;const k=e.key.toLowerCase();if(/^[a-z]$/.test(k)&&P.active)guess(k)});
function drawWord(fresh){$('word').innerHTML=word.split('').map(ch=>ch===' '?'<span class="sp"></span>':`<span class="l${got.has(ch)&&fresh===ch?' got':''}">${got.has(ch)?ch:'&nbsp;'}</span>`).join('');
  $('word').setAttribute('aria-label','Word: '+word.split('').map(c=>got.has(c)?c:'blank').join(' '))}
function erase(){const n=Math.round(miss*partsEl.length/TRIES[P.diff]);partsEl.forEach((p,i)=>p.classList.toggle('gone',i<n));
  if(n>0&&n<=partsEl.length){const bb=partsEl[n-1].getBBox();const er=$('eraser');er.setAttribute('transform',`translate(${bb.x+bb.width/2},${bb.y+bb.height/2}) rotate(-20)`);er.style.opacity=1;setTimeout(()=>er.style.opacity=0,600)}
  $('mouth').setAttribute('d',miss>=TRIES[P.diff]-1&&miss>0?'M90 74 C96 68 104 68 110 74':'M90 70 C96 76 104 76 110 70')}
function guess(ch){if(!P.active||keyBtn[ch].disabled)return;P.go();keyBtn[ch].disabled=true;
  if(word.includes(ch)){got.add(ch);keyBtn[ch].classList.add('yes');P.sfx('good');drawWord(ch);
    if([...word].every(c=>c===' '||got.has(c))){streak++;P.stat(streak);P.setBest(streak);P.pop('Saved!');P.win(streak,`The word was “${word.toUpperCase()}”. Streak: ${streak}.`)}}
  else{miss++;keyBtn[ch].classList.add('no');P.sfx('bad');erase();const left=TRIES[P.diff]-miss;P.msg(left>0?(left===1?'Careful! One try left.':left+' tries left'):'');
    if(miss>=TRIES[P.diff]){got=new Set(word);$('word').innerHTML=word.split('').map(c=>c===' '?'<span class="sp"></span>':`<span class="l miss">${c}</span>`).join('');
      const s=streak;streak=0;P.stat(0);P.lose(`The word was “${word.toUpperCase()}”.`+(s?` Your streak was ${s}.`:''))}}}
const GAME={reset(d){if(GAME.lastDiff!==d){streak=0;GAME.lastDiff=d}
    const cats=Object.keys(WORDS[d]);let w,c,t=0;do{c=P.pick(cats);w=P.pick(WORDS[d][c]);t++}while(lastWords.includes(w)&&t<50);
    lastWords.push(w);if(lastWords.length>25)lastWords.shift();word=w;cat=c;got=new Set();miss=0;
    $('clue').textContent=c;Object.values(keyBtn).forEach(b=>{b.disabled=false;b.className=''});partsEl.forEach(p=>p.classList.remove('gone'));erase();drawWord();
    P.stat(streak);P.msg(TRIES[d]+' tries · '+w.length+' letters')}};
