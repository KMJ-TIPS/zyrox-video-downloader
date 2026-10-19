#!/data/data/com.termux/files/usr/bin/bash
# ⚡ ZYROX VIDEO DOWNLOADER — Termux runner (keeps bot alive 24/7)
cd "$(dirname "$0")"

# prevent Android from killing the bot
termux-wake-lock 2>/dev/null || true

export PYTHONUNBUFFERED=1
python bot.py
