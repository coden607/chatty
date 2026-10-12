#!/bin/bash
# SUPER SIMPLE AUTOMATION LAUNCHER
# Just run this and press ENTER when prompted

echo "🚀 CHATTY - COMPLETE AUTOMATION SETUP"
echo "======================================"
echo ""
echo "This will set up everything automatically."
echo "Just press ENTER at each step!"
echo ""
echo "Press ENTER to start..."
read

cd "$(dirname "$0")"
python3 ONE_CLICK_SETUP.py

echo ""
echo "✅ Setup complete!"
echo ""
