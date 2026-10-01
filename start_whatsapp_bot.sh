#!/bin/bash
# DU 5th Grade WhatsApp Personal Account Bot Launcher

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BRIDGE_DIR="$DIR/whatsapp_bridge"

echo "============================================================"
echo "🤖 DU 5th Grade WhatsApp Personal Account Bot"
echo "============================================================"

# Check for reset flag
if [ "$1" == "--reset" ] || [ "$1" == "--new-qr" ]; then
    echo "🧹 Resetting saved WhatsApp session for fresh QR code pairing..."
    rm -rf "$BRIDGE_DIR/.wwebjs_auth"
fi

# Kill any previous leftover chrome/puppeteer instances for this session
pkill -f "session-du_5th_grade_parent_bot" 2>/dev/null || true
rm -f "$BRIDGE_DIR/.wwebjs_auth/session-du_5th_grade_parent_bot/SingletonLock" 2>/dev/null || true
rm -f "$BRIDGE_DIR/.wwebjs_auth/session-du_5th_grade_parent_bot/SingletonSocket" 2>/dev/null || true

# Ensure latest data is fresh
echo "[1/2] Refreshing weekly scraped dataset..."
python3 "$DIR/agent.py" --run-now

# Navigate to bridge directory
cd "$BRIDGE_DIR"

if [ ! -d "node_modules" ]; then
    echo "[2/2] Installing WhatsApp Web bridge dependencies (one-time setup)..."
    npm install
fi

echo "[2/2] Starting WhatsApp Personal Account Bridge..."
npm start
