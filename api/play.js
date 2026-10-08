// POST /api/play?game=<slug>  — adds one play to that game's all-time and daily tallies.
// The browser only calls this once per game per day, so refreshing doesn't inflate counts.
import { ready, pipeline, ALL_KEY, dayKey, RECENT_DAYS } from "./_redis.js";
import { SLUGS } from "./_slugs.js";

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  const slug = String(req.query.game || "");
  if (!SLUGS.includes(slug)) return res.status(400).json({ error: "unknown game" });
  if (!ready) return res.status(503).json({ error: "play counter not connected" });
  const day = dayKey(new Date());
  try {
    await pipeline([
      ["ZINCRBY", ALL_KEY, "1", slug],
      ["ZINCRBY", day, "1", slug],
      ["EXPIRE", day, String((RECENT_DAYS + 5) * 86400)],
    ]);
    res.setHeader("Cache-Control", "no-store");
    return res.status(204).end();
  } catch (e) {
    return res.status(502).json({ error: "counter unavailable" });
  }
}
