// GET /api/stats — play counts for the /stats page.
// A "play" is one player opening a game on a given day (see count_js in build.py).
// { today, days: [{date, total, games: {slug: plays}, visits}] (oldest first, last 30 days), allTime: {slug: plays},
//   events: {<event>: {all, recent, d7, d1: {key: n}}} } — engagement tallies from api/event.js; recent = last 30 days,
//   d7 = last 7 days, d1 = today. Source events (visit, play_src, …) are keyed by first-visit source instead of game.
import { ready, pipeline, ALL_KEY, dayKey, RECENT_DAYS, EVENTS, evAll, evDay, SOURCES } from "./_redis.js";
import { SLUGS, PAGES } from "./_slugs.js";

const KNOWN = new Set([...SLUGS, ...PAGES, ...SOURCES]);
const toMap = (flat) => {
  const out = {};
  for (let i = 0; i < (flat || []).length; i += 2) {
    if (KNOWN.has(flat[i])) out[flat[i]] = Math.round(Number(flat[i + 1]));
  }
  return out;
};
const total = (flat) => {
  let n = 0;
  for (let i = 1; i < (flat || []).length; i += 2) n += Number(flat[i]);
  return Math.round(n);
};

export default async function handler(req, res) {
  if (!ready) return res.status(503).json({ error: "play counter not connected" });
  const now = Date.now();
  const dates = Array.from({ length: RECENT_DAYS }, (_, i) => new Date(now - (RECENT_DAYS - 1 - i) * 86400000));
  const union = (e, n) => {
    const keys = dates.slice(-n).map((d) => evDay(e, d));
    return ["ZUNION", String(keys.length), ...keys, "WITHSCORES"];
  };
  try {
    const results = await pipeline([
      ["ZREVRANGE", ALL_KEY, "0", "-1", "WITHSCORES"],
      ...dates.map((d) => ["ZREVRANGE", dayKey(d), "0", "-1", "WITHSCORES"]),
      ...dates.map((d) => ["ZRANGE", evDay("visit", d), "0", "-1", "WITHSCORES"]),
      ...EVENTS.flatMap((e) => [
        ["ZREVRANGE", evAll(e), "0", "-1", "WITHSCORES"],
        union(e, dates.length),
        union(e, 7),
        union(e, 1),
      ]),
    ]);
    const v0 = 1 + dates.length, ev0 = v0 + dates.length, events = {};
    EVENTS.forEach((e, i) => {
      const b = ev0 + 4 * i;
      events[e] = { all: toMap(results[b]), recent: toMap(results[b + 1]), d7: toMap(results[b + 2]), d1: toMap(results[b + 3]) };
    });
    const allTime = toMap(results[0]);
    const days = dates.map((d, i) => {
      const games = toMap(results[i + 1]);
      return { date: d.toISOString().slice(0, 10), total: Object.values(games).reduce((a, b) => a + b, 0), games, visits: total(results[v0 + i]) };
    });
    res.setHeader("Cache-Control", "no-store");
    return res.status(200).json({ today: days[days.length - 1].date, days, allTime, events });
  } catch (e) {
    return res.status(502).json({ error: "counter unavailable" });
  }
}
