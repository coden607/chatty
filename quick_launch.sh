#!/bin/bash
# CHATTY Quick Launch Script

cd "$(dirname "$0")"
source .venv/bin/activate
export $(cat .env | grep -v "^#" | xargs)

echo "================================================================================"
echo "🚀 CHATTY QUICK LAUNCH"
echo "================================================================================"
echo ""
echo "Starting CHATTY with all features enabled:"
echo "  • OpenClaw - File chunking & self-repair"
echo "  • YouTube Learning - Video transcript analysis"
echo "  • TokenSpin - Token management & routing"
echo "  • NVIDIA Kimi K2.5 - Real data AI orchestration"
echo "  • Unified AI - Multi-framework orchestration"
echo "  • Archon2 - 14-agent hierarchy"
echo "  • Agent Zero - Fleet management"
echo ""
echo "================================================================================"

python3 START_COMPLETE_AUTOMATION.py
