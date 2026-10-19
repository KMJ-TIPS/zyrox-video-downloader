#!/usr/bin/env python3
"""
⚡ ZYROX VIDEO DOWNLOADER — main entry point
All-in-One Social Media Downloader Telegram Bot
• Force-join channels • Admin panel • Broadcast • Live progress
Run:  python bot.py
"""

import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

import config
import database
from handlers import admin, download, start

# ───────────────────── logging ─────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("yt_dlp").setLevel(logging.WARNING)
log = logging.getLogger("zyrox")

BANNER = """
╔══════════════════════════════════════════════╗
║                                              ║
║      ⚡ ZYROX VIDEO DOWNLOADER v{version} ⚡      ║
║                                              ║
║   🎵 MP3 • 🎥 MP4 • HD • 2K • 4K             ║
║   🌐 YouTube • Instagram • TikTok • 1000+    ║
║   📊 Live Progress • 🔒 Force Join           ║
║   👑 Admin Panel • 📢 Broadcast              ║
║                                              ║
╚══════════════════════════════════════════════╝
"""


# ───────────────────── error handler ─────────────────────

async def error_handler(update: object, context) -> None:
    log.error("Unhandled error:", exc_info=context.error)
    try:
        if isinstance(update, Update) and update.effective_chat:
            await context.bot.send_message(
                update.effective_chat.id,
                "⚠️ <b>Oops! Something went wrong.</b>\n"
                "Please try again in a moment ⚡",
                parse_mode="HTML",
            )
    except Exception:
        pass


# ───────────────────── application factory ─────────────────────

def build_application(serverless: bool = False) -> Application:
    """Build a fully configured Application.

    serverless=False → long-polling (Termux / VPS, run via `python bot.py`)
    serverless=True  → webhook mode (Vercel; updates delivered via api/index.py)
    """
    builder = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .read_timeout(60)
        .write_timeout(120)
        .connect_timeout(30)
        .pool_timeout(30)
        .media_write_timeout(3600)
    )
    if serverless:
        builder = builder.updater(None)

    app = builder.build()
    app.bot_data["pool"] = ThreadPoolExecutor(max_workers=config.MAX_CONCURRENT_DOWNLOADS)
    app.bot_data["serverless"] = serverless

    # commands
    app.add_handler(CommandHandler("start", start.cmd_start))
    app.add_handler(CommandHandler("help", start.cmd_help))
    app.add_handler(CommandHandler("about", start.cmd_about))
    app.add_handler(CommandHandler("sites", start.cmd_sites))
    app.add_handler(CommandHandler("id", start.cmd_id))
    app.add_handler(CommandHandler("admin", admin.cmd_admin))
    app.add_handler(CommandHandler("cancel", admin.cmd_cancel))

    # callbacks
    app.add_handler(CallbackQueryHandler(start.on_menu, pattern=r"^menu:|^noop$"))
    app.add_handler(CallbackQueryHandler(start.on_force_join_check, pattern=r"^fj:"))
    app.add_handler(CallbackQueryHandler(admin.on_admin, pattern=r"^admin:|^admchan:"))
    app.add_handler(CallbackQueryHandler(download.on_quality, pattern=r"^dl:"))

    # all private messages (links, admin modes, fallback hints)
    app.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, start.route_message)
    )

    app.add_error_handler(error_handler)
    return app


class _SentinelUpdater:
    """Deprecated placeholder — kept for backwards compatibility."""


# ───────────────────── main ─────────────────────

def main():
    print(BANNER.format(version=config.BOT_VERSION))

    if not config.BOT_TOKEN or "PASTE_YOUR" in config.BOT_TOKEN:
        print("\n❌ BOT TOKEN MISSING!")
        print("   1. Open @BotFather on Telegram")
        print("   2. Send /newbot and follow steps")
        print("   3. Copy the token into config.py → BOT_TOKEN\n")
        sys.exit(1)

    database.init()
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)

    app = build_application(serverless=False)

    channels = ", ".join(config.DEFAULT_CHANNELS) or "—"
    log.info("Force-join channels: %s", channels)
    log.info("Max upload: %s MB | Pool workers: %s", config.MAX_FILESIZE_MB, config.MAX_CONCURRENT_DOWNLOADS)
    log.info("Bot is starting... Press Ctrl+C to stop")

    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped. Bye! ⚡")
