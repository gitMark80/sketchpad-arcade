// Tiny Upstash Redis REST client (no npm packages needed).
// Vercel's Upstash Redis integration sets one of these pairs of environment variables.
const URL = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const TOKEN = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;

export const ready = Boolean(URL && TOKEN);

// Runs several Redis commands in one request; returns their results in order.
export async function pipeline(cmds) {
  const r = await fetch(`${URL}/pipeline`, {
    method: "POST",
    headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify(cmds),
  });
  if (!r.ok) throw new Error(`Redis HTTP ${r.status}`);
  const out = await r.json();
  return out.map((x) => {
    if (x.error) throw new Error(x.error);
    return x.result;
  });
}

// Sketchpad shares Beach Day Arcade's Upstash database (one free database per account),
// so every key it writes starts with "sketch:" to keep the two sites' data apart.
export const PREFIX = "sketch:";
export const ALL_KEY = `${PREFIX}plays:all`;
export const dayKey = (d) => `${PREFIX}plays:day:${d.toISOString().slice(0, 10)}`;
export const RECENT_DAYS = 30;

// Engagement events (api/event.js), anonymous tallies per game or page: <prefix>ev:<event>:all and <prefix>ev:<event>:day:<date>
export const EVENTS = ["view", "start", "complete", "restart", "repeat", "related", "twin", "book_view", "amazon", "amazon_via", "return"];
export const evAll = (e) => `${PREFIX}ev:${e}:all`;
export const evDay = (e, d) => `${PREFIX}ev:${e}:day:${d.toISOString().slice(0, 10)}`;
