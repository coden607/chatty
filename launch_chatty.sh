#!/bin/bash
# Chatty One-Click Launcher

# Change to the project directory
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Activate the virtual environment

# Use external secrets file if present
SECRETS_FILE="${CHATTY_SECRETS_FILE:-$HOME/.config/chatty/secrets.env}"
if [ -f "$SECRETS_FILE" ]; then
  export CHATTY_SECRETS_FILE="$SECRETS_FILE"
else
  echo "Warning: secrets file not found at $SECRETS_FILE" >&2
fi


echo "===================================================="
echo "🚀 OPEN NARCOGUARD APP: https://v0-narcoguard-pwa-build.vercel.app"
echo "===================================================="
echo ""

# Start the complete automation system
./python3 START_COMPLETE_AUTOMATION.py

echo ""
echo "===================================================="
echo "🛑 Execution finished or interrupted."
echo "Press Enter to close this terminal..."
echo "===================================================="
read
