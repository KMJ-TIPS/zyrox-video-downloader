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
    if request.query_params.get("diag") == "ff":
        import downloader
        import yt_dlp
        return {
            "ffmpeg_path": downloader.FFMPEG_PATH,
            "ffmpeg_found": bool(downloader.FFMPEG_PATH),
            "yt_dlp": yt_dlp.version.__version__,
            "runtime_dir": config.RUNTIME_DIR,
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
