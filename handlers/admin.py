"""
⚡ ZYROX VIDEO DOWNLOADER — admin panel
Broadcast • user list + export • force-join channel management
"""

import asyncio
import logging
import os
import re
import tempfile
import time
from datetime import datetime

from telegram import Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import Forbidden, TelegramError
from telegram.ext import ContextTypes

import config
import cookies as cookie_store
import database
import keyboards
import texts
import utils
from handlers import common

log = logging.getLogger("zyrox")


# ───────────────────── new user notification ─────────────────────

async def notify_new_user(context, user):
    total = database.user_count()
    for admin_id in common.admin_ids():
        try:
            await context.bot.send_message(
                admin_id,
                texts.NEW_USER_ALERT.format(
                    name=utils.esc(user.first_name or "—"),
                    username=("@" + user.username) if user.username else "—",
                    uid=user.id,
                    total=total,
                ),
                parse_mode=ParseMode.HTML,
            )
        except TelegramError:
            pass


# ───────────────────── panel ─────────────────────

def _panel_text() -> str:
    return texts.ADMIN_PANEL.format(
        users=database.user_count(),
        active=database.active_users(24),
        downloads=database.total_downloads(),
        channels=len(database.get_all_force_channels()),
    )


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not common.is_admin(user.id):
        await common.reply_html(update, texts.ADMIN_DENIED)
        return
    await update.effective_message.reply_html(
        _panel_text(), reply_markup=keyboards.admin_panel()
    )


async def on_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    data = query.data or ""

    if not common.is_admin(user.id):
        await query.answer(texts.ADMIN_DENIED, show_alert=True)
        return

    # ── panel / refresh / back ──
    if data in ("admin:panel", "admin:refresh"):
        await query.answer()
        await common.safe_edit(query.message, _panel_text(), reply_markup=keyboards.admin_panel())

    elif data == "admin:menu":
        await query.answer()
        await common.safe_edit(
            query.message,
            texts.WELCOME.format(name=utils.esc(user.first_name or "friend")),
            reply_markup=keyboards.main_menu(True),
        )

    elif data == "admin:users":
        await query.answer()
        await common.safe_edit(
            query.message,
            texts.USERS_PAGE.format(total=database.user_count(), active=database.active_users(24)),
            reply_markup=keyboards.admin_users(),
        )

    elif data == "admin:export":
        await query.answer("📤 Building file...")
        await _export_users(context, query)

    elif data == "admin:channels":
        await query.answer()
        await common.safe_edit(
            query.message,
            _channels_text(),
            reply_markup=keyboards.admin_channels(database.get_all_force_channels()),
        )

    elif data == "admin:addchannel":
        await query.answer()
        context.user_data["mode"] = "add_channel"
        await common.safe_edit(query.message, texts.ADD_CHANNEL_PROMPT)

    elif data == "admin:broadcast":
        await query.answer()
        context.user_data["mode"] = "broadcast"
        await common.safe_edit(query.message, texts.BROADCAST_PROMPT)

    elif data.startswith("admchan:del:"):
        await query.answer("🗑 Removed")
        channel_id = int(data.split(":")[2])
        database.remove_channel(channel_id)
        await common.safe_edit(
            query.message,
            _channels_text(),
            reply_markup=keyboards.admin_channels(database.get_all_force_channels()),
        )


def _channels_text() -> str:
    channels = database.get_all_force_channels()
    rows = []
    for ch in channels:
        title = utils.esc(ch["title"])
        rows.append(f"⚡ <b>{title}</b> — <code>{utils.esc(ch['handle'])}</code>")
    listing = "\n".join(rows) if rows else texts.CHANNELS_EMPTY
    return texts.CHANNELS_LIST.format(list=listing)


# ───────────────────── export users ─────────────────────

async def _export_users(context, query):
    users = database.all_users()
    stamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    path = os.path.join(tempfile.gettempdir(), f"zyrox_users_{int(datetime.utcnow().timestamp())}.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"⚡ ZYROX VIDEO DOWNLOADER — USER LIST\nExported: {stamp}\nTotal: {len(users)} users\n")
        fh.write("─" * 60 + "\n")
        for u in users:
            uname = f"@{u['username']}" if u["username"] else "—"
            fh.write(
                f"{u['user_id']} | {u['first_name']} | {uname} | "
                f"downloads: {u['downloads']} | joined: {u['joined_at'][:10]}\n"
            )
    try:
        with open(path, "rb") as fh:
            await context.bot.send_document(query.message.chat_id, fh, filename="zyrox_users.txt")
        os.remove(path)
    except TelegramError as e:
        log.error("export failed: %s", e)


# ───────────────────── YouTube bot-check owner alert ─────────────────────

_botcheck_last = 0.0
BOTCHECK_COOLDOWN = 6 * 3600  # seconds between owner alerts


def _cookies_status_label() -> str:
    src = cookie_store.source()
    return {"uploaded": "✅ active (uploaded)", "env": "✅ active (env var)", "none": "❌ none"}.get(src, src)


async def notify_botcheck(context, url: str) -> None:
    """DM every admin the cookies fix guide (rate-limited)."""
    global _botcheck_last
    now = time.time()
    if now - _botcheck_last < BOTCHECK_COOLDOWN:
        return
    _botcheck_last = now
    for admin_id in common.admin_ids():
        try:
            await context.bot.send_message(
                admin_id,
                texts.OWNER_BOTCHECK.format(url=url, status=_cookies_status_label()),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except TelegramError:
            pass


# ───────────────────── cookies management (/cookies) ─────────────────────

async def cmd_cookies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not common.is_admin(user.id):
        await common.reply_html(update, texts.ADMIN_DENIED)
        return
    if cookie_store.source() == "none":
        context.user_data["mode"] = "cookies_upload"
        await common.reply_html(update, texts.COOKIES_STATUS_OFF)
    else:
        context.user_data["mode"] = "cookies_upload"
        await common.reply_html(
            update, texts.COOKIES_STATUS_ON.format(source=_cookies_status_label())
        )


async def cmd_cookies_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not common.is_admin(user.id):
        await common.reply_html(update, texts.ADMIN_DENIED)
        return
    cookie_store.clear_uploaded()
    await common.reply_html(update, texts.COOKIES_CLEARED)


async def _do_cookies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    content: str | None = None

    doc = message.document
    if doc is not None:
        if (doc.file_size or 0) > 2 * 1024 * 1024:
            await message.reply_html(texts.COOKIES_BAD.format(err="file too large (max 2 MB)"))
            return
        try:
            tg_file = await doc.get_file()
            data = await tg_file.download_as_bytearray()
            content = bytes(data).decode("utf-8", errors="replace")
        except TelegramError as e:
            log.error("cookies download failed: %s", e)
            await message.reply_html(
                texts.COOKIES_BAD.format(err="could not read that file from Telegram")
            )
            return
    else:
        content = message.text or ""

    err = cookie_store.validate(content or "")
    if err:
        await message.reply_html(texts.COOKIES_BAD.format(err=err))
        return

    cookie_store.install_from_text(content)
    context.user_data["mode"] = None
    await message.reply_html(texts.COOKIES_SAVED)
    log.info("cookies installed by owner (%s bytes)", len(content))


# ───────────────────── conversation modes ─────────────────────

async def handle_mode_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")
    message = update.effective_message

    if mode == "broadcast":
        context.user_data["mode"] = None
        await _do_broadcast(update, context)
    elif mode == "add_channel":
        context.user_data["mode"] = None
        await _do_add_channel(update, context)
    elif mode == "cookies_upload":
        await _do_cookies(update, context)


async def _do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    users = database.all_users()
    total = len(users)

    progress = await message.reply_html(
        texts.BROADCAST_PROGRESS.format(sent=0, failed=0, total=total)
    )

    sent = failed = 0
    for idx, u in enumerate(users, 1):
        uid = u["user_id"]
        try:
            await context.bot.copy_message(
                chat_id=uid,
                from_chat_id=message.chat_id,
                message_id=message.message_id,
            )
            sent += 1
        except Forbidden:
            failed += 1
        except TelegramError:
            failed += 1
        if idx % 25 == 0:
            await common.safe_edit(
                progress, texts.BROADCAST_PROGRESS.format(sent=sent, failed=failed, total=total)
            )
        await asyncio.sleep(0.05)  # flood-safe pace

    await common.safe_edit(
        progress, texts.BROADCAST_DONE.format(total=total, sent=sent, failed=failed)
    )


_HANDLE_PATTERNS = [
    re.compile(r"^@([A-Za-z0-9_]{4,64})$"),
    re.compile(r"(?:https?://)?t\.me/([A-Za-z0-9_]{4,64})/?$", re.IGNORECASE),
    re.compile(r"^(-100\d{8,})$"),
]


def _normalize_channel(text: str) -> str | None:
    text = (text or "").strip()
    for pat in _HANDLE_PATTERNS:
        m = pat.match(text)
        if m:
            g = m.group(1)
            return g if g.startswith("-100") else f"@{g}"
    return None


async def _do_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    handle = _normalize_channel(message.text or "")

    if not handle:
        context.user_data["mode"] = "add_channel"   # let them retry
        await message.reply_html(
            "⚠️ That doesn't look like a channel handle.\n\n" + texts.ADD_CHANNEL_PROMPT
        )
        return

    # validate: bot must see the channel
    try:
        chat = await context.bot.get_chat(handle)
    except TelegramError:
        await message.reply_html(texts.ADMIN_ERR_CHANNEL, reply_markup=keyboards.admin_back())
        return

    if chat.type not in ("channel", "supergroup"):
        await message.reply_html(
            "⚠️ That is not a channel/supergroup.\n\n" + texts.ADMIN_ERR_CHANNEL,
            reply_markup=keyboards.admin_back(),
        )
        return

    added = database.add_channel(
        handle,
        chat.title or handle,
        update.effective_user.id,
        invite=getattr(chat, "invite_link", None),
    )
    if not added:
        await message.reply_html(
            "ℹ️ This channel is <b>already</b> in the force-join list.",
            reply_markup=keyboards.admin_back(),
        )
        return

    await message.reply_html(
        texts.CHANNEL_ADDED.format(
            title=utils.esc(chat.title or handle), handle=utils.esc(handle)
        )
    )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    had_mode = context.user_data.pop("mode", None)
    context.user_data["cancel"] = True
    if had_mode:
        await update.effective_message.reply_html(texts.MODE_CANCELLED)
    else:
        context.user_data["cancel"] = False
        await update.effective_message.reply_html(
            "ℹ️ Nothing to cancel.\n\n⚡ Send a video link to download!"
        )
