"""
⚡ ZYROX VIDEO DOWNLOADER — SQLite database layer
Tables: users, channels (extra force-join), settings
"""

import os
import sqlite3
from datetime import datetime, timedelta

import config

_conn: sqlite3.Connection | None = None


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def init() -> None:
    """Create tables if they do not exist."""
    global _conn
    os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
    _conn = sqlite3.connect(config.DATABASE_PATH, check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.execute(
        """CREATE TABLE IF NOT EXISTS users(
            user_id     INTEGER PRIMARY KEY,
            first_name  TEXT,
            username    TEXT,
            joined_at   TEXT,
            last_seen   TEXT,
            downloads   INTEGER DEFAULT 0
        )"""
    )
    _conn.execute(
        """CREATE TABLE IF NOT EXISTS channels(
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            handle   TEXT UNIQUE,
            title    TEXT,
            invite   TEXT,
            added_by INTEGER,
            added_at TEXT
        )"""
    )
    # migration for older databases
    try:
        _conn.execute("ALTER TABLE channels ADD COLUMN invite TEXT")
    except sqlite3.OperationalError:
        pass
    _conn.execute(
        """CREATE TABLE IF NOT EXISTS settings(
            key   TEXT PRIMARY KEY,
            value TEXT
        )"""
    )
    _conn.commit()


def _c() -> sqlite3.Connection:
    if _conn is None:
        init()
    return _conn


# ───────────────────── USERS ─────────────────────

def add_user(user_id: int, first_name: str, username: str | None) -> bool:
    """Insert user if new. Returns True when the user is NEW."""
    now = _now()
    cur = _c().execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
    is_new = cur.fetchone() is None
    if is_new:
        _c().execute(
            "INSERT INTO users(user_id, first_name, username, joined_at, last_seen, downloads) "
            "VALUES(?,?,?,?,?,0)",
            (user_id, first_name, username, now, now),
        )
    else:
        _c().execute(
            "UPDATE users SET first_name=?, username=?, last_seen=? WHERE user_id=?",
            (first_name, username, now, user_id),
        )
    _c().commit()
    return is_new


def touch_user(user_id: int) -> None:
    _c().execute("UPDATE users SET last_seen=? WHERE user_id=?", (_now(), user_id))
    _c().commit()


def get_user(user_id: int) -> sqlite3.Row | None:
    cur = _c().execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()


def all_users() -> list[sqlite3.Row]:
    return _c().execute("SELECT * FROM users ORDER BY joined_at DESC").fetchall()


def user_count() -> int:
    return _c().execute("SELECT COUNT(*) c FROM users").fetchone()["c"]


def active_users(hours: int = 24) -> int:
    since = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    return _c().execute("SELECT COUNT(*) c FROM users WHERE last_seen>=?", (since,)).fetchone()["c"]


def increment_download(user_id: int) -> None:
    _c().execute("UPDATE users SET downloads=downloads+1 WHERE user_id=?", (user_id,))
    _c().execute(
        "INSERT INTO settings(key,value) VALUES('total_downloads','0') "
        "ON CONFLICT(key) DO NOTHING"
    )
    _c().execute("UPDATE settings SET value=CAST(CAST(value AS INTEGER)+1 AS TEXT) WHERE key='total_downloads'")
    _c().commit()


def total_downloads() -> int:
    cur = _c().execute("SELECT value FROM settings WHERE key='total_downloads'")
    row = cur.fetchone()
    return int(row["value"]) if row else 0


# ───────────────────── SETTINGS ─────────────────────

def get_setting(key: str) -> str | None:
    cur = _c().execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    return row["value"] if row else None


def set_setting(key: str, value: str) -> None:
    _c().execute(
        "INSERT INTO settings(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    _c().commit()


# ───────────────────── FORCE-JOIN CHANNELS ─────────────────────

def add_channel(handle: str, title: str, added_by: int, invite: str | None = None) -> bool:
    """Add channel. Returns False if it already exists."""
    try:
        _c().execute(
            "INSERT INTO channels(handle,title,invite,added_by,added_at) VALUES(?,?,?,?,?)",
            (handle, title, invite, added_by, _now()),
        )
        _c().commit()
        return True
    except sqlite3.IntegrityError:
        return False


def remove_channel(channel_id: int) -> bool:
    cur = _c().execute("DELETE FROM channels WHERE id=?", (channel_id,))
    _c().commit()
    return cur.rowcount > 0


def list_channels() -> list[sqlite3.Row]:
    return _c().execute("SELECT * FROM channels ORDER BY id").fetchall()


def get_all_force_channels() -> list[dict]:
    """Config defaults (built-in) + admin-added channels, de-duplicated."""
    merged: list[dict] = []
    seen: set[str] = set()
    for h in config.DEFAULT_CHANNELS:
        key = h.lower()
        if key not in seen:
            seen.add(key)
            merged.append({"id": 0, "handle": h, "title": h, "default": True})
    for r in list_channels():
        key = r["handle"].lower()
        if key not in seen:
            seen.add(key)
            merged.append(
                {
                    "id": r["id"],
                    "handle": r["handle"],
                    "title": r["title"],
                    "invite": r["invite"] or None,
                    "default": False,
                }
            )
    return merged
