"""
⚡ ZYROX VIDEO DOWNLOADER — cookies store
=========================================
YouTube blocks datacenter IPs (Vercel/serverless) unless the request
carries a logged-in session. This store manages cookies with priority:

  1. Owner-uploaded via /cookies chat command → saved in DB + runtime file
  2. YOUTUBE_COOKIES env var (raw cookies.txt content) → written by config.py
  3. COOKIES_FILE env var (path to an existing cookies.txt)

On Termux the upload is permanent. On Vercel cold starts /tmp + DB reset,
so the YOUTUBE_COOKIES env var is the durable fix (the bot DMs the owner
a step-by-step guide when YouTube is blocked without cookies).
"""

import os

import config
import database

RUNTIME_COOKIES = os.path.join(config.RUNTIME_DIR, "cookies_owner.txt")


# ───────────────────── install / clear ─────────────────────

def validate(content: str) -> str | None:
    """Basic sanity check for a Netscape cookies.txt. Returns error or None."""
    text = (content or "").strip()
    if not text:
        return "file is empty"
    has_tab_rows = any("\t" in line for line in text.splitlines()[:60])
    mentions_netscape = "netscape" in text[:2000].lower()
    if not has_tab_rows and not mentions_netscape:
        return (
            "this does not look like a <b>Netscape cookies.txt</b> file.\n"
            "   Export it with the <b>Get cookies.txt LOCALLY</b> browser extension."
        )
    return None


def install_from_text(content: str) -> str:
    """Persist owner cookies (DB + runtime file). Returns the active path."""
    text = (content or "").replace("\r\n", "\n").strip()
    database.set_setting("cookies_txt", text)
    return _write_runtime(text)


def clear_uploaded() -> None:
    database.set_setting("cookies_txt", "")
    try:
        os.remove(RUNTIME_COOKIES)
    except OSError:
        pass


# ───────────────────── query ─────────────────────

def uploaded_exists() -> bool:
    v = database.get_setting("cookies_txt")
    return bool(v and v.strip())


def source() -> str:
    """'uploaded' | 'env' | 'none'"""
    if uploaded_exists():
        return "uploaded"
    if config.COOKIES_FILE and os.path.exists(config.COOKIES_FILE):
        return "env"
    return "none"


def active_path() -> str | None:
    """Best available cookies file path, restoring from DB if needed."""
    if uploaded_exists():
        if not os.path.exists(RUNTIME_COOKIES):
            content = database.get_setting("cookies_txt")
            if content and content.strip():
                try:
                    _write_runtime(content)
                except OSError:
                    return None
        if os.path.exists(RUNTIME_COOKIES):
            return RUNTIME_COOKIES
        return None
    if config.COOKIES_FILE and os.path.exists(config.COOKIES_FILE):
        return config.COOKIES_FILE
    return None


# ───────────────────── internal ─────────────────────

def _write_runtime(content: str) -> str:
    os.makedirs(config.RUNTIME_DIR, exist_ok=True)
    with open(RUNTIME_COOKIES, "w", encoding="utf-8") as fh:
        fh.write(content if content.endswith("\n") else content + "\n")
    return RUNTIME_COOKIES
