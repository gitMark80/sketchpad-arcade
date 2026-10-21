#!/usr/bin/env python3
"""Builds the two-player games (Play vs Friend / Play vs Bot) into src/games/<slug>.html.

Each game is tools/versus/<slug>.html (board markup), <slug>.css and <slug>.js, wrapped in the shared
shell (tools/versus/shell.css + shell.js: mode and difficulty pickers, scores, turns, sound, bot record).
Edit those files, then run:  python3 tools/versus.py   (then python3 build.py)
"""
import json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V = ROOT / "tools" / "versus"

GAMES = {
    "tic-tac-doodle": {"name": "Tic-Tac-Doodle", "intro": "Three in a row wins. Blue X goes against pink O.",
        "rules": ["Take turns drawing your mark in an empty square.", "Get three in a row (across, down or corner to corner) to win the round.",
                  "Fill the board with no line of three and it's a draw.", "Who goes first swaps every round."]},
    "doodle-sos": {"name": "Doodle SOS", "intro": "Spell S-O-S in a line to score, and you get another go.",
        "rules": ["On your turn, pick S or O, then tap an empty square to write it.", "If your letter finishes S-O-S across, down or corner to corner, you score a point for each one and go again.",
                  "When the grid is full, the player with the most SOS lines wins.", "Watch out: an S next to an empty square and an O can hand your opponent a point."]},
    "box-doodles": {"name": "Box Doodles", "intro": "Join the dots. Close a box to claim it and go again.",
        "rules": ["Take turns drawing one line between two dots next to each other.", "Draw the fourth side of a box and it's yours: you score a point and draw again.",
                  "When every box is claimed, the player with the most boxes wins.", "Try not to draw the third side of a box. That hands it to the other player!"]},
    "paper-boats": {"name": "Paper Boats", "intro": "Find all of the other player's hidden paper boats first.",
        "rules": ["Each player hides four paper boats on their own 8×8 page. Tap Shuffle to move yours, then tap Ready.",
                  "Take turns tapping a square on the other player's page. A miss is a splash; a hit puts a pencil X on a boat.",
                  "Hit every square of a boat and it floats away. Find all four boats to win.",
                  "Playing a friend on one phone? Each turn the game asks you to pass it over, so nobody peeks."]},
    "connect-sketch": {"name": "Connect Sketch", "intro": "Drop your crayon counters down the page. Four in a row wins.",
        "rules": ["Take turns tapping a column to drop a counter. It falls to the lowest empty space.", "Get four of your colour in a row (across, down or corner to corner) to win the round.",
                  "Fill the whole page with no four in a row and it's a draw.", "Who goes first swaps every round."]},
    "sketchers": {"name": "Sketchers", "intro": "Checkers on a sketchbook page. Jump your friend's pieces to win.",
        "rules": ["Tap one of your pieces, then tap a highlighted square to move it diagonally forward.", "Jump over the other player's piece into an empty square to capture it. If you can jump, you must, and keep jumping if you can.",
                  "Reach the far side and your piece is crowned. Crowned pieces can move backward too.", "Win by capturing every piece or leaving the other player with no moves."]},
    "guess-my-doodle": {"name": "Guess My Doodle", "intro": "Draw a word for your friend, then guess theirs. Score points together.",
        "rules": ["On your turn, pick one of three words and draw it. No letters or numbers!", "Your friend watches your drawing appear line by line and taps letters to guess the word.",
                  "Guess it and you both score: harder words are worth more. Then the guesser becomes the drawer.", "Stuck? Tap Skip to see the word and keep the game going. Ten drawings make a game."]},
    "sketch-with-friends": {"name": "Sketch with Friends", "intro": "Make words on the board with your letter tiles. Highest score wins.",
        "rules": ["Drag tiles from your rack onto the board to make a word across or down. The first word must cover the star in the middle.",
                  "Every new word must join onto words already on the board. Tap Play to score it; tiles you place stay in one line.",
                  "Each letter has points. Coloured squares double or triple a letter (DL, TL) or the whole word (DW, TW). Use all 7 tiles in one turn for a 35-point bonus.",
                  "Swap tiles or pass if you're stuck. The game ends when the bag is empty and someone uses their last tile, or after four passes in a row."]},
}

def build(slug):
    g = GAMES[slug]
    name = g["name"]
    rules = "".join(f"<li>{html.escape(r)}</li>" for r in g["rules"])
    info = {"slug": slug, "name": name}
    css = (V / "shell.css").read_text() + "\n" + (V / f"{slug}.css").read_text()
    board = (V / f"{slug}.html").read_text()
    js = (V / f"{slug}.js").read_text()
    shell = (V / "shell.js").read_text()
    online = (V / "online.js").read_text()
    out = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<style>*,*::before,*::after{{box-sizing:border-box}}:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
<title>{html.escape(name)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gloria+Hallelujah&family=Patrick+Hand&display=swap">
<!-- Generated by tools/versus.py from tools/versus/{slug}.* and the shared shell. Edit those, not this file. -->
<style>
{css}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{html.escape(name)}</h1>
    <button class="icon" id="helpb" type="button" aria-label="How to play">?</button>
  </header>
  <div class="score">
    <div class="pl p0" id="p0"><span class="dot"></span><span class="nm" id="n0">Player 1</span><b id="s0">0</b></div>
    <span class="vs">vs</span>
    <div class="pl p1" id="p1"><span class="dot"></span><span class="nm" id="n1">Player 2</span><b id="s1">0</b></div>
  </div>
  <div class="turn" id="turn" aria-live="polite"></div>
  <div class="stage" id="stage">
{board}
    <div class="over" id="start">
      <h2>{html.escape(name)}</h2>
      <p>{html.escape(g["intro"])}</p>
      <p>Who do you want to play against?</p>
      <div class="modes">
        <button type="button" id="vsFriend"><span class="em">👥</span><b>vs Friend</b><small>Pass &amp; play on this device</small></button>
        <button type="button" id="vsBot"><span class="em">🤖</span><b>vs Bot</b><small>Easy, Medium or Hard</small></button>
        <button type="button" id="vsInvite"><span class="em">📲</span><b>Invite a friend</b><small>Send a link · take turns whenever</small></button>
      </div>
      <p class="rec" id="startRec"></p>
    </div>
    <div class="over" id="diff" hidden>
      <h2>Pick a level</h2>
      <p>How tricky should the bot be?</p>
      <div class="diffs">
        <button type="button" data-diff="easy"><span>😊</span>Easy<small>for little ones</small></button>
        <button type="button" data-diff="medium"><span>🧠</span>Medium<small>a fair fight</small></button>
        <button type="button" data-diff="hard"><span>🔥</span>Hard<small>good luck!</small></button>
      </div>
      <button class="link" type="button" id="diffBack">← Back</button>
    </div>
    <div class="over" id="over" hidden>
      <h2 id="overH"></h2>
      <p id="overMsg"></p>
      <p class="rec" id="overRec"></p>
      <div class="btns"><button class="primary" id="again" type="button">Play again</button></div>
      <button class="link" type="button" id="overMode">Change who you play</button>
    </div>
    <div class="over" id="pass" hidden>
      <h2 id="passH">Pass the phone</h2>
      <p>No peeking! Hand it over, then tap below.</p>
      <button class="primary" id="passGo" type="button">Go</button>
    </div>
    <div class="over" id="invite" hidden>
      <h2>Invite a friend</h2>
      <p>Send this link to a friend. They tap it to join as pink. You're blue and you go first.</p>
      <p class="invlink" id="invLink"></p>
      <div class="btns"><button class="primary" id="invShare" type="button">📲 Send link</button></div>
      <button class="link" type="button" id="invGo">Make my first move</button>
      <p class="rec">Take turns whenever you like. Open the game from the home page any time to see if it's your move.</p>
    </div>
    <div class="over help" id="help" hidden>
      <h2>How to play</h2>
      <ul class="rules">{rules}</ul>
      <button class="primary" id="helpClose" type="button">Got it</button>
    </div>
  </div>
  <div class="onbar" id="onbar" hidden><span id="onText"></span><button type="button" id="onShare">📲 Share link</button></div>
  <div class="tally" id="tally"></div>
  <div class="bar">
    <button id="newr" type="button">↻ New round</button>
    <button id="modeb" type="button">👥 Mode</button>
    <button id="snd" type="button">🔊 Sound: On</button>
  </div>
</div>
<script>
const INFO={json.dumps(info)};
{shell}
{js}
{online}
S.boot();
</script>
</body>
</html>
"""
    (ROOT / "src" / "games" / f"{slug}.html").write_text(out)
    print("wrote", slug)

if __name__ == "__main__":
    import sys
    for s in (sys.argv[1:] or list(GAMES)):
        build(s)
