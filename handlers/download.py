"""
⚡ ZYROX VIDEO DOWNLOADER — link handler, quality menu, live progress, upload
"""

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

import cobalt
import config
import database
import downloader
import keyboards
import texts
import utils
from yt_dlp.utils import DownloadCancelled, DownloadError
from handlers import admin, common

log = logging.getLogger("zyrox")


def _get_pool(context) -> ThreadPoolExecutor:
    return context.application.bot_data["pool"]


async def _cobalt_fallback(update, context, url, status) -> bool:
    """YouTube bot-check → fetch via a public cobalt instance.

    Returns True when the fallback handled the request (file sent, direct
    link shown, or a friendly size message). False = cobalt also failed,
    caller falls through to the normal FETCH_FAILED message.
    """
    chat = update.effective_chat
    user = update.effective_user
    await common.safe_edit(status, texts.COBALT_TRYING)
    try:
        res = await asyncio.to_thread(cobalt.fetch, url, "video", "720")
    except Exception as e:
        log.warning("cobalt fetch failed: %s", e)
        return False

    if res["kind"] == "redirect":
        # Direct googlevideo URL — the bot (Vercel IP) can't fetch it, but
        # the user's phone can. Hand them the link instead of failing.
        await common.safe_edit(status, texts.COBALT_REDIRECT.format(url=res["url"]))
        return True

    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
    dest = os.path.join(config.DOWNLOAD_DIR, res["filename"])
    try:
        total = await asyncio.to_thread(
            cobalt.download_file, res["url"], dest,
            config.MAX_FILESIZE_MB * 1024 * 1024,
        )
    except ValueError:
        _cleanup(dest)
        await common.safe_edit(status, texts.TOO_BIG.format(size=">50 MB"))
        return True
    except Exception as e:
        log.warning("cobalt download failed: %s", e)
        _cleanup(dest)
        return False

    size_txt = utils.human_size(total)
    caption = texts.VIDEO_DONE.format(
        title="YouTube Video",
        platform="🎬 YouTube",
        quality="720p (mirror)",
        size=size_txt,
    )
    try:
        with open(dest, "rb") as f:
            await context.bot.send_video(
                chat.id, video=f, caption=caption, parse_mode=ParseMode.HTML,
                supports_streaming=True,
                read_timeout=60, write_timeout=600,
                connect_timeout=60, pool_timeout=60,
            )
    except TelegramError as e:
        log.error("cobalt upload failed: %s", e)
        await common.safe_edit(
            status,
            texts.FETCH_FAILED.format(reason="☁️ <b>Upload to Telegram failed.</b> Please try again."),
        )
        _cleanup(dest)
        return True
    _cleanup(dest)
    try:
        await status.delete()
    except Exception:
        pass
    database.increment_download(user.id)
    return True


# ──────────────────────────────────────────────
#  STEP 1: user sends a link → quality menu
# ──────────────────────────────────────────────

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    user = update.effective_user
    chat = update.effective_chat

    # force-join gate before every download
    if not await common.ensure_joined(update, context):
        return

    # one download per user at a time
    if context.user_data.get("busy"):
        await update.effective_message.reply_html(texts.BUSY)
        return

    status = await update.effective_message.reply_html(texts.FETCHING)
    await context.bot.send_chat_action(chat.id, ChatAction.TYPING)

    try:
        info = await asyncio.wait_for(
            asyncio.to_thread(downloader.extract_info, url), timeout=150
        )
    except DownloadCancelled:
        return
    except DownloadError as e:
        if downloader.is_botcheck_error(str(e)):
            await admin.notify_botcheck(context, url)
            # YouTube bot-check → try the cobalt mirror before giving up.
            if downloader._is_youtube(url) and await _cobalt_fallback(update, context, url, status):
                return
        await common.safe_edit(status, texts.FETCH_FAILED.format(reason=utils.clean_error_message(str(e))))
        return
    except asyncio.TimeoutError:
        # Slow extract (proxy rotation used to eat the whole budget) —
        # still try the cobalt mirror before giving up.
        if downloader._is_youtube(url) and await _cobalt_fallback(update, context, url, status):
            return
        await common.safe_edit(status, texts.FETCH_FAILED.format(reason="⏱ <b>Timed out</b> while reading the link."))
        return
    except Exception as e:
        log.exception("extract_info failed")
        await common.safe_edit(status, texts.FETCH_FAILED.format(reason=utils.clean_error_message(str(e))))
        return

    if not info:
        await common.safe_edit(status, texts.FETCH_FAILED.format(reason="⚠️ No video info returned for this link."))
        return

    q = downloader.build_quality_menu(info)
    platform = utils.detect_platform(url)
    meta = {
        "title": info.get("title") or "Video",
        "duration": utils.fmt_duration(info.get("duration")),
        "uploader": info.get("uploader") or info.get("channel") or "Unknown",
        "platform": platform,
        "thumb": info.get("thumbnail"),
    }

    caption = texts.QUALITY_CAPTION.format(
        title=utils.esc(utils.trunc(meta["title"], 70)),
        platform=meta["platform"],
        duration=meta["duration"],
        uploader=utils.esc(utils.trunc(meta["uploader"], 30)),
    )
    if q["note"]:
        caption += "\n" + q["note"]

    keyboard = keyboards.quality_menu(q)

    sent = None
    if meta["thumb"]:
        try:
            sent = await context.bot.send_photo(
                chat.id, photo=meta["thumb"], caption=caption,
                parse_mode=ParseMode.HTML, reply_markup=keyboard,
            )
        except TelegramError:
            sent = None
    if sent is None:
        sent = await context.bot.send_message(
            chat.id, caption, parse_mode=ParseMode.HTML, reply_markup=keyboard
        )

    # cache for callback (per message → old menus expire naturally)
    context.user_data["q"] = {
        "url": url,
        "videos": q["videos"],
        "audios": q["audios"],
        "meta": meta,
        "msg_id": sent.message_id,
    }

    try:
        await status.delete()
    except Exception:
        pass


# ──────────────────────────────────────────────
#  STEP 2: user taps a quality → download + upload
# ──────────────────────────────────────────────

async def on_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""
    user = update.effective_user

    # ---- close menu ----
    if data == "dl:close":
        await query.answer()
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    # ---- cancel running download ----
    if data == "dl:cancel":
        await query.answer("🛑 Cancelling...")
        context.user_data["cancel"] = True
        return

    await query.answer("⚡ Starting download...")
    cache = context.user_data.get("q")

    if not cache or cache.get("msg_id") != query.message.message_id:
        await common.safe_edit(query.message, texts.MENU_EXPIRED)
        return

    if context.user_data.get("busy"):
        await query.answer("⏳ A download is already running!", show_alert=True)
        return

    # force-join gate again (cheap)
    pending = await common.not_joined_channels(context.bot, user.id)
    if pending:
        await query.answer("🔒 Join all required channels first!", show_alert=True)
        return

    mode = data.split(":")[1]          # "v" or "a"
    index = int(data.split(":")[2])
    try:
        if mode == "v":
            choice = cache["videos"][index]
            format_id, kbps = choice["format_id"], None
            quality_label = choice["label"]
        else:
            choice = cache["audios"][index]
            format_id, kbps = None, choice["kbps"]
            quality_label = choice["label"]
    except (IndexError, KeyError):
        await common.safe_edit(query.message, texts.MENU_EXPIRED)
        return

    url = cache["url"]
    meta = cache["meta"]
    title = meta["title"]
    title_short = utils.esc(utils.trunc(title, 42))

    context.user_data["busy"] = True
    context.user_data["cancel"] = False

    chat_id = update.effective_chat.id

    # remove quality menu, open live progress panel
    try:
        await query.message.delete()
    except Exception:
        pass
    status = await context.bot.send_message(
        chat_id,
        texts.DL_START.format(
            title=title_short, bar=utils.progress_bar(0), pct="0.0",
            done="0 KB", total="—", quality=quality_label,
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.cancel_button(),
    )

    state = {"done": 0, "total": 0, "pct": 0.0, "phase": "downloading"}

    def progress_hook(d):
        if d.get("status") == "downloading":
            state["phase"] = "downloading"
            state["done"] = d.get("downloaded_bytes") or 0
            state["total"] = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            if state["total"]:
                state["pct"] = state["done"] * 100.0 / state["total"]
        elif d.get("status") == "finished":
            state["phase"] = "processing"
            state["pct"] = 100.0

    loop = asyncio.get_running_loop()
    worker = partial(
        downloader.download, url, mode,
        format_id=format_id, audio_kbps=kbps or 320,
        progress_hook=progress_hook,
        cancel_check=lambda: bool(context.user_data.get("cancel")),
    )
    fut = loop.run_in_executor(_get_pool(context), worker)

    async def progress_editor():
        """Live bar+percent animation while downloading."""
        while not fut.done():
            await asyncio.sleep(config.PROGRESS_INTERVAL)
            if state["phase"] == "processing":
                await common.safe_edit(
                    status,
                    texts.PROCESSING.format(title=title_short),
                )
            else:
                total_txt = utils.human_size(state["total"]) if state["total"] else "—"
                await common.safe_edit(
                    status,
                    texts.DL_START.format(
                        title=title_short,
                        bar=utils.progress_bar(state["pct"]),
                        pct=f"{state['pct']:.1f}",
                        done=utils.human_size(state["done"]),
                        total=total_txt,
                        quality=quality_label,
                    ),
                    reply_markup=keyboards.cancel_button(),
                )

    editor_task = asyncio.create_task(progress_editor())

    filepath, dl_info = None, None
    try:
        filepath, dl_info = await fut
    except DownloadCancelled:
        pass
    except DownloadError as e:
        log.warning("download failed: %s", e)
        if downloader.is_botcheck_error(str(e)):
            await admin.notify_botcheck(context, url)
        await common.safe_edit(
            status,
            texts.FETCH_FAILED.format(reason=utils.clean_error_message(str(e))),
        )
        return
    except Exception as e:
        log.exception("download crashed")
        await common.safe_edit(
            status,
            texts.FETCH_FAILED.format(reason=utils.clean_error_message(str(e))),
        )
        return
    finally:
        context.user_data["busy"] = False
        editor_task.cancel()
        try:
            await editor_task
        except (asyncio.CancelledError, Exception):
            pass

    if not filepath or not os.path.exists(filepath):
        await common.safe_edit(status, texts.CANCELLED)
        return

    # ── size guard (50 MB bot API limit) ──
    file_size = os.path.getsize(filepath)
    if file_size > config.MAX_FILESIZE_MB * 1024 * 1024:
        try:
            os.remove(filepath)
        except OSError:
            pass
        await common.safe_edit(
            status, texts.TOO_BIG.format(size=utils.human_size(file_size))
        )
        return

    # ── upload with spinner animation ──
    size_txt = utils.human_size(file_size)
    await common.safe_edit(
        status,
        texts.UPLOADING.format(title=title_short, size=size_txt, spinner=utils.spinner_at(0)),
        reply_markup=None,
    )

    spinner_on = {"run": True}

    async def upload_spinner():
        i = 0
        action = ChatAction.UPLOAD_VOICE if mode == "audio" else ChatAction.UPLOAD_VIDEO
        while spinner_on["run"]:
            await context.bot.send_chat_action(chat_id, action)
            await common.safe_edit(
                status,
                texts.UPLOADING.format(
                    title=title_short, size=size_txt, spinner=utils.spinner_at(i)
                ),
            )
            i += 1
            await asyncio.sleep(2.0)

    spinner_task = asyncio.create_task(upload_spinner())

    caption = (
        texts.AUDIO_DONE if mode == "audio" else texts.VIDEO_DONE
    ).format(
        title=utils.esc(utils.trunc(title, 60)),
        platform=meta["platform"],
        quality=quality_label,
        size=size_txt,
    )

    try:
        with open(filepath, "rb") as f:
            if mode == "audio":
                cover = downloader.find_cover_art(dl_info or {})
                thumb = open(cover, "rb") if cover else None
                try:
                    try:
                        await context.bot.send_audio(
                            chat_id,
                            audio=f,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            title=utils.trunc(title, 60),
                            performer=utils.trunc(meta["uploader"], 30),
                            thumb=thumb,
                            read_timeout=60,
                            write_timeout=600,
                            connect_timeout=60,
                            pool_timeout=60,
                        )
                    except TelegramError:
                        if thumb:
                            # retry without cover art (thumbnail too big etc.)
                            f.seek(0)
                            await context.bot.send_audio(
                                chat_id,
                                audio=f,
                                caption=caption,
                                parse_mode=ParseMode.HTML,
                                title=utils.trunc(title, 60),
                                performer=utils.trunc(meta["uploader"], 30),
                                read_timeout=60,
                                write_timeout=600,
                                connect_timeout=60,
                                pool_timeout=60,
                            )
                finally:
                    if thumb:
                        thumb.close()
            else:
                try:
                    await context.bot.send_video(
                        chat_id,
                        video=f,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        supports_streaming=True,
                        read_timeout=60,
                        write_timeout=600,
                        connect_timeout=60,
                        pool_timeout=60,
                    )
                except TelegramError as e:
                    if "thumb" in str(e).lower():
                        f.seek(0)
                        await context.bot.send_video(
                            chat_id,
                            video=f,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            supports_streaming=True,
                            read_timeout=60,
                            write_timeout=600,
                            connect_timeout=60,
                            pool_timeout=60,
                        )
                    else:
                        raise
    except TelegramError as e:
        log.error("upload failed: %s", e)
        spinner_on["run"] = False
        await common.safe_edit(
            status,
            texts.FETCH_FAILED.format(reason="☁️ <b>Upload to Telegram failed.</b> Please try again."),
        )
        _cleanup(filepath)
        return
    finally:
        spinner_on["run"] = False
        spinner_task.cancel()
        try:
            await spinner_task
        except (asyncio.CancelledError, Exception):
            pass

    _cleanup(filepath)

    try:
        await status.delete()
    except Exception:
        pass

    database.increment_download(user.id)


def _cleanup(filepath: str):
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except OSError:
        pass
