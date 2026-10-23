// POST /api/event?e=<event>&g=<slug>  — adds one to an anonymous tally for that event and game (all-time and per day).
// Nothing about the visitor is stored: no IP address, no ID, no cookie. Only known events and known slugs are accepted.
// Events (sent by src/arcade.js): view (game page, once a day per browser), start, complete, restart, repeat (played this
// game on an earlier day), related (clicked a related game), twin (clicked through to the sister site's version),
// book_view, amazon (Amazon link clicked on this page), amazon_via (Amazon clicked after playing this game), return (_site).
import { ready, pipeline, RECENT_DAYS, EVENTS, evAll, evDay } from "./_redis.js";
import { SLUGS, PAGES } from "./_slugs.js";

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  const e = String(req.query.e || ""), g = String(req.query.g || "");
  if (!EVENTS.includes(e)) return res.status(400).json({ error: "unknown event" });
  if (!SLUGS.includes(g) && !PAGES.includes(g)) return res.status(400).json({ error: "unknown page" });
  if (!ready) return res.status(503).json({ error: "counter not connected" });
  const day = evDay(e, new Date());
  try {
    await pipeline([
      ["ZINCRBY", evAll(e), "1", g],
      ["ZINCRBY", day, "1", g],
      ["EXPIRE", day, String((RECENT_DAYS + 5) * 86400)],
    ]);
    res.setHeader("Cache-Control", "no-store");
    return res.status(204).end();
  } catch (err) {
    return res.status(502).json({ error: "counter unavailable" });
  }
}
