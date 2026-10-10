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

`sketchify.py` takes the Beach Day Arcade slug and writes to the Sketchpad slug.

- `site/` is the finished website that Vercel serves (set by `vercel.json`).
- `src/games/<slug>.html` holds each game, `src/img/<slug>.jpg` its square pencil cover, and `src/assets/<slug>/` its pencil art (served at `/assets/<slug>/`).
- `games.json` lists the site settings and every game's text (copied from the matching Beach Day Arcade entry).
- `build.py` rebuilds `site/` from those: `python3 build.py`.
- `src/reel.html` is Reel Studio (`/reel`, unlisted): it frames a live game on a sketchbook page for one-take phone screen recordings. Hooks live in `src/reel-hooks.json` and the post title/caption/comment text in `src/reel-copy.json`.
- `api/` counts plays and ranks favorites through an Upstash Redis database connected in Vercel; without it the site still works.

## Adding a game

Clone Beach Day Arcade next to this repo (`../beach-day-arcade`) or set `BDA_REPO` to its path, then follow `STYLE.md`:

1. `cp ../beach-day-arcade/src/games/<slug>.html src/games/`
2. `python3 sketchify.py <slug>` (pencil cover and art; add `--inline` if the game embeds base64 images)
3. Restyle the page and canvas colours per `STYLE.md`
4. Add the game's entry to `games.json`, run `python3 build.py`, and push.
