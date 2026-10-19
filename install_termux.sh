#!/data/data/com.termux/files/usr/bin/bash
# ⚡ ZYROX VIDEO DOWNLOADER — Termux one-click installer
set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ⚡ ZYROX VIDEO DOWNLOADER — INSTALLER   ║"
echo "║        Termux • Android • 24/7           ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 1. system packages
echo "📦 [1/4] Installing system packages (python, ffmpeg)..."
pkg update -y
pkg install -y python ffmpeg

# 2. pip upgrade
echo "🐍 [2/4] Upgrading pip..."
pip install --upgrade pip

# 3. python requirements
echo "📚 [3/4] Installing python-telegram-bot + yt-dlp..."
pip install -r requirements.txt

# 4. folders
mkdir -p downloads

echo ""
echo "✅ INSTALL COMPLETE!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 NEXT STEPS:"
echo ""
echo "1. Get your bot token from @BotFather (Telegram)"
echo "2. Open config.py and paste it:"
echo "      nano config.py"
echo "      → BOT_TOKEN = \"123456:ABC-your-token\""
echo "3. Start the bot:"
echo "      bash run.sh"
echo ""
echo "💡 First user to press /start becomes the owner!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
