"""
⚡ ZYROX VIDEO DOWNLOADER — /start, main menu, info pages, message router
"""

import logging

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

import config
import database
import keyboards
import texts
import utils
from handlers import admin, common, download

log = logging.getLogger("zyrox")


# ───────────────────── /start ─────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if not user or chat.type != "private":
        return

    database.touch_user(user.id)
    is_new = database.add_user(
        user.id, user.first_name or "", user.username or ""
    )
    claimed = common.maybe_claim_owner(user.id)

    if is_new:
        await admin.notify_new_user(context, user)

    if not await common.ensure_joined(update, context):
        return

    name = utils.esc(user.first_name or "friend")
    await update.effective_message.reply_html(
        texts.WELCOME.format(name=name),
        reply_markup=keyboards.main_menu(common.is_admin(user.id)),
    )
    if claimed:
        await update.effective_message.reply_html(
            "👑 <b>You are now the OWNER of this bot!</b>\n"
            "Open <b>/admin</b> to manage it.\n\n"
            "⚠️ Tip: also put your ID in <code>config.py → ADMIN_IDS</code>"
        )


# ───────────────────── simple commands ─────────────────────

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    database.touch_user(update.effective_user.id)
    await common.reply_html(update, texts.HELP, reply_markup=keyboards.back_to_menu())


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    database.touch_user(update.effective_user.id)
    await common.reply_html(
        update,
        texts.ABOUT.format(version=config.BOT_VERSION, channel=config.UPDATE_CHANNEL),
        reply_markup=keyboards.back_to_menu(),
    )


async def cmd_sites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    database.touch_user(update.effective_user.id)
    await common.reply_html(update, texts.SITES, reply_markup=keyboards.back_to_menu())


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    await common.reply_html(
        update,
        "🆔 Your Telegram ID:\n<code>{}</code>".format(update.effective_user.id),
    )


# ───────────────────── menu callbacks ─────────────────────

async def on_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "noop":
        return

    user = update.effective_user
    database.touch_user(user.id)

    if data == "menu:back":
        await query.edit_message_text(
            texts.WELCOME.format(name=utils.esc(user.first_name or "friend")),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboards.main_menu(common.is_admin(user.id)),
        )
    elif data == "menu:about":
        await query.edit_message_text(
            texts.ABOUT.format(version=config.BOT_VERSION, channel=config.UPDATE_CHANNEL),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboards.back_to_menu(),
        )
    elif data == "menu:help":
        await query.edit_message_text(
            texts.HELP, parse_mode=ParseMode.HTML, reply_markup=keyboards.back_to_menu()
        )
    elif data == "menu:sites":
        await query.edit_message_text(
            texts.SITES, parse_mode=ParseMode.HTML, reply_markup=keyboards.back_to_menu()
        )
    elif data == "menu:account":
        row = database.get_user(user.id)
        await query.edit_message_text(
            texts.ACCOUNT.format(
                uid=user.id,
                name=utils.esc(user.first_name or "—"),
                username=("@" + user.username) if user.username else "—",
                joined=(row["joined_at"][:10] if row else "—"),
                downloads=(row["downloads"] if row else 0),
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboards.back_to_menu(),
        )


async def on_force_join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""

    if data == "fj:hint":
        await query.answer(
            "🔒 This is a private channel — join it using your invite link, "
            "then come back and verify!",
            show_alert=True,
        )
        return

    await query.answer()
    user = update.effective_user
    pending = await common.not_joined_channels(context.bot, user.id)
    if pending:
        await query.answer("🔒 You still need to join all channels!", show_alert=True)
        try:
            await query.edit_message_reply_markup(reply_markup=keyboards.force_join(pending))
        except Exception:
            pass
        return
    try:
        await query.message.delete()
    except Exception:
        pass
    name = utils.esc(user.first_name or "friend")
    await context.bot.send_message(
        update.effective_chat.id,
        texts.UNLOCKED.format(name=name),
        parse_mode=ParseMode.HTML,
    )
    await context.bot.send_message(
        update.effective_chat.id,
        texts.WELCOME.format(name=name),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.main_menu(common.is_admin(user.id)),
    )


# ───────────────────── message router ─────────────────────
# Single entry for every private non-command message:
#   admin modes (broadcast / add channel) → admin handler
#   link → download handler
#   anything else → hint

async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    if not message or not user:
        return
    database.touch_user(user.id)

    mode = context.user_data.get("mode")

    # 1) admin conversation modes first
    if mode and common.is_admin(user.id):
        await admin.handle_mode_message(update, context)
        return

    text = message.text or message.caption or ""
    url = utils.extract_url(text)

    # 2) link → downloader
    if url:
        await download.handle_link(update, context, url)
        return

    # 3) media without link
    if not text:
        await message.reply_html(texts.NOT_A_LINK)
        return

    # 4) plain text without link
    if common.is_admin(user.id) and text.startswith("/broadcast"):
        return
    await message.reply_html(texts.NOT_A_LINK)
