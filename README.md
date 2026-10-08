# Sketchpad Arcade

Free, family-friendly browser games drawn like a page from a kid's sketchbook, at https://www.sketchpadarcade.com, by Restless Faith Media LLC.

Every game is a pencil-styled twin of a [Beach Day Arcade](https://github.com/gitMark80/beach-day-arcade) game, under the same slug. Gameplay is identical; only the look changes.

- `site/` is the finished website that Vercel serves (set by `vercel.json`).
- `src/games/<slug>.html` holds each game, `src/img/<slug>.jpg` its square pencil cover, and `src/assets/<slug>/` its pencil art (served at `/assets/<slug>/`).
- `games.json` lists the site settings and every game's text (copied from the matching Beach Day Arcade entry).
- `build.py` rebuilds `site/` from those: `python3 build.py`.
- `api/` counts plays and ranks favorites through an Upstash Redis database connected in Vercel; without it the site still works.

## Adding a game

Clone Beach Day Arcade next to this repo (`../beach-day-arcade`) or set `BDA_REPO` to its path, then follow `STYLE.md`:

1. `cp ../beach-day-arcade/src/games/<slug>.html src/games/`
2. `python3 sketchify.py <slug>` (pencil cover and art; add `--inline` if the game embeds base64 images)
3. Restyle the page and canvas colours per `STYLE.md`
4. Add the game's entry to `games.json`, run `python3 build.py`, and push.
