// Player profiles: a name plus a short code that carries saved game progress between devices.
//   POST /api/profile            body {name}            → {code, name}     creates a profile
//   GET  /api/profile?code=X                            → {name, games:{slug:data}, updated:{slug:ms}}
//   PUT  /api/profile?code=X     body {game, data}      → 204              saves one game's progress
// Progress is whatever the game chooses to store (level, coins, a half-finished board). Nothing else is kept.
import { ready, pipeline } from "./_redis.js";
import { SLUGS } from "./_slugs.js";

const ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // no 0/O or 1/I so codes are easy to read out
const CODE_RE = /^[A-Z2-9]{6}$/;
const KEEP = 400 * 86400; // a profile lives 400 days past its last save
const MAX_DATA = 64 * 1024;

function makeCode() {
  let s = "";
  for (let i = 0; i < 6; i++) s += ALPHABET[Math.floor(Math.random() * ALPHABET.length)];
  return s;
}
function cleanName(v) {
  return String(v || "").replace(/\s+/g, " ").trim().slice(0, 24);
}
function parseBody(req) {
  if (req.body && typeof req.body === "object") return req.body;
  try { return JSON.parse(req.body || "{}"); } catch (e) { return {}; }
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  if (!ready) return res.status(503).json({ error: "profiles not connected" });
  try {
    if (req.method === "POST") {
      const name = cleanName(parseBody(req).name);
      if (!name) return res.status(400).json({ error: "name needed" });
      for (let tries = 0; tries < 5; tries++) {
        const code = makeCode();
        const [made] = await pipeline([["HSETNX", `profile:${code}`, "name", name]]);
        if (made) {
          await pipeline([["HSET", `profile:${code}`, "created", String(Date.now())], ["EXPIRE", `profile:${code}`, String(KEEP)]]);
          return res.status(200).json({ code, name });
        }
      }
      return res.status(500).json({ error: "try again" });
    }

    const code = String(req.query.code || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (!CODE_RE.test(code)) return res.status(400).json({ error: "bad code" });
    const key = `profile:${code}`;

    if (req.method === "GET") {
      const [flat] = await pipeline([["HGETALL", key]]);
      if (!flat || !flat.length) return res.status(404).json({ error: "no such profile" });
      const h = {};
      for (let i = 0; i < flat.length; i += 2) h[flat[i]] = flat[i + 1];
      const games = {}, updated = {};
      for (const k in h) {
        if (k.startsWith("g:")) { try { games[k.slice(2)] = JSON.parse(h[k]); } catch (e) {} }
        else if (k.startsWith("t:")) updated[k.slice(2)] = Number(h[k]) || 0;
      }
      return res.status(200).json({ code, name: h.name || "", games, updated });
    }

    if (req.method === "PUT") {
      const { game, data } = parseBody(req);
      if (!SLUGS.includes(game)) return res.status(400).json({ error: "unknown game" });
      const json = JSON.stringify(data == null ? {} : data);
      if (json.length > MAX_DATA) return res.status(413).json({ error: "too much data" });
      const [exists] = await pipeline([["EXISTS", key]]);
      if (!exists) return res.status(404).json({ error: "no such profile" });
      await pipeline([
        ["HSET", key, `g:${game}`, json, `t:${game}`, String(Date.now())],
        ["EXPIRE", key, String(KEEP)],
      ]);
      return res.status(204).end();
    }

    return res.status(405).json({ error: "GET, POST or PUT" });
  } catch (e) {
    return res.status(502).json({ error: "profiles unavailable" });
  }
}
