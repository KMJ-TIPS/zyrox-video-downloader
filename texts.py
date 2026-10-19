"""
⚡ ZYROX VIDEO DOWNLOADER — All bot texts (Premium Dark UI, English)
All texts use HTML parse mode. Dynamic values are inserted with .format()
"""

import config

SEP = "━━━━━━━━━━━━━━━━━━━━"

WELCOME = (
    f"⚡️ <b>ZYROX VIDEO DOWNLOADER</b> 🖤\n"
    f"{SEP}\n"
    "👋 Hey <b>{name}</b>!\n\n"
    "🎬 Send me any video link — I will download it in "
    "<b>your favourite quality</b> with a live progress bar!\n\n"
    "▸ 🎵 MP3  •  🎥 MP4  •  HD  •  2K  •  4K\n"
    "▸ 🌐 YouTube, Instagram, TikTok, Facebook &amp; 1000+ sites\n\n"
    "⚡ <b>Just paste a link to start...</b>"
)

LOCKED = (
    f"🔒 <b>ACCESS LOCKED</b> ⚡\n"
    f"{SEP}\n"
    "👋 Hey <b>{name}</b>!\n\n"
    "To use <b>ZYROX VIDEO DOWNLOADER</b> you must join our "
    "official channel first 👇\n\n"
    "After joining, tap <b>✅ I'VE JOINED</b> to unlock the bot."
)

UNLOCKED = (
    f"✅ <b>ACCESS GRANTED!</b> ⚡\n"
    f"{SEP}\n"
    "🎉 Welcome aboard <b>{name}</b>!\n"
    "🎬 Send me any video link to download."
)

FETCHING = (
    f"⚡️ <b>ZYROX DOWNLOADER</b> 🖤\n"
    f"{SEP}\n"
    "🔍 <b>Fetching link info...</b>\n"
    "📡 Analysing available qualities..."
)

FETCH_FAILED = (
    f"❌ <b>FETCH FAILED</b> ⚡\n"
    f"{SEP}\n"
    "I could not read that link 😕\n\n"
    "{reason}\n\n"
    "💡 Make sure the link is correct and public."
)

QUALITY_CAPTION = (
    f"📥 <b>READY TO DOWNLOAD</b> ⚡\n"
    f"{SEP}\n"
    "🎬 <b>{title}</b>\n\n"
    "📡 Platform: {platform}\n"
    "⏱ Duration: {duration}\n"
    "👤 Source: {uploader}\n\n"
    "⚡ <b>Tap a quality button below 👇</b>\n"
    "💡 Sizes are approximate"
)

DL_START = (
    f"📥 <b>DOWNLOADING...</b> ⚡\n"
    f"{SEP}\n"
    "🎬 {title}\n\n"
    "{bar} <b>{pct}%</b>\n"
    "📦 {done} / {total}\n\n"
    "▸ ⚙️ Quality: {quality}"
)

PROCESSING = (
    f"⚙️ <b>PROCESSING...</b> ⚡\n"
    f"{SEP}\n"
    "🎬 {title}\n\n"
    "🔧 Merging / converting with ffmpeg,\n"
    "almost done — hang tight!"
)

UPLOADING = (
    f"☁️ <b>UPLOADING TO TELEGRAM...</b> ⚡\n"
    f"{SEP}\n"
    "🎬 {title}\n\n"
    "📦 {size}  {spinner}\n\n"
    "▸ Almost there, stay tuned!"
)

VIDEO_DONE = (
    f"✅ <b>DOWNLOAD COMPLETE!</b> ⚡\n"
    f"{SEP}\n"
    "🎬 <b>{title}</b>\n"
    "📡 {platform}\n"
    "⚙️ Quality: {quality}\n"
    "📦 Size: {size}\n\n"
    "🖤 <b>ZYROX VIDEO DOWNLOADER</b>\n"
    f"📢 @{config.UPDATE_CHANNEL}"
)

AUDIO_DONE = (
    f"✅ <b>DOWNLOAD COMPLETE!</b> ⚡\n"
    f"{SEP}\n"
    "🎵 <b>{title}</b>\n"
    "📡 {platform}\n"
    "⚙️ MP3 • {quality} kbps\n"
    "📦 Size: {size}\n\n"
    "🖤 <b>ZYROX VIDEO DOWNLOADER</b>\n"
    f"📢 @{config.UPDATE_CHANNEL}"
)

CANCELLED = (
    f"❌ <b>DOWNLOAD CANCELLED</b> ⚡\n"
    f"{SEP}\n"
    "No problem! Send a new link anytime."
)

TOO_BIG = (
    f"🚫 <b>FILE TOO LARGE</b> ⚡\n"
    f"{SEP}\n"
    "📦 Size: <b>{size}</b>\n"
    "🤖 Telegram bots can upload max <b>50 MB</b>.\n\n"
    "💡 Please choose a <b>lower quality</b>!"
)

BUSY = (
    "⏳ <b>You already have a download running!</b>\n"
    "Please wait or press ❌ CANCEL on it first."
)

MENU_EXPIRED = "⌛ <b>Menu expired!</b> Send the link again ⚡"

NOT_A_LINK = (
    "🤖 <b>Send me a video link!</b> ⚡\n\n"
    "Example:\n"
    "<code>https://youtube.com/watch?v=...</code>\n\n"
    "▸ 🌐 YouTube • Instagram • TikTok • Facebook\n"
    "▸ Twitter/X • Pinterest • Reddit • 1000+ more"
)

HELP = (
    f"❓ <b>HOW TO USE</b> ⚡\n"
    f"{SEP}\n"
    "1️⃣ Copy a video link from any platform\n"
    "2️⃣ Paste it here and send\n"
    "3️⃣ Pick your quality (MP3 or MP4)\n"
    "4️⃣ Watch the live progress bar ⚡\n"
    "5️⃣ Get your file — done! ✅\n\n"
    "📌 <b>Commands</b>\n"
    "/start — Main menu\n"
    "/help — This guide\n"
    "/sites — Supported platforms\n"
    "/about — About the bot\n"
    "/id — Your Telegram ID\n"
    "/admin — Admin panel (admins)\n"
    "/cancel — Cancel current action\n\n"
    "⚠️ Max file size: 50 MB (Telegram bot limit)"
)

ABOUT = (
    f"ℹ️ <b>ABOUT ZYROX</b> ⚡\n"
    f"{SEP}\n"
    "🖤 <b>ZYROX VIDEO DOWNLOADER</b>\n"
    "⚡ All-in-One Social Media Downloader\n\n"
    "▸ 🧩 Version: {version}\n"
    "▸ 🌐 1000+ supported websites\n"
    "▸ 🎵 MP3 64-320 kbps\n"
    "▸ 🎥 MP4 up to 4K*\n"
    "▸ 📊 Live progress bar\n\n"
    "* Max upload 50 MB (bot limit)\n\n"
    "📢 Updates: @{channel}\n"
    "👨‍💻 Powered by ZYROX"
)

SITES = (
    f"🌐 <b>SUPPORTED PLATFORMS</b> ⚡\n"
    f"{SEP}\n"
    "🎬 YouTube\n"
    "📸 Instagram\n"
    "🎵 TikTok\n"
    "👥 Facebook\n"
    "🐦 Twitter / X\n"
    "👻 Snapchat\n"
    "📌 Pinterest\n"
    "👽 Reddit\n"
    "🎥 Vimeo\n"
    "🎧 SoundCloud\n"
    "📺 Dailymotion\n"
    "🎮 Twitch\n"
    "💜 Likee\n"
    "💼 LinkedIn\n\n"
    "➕ Plus <b>1000+ more websites</b> —\n"
    "just send the link and try your luck! ⚡"
)

ACCOUNT = (
    f"👤 <b>MY ACCOUNT</b> ⚡\n"
    f"{SEP}\n"
    "🆔 ID: <code>{uid}</code>\n"
    "👤 Name: {name}\n"
    "🔗 Username: {username}\n"
    "📅 Joined: {joined}\n"
    "📥 Downloads: {downloads}\n\n"
    f"📢 @{config.UPDATE_CHANNEL}"
)

# ───────────────────── ADMIN TEXTS ─────────────────────

ADMIN_PANEL = (
    f"👑 <b>ZYROX ADMIN PANEL</b> ⚡\n"
    f"{SEP}\n"
    "👥 Total Users: <b>{users}</b>\n"
    "🟢 Active (24h): <b>{active}</b>\n"
    "📥 Total Downloads: <b>{downloads}</b>\n"
    "📢 Force-Join Channels: <b>{channels}</b>"
)

ADMIN_DENIED = "⛔ <b>Admins only!</b> This panel is restricted."

BROADCAST_PROMPT = (
    f"📢 <b>BROADCAST MODE</b> ⚡\n"
    f"{SEP}\n"
    "Send me the message you want to broadcast now.\n\n"
    "▸ Text / photo / video / audio — anything works\n"
    "▸ It will be copied to <b>ALL users</b>\n\n"
    "❌ Send /cancel to abort"
)

BROADCAST_PROGRESS = (
    f"📤 <b>BROADCASTING...</b>\n"
    f"{SEP}\n"
    "✅ Sent: <b>{sent}</b> / {total}\n"
    "❌ Failed: <b>{failed}</b>"
)

BROADCAST_DONE = (
    f"✅ <b>BROADCAST COMPLETE!</b> ⚡\n"
    f"{SEP}\n"
    "👥 Total users: <b>{total}</b>\n"
    "✅ Delivered: <b>{sent}</b>\n"
    "❌ Failed / blocked: <b>{failed}</b>"
)

ADD_CHANNEL_PROMPT = (
    f"➕ <b>ADD FORCE-JOIN CHANNEL</b> ⚡\n"
    f"{SEP}\n"
    "Send me the channel now:\n\n"
    "▸ @username (public), e.g. <code>@mychannel</code>\n"
    "▸ or t.me link: <code>https://t.me/mychannel</code>\n"
    "▸ or channel ID: <code>-1001234567890</code> (private)\n\n"
    "⚠️ The bot must be <b>admin</b> in that channel!\n"
    "❌ Send /cancel to abort"
)

CHANNEL_ADDED = (
    f"✅ <b>CHANNEL ADDED!</b> ⚡\n"
    f"{SEP}\n"
    "📢 Channel: <b>{title}</b>\n"
    "🔗 Handle: <code>{handle}</code>\n\n"
    "All users must now join it to use the bot 🔒"
)

CHANNELS_LIST = (
    f"📋 <b>FORCE-JOIN CHANNELS</b> ⚡\n"
    f"{SEP}\n"
    "⚡ = built-in (cannot be removed)\n"
    "🗑 Tap a button to remove a channel\n\n"
    "{list}"
)

CHANNELS_EMPTY = "No extra channels added yet.\nUse ➕ ADD CHANNEL below."

USERS_PAGE = (
    f"👥 <b>USER LIST</b> ⚡\n"
    f"{SEP}\n"
    "👥 Total users: <b>{total}</b>\n"
    "🟢 Active (24h): <b>{active}</b>\n\n"
    "Export the full list as a .txt file 👇"
)

NEW_USER_ALERT = (
    f"🆕 <b>NEW USER ALERT!</b> ⚡\n"
    f"{SEP}\n"
    "👤 Name: {name}\n"
    "🔗 Username: {username}\n"
    "🆔 ID: <code>{uid}</code>\n"
    "👥 Total users now: <b>{total}</b>"
)

MODE_CANCELLED = "❌ <b>Cancelled.</b> Back to normal mode ⚡"

ADMIN_ERR_CHANNEL = (
    "❌ <b>Could not find that channel!</b>\n\n"
    "Check these:\n"
    "▸ Handle/link is correct\n"
    "▸ The bot is added as <b>admin</b> there\n"
    "▸ For private channels use the <code>-100...</code> ID"
)
