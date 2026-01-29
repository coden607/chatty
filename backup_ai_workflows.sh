#!/bin/bash
# AI Workflow Backup & Recovery System

BACKUP_DIR="$HOME/ai_workflow_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "💾 AI WORKFLOW BACKUP & RECOVERY"
echo "================================="

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup N8N workflows
echo "📁 Backing up N8N workflows..."
if [ -d "$HOME/n8n-workflows" ]; then
    tar -czf "$BACKUP_DIR/workflows_$TIMESTAMP.tar.gz" -C "$HOME" n8n-workflows/
    echo "✅ Workflows backed up: workflows_$TIMESTAMP.tar.gz"
else
    echo "⚠️ No N8N workflows directory found"
fi

# Backup API configurations
echo "🔑 Backing up API configurations..."
if [ -f "$HOME/affiliate_api_config.json" ]; then
    cp "$HOME/affiliate_api_config.json" "$BACKUP_DIR/api_config_$TIMESTAMP.json"
    echo "✅ API config backed up: api_config_$TIMESTAMP.json"
fi

# Backup desktop shortcuts
echo "🖥️ Backing up desktop configurations..."
if [ -f "$HOME/.local/share/applications/n8n.desktop" ]; then
    cp "$HOME/.local/share/applications/n8n.desktop" "$BACKUP_DIR/desktop_$TIMESTAMP.desktop"
    echo "✅ Desktop config backed up: desktop_$TIMESTAMP.desktop"
fi

# Create recovery script
cat > "$BACKUP_DIR/recovery_$TIMESTAMP.sh" << 'EOF'
#!/bin/bash
# Recovery script for AI workflows

echo "🔄 RESTORING AI WORKFLOWS..."

# Extract workflows
if [ -f "workflows_*.tar.gz" ]; then
    tar -xzf workflows_*.tar.gz -C "$HOME"
    echo "✅ Workflows restored"
fi

# Restore API config
if [ -f "api_config_*.json" ]; then
    cp api_config_*.json "$HOME/affiliate_api_config.json"
    echo "✅ API config restored"
fi

# Restore desktop shortcut
if [ -f "desktop_*.desktop" ]; then
    cp desktop_*.desktop "$HOME/.local/share/applications/n8n.desktop"
    update-desktop-database "$HOME/.local/share/applications/" 2>/dev/null || true
    echo "✅ Desktop shortcut restored"
fi

echo "🎉 RECOVERY COMPLETE!"
EOF

chmod +x "$BACKUP_DIR/recovery_$TIMESTAMP.sh"

# Clean old backups (keep last 10)
cd "$BACKUP_DIR"
ls -t | tail -n +11 | xargs -r rm -f

echo "✅ Backup complete: $TIMESTAMP"
echo "📍 Location: $BACKUP_DIR"
echo "🔄 Recovery script: recovery_$TIMESTAMP.sh"
echo "🧹 Cleaned old backups (keeping last 10)"
