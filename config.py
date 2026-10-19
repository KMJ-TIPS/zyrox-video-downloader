"""
⚡ ZYROX VIDEO DOWNLOADER — Configuration
=========================================
Edit the values below OR set environment variables.
"""

import os

# ──────────────────────────────────────────────
# 1. BOT TOKEN (required!)
# ──────────────────────────────────────────────
# Get it from @BotFather on Telegram → /newbot → copy token
# You can also set it with:  export BOT_TOKEN="123456:ABC..."
BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_BOTFATHER_TOKEN_HERE")

# ──────────────────────────────────────────────
# 2. ADMIN IDS (owner accounts)
# ──────────────────────────────────────────────
# Send /id to the bot to get your Telegram ID, then paste it here.
# Example: ADMIN_IDS = [123456789, 987654321]
# Or set with:  export ADMIN_IDS="123456789,987654321"
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x.strip().isdigit()]

# If True and no admin is configured anywhere, the FIRST user who
# presses /start automatically becomes the owner (handy for
# personal Termux bots). Set False for public deployments.
AUTO_CLAIM_FIRST_ADMIN = True

# ──────────────────────────────────────────────
# 3. FORCE-JOIN CHANNELS (built-in, cannot be removed)
# ──────────────────────────────────────────────
# These are ALWAYS required. More channels can be added
# later from the Admin Panel.
DEFAULT_CHANNELS = ["@Zyroxv1"]

# ──────────────────────────────────────────────
# 4. DOWNLOAD LIMITS
# ──────────────────────────────────────────────
# Telegram Bot API lets bots upload max 50 MB.
# Quality buttons bigger than this are auto-hidden.
MAX_FILESIZE_MB = int(os.getenv("MAX_FILESIZE_MB", "50"))

# How many downloads can run at the same time (server side)
MAX_CONCURRENT_DOWNLOADS = 3

# Progress message update interval (seconds) — flood-safe
PROGRESS_INTERVAL = 2.5

# ──────────────────────────────────────────────
# 5. PATHS
# ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
DATABASE_PATH = os.path.join(BASE_DIR, "zyrox.db")

# ──────────────────────────────────────────────
# 6. OPTIONAL: cookies.txt for Instagram / private content
# ──────────────────────────────────────────────
# Export cookies with a browser extension and put the path here.
# Example: "/data/data/com.termux/files/home/cookies.txt"
COOKIES_FILE = os.getenv("COOKIES_FILE", "")

# ──────────────────────────────────────────────
# 7. BRANDING
# ──────────────────────────────────────────────
BOT_NAME = "ZYROX VIDEO DOWNLOADER"
BOT_VERSION = "1.0"
UPDATE_CHANNEL = "Zyroxv1"          # shown in buttons / credits
UPDATE_CHANNEL_URL = "https://t.me/Zyroxv1"
