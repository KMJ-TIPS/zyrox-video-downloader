#!/data/data/com.termux/files/usr/bin/bash
# Bot dobara chalane ke liye: bash termux/run.sh
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
# shellcheck disable=SC1091
. venv/bin/activate
termux-wake-lock 2>/dev/null || true
python bot.py
