# ⚡ ZYROX VIDEO DOWNLOADER

> **All-in-One Social Media Downloader Telegram Bot**
> 🎵 MP3 • 🎥 MP4 • HD • 2K • 4K — YouTube, Instagram, TikTok, Facebook & 1000+ sites

---

## ✨ Features

| | |
|---|---|
| 🎬 **All qualities** | Video up to 4K + MP3 128/192/320 kbps |
| 📊 **Live progress** | Animated bar ▓▓▓░░ + percentage, size shown live |
| 🖼 **Thumbnail menu** | Video thumbnail + title + duration + size on every button |
| 🌐 **1000+ sites** | Powered by yt-dlp (YouTube, Insta, TikTok, FB, X...) |
| 🔒 **Force join** | Built-in `@Zyroxv1` + unlimited extra channels from admin panel |
| 👑 **Admin panel** | Broadcast, user list + .txt export, channel manager, stats |
| 🆕 **New user alerts** | Admins get instant notifications |
| 🛡 **Safe** | Flood-safe edits, per-user queue, auto temp cleanup, 50 MB guard |

---

## 📱 Install on Termux (Android)

```bash
# 1. Install Termux from F-Droid: https://f-droid.org/en/packages/com.termux/

# 2. Enter the project folder
cd zyrox-video-downloader

# 3. One-click install
bash install_termux.sh

# 4. Add your bot token
nano config.py        # → BOT_TOKEN = "123456:ABC..."

# 5. Run 24/7
bash run.sh
```

**Get a token:** open [@BotFather](https://t.me/BotFather) → `/newbot` → copy token.

**Make the bot admin** in your force-join channels (`@Zyroxv1` and any you add later) — otherwise membership cannot be checked.

---

## 👑 First owner

The **first user who presses /start** becomes the owner automatically.
For extra security also paste your ID in `config.py → ADMIN_IDS`.
Not sure of your ID? Send `/id` to the bot.

---

## 👑 Admin Panel (`/admin`)

| Button | What it does |
|---|---|
| 📢 **BROADCAST** | Send any message (text/photo/video) to **all users** with live progress |
| 👥 **USER LIST** | Total + active users, export full list as `.txt` |
| ➕ **ADD CHANNEL** | Add force-join channel: `@handle`, `t.me/link` or `-100...` ID |
| 📋 **CHANNEL LIST** | See all channels, 🗑 tap to remove (built-in `@Zyroxv1` stays) |
| 🔄 **REFRESH** | Reload live stats |

---

## 🎬 How it works

```
1. User sends link  →  🖼 thumbnail + quality buttons with sizes
2. User taps quality →  ▓▓▓▓░░░░ 45.2%  📦 12.4 MB / 27.5 MB
3. Merge (ffmpeg)    →  ⚙️ PROCESSING...
4. Upload            →  ☁️ UPLOADING with spinner
5. Delivered!        →  ✅ video (streamable) / MP3 with cover art
```

Max upload: **50 MB** (Telegram bot limit) — bigger quality buttons are hidden automatically.

---

## ⚙️ config.py

```python
BOT_TOKEN          = "your-token"        # required
ADMIN_IDS          = []                  # owner IDs (auto-claims first /start if empty)
DEFAULT_CHANNELS   = ["@Zyroxv1"]        # built-in force-join
MAX_FILESIZE_MB    = 50
COOKIES_FILE       = ""                  # optional cookies.txt for Instagram etc.
```

---

## 🐧 VPS (Ubuntu) quick start

```bash
sudo apt update && sudo apt install -y python3-pip ffmpeg
pip3 install -r requirements.txt
nano config.py          # add token
python3 bot.py
```

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot verify membership` warning | Make the bot **admin** in the force-join channel |
| Instagram link fails | Content may be private — try `COOKIES_FILE` in config |
| Download stuck at 0% | `pip install -U yt-dlp` (extractors update weekly) |
| Force-join not unlocking | User must tap **✅ I'VE JOINED — VERIFY** after joining |

---

## ⚠️ Disclaimer

For personal / educational use only. Respect copyright — download only content you have the right to save. ZYROX is not affiliated with any platform.
