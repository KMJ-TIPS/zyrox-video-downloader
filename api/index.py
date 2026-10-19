"""
⚡ ZYROX VIDEO DOWNLOADER — Vercel serverless webhook entry
============================================================
Telegram sends updates to  https://<project>.vercel.app/api

The PTB Application is built once per warm instance and reused.
Each update is processed INLINE (downloads included) so the
serverless function stays alive until the job finishes.
"""

import asyncio
import logging
import os

from fastapi import FastAPI, Request, Response

import config
import database
from bot import build_application
from telegram import Update

logging.basicConfig(
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("yt_dlp").setLevel(logging.WARNING)
log = logging.getLogger("zyrox.webhook")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

_app = None
_app_lock = asyncio.Lock()
_seen_updates: set[int] = set()


async def get_application():
    """Lazily build + initialize the Application (once per warm instance)."""
    global _app
    async with _app_lock:
        if _app is None:
            database.init()
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            app = build_application(serverless=True)
            await app.initialize()
            await app.start()
            _app = app
            channels = ", ".join(config.DEFAULT_CHANNELS) or "—"
            log.info("ZYROX warm instance ready | force-join: %s", channels)
    return _app


app = FastAPI(title="ZYROX VIDEO DOWNLOADER")


@app.get("/")
@app.get("/api")
@app.get("/api/")
async def health(request: Request):
    """GET /  →  served at https://<project>.vercel.app/api"""
    if request.query_params.get("diag") == "extract":
        # owner-only extraction test: /api?diag=extract&url=...&key=WEBHOOK_SECRET
        import asyncio
        import downloader
        key_ok = (
            not WEBHOOK_SECRET
            or request.query_params.get("key") == WEBHOOK_SECRET
        )
        url = request.query_params.get("url", "")
        if not key_ok:
            return {"error": "unauthorized"}
        if not url:
            return {"error": "missing url param"}
        try:
            clients = request.query_params.get("clients")
            saved = config.YOUTUBE_CLIENTS
            if clients:
                config.YOUTUBE_CLIENTS = [c.strip() for c in clients.split(",") if c.strip()]
            try:
                info = await asyncio.wait_for(
                    asyncio.to_thread(downloader.extract_info, url), timeout=280
                )
            finally:
                config.YOUTUBE_CLIENTS = saved
            fmts = info.get("formats") or []
            heights = sorted({f.get("height") for f in fmts if f.get("height")}, reverse=True)
            import cookies as cookie_store
            return {
                "ok": True,
                "title": (info.get("title") or "")[:80],
                "duration": info.get("duration"),
                "formats": len(fmts),
                "heights": heights[:8],
                "pot": bool(config.POT_SERVER_URL),
                "cookies": cookie_store.source(),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    if request.query_params.get("diag") == "pot_trace":
        # Owner-only: single verbose extract capturing the PO-token
        # plugin's log lines (was a token fetched? attached? rejected?).
        # /api?diag=pot_trace&url=...&key=WEBHOOK_SECRET
        import asyncio
        import downloader
        key_ok = (
            not WEBHOOK_SECRET
            or request.query_params.get("key") == WEBHOOK_SECRET
        )
        url = request.query_params.get("url", "")
        if not key_ok:
            return {"error": "unauthorized"}
        if not url:
            return {"error": "missing url param"}
        lines: list[str] = []

        class _Cap:
            def _push(self, msg):
                s = str(msg)
                low = s.lower()
                if any(k in low for k in ("pot", "bgutil", "visitor", "429", "bot", "sign in", "attestation", "challenge", "impersonat")):
                    lines.append(s[:300])
            def debug(self, m): self._push(m)
            def info(self, m): self._push(m)
            def warning(self, m): self._push(m)
            def error(self, m): self._push(m)
            def trace(self, m): self._push(m)

        def _run():
            from yt_dlp import YoutubeDL
            opts = downloader._base_opts()
            opts.update({"skip_download": True, "quiet": False, "no_warnings": False,
                         "verbose": True, "logger": _Cap(), "socket_timeout": 30, "retries": 1})
            try:
                with YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                return {"ok": True, "title": (info.get("title") or "")[:80],
                        "formats": len(info.get("formats") or [])}
            except Exception as e:
                return {"ok": False, "error": str(e)[:300]}
        try:
            res = await asyncio.wait_for(asyncio.to_thread(_run), timeout=280)
        except Exception as e:
            res = {"ok": False, "error": f"trace timeout/crash: {e}"[:300]}
        res["pot_log"] = lines[-40:]
        res["pot_url"] = config.POT_SERVER_URL
        # Direct self-call to the POT server with the exact payload the
        # plugin sends: proves whether get_pot works from inside Vercel
        # (vs. only when called from outside).
        try:
            import json as _json
            import urllib.request as _urlreq
            payload = _json.dumps({
                "bypass_cache": False, "challenge": None,
                "content_binding": url.split("v=")[-1].split("&")[0].split("/")[-1].split("?")[0] or "PEylwLDmayE",
                "disable_tls_verification": True, "proxy": None,
                "innertube_context": {"client": {"clientName": "WEB", "clientVersion": "2.20260708.00.00",
                                                 "hl": "en", "timeZone": "UTC", "utcOffsetMinutes": 0}},
                "source_address": None}).encode()
            req = _urlreq.Request(config.POT_SERVER_URL + "/get_pot", data=payload,
                                  headers={"Content-Type": "application/json"})
            with _urlreq.urlopen(req, timeout=60) as r:
                body = _json.loads(r.read().decode())
                res["pot_selfcall"] = {"http": r.status,
                                       "token_len": len(body.get("poToken") or ""),
                                       "has_binding": bool(body.get("contentBinding"))}
        except Exception as e:
            res["pot_selfcall"] = {"http": "ERR", "error": str(e)[:200]}
        return res

    if request.query_params.get("diag") == "ff":
        import subprocess
        import cookies as cookie_store
        import downloader
        import yt_dlp
        node_info = {}
        try:
            r = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
            node_info = {"node": r.stdout.strip() or r.stderr.strip(), "rc": r.returncode}
        except FileNotFoundError:
            node_info = {"node": "not found"}
        except Exception as e:
            node_info = {"node": f"error: {e}"}
        # Anti-bot toolchain status: confirms the PO-token plugin,
        # TLS impersonation and the JS runtime are actually present in
        # this deployment (a missing piece here = YouTube bot-checks
        # even with correct config).
        import importlib.util as _ilu
        _spec = lambda name: bool(_ilu.find_spec(name))
        return {
            "ffmpeg_path": downloader.FFMPEG_PATH,
            "ffmpeg_found": bool(downloader.FFMPEG_PATH),
            "yt_dlp": yt_dlp.version.__version__,
            "runtime_dir": config.RUNTIME_DIR,
            "node": node_info,
            "pot_url": config.POT_SERVER_URL,
            "clients": config.YOUTUBE_CLIENTS,
            "fetch_pot": config.FETCH_POT,
            "cookies": cookie_store.source(),
            "pot_plugin_installed": _spec("yt_dlp_plugins.extractor.getpot_bgutil"),
            "curl_cffi_installed": _spec("curl_cffi"),
        }
    return {
        "ok": True,
        "bot": config.BOT_NAME,
        "version": config.BOT_VERSION,
        "mode": "webhook",
    }


@app.post("/")
@app.post("/api")
@app.post("/api/")
async def webhook(request: Request):
    # optional secret-token check (set via setWebhook secret_token)
    if WEBHOOK_SECRET and request.headers.get("x-telegram-bot-api-secret-token") != WEBHOOK_SECRET:
        return Response(status_code=401)

    try:
        payload = await request.json()
    except Exception:
        return Response(status_code=400)

    update_id = payload.get("update_id")
    if update_id is not None:
        if update_id in _seen_updates:
            # Telegram retry for a request we already handled → ack fast
            return Response(status_code=200)
        _seen_updates.add(update_id)
        if len(_seen_updates) > 10000:
            _seen_updates.clear()

    application = await get_application()
    update = Update.de_json(payload, application.bot)
    if update is None:
        return Response(status_code=200)

    try:
        # inline processing → function stays alive during download + upload
        await application.process_update(update)
    except Exception:
        log.exception("failed processing update %s", update_id)

    return Response(status_code=200)
