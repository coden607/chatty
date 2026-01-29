#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SYSTEMD_DIR="$HOME/.config/systemd/user"
AUTOMATION_SERVICE="chatty-automation.service"
API_SERVICE="chatty-api.service"
UI_SERVICE="chatty-ui.service"
AUTOPILOT_SERVICE="chatty-autopilot.service"
AUTOPILOT_TIMER="chatty-autopilot.timer"
TRENDS_SERVICE="chatty-trends.service"
TRENDS_TIMER="chatty-trends.timer"

install_systemd_units() {
  mkdir -p "$SYSTEMD_DIR"
  sed "s|__CHATTY_ROOT__|$ROOT|g" "$ROOT/systemd/$AUTOMATION_SERVICE" > "$SYSTEMD_DIR/$AUTOMATION_SERVICE"
  sed "s|__CHATTY_ROOT__|$ROOT|g" "$ROOT/systemd/$API_SERVICE" > "$SYSTEMD_DIR/$API_SERVICE"
  sed "s|__CHATTY_ROOT__|$ROOT|g" "$ROOT/systemd/$UI_SERVICE" > "$SYSTEMD_DIR/$UI_SERVICE"
  sed "s|__CHATTY_ROOT__|$ROOT|g" "$ROOT/systemd/$AUTOPILOT_SERVICE" > "$SYSTEMD_DIR/$AUTOPILOT_SERVICE"
  cp "$ROOT/systemd/$AUTOPILOT_TIMER" "$SYSTEMD_DIR/$AUTOPILOT_TIMER"
  sed "s|__CHATTY_ROOT__|$ROOT|g" "$ROOT/systemd/$TRENDS_SERVICE" > "$SYSTEMD_DIR/$TRENDS_SERVICE"
  cp "$ROOT/systemd/$TRENDS_TIMER" "$SYSTEMD_DIR/$TRENDS_TIMER"
}

start_systemd_units() {
  systemctl --user daemon-reload
  systemctl --user enable --now "$AUTOMATION_SERVICE"
  systemctl --user enable --now "$API_SERVICE"
  systemctl --user enable --now "$UI_SERVICE"
  systemctl --user enable --now "$AUTOPILOT_TIMER"
  systemctl --user enable --now "$TRENDS_TIMER"
}

fallback_start() {
  "$ROOT/chatty_daemon.sh" start
}

echo "Chatty single-click installer"
echo "Root: $ROOT"

install_systemd_units

if command -v systemctl >/dev/null 2>&1; then
  if systemctl --user status >/dev/null 2>&1; then
    start_systemd_units
    echo "Installed and started systemd user services."
    exit 0
  fi
fi

echo "systemd user services unavailable. Falling back to local daemon."
fallback_start
echo "Chatty started via local daemon."
