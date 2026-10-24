# Sketchpad Arcade

Free, family-friendly browser games drawn like a page from a kid's sketchbook, at https://www.sketchpadarcade.com, by Restless Faith Media LLC.

Every game started as a pencil-styled twin of a [Beach Day Arcade](https://github.com/gitMark80/beach-day-arcade) game. In October 2026 they were renamed for Sketchpad Arcade (old slugs redirect to the new ones in `vercel.json`):

| Beach Day Arcade | Sketchpad Arcade |
|---|---|
| Seaside Sprint (`seaside-sprint`) | Sketch Sprint (`sketch-sprint`) |
| Plank Plunk (`plank-plunk`) | Pencil Plunk (`pencil-plunk`) |
| Letter Lagoon (`letter-lagoon`) | Letter Links (`letter-links`) |
| Lighthouse Drop (`lighthouse-drop`) | Doodle Drop (`doodle-drop`) |
| Tide Clash (`tide-clash`) | Draw Brawl (`draw-brawl`) |
| Shore Search (`shore-search`) | Sketch Search (`sketch-search`) |
| Shell Stacks (`shell-stacks`) | Doodle Stacks (`doodle-stacks`) |
| Tiki Putt (`tiki-putt`) | Pencil Putt (`pencil-putt`) |
| Splash Slice (`splash-slice`) | Scribble Slice (`scribble-slice`) |
| Sea Merge (`sea-merge`) | Margin Merge (`margin-merge`) |
| Boardwalk Darts (`boardwalk-darts`) | Doodle Darts (`doodle-darts`) |
| Word Waves (`word-waves`) | Word Workshop (`word-workshop`) |
| Tide Pop (`tide-pop`) | Bubble Doodle (`bubble-doodle`) |
| Crab Hop (`crab-hop`) | Sidewalk Hop (`sidewalk-hop`) |
| Tide Gates (`tide-gates`) | Paper Gates (`paper-gates`) |
| Four by Sea (`four-by-sea`) | Four in a Frame (`four-in-a-frame`) |
| Whirlpool Gulp (`whirlpool-gulp`) | Eraser Gulp (`eraser-gulp`) |
| Bottle Words (`bottle-words`) | Note Quest (`note-quest`) |
| Octo Swing (`octo-swing`) | Shoe String Swing (`shoe-string-swing`; was Scribble Swing) |
| Treasure Trio (`treasure-trio`) | Margin Match (`margin-match`) |
| Beach Link (`beach-link`) | No. 2 Pencil (`no-2-pencil`) |
| Pearl Blocks (`pearl-blocks`) | Scribble Blocks (`scribble-blocks`) |
| Shell Swap (`shell-swap`) | Drop Swap (`drop-swap`) |
| Turtle Dash (`turtle-dash`) | Pencil Path (`pencil-path`) |
| Sonar Sub (`sonar-sub`) | Space Blaster (`space-blaster`) |
| Sea Glass (`sea-glass`) | Space Glass (`space-glass`) |
| Gem Cove (`gem-cove`) | Chibi Chib (`chibi-chib`) |
| Word Plop (`word-plop`) | Word Scribble (`word-scribble`) |
| Pearl Patrol (`pearl-patrol`) | Pencil Patrol (`pencil-patrol`) |
| Tide Jars (`tide-jars`) | Ink Jars (`ink-jars`) |
| Shell Scramble (`shell-scramble`) | Letter Scramble (`letter-scramble`) |
| Castle Keeper (`castle-keeper`) | Doodle Keeper (`doodle-keeper`) |
| Even-Tide (`even-tide`) | Even Sketch (`even-sketch`) |
| Sand Peaks (`sand-peaks`) | Paper Peaks (`paper-peaks`) |
| Beach Ball Blitz (`beach-ball-blitz`) | Marble Blitz (`marble-blitz`) |
| Sandy Strikes (`sandy-strikes`) | Desk Strikes (`desk-strikes`) |
| Taffy Drop (`taffy-drop`) | Cookie Drop (`cookie-drop`) |
| Wiggle Reef (`wiggle-reef`) | Squiggle Worm (`squiggle-worm`) |
| Piper Parade (`piper-parade`) | Pencil Parade (`pencil-parade`) |
| Tide Jars (`tide-jars`) | Ink Jars (`ink-jars`) |
| Shell Scramble (`shell-scramble`) | Letter Scramble (`letter-scramble`) |
| Castle Keeper (`castle-keeper`) | Doodle Keeper (`doodle-keeper`) |
| Even-Tide (`even-tide`) | Even Sketch (`even-sketch`) |
| Sand Peaks (`sand-peaks`) | Paper Peaks (`paper-peaks`) |
| Beach Ball Blitz (`beach-ball-blitz`) | Marble Blitz (`marble-blitz`) |
| Sandy Strikes (`sandy-strikes`) | Desk Strikes (`desk-strikes`) |
| Taffy Drop (`taffy-drop`) | Cookie Drop (`cookie-drop`) |
| Wiggle Reef (`wiggle-reef`) | Squiggle Worm (`squiggle-worm`) |
| Piper Parade (`piper-parade`) | Pencil Parade (`pencil-parade`) |

`sketchify.py` takes the Beach Day Arcade slug and writes to the Sketchpad slug.

- `site/` is the finished website that Vercel serves (set by `vercel.json`).
- `src/games/<slug>.html` holds each game, `src/img/<slug>.jpg` its square pencil cover, and `src/assets/<slug>/` its pencil art (served at `/assets/<slug>/`).
- `games.json` lists the site settings, every game's text and the coloring books (`site.books`: each has a `slug`, a `dir` under `src/` holding `cover.jpg`, `thumb.jpg`, `share.jpg` and `pages/<game>.webp` samples, and its Amazon link), and `posts.json` holds the news posts (built to `/news`).(copied from the matching Beach Day Arcade entry).
- `build.py` rebuilds `site/` from those: `python3 build.py`.
- `src/reel.html` is Reel Studio (`/reel`, unlisted): it frames a live game on a sketchbook page for one-take phone screen recordings. Hooks live in `src/reel-hooks.json` and the post title/caption/comment text in `src/reel-copy.json`.
- `api/` counts plays and ranks favorites through an Upstash Redis database connected in Vercel; without it the site still works.

## Adding a game

Clone Beach Day Arcade next to this repo (`../beach-day-arcade`) or set `BDA_REPO` to its path, then follow `STYLE.md`:

1. `cp ../beach-day-arcade/src/games/<slug>.html src/games/`
2. `python3 sketchify.py <slug>` (pencil cover and art; add `--inline` if the game embeds base64 images)
3. Restyle the page and canvas colours per `STYLE.md`
4. Add the game's entry to `games.json`, run `python3 build.py`, and push.

## Two-player games (Versus)

Tic-Tac-Doodle, Doodle SOS, Box Doodles and Paper Boats are original builds, not Beach Day twins. Each has Play vs Friend (pass & play on one device) and Play vs Bot (Easy, Medium, Hard), and remembers the player's record against the bot on that device. They share one shell: edit `tools/versus/shell.css`, `tools/versus/shell.js` or a game's `tools/versus/<slug>.html/.css/.js`, then run `python3 tools/versus.py` (it rewrites `src/games/<slug>.html`) and `python3 build.py`. Don't hand-edit the generated game files.

## One-player puzzles

Blot Sweeper, Save the Doodle, Doodle Doku and Crayon Code share a puzzle shell (Easy, Medium and Hard picker, timer, best results saved on the device). Edit `tools/solo/base.css`, `tools/solo/base.js` or a game's `tools/solo/<slug>.html/.css/.js`, then run `python3 tools/solo.py` and `python3 build.py`. Don't hand-edit the generated game files.

## Invite a friend (online, take turns whenever)

Tic-Tac-Doodle, Doodle SOS, Box Doodles, Connect Sketch, Sketchers, Guess My Doodle and Sketch with Friends have **Invite a friend**: it makes a game with a 6-letter code and shares a link (`/<slug>?game=CODE`, which forwards to the play page and shows the cover in link previews). The friend who opens it plays pink; moves sync through Supabase (project `sketchpad-arcade`), each phone checking for the other player's move every few seconds while it's waiting. Games on this device show in **Your Games with Friends** on the home page.

- Turn it on per game with `"online": true` in `games.json`; the Supabase URL and publishable key are in `site.online`. Remove `site.online` to switch the feature off everywhere.
- The database is in `supabase/migrations/`: one locked table, `vs_games`, reached only through the `vs_*` functions, which check each phone's secret id (only its hash is stored) and whose turn it is.
- A game supports it by defining `GAME.save()` and `GAME.load(state)`; the code is in `tools/versus/online.js`. Paper Boats is left out until its boats can be hidden on the server.

Sketch with Friends checks words against `src/assets/sketch-with-friends/words.txt`, built by `tools/sketch-with-friends-words.py` from the Hunspell en_US dictionary with a family blocklist (add words to `BLOCK` there and rerun).

## Retention, pause and engagement counts (`src/arcade.js`)

`src/arcade.js` is shared by Sketchpad Arcade and Beach Day Arcade (keep the two copies identical). `build.py` serves it as `/arcade.js` on every page with a small `window.ARC` config.

- **Keep Playing**: the last games played on this device (localStorage `arc-recent`) show as the first row on the home page.
- **Up Next**: under a game's end screen, next to the Home button, a link to its first related game and a line linking to the coloring book that has that game's page.
- **Related games**: each game page lists 8 related games (its `related` list in `games.json`, then the same genre, then the site's picks) and a "See all games" button, instead of every game on the site.
- **Pause**: games that define `window.SA_PAUSE = {playing(), pause(), resume()}` get a Pause button in the header and pause automatically when the player switches apps, with a Keep Playing card to resume. 2048 Drop, Cookie Drop and Sidewalk Hop have it so far.
- **Portrait-only games**: `"portrait": true` in `games.json` pauses the game with a "turn your phone upright" note when a phone is held sideways.
- **Sister-site links**: `"twin"` in `games.json` is the same game's slug on Beach Day Arcade; the game page links to it.
- **Engagement counts**: anonymous tallies per game and day (`POST /api/event`, stored next to the play counts): page views, starts, finishes, replays, repeat players, related-game clicks, sister-site clicks, book page views and Amazon clicks. No IDs, cookies or IP addresses. They show in the Engagement table on `/stats`.
- **Where players come from**: each browser remembers the source of its first visit (`arc-src`: youtube, pinterest, google, direct…, from `?s=yt|pin|fb|ig|tt`, `utm_source` or the referrer). `/stats` shows visits, returning visits, plays, plays per visit and Amazon clicks per source (events `visit`, `return_src`, `play_src`, `amazon_src`, keyed by source). Engagement tables follow the Today / 7 days / 30 days / All time tabs.
- **Don't count me**: the switch at the bottom of `/stats` sets `arc-nocount` on that device; `arcade.js` and the play counter then skip it.
- **Card thumbnails**: `build.py` makes 400px WebP copies of the covers in `src/img/t/` (needs Pillow; they are committed so builds without it still work).
- **Share kit**: `/share-kit` (unlisted) has every game's Facebook, Pinterest and YouTube text ready to copy, and `/social.json` has the same data. Nothing is posted automatically.
- Internal links use clean URLs (`/cookie-drop`, not `cookie-drop.html`), so Vercel serves them without a redirect.
