#!/bin/bash
# SHOW AUTOMATION STATUS
# Quick visual status display

clear

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    🚀 CHATTY AUTOMATION STATUS                             ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if automation is running
if pgrep -f "START_COMPLETE_AUTOMATION" > /dev/null; then
    echo "  ✅ Automation:        🟢 RUNNING"
else
    echo "  ❌ Automation:        🔴 STOPPED"
fi

# Check if API server is running
if pgrep -f "AUTOMATION_API_SERVER" > /dev/null; then
    echo "  ✅ API Server:        🟢 RUNNING"
else
    echo "  ❌ API Server:        🔴 STOPPED"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                         📊 QUICK STATS                                     ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Count generated files
if [ -d "generated_content" ]; then
    FILE_COUNT=$(find generated_content -type f | wc -l)
    echo "  📄 Generated Files:   $FILE_COUNT"
else
    echo "  📄 Generated Files:   0"
fi

# Check log size
if [ -f "logs/complete_automation.log" ]; then
    LOG_SIZE=$(du -h logs/complete_automation.log | cut -f1)
    echo "  📋 Log Size:          $LOG_SIZE"
else
    echo "  📋 Log Size:          N/A"
fi

# Check API keys
if [ -f "$HOME/.config/chatty/secrets.env" ]; then
    KEY_COUNT=$(grep -c "API_KEY\|TOKEN" "$HOME/.config/chatty/secrets.env" 2>/dev/null || echo "0")
    echo "  🔑 API Keys:          $KEY_COUNT configured"
else
    echo "  🔑 API Keys:          Not configured"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                       🎯 QUICK COMMANDS                                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "  Setup:       ./AUTOMATE_EVERYTHING.sh"
echo "  Status:      python3 check_automation_status.py"
echo "  Dashboard:   http://localhost:5000"
echo "  Leads:       http://localhost:5000/leads"
echo "  Logs:        tail -f logs/automation.log"
echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    ✨ AUTOMATION FEATURES                                  ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "  ✅ AI-powered content generation"
echo "  ✅ Grant proposal writing"
echo "  ✅ Lead acquisition & conversion"
echo "  ✅ Social media automation"
echo "  ✅ Revenue generation (24/7)"
echo "  ✅ Customer acquisition"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
