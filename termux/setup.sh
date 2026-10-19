#!/data/data/com.termux/files/usr/bin/bash
# ZYROX VIDEO DOWNLOADER — Termux setup (polling mode)
# Phone ka IP residential hota hai, isliye YouTube bot-check nahi aata.
# Vercel wala bot sirf PO-token server ke liye rehta hai (POT_SERVER_URL).
set -e
echo "== 1/5 packages =="
pkg update -y
pkg install -y python git ffmpeg
echo "== 2/5 repo =="
if [ ! -d zyrox-video-downloader ]; then
  git clone https://github.com/KMJ-TIPS/zyrox-video-downloader
fi
cd zyrox-video-downloader
git pull --ff-only || true
echo "== 3/5 venv + deps =="
[ -d venv ] || python -m venv venv
# shellcheck disable=SC1091
. venv/bin/activate
pip install -U pip
pip install -r requirements.txt
echo "== 4/5 config =="
if [ ! -f .env ]; then
  read -rp "BOT_TOKEN: " BOT_TOKEN
  read -rp "ADMIN_IDS [8923702128]: " ADMIN_IDS
  ADMIN_IDS=${ADMIN_IDS:-8923702128}
  cat > .env <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS
POT_SERVER_URL=https://zyrox-video-downloader.vercel.app/api/pot
MAX_FILESIZE_MB=50
EOF
  echo ".env likha gaya."
fi
echo "== 5/5 webhook hatana (polling ke liye zaroori) =="
set -a; . ./.env; set +a
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook?drop_pending_updates=true" | head -c 200; echo
echo "== Bot start ho raha hai (band karne ke liye Ctrl+C) =="
termux-wake-lock 2>/dev/null || true
python bot.py
