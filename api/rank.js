// GET /api/rank — play counts for the home page rows.
// { allTime: [{slug, plays}], recent: [{slug, plays}] }, most played first.
// "recent" adds up the last 30 days. Cached at Vercel's edge for 5 minutes.
import { ready, pipeline, ALL_KEY, dayKey, RECENT_DAYS } from "./_redis.js";
import { SLUGS } from "./_slugs.js";

const pairs = (flat) => {
  const out = [];
  for (let i = 0; i < flat.length; i += 2) {
    if (SLUGS.includes(flat[i])) out.push({ slug: flat[i], plays: Math.round(Number(flat[i + 1])) });
  }
  return out.filter((x) => x.plays > 0).sort((a, b) => b.plays - a.plays);
};

export default async function handler(req, res) {
  if (!ready) return res.status(503).json({ error: "play counter not connected" });
  const now = Date.now();
  const days = Array.from({ length: RECENT_DAYS }, (_, i) => dayKey(new Date(now - i * 86400000)));
  try {
    const [all, recent] = await pipeline([
      ["ZREVRANGE", ALL_KEY, "0", "-1", "WITHSCORES"],
      ["ZUNION", String(days.length), ...days, "WITHSCORES"],
    ]);
    res.setHeader("Cache-Control", "public, s-maxage=300, stale-while-revalidate=3600");
    return res.status(200).json({ allTime: pairs(all), recent: pairs(recent) });
  } catch (e) {
    return res.status(502).json({ error: "counter unavailable" });
  }
}
