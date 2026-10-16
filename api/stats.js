// GET /api/stats — play counts for the /stats page.
// A "play" is one player opening a game on a given day (see count_js in build.py).
// { today, days: [{date, total, games: {slug: plays}}] (oldest first, last 30 days), allTime: {slug: plays} }
import { ready, pipeline, ALL_KEY, dayKey, RECENT_DAYS } from "./_redis.js";
import { SLUGS } from "./_slugs.js";

const toMap = (flat) => {
  const out = {};
  for (let i = 0; i < (flat || []).length; i += 2) {
    if (SLUGS.includes(flat[i])) out[flat[i]] = Math.round(Number(flat[i + 1]));
  }
  return out;
};

export default async function handler(req, res) {
  if (!ready) return res.status(503).json({ error: "play counter not connected" });
  const now = Date.now();
  const dates = Array.from({ length: RECENT_DAYS }, (_, i) => new Date(now - (RECENT_DAYS - 1 - i) * 86400000));
  try {
    const results = await pipeline([
      ["ZREVRANGE", ALL_KEY, "0", "-1", "WITHSCORES"],
      ...dates.map((d) => ["ZREVRANGE", dayKey(d), "0", "-1", "WITHSCORES"]),
    ]);
    const allTime = toMap(results[0]);
    const days = dates.map((d, i) => {
      const games = toMap(results[i + 1]);
      return { date: d.toISOString().slice(0, 10), total: Object.values(games).reduce((a, b) => a + b, 0), games };
    });
    res.setHeader("Cache-Control", "no-store");
    return res.status(200).json({ today: days[days.length - 1].date, days, allTime });
  } catch (e) {
    return res.status(502).json({ error: "counter unavailable" });
  }
}
