"""
⚡ ZYROX VIDEO DOWNLOADER — Utility helpers
Progress bar, human sizes, platform badges, HTML escaping.
"""

import html
import re
from urllib.parse import urlparse

SEP = "━━━━━━━━━━━━━━━━━━━━"
BAR_WIDTH = 16
SPINNER_FRAMES = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "▆", "▅", "▄", "▃", "▂"]


def esc(text) -> str:
    """HTML-escape dynamic values used inside HTML parse mode texts."""
    return html.escape(str(text or ""), quote=False)


def trunc(text: str, limit: int = 60) -> str:
    text = str(text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def human_size(num_bytes) -> str:
    if not num_bytes or num_bytes <= 0:
        return "—"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    i = 0
    while size >= 1024 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.1f} {units[i]}" if i > 1 else f"{int(size)} {units[i]}"


def fmt_duration(seconds) -> str:
    if not seconds or seconds <= 0:
        return "—"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def progress_bar(pct: float, width: int = BAR_WIDTH) -> str:
    """Animated bar: ▓▓▓▓▓▓▓▓░░░░░░░░"""
    pct = max(0.0, min(100.0, pct))
    filled = int(round(width * pct / 100.0))
    return "▓" * filled + "░" * (width - filled)


def spinner_at(index: int) -> str:
    return SPINNER_FRAMES[index % len(SPINNER_FRAMES)]


# ───────────────────── PLATFORM BADGES ─────────────────────

PLATFORMS = [
    (r"(youtube\.com|youtu\.be)", "🎬 YouTube"),
    (r"(instagram\.com|instagr\.am)", "📸 Instagram"),
    (r"tiktok\.com", "🎵 TikTok"),
    (r"(facebook\.com|fb\.watch|fb\.com|fb\.me)", "👥 Facebook"),
    (r"(twitter\.com|x\.com)", "🐦 Twitter / X"),
    (r"snapchat\.com", "👻 Snapchat"),
    (r"(pinterest\.[a-z.]+|pin\.it)", "📌 Pinterest"),
    (r"(reddit\.com|redd\.it)", "👽 Reddit"),
    (r"vimeo\.com", "🎥 Vimeo"),
    (r"soundcloud\.com", "🎧 SoundCloud"),
    (r"(dailymotion\.com|dai\.ly)", "📺 Dailymotion"),
    (r"twitch\.tv", "🎮 Twitch"),
    (r"likee\.video", "💜 Likee"),
    (r"linkedin\.com", "💼 LinkedIn"),
    (r"imgur\.com", "🖼️ Imgur"),
]

URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)


def extract_url(text: str) -> str | None:
    """Return the first URL found in text (adds scheme for www. links)."""
    m = URL_RE.search(text or "")
    if not m:
        return None
    url = m.group(1).strip()
    if url.lower().startswith("www."):
        url = "https://" + url
    # strip trailing punctuation that often sticks to links
    return url.rstrip(").,!?;:'\"")


def detect_platform(url: str) -> str:
    low = (url or "").lower()
    for pattern, badge in PLATFORMS:
        if re.search(pattern, low):
            return badge
    host = urlparse(low).netloc if low else ""
    return f"🌐 {host.replace('www.', '') or 'Web'}" if host else "🌐 Web"


def quality_name(height: int) -> str:
    names = {4320: "8K", 2880: "5K", 2160: "4K", 1440: "2K", 1080: "FHD", 720: "HD"}
    return names.get(height, f"{height}p")


def clean_error_message(err_text: str) -> str:
    """Map common yt-dlp errors to friendly English messages."""
    low = (err_text or "").lower()
    if "sign in to confirm" in low or "not a bot" in low:
        return (
            "🤖 <b>YouTube bot-check blocked this server.</b>\n\n"
            "💡 The owner can fix this by adding <b>YOUTUBE_COOKIES</b> "
            "(or a proxy) in the hosting settings."
        )
    if any(k in low for k in ("login", "cookies", "sign in", "age", "private", "authentication")):
        return "🔒 This content is <b>private or requires login</b>.\n   (Instagram/age-restricted content may need cookies)"
    if any(k in low for k in ("not available", "unavailable", "removed", "404")):
        return "🗑 This content is <b>unavailable or was removed</b>."
    if "unsupported url" in low:
        return "🚫 This website is <b>not supported</b>.\n   Try another link!"
    if "timed out" in low or "timeout" in low:
        return "📡 <b>Network timeout.</b> Please try again."
    if "playlist" in low:
        return "📋 Playlist detected — send a <b>single video link</b>."
    return "⚠️ Something went wrong while reading this link.\n   Please check the URL and try again."
