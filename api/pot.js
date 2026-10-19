/**
 * ⚡ ZYROX POT PROVIDER — Vercel Node function
 * ============================================
 * Serves the bgutils BotGuard PO-token generator (bgutil-ytdlp-pot-provider,
 * bundled via esbuild) so the Python bot function can fetch PO tokens over HTTP.
 *
 * Routes (rewrites in vercel.json point sub-paths here):
 *   GET  /api/pot[/ping]              → health/ping
 *   POST /api/pot[/get_pot]           → generate PO token
 *   POST /api/pot/invalidate_caches   → clear caches
 *   POST /api/pot/invalidate_it       → invalidate innertube session
 */

let SessionManager;
try {
  ({ SessionManager } = require("./pot_lib.cjs"));
} catch (e) {
  console.error("pot_lib load failed:", e);
}

let _sm = null;
function getSm() {
  if (!_sm) _sm = new SessionManager();
  return _sm;
}

module.exports = async (req, res) => {
  const url = req.url || "";

  if (req.method === "GET") {
    return res.status(200).json({
      ping: true,
      provider: "bgutil-vercel",
      version: "2.0.2", // must match the bgutil-ytdlp-pot-provider pip plugin version
      server_uptime: process.uptime(),
    });
  }

  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  if (!SessionManager) {
    return res.status(500).json({ error: "pot_lib not loaded" });
  }

  if (url.includes("/invalidate_caches")) {
    try { getSm().invalidateCaches(); } catch (e) { /* noop */ }
    return res.status(204).end();
  }
  if (url.includes("/invalidate_it")) {
    try { getSm().invalidateIT(); } catch (e) { /* noop */ }
    return res.status(204).end();
  }

  // default → /get_pot
  let body = req.body || {};
  if (typeof body === "string") {
    try { body = JSON.parse(body); } catch { body = {}; }
  }

  try {
    const data = await getSm().generatePoToken(
      body.content_binding,
      body.proxy,
      !!body.bypass_cache,
      body.source_address,
      !!body.disable_tls_verification,
      body.challenge,
      body.innertube_context
    );
    return res.status(200).json(data);
  } catch (e) {
    console.error("get_pot failed:", e);
    return res.status(500).json({ error: String((e && e.message) || e) });
  }
};
