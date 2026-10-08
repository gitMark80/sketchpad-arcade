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

export const ALL_KEY = "plays:all";
export const dayKey = (d) => `plays:day:${d.toISOString().slice(0, 10)}`;
export const RECENT_DAYS = 30;
