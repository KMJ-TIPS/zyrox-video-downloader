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
# On Vercel (serverless) only /tmp is writable — keep runtime files there.
IS_SERVERLESS = bool(os.getenv("VERCEL"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if IS_SERVERLESS:
    RUNTIME_DIR = "/tmp/zyrox"
else:
    RUNTIME_DIR = BASE_DIR
DOWNLOAD_DIR = os.path.join(RUNTIME_DIR, "downloads")
DATABASE_PATH = os.path.join(RUNTIME_DIR, "zyrox.db")

# ──────────────────────────────────────────────
# 6. OPTIONAL: cookies.txt for Instagram / private content
# ──────────────────────────────────────────────
# Export cookies with a browser extension and put the path here.
# Example: "/data/data/com.termux/files/home/cookies.txt"
COOKIES_FILE = os.getenv("COOKIES_FILE", "")

# Or paste raw cookies.txt content into the YOUTUBE_COOKIES env var
# (recommended on Vercel — no file upload needed). It is written to
# the runtime dir at startup and used for YouTube/Instagram.
_yt_cookies_raw = os.getenv("YOUTUBE_COOKIES", "").strip()
if _yt_cookies_raw:
    try:
        os.makedirs(RUNTIME_DIR, exist_ok=True)
        _cookie_path = os.path.join(RUNTIME_DIR, "cookies.txt")
        with open(_cookie_path, "w", encoding="utf-8") as _f:
            _f.write(_yt_cookies_raw.replace("\\n", "\n") + "\n")
        COOKIES_FILE = COOKIES_FILE or _cookie_path
    except OSError:
        pass

# ──────────────────────────────────────────────
# 7. YOUTUBE ANTI-BOT (PO token provider / proxy)
# ──────────────────────────────────────────────
# On serverless (datacenter IPs) YouTube demands PO tokens.
# POT_SERVER_URL points to a bgutil HTTP provider (see api/pot.js).
POT_SERVER_URL = os.getenv("POT_SERVER_URL", "")
if not POT_SERVER_URL and IS_SERVERLESS and os.getenv("VERCEL_URL"):
    POT_SERVER_URL = f"https://{os.getenv('VERCEL_URL')}/api/pot"

# Player clients tried in order. "tv" + PO token works best on datacenter IPs.
YOUTUBE_CLIENTS = [
    c.strip() for c in os.getenv("YOUTUBE_CLIENTS", "web,web_safari,tv").split(",") if c.strip()
]
# fetch_pot: always | auto | never  ("always" → attach PO token to player request)
FETCH_POT = os.getenv("FETCH_POT", "always" if POT_SERVER_URL else "auto")

# Optional outbound proxy for yt-dlp (http/socks5 URL), e.g. http://user:pass@host:port
YTDLP_PROXY = os.getenv("YTDLP_PROXY", "")

# ──────────────────────────────────────────────
# 8. BRANDING
# ──────────────────────────────────────────────
BOT_NAME = "ZYROX VIDEO DOWNLOADER"
BOT_VERSION = "1.1"
UPDATE_CHANNEL = "Zyroxv1"          # shown in buttons / credits
UPDATE_CHANNEL_URL = "https://t.me/Zyroxv1"
