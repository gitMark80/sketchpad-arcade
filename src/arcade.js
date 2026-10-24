/* arcade.js: shared by Sketchpad Arcade and Beach Day Arcade (keep the two copies identical).
   build.py puts it on every page with a small window.ARC config in front of it:
     ARC = {page: "home"|"game"|"play"|"book"|"other", slug, name, site, next: [{slug,name}], book: {slug,title}|null, portrait: bool}
   What it does, with no accounts and nothing personal leaving the device:
   - Counts events for the /stats page: anonymous tallies per game, per day (POST /api/event). The only things stored
     on the device are dates and game slugs in localStorage, used so a refresh or a second visit the same day isn't counted twice,
     and the coarse source of the browser's first visit ("youtube", "pinterest", "google"…) so /stats can show where players
     come from. Nothing is counted inside Reel Studio, or on a device where "Don't count my visits" was switched on at /stats.
   - Remembers recently played games on this device and shows them on the home page (Keep Playing).
   - On play pages: an Up Next link (and, where the site has one, a coloring-book link) under the game's own end screen,
     a Pause button, auto-pause when the player switches apps, and a "turn your phone upright" note for portrait-only games
     played in landscape. Games opt in to pausing by defining window.SA_PAUSE = {playing(), pause(), resume()}. */
(() => {
  const A = window.ARC || {}, ls = window.localStorage, today = new Date().toISOString().slice(0, 10);
  const get = (k, d) => { try { const v = ls.getItem(k); return v == null ? d : JSON.parse(v) } catch (e) { return d } };
  const set = (k, v) => { try { ls.setItem(k, JSON.stringify(v)) } catch (e) { } };
  const reel = window.name === 'bda-reel';
  let mute = false; try { mute = ls.getItem('arc-nocount') === '1' } catch (e) { }

  /* ---------- where this browser's first visit came from ---------- */
  // ?s=yt (or utm_source) on our own links wins; otherwise the referrer. Kept on the device as "arc-src".
  const TAGS = { yt: 'youtube', fb: 'facebook', ig: 'instagram', tt: 'tiktok', pin: 'pinterest', em: 'email', x: 'x' };
  function sourceNow() {
    let p = null; try { p = new URLSearchParams(location.search) } catch (e) { }
    let t = p && (p.get('s') || p.get('utm_source'));
    if (t) { t = String(t).toLowerCase().slice(0, 24); return TAGS[t] || t.replace(/[^a-z0-9_-]/g, '') || 'other' }
    let h = ''; try { h = document.referrer ? new URL(document.referrer).hostname.replace(/^www\./, '') : '' } catch (e) { }
    if (!h || h === location.hostname) return 'direct';
    const is = re => re.test(h);
    if (is(/(^|\.)(youtube\.com|youtu\.be)$/)) return 'youtube';
    if (is(/(^|\.)(pinterest\.[a-z.]+|pin\.it)$/)) return 'pinterest';
    if (is(/(^|\.)(facebook\.com|fb\.com|fb\.me)$/)) return 'facebook';
    if (is(/(^|\.)instagram\.com$/)) return 'instagram';
    if (is(/(^|\.)tiktok\.com$/)) return 'tiktok';
    if (is(/(^|\.)(t\.co|x\.com|twitter\.com)$/)) return 'x';
    if (is(/(^|\.)reddit\.com$/)) return 'reddit';
    if (is(/(^|\.)google\./)) return 'google';
    if (is(/(^|\.)bing\.com$/)) return 'bing';
    if (is(/duckduckgo|yahoo|ecosia|brave|search/)) return 'search';
    if (is(/(^|\.)(beachdayarcade|sketchpadarcade|gullrunevo|restless)\./)) return 'sister';
    if (is(/amazon\./)) return 'amazon';
    return 'other';
  }
  let src = get('arc-src'); if (!src) { src = sourceNow(); set('arc-src', src) }

  /* ---------- anonymous event tallies ---------- */
  function ev(e, g, once) {
    if (reel || mute || !g) return;
    if (once) { const k = 'arc-ev-' + e + '-' + g; if (get(k) === today) return; set(k, today) }
    const u = '/api/event?e=' + encodeURIComponent(e) + '&g=' + encodeURIComponent(g);
    try { if (navigator.sendBeacon && navigator.sendBeacon(u)) return } catch (x) { }
    try { fetch(u, { method: 'POST', keepalive: true }).catch(() => { }) } catch (x) { }
  }
  window.ARC_EV = ev;
  // a visit (once a day per browser), by first source; and a returning visitor: this browser has been here on an earlier day
  (() => {
    const d = get('arc-day');
    if (d !== today) { ev('visit', src); if (d) { ev('return', '_site'); ev('return_src', src) } set('arc-day', today) }
  })();
  // outbound Amazon clicks, credited to this page and to the last game played this visit
  document.addEventListener('click', e => {
    const a = e.target.closest && e.target.closest('a[href]'); if (!a) return;
    if (/(^|\.)amazon\.[a-z.]+|amzn\.to/i.test(a.hostname || '')) {
      ev('amazon', A.slug || A.page || 'home');
      ev('amazon_src', src);
      let via = null; try { via = sessionStorage.getItem('arc-last') } catch (x) { }
      if (via) ev('amazon_via', via);
    } else if (a.hasAttribute('data-arc-rel')) ev('related', A.slug || 'home');
    else if (a.hasAttribute('data-arc-twin')) ev('twin', A.slug || 'home');
  }, true);

  if (A.page === 'game' && A.slug) ev('view', A.slug, true);
  if (A.page === 'book' && A.slug) ev('book_view', A.slug, true);
  if (A.page === 'home') keepPlaying();
  if (A.page !== 'play' || !A.slug) return;

  /* ---------- play pages ---------- */
  const slug = A.slug;
  // a play by source, once per game per day (matching the play counter in build.py)
  if (get('arc-ps-' + slug) !== today) { set('arc-ps-' + slug, today); ev('play_src', src) }
  try { sessionStorage.setItem('arc-last', slug) } catch (x) { }
  // recently played (newest first) and repeat players: someone who played this game on an earlier day
  const seen = get('arc-seen-' + slug);
  if (seen && seen !== today) ev('repeat', slug, true);
  if (seen !== today) set('arc-seen-' + slug, today);
  set('arc-recent', [slug, ...get('arc-recent', []).filter(s => s !== slug)].slice(0, 12));

  // started: the first real tap, click or key press. complete: the game's own end screen appears. restart: its Play Again button.
  let started = false, ended = false;
  const startEv = e => { if (started || (e.target.closest && e.target.closest('.sa-head,.arc-veil'))) return; started = true; ev('start', slug) };
  ['pointerdown', 'keydown'].forEach(t => addEventListener(t, startEv, { capture: true, passive: true }));
  const AGAIN = /(^|\s)again\b|^(retry|replay|try again|start over|new game|restart|play on|keep going)\b/i;
  addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('button,a'); if (!b || b.closest('.sa-head,.arc-next,.arc-veil')) return;
    const t = (b.textContent || '').replace(/\s+/g, ' ').trim();
    if (t && t.length < 26 && AGAIN.test(t)) { ev('restart', slug); ended = false }
  }, true);

  /* Up Next (and the coloring books) under the end screen, next to the Home button build.py's script adds there */
  const nxt = (A.next || [])[0], esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function extras() {
    document.querySelectorAll('.arc-next').forEach(x => { const p = x.previousElementSibling; if (!p || !p.classList.contains('sa-endhome')) x.remove() });
    const shown = el => { const r = el.getBoundingClientRect(); return r.width > 1 && r.height > 1 && getComputedStyle(el).visibility !== 'hidden' };
    const homes = [...document.querySelectorAll('.sa-endhome')].filter(shown);
    if (homes.length && !ended) { ended = true; ev('complete', slug) }
    if (!homes.length) ended = false;
    homes.forEach(h => {
      if (h.nextElementSibling && h.nextElementSibling.classList.contains('arc-next')) return;
      if (!nxt && !A.book) return;
      const d = document.createElement('div'); d.className = 'arc-next';
      d.innerHTML = (nxt ? `<a class="arc-up" href="/${esc(nxt.slug)}" data-arc-rel><img src="/img/t/${esc(nxt.slug)}.webp" alt="" width="40" height="40" loading="lazy"><span><small>Up next</small>${esc(nxt.name)}</span></a>` : '') +
        (A.book ? `<a class="arc-bk" href="/${esc(A.book.slug)}">Love the games? Color them too: ${esc(A.book.title)}</a>` : '');
      h.insertAdjacentElement('afterend', d);
    });
  }
  let mt; new MutationObserver(() => { clearTimeout(mt); mt = setTimeout(extras, 200) }).observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: ['hidden', 'class', 'style', 'open'] });

  /* Pause: a button in the header, automatic when the page is hidden, and while a portrait-only game is held sideways */
  const P = () => window.SA_PAUSE;
  let veil = null, why = '';
  function holdOn(reason) {
    const p = P(); if (!p || !p.playing() || veil) return;
    p.pause(); why = reason;
    veil = document.createElement('div'); veil.className = 'arc-veil'; veil.setAttribute('role', 'dialog'); veil.setAttribute('aria-modal', 'true'); veil.setAttribute('aria-label', 'Paused');
    veil.innerHTML = '<div class="arc-card"><h2>Paused</h2><p class="arc-rot">Turn your phone upright to keep playing.</p><button type="button" class="arc-go">Keep playing</button><a class="arc-more" href="/">More games</a></div>';
    veil.querySelector('.arc-go').onclick = holdOff;
    document.body.appendChild(veil); syncRot();
    try { veil.querySelector('.arc-go').focus({ preventScroll: true }) } catch (e) { }
  }
  function holdOff() { if (!veil || rotBad()) return; veil.remove(); veil = null; const p = P(); if (p) p.resume() }
  window.ARC_PAUSE = { on: holdOn, off: holdOff };
  // while paused, the game underneath doesn't see key presses (Escape or Enter resumes)
  addEventListener('keydown', e => { if (!veil || e.key === 'Tab') return; if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') holdOff(); e.stopPropagation(); e.preventDefault() }, true);
  document.addEventListener('visibilitychange', () => { if (document.hidden) holdOn('hidden') });
  addEventListener('pagehide', () => holdOn('hidden'));
  // portrait-only games: a phone held sideways can't fit the board, so pause and ask to turn it
  const land = window.matchMedia('(orientation: landscape) and (max-height: 520px) and (pointer: coarse)');
  const rotBad = () => !!A.portrait && land.matches;
  function syncRot() { document.documentElement.classList.toggle('arc-sideways', rotBad()); if (rotBad()) holdOn('rotate') }
  if (A.portrait) { try { land.addEventListener('change', syncRot) } catch (e) { land.addListener(syncRot) } syncRot() }
  // the header Pause button, once the game says it can pause
  function addBtn() {
    const head = document.querySelector('.sa-head'), sh = head && head.querySelector('.sa-share');
    if (!P() || !head || head.querySelector('.arc-pause')) return;
    const b = document.createElement('button'); b.type = 'button'; b.className = 'arc-pause'; b.setAttribute('aria-label', 'Pause');
    b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1.2"/><rect x="14" y="5" width="4" height="14" rx="1.2"/></svg>';
    b.onclick = () => { const p = P(); if (p && p.playing()) holdOn('button') };
    (sh || head.lastElementChild).insertAdjacentElement('beforebegin', b);
    const sync = () => { const p = P(); b.hidden = !(p && p.playing()); if (A.portrait) syncRot() }; sync(); setInterval(sync, 500);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addBtn); else addBtn();

  /* ---------- home page: Keep Playing, from this device's recently played list ---------- */
  function keepPlaying() {
    const go = () => {
      const row = document.getElementById('row-keep'); if (!row) return;
      const strip = row.querySelector('.strip');
      get('arc-recent', []).slice(0, 8).forEach(s => {
        const c = document.querySelector(`.card[data-slug="${CSS.escape(s)}"]:not([data-keep])`); if (!c) return;
        const k = c.cloneNode(true); k.removeAttribute('hidden'); k.dataset.keep = '1'; strip.appendChild(k);
      });
      if (strip.children.length) row.hidden = false;
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
  }
})();
