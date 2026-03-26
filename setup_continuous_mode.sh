#!/bin/bash
# CHATTY Continuous Mode Setup Script
# Sets up CHATTY to run 24/7 with all features

set -e

echo "================================================================================"
echo "🚀 CHATTY CONTINUOUS MODE SETUP"
echo "================================================================================"
echo ""
echo "This will configure CHATTY to:"
echo "  ✅ Run 24/7 as a systemd service"
echo "  ✅ Auto-restart on failure"
echo "  ✅ Auto-rotate API keys (OpenRouter, xAI)"
echo "  ✅ Monitor OpenClaw, Nemoclaw, Agent Zero health"
echo "  ✅ Collect metrics every 5 minutes"
echo "  ✅ Generate hourly status reports"
echo ""
echo "================================================================================"

# Get CHATTY root directory
CHATTY_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$CHATTY_ROOT"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Run setup first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

echo ""
echo "🔧 Step 1: Checking API Keys..."
echo "================================================================================"
python3 ENHANCED_AUTO_SETUP.py --status

echo ""
echo "🔧 Step 2: Testing Component Initialization..."
echo "================================================================================"

# Test key components
test_component() {
    local name=$1
    local import_test=$2
    
    if python3 -c "$import_test" 2>/dev/null; then
        echo "  ✅ $name"
        return 0
    else
        echo "  ⚠️  $name (will use fallback)"
        return 1
    fi
}

test_component "OpenClaw" "from openclaw_integration import FileChunker, SelfRepairEngine"
test_component "NVIDIA Nemoclaw" "from NVIDIA_REAL_AI_ORCHESTRATION import get_orchestrator"
test_component "Agent Zero" "from AGENT_ZERO_FLEET import AgentZeroFleet"
test_component "Archon2" "from ARCHON2_ORCHESTRATION import Archon2Orchestrator"
test_component "Unified AI" "from UNIFIED_AI_ORCHESTRATION import UnifiedAIOrchestrator"
test_component "YouTube Learning" "from REAL_YOUTUBE_LEARNER import RealYouTubeLearner"
test_component "TokenSpin" "from TOKENSPIN_BRIDGE import TokenspinBridge"
test_component "Model Router" "from CHATTY_MODEL_ROUTER import ModelRouter"

echo ""
echo "🔧 Step 3: Setting up systemd services..."
echo "================================================================================"

# Create user systemd directory
USER_SYSTEMD="$HOME/.config/systemd/user"
mkdir -p "$USER_SYSTEMD"

# Main CHATTY continuous service
cat > "$USER_SYSTEMD/chatty-continuous.service" << EOF
[Unit]
Description=CHATTY Continuous Mode - 24/7 AI Automation
Documentation=https://github.com/coden809/chatty
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$CHATTY_ROOT
Environment=CHATTY_SECRETS_FILE=%h/.config/chatty/secrets.env
Environment=CHATTY_OFFLINE_MODE=false
Environment=CHATTY_SUPERVISOR_INTERVAL_SECONDS=15
Environment=CHATTY_RESTART_LIMIT=5
Environment=CHATTY_RESTART_WINDOW_SECONDS=300
Environment=PATH=/usr/local/bin:/usr/bin:/bin:$CHATTY_ROOT/.venv/bin
Environment=PYTHONPATH=$CHATTY_ROOT
Environment=HOME=%h
Environment=USER=%u

# Use virtual environment Python
ExecStart=$CHATTY_ROOT/.venv/bin/python $CHATTY_ROOT/CHATTY_CONTINUOUS_MODE.py

# Auto-restart configuration
Restart=always
RestartSec=10
StartLimitInterval=300
StartLimitBurst=5

# Graceful shutdown
TimeoutStopSec=30
KillSignal=SIGTERM

# Resource limits (adjust based on your system)
LimitNOFILE=65536
MemoryMax=6G
CPUQuota=90%

# Logging
StandardOutput=append:$CHATTY_ROOT/logs/chatty-continuous.log
StandardError=append:$CHATTY_ROOT/logs/chatty-continuous-error.log

# Security
NoNewPrivileges=false
ProtectSystem=false
ProtectHome=false

[Install]
WantedBy=default.target
EOF

echo "  ✅ Created: chatty-continuous.service"

# API Key health check timer
cat > "$USER_SYSTEMD/chatty-key-rotation.timer" << EOF
[Unit]
Description=CHATTY API Key Rotation Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "  ✅ Created: chatty-key-rotation.timer"

# Key rotation service
cat > "$USER_SYSTEMD/chatty-key-rotation.service" << EOF
[Unit]
Description=CHATTY API Key Health Check & Rotation

[Service]
Type=oneshot
WorkingDirectory=$CHATTY_ROOT
Environment=CHATTY_SECRETS_FILE=%h/.config/chatty/secrets.env
Environment=PATH=/usr/local/bin:/usr/bin:/bin:$CHATTY_ROOT/.venv/bin
ExecStart=$CHATTY_ROOT/.venv/bin/python $CHATTY_ROOT/ENHANCED_AUTO_SETUP.py --check-keys
StandardOutput=append:$CHATTY_ROOT/logs/key-rotation.log
EOF

echo "  ✅ Created: chatty-key-rotation.service"

# Metrics collection timer
cat > "$USER_SYSTEMD/chatty-metrics.timer" << EOF
[Unit]
Description=CHATTY Metrics Collection Timer

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "  ✅ Created: chatty-metrics.timer"

# Enable user lingering (services run after logout)
echo ""
echo "🔧 Step 4: Enabling user lingering..."
echo "================================================================================"
if ! loginctl show-user "$USER" | grep -q "Linger=yes"; then
    loginctl enable-linger "$USER"
    echo "  ✅ User lingering enabled"
else
    echo "  ✅ User linger already enabled"
fi

# Reload systemd
echo ""
echo "🔧 Step 5: Reloading systemd..."
echo "================================================================================"
systemctl --user daemon-reload
echo "  ✅ Systemd daemon reloaded"

# Create log directory
mkdir -p "$CHATTY_ROOT/logs"

echo ""
echo "================================================================================"
echo "✅ CHATTY CONTINUOUS MODE SETUP COMPLETE"
echo "================================================================================"
echo ""
echo "📋 AVAILABLE COMMANDS:"
echo ""
echo "  Start CHATTY:"
echo "    systemctl --user start chatty-continuous"
echo ""
echo "  Stop CHATTY:"
echo "    systemctl --user stop chatty-continuous"
echo ""
echo "  Check Status:"
echo "    systemctl --user status chatty-continuous"
echo ""
echo "  View Logs:"
echo "    journalctl --user -u chatty-continuous -f"
echo "    tail -f $CHATTY_ROOT/logs/chatty-continuous.log"
echo ""
echo "  Enable Auto-Start (on boot):"
echo "    systemctl --user enable chatty-continuous"
echo ""
echo "  Disable Auto-Start:"
echo "    systemctl --user disable chatty-continuous"
echo ""
echo "  Check API Keys:"
echo "    systemctl --user start chatty-key-rotation"
echo ""
echo "  View All Timers:"
echo "    systemctl --user list-timers"
echo ""
echo "================================================================================"
echo ""
read -p "🚀 Start CHATTY now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting CHATTY Continuous Mode..."
    systemctl --user start chatty-continuous
    sleep 2
    echo ""
    echo "Status:"
    systemctl --user status chatty-continuous --no-pager
    echo ""
    echo "📊 View logs: journalctl --user -u chatty-continuous -f"
fi

echo ""
echo "🎉 Setup complete! CHATTY is ready for 24/7 operation."
echo ""
