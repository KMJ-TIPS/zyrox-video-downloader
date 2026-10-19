"""
⚡ ZYROX VIDEO DOWNLOADER — shared handler helpers
Force-join verification, admin checks, safe message editing.
"""

import asyncio
import logging

from telegram import Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import BadRequest, Forbidden, RetryAfter, TelegramError

import config
import database
import texts
import utils
import keyboards

log = logging.getLogger("zyrox")


# ───────────────────── ADMIN ─────────────────────

def is_admin(user_id: int) -> bool:
    if user_id in config.ADMIN_IDS:
        return True
    owner = database.get_setting("owner_id")
    return owner is not None and str(user_id) == owner


def admin_ids() -> list[int]:
    """Configured admins + claimed owner."""
    ids = list(config.ADMIN_IDS)
    owner = database.get_setting("owner_id")
    if owner and int(owner) not in ids:
        ids.append(int(owner))
    return ids


def maybe_claim_owner(user_id: int) -> bool:
    """Auto-claim first admin if nothing is configured. Returns True if claimed."""
    if not config.AUTO_CLAIM_FIRST_ADMIN:
        return False
    if config.ADMIN_IDS or database.get_setting("owner_id"):
        return False
    database.set_setting("owner_id", str(user_id))
    log.warning("Auto-claimed first admin: %s (configure ADMIN_IDS in config.py!)", user_id)
    return True


# ───────────────────── FORCE JOIN ─────────────────────

async def not_joined_channels(bot, user_id: int) -> list[dict]:
    """Return list of force-join channels the user has NOT joined."""
    pending = []
    for ch in database.get_all_force_channels():
        handle = ch["handle"]
        try:
            member = await bot.get_chat_member(handle, user_id)
            if member.status not in (
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER,
            ):
                pending.append(ch)
        except Forbidden:
            # bot can't verify (kicked / not admin) → don't lock the user
            log.warning("Cannot verify membership in %s — is the bot admin there?", handle)
        except BadRequest as e:
            msg = str(e).lower()
            if "member" in msg and "not found" in msg:
                pending.append(ch)
            elif "chat member not found" in msg:
                pending.append(ch)
            elif "not a member" in msg or "not enough rights" in msg or "admin" in msg:
                log.warning("Bot lacks rights in %s: %s", handle, e)
            else:
                pending.append(ch)
        except TelegramError as e:
            log.warning("Force-join check failed for %s: %s", handle, e)
    return pending


async def ensure_joined(update: Update, context) -> bool:
    """
    Check force-join. If user must join, show the locked screen.
    Returns True when the user is allowed to continue.
    """
    user = update.effective_user
    chat = update.effective_chat
    pending = await not_joined_channels(context.bot, user.id)
    if not pending:
        return True
    name = utils.esc(user.first_name or "friend")
    await context.bot.send_message(
        chat.id,
        texts.LOCKED.format(name=name),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.force_join(pending),
    )
    return False


# ───────────────────── SAFE EDIT / SEND ─────────────────────

async def safe_edit(message, text: str, reply_markup=None):
    """Edit a message, ignoring 'not modified' and handling flood waits."""
    try:
        return await message.edit_text(
            text, parse_mode=ParseMode.HTML, reply_markup=reply_markup
        )
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after + 1)
        try:
            return await message.edit_text(
                text, parse_mode=ParseMode.HTML, reply_markup=reply_markup
            )
        except TelegramError:
            return message
    except BadRequest as e:
        if "not modified" in str(e).lower():
            return message
        log.debug("safe_edit failed: %s", e)
        return message
    except Forbidden:
        return message
    except TelegramError as e:
        log.debug("safe_edit failed: %s", e)
        return message


async def reply_html(update: Update, text: str, reply_markup=None, **kwargs):
    return await update.effective_message.reply_text(
        text, parse_mode=ParseMode.HTML, reply_markup=reply_markup, **kwargs
    )
