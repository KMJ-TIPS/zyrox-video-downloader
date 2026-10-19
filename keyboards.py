"""
⚡ ZYROX VIDEO DOWNLOADER — Inline keyboards (Premium Dark UI)
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import config


def _btn(text, data):
    return InlineKeyboardButton(text, callback_data=data)


def main_menu(is_admin: bool) -> InlineKeyboardMarkup:
    rows = [
        [_btn("🌐 SUPPORTED SITES", "menu:sites"), _btn("ℹ️ ABOUT", "menu:about")],
        [_btn("❓ HELP", "menu:help"), _btn("👤 MY ACCOUNT", "menu:account")],
        [
            InlineKeyboardButton("📢 UPDATES", url=config.UPDATE_CHANNEL_URL),
            _btn("⚡ START", "noop"),
        ],
    ]
    if is_admin:
        rows.append([_btn("👑 ADMIN PANEL", "admin:panel")])
    return InlineKeyboardMarkup(rows)


def force_join(channels: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        handle = str(ch["handle"])
        invite = ch.get("invite")
        if invite:
            rows.append([InlineKeyboardButton("📢 JOIN CHANNEL", url=invite)])
        elif handle.startswith("@"):
            rows.append(
                [InlineKeyboardButton(f"📢 JOIN {handle}", url=f"https://t.me/{handle[1:]}")]
            )
        else:
            # private channel id without invite link
            rows.append([_btn("📢 JOIN CHANNEL (private)", "fj:hint")])
    rows.append([_btn("✅ I'VE JOINED — VERIFY", "fj:check")])
    return InlineKeyboardMarkup(rows)


def quality_menu(q: dict, has_thumb_msg: bool = True) -> InlineKeyboardMarkup:
    rows = []
    for i, v in enumerate(q["videos"]):
        rows.append([_btn(f"🎬 {v['label']}  ▸  {v['size_txt']}", f"dl:v:{i}")])
    for i, a in enumerate(q["audios"]):
        rows.append([_btn(f"🎵 {a['label']}  ▸  {a['size_txt']}", f"dl:a:{i}")])
    rows.append([_btn("❌ CLOSE", "dl:close")])
    return InlineKeyboardMarkup(rows)


def cancel_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[_btn("❌ CANCEL", "dl:cancel")]])


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[_btn("⬅️ BACK TO MENU", "menu:back")]])


def admin_panel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [_btn("📢 BROADCAST", "admin:broadcast"), _btn("👥 USER LIST", "admin:users")],
            [_btn("➕ ADD CHANNEL", "admin:addchannel"), _btn("📋 CHANNEL LIST", "admin:channels")],
            [_btn("🔄 REFRESH", "admin:refresh"), _btn("🏠 MAIN MENU", "admin:menu")],
        ]
    )


def admin_users() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[_btn("📤 EXPORT USERS .TXT", "admin:export")], [_btn("⬅️ BACK", "admin:panel")]]
    )


def admin_channels(channels: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        if ch["default"]:
            rows.append([_btn(f"⚡ {ch['handle']}  (BUILT-IN)", "noop")])
        else:
            rows.append([_btn(f"🗑 {ch['handle']}  ✕", f"admchan:del:{ch['id']}")])
    rows.append([_btn("➕ ADD CHANNEL", "admin:addchannel")])
    rows.append([_btn("⬅️ BACK", "admin:panel")])
    return InlineKeyboardMarkup(rows)


def admin_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[_btn("⬅️ BACK", "admin:panel")]])


def close_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[_btn("❌ CLOSE", "dl:close")]])
