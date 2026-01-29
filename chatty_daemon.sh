#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$ROOT/runtime"
CHAT_PID="$RUNTIME_DIR/chatty.pid"
API_PID="$RUNTIME_DIR/api.pid"
CHAT_LOG="$RUNTIME_DIR/chatty.out"
API_LOG="$RUNTIME_DIR/api.out"

SECRETS_FILE="${CHATTY_SECRETS_FILE:-$HOME/.config/chatty/secrets.env}"

is_running() {
  local pid_file="$1"
  if [ -f "$pid_file" ]; then
    local pid
    pid="$(cat "$pid_file")"
    if ps -p "$pid" >/dev/null 2>&1; then
      return 0
    fi
  fi
  return 1
}

start_services() {
  mkdir -p "$RUNTIME_DIR"
  if [ -f "$SECRETS_FILE" ]; then
    export CHATTY_SECRETS_FILE="$SECRETS_FILE"
  else
    echo "Warning: secrets file not found at $SECRETS_FILE" >&2
  fi

  if is_running "$CHAT_PID"; then
    echo "Chatty automation already running."
  else
    cd "$ROOT"
    nohup ./python3 START_COMPLETE_AUTOMATION.py >"$CHAT_LOG" 2>&1 &
    echo $! >"$CHAT_PID"
    echo "Started Chatty automation (pid $(cat "$CHAT_PID"))."
  fi

  if is_running "$API_PID"; then
    echo "API server already running."
  else
    cd "$ROOT"
    nohup ./python3 -m uvicorn AUTOMATION_API_SERVER:app --host 0.0.0.0 --port 8080 >"$API_LOG" 2>&1 &
    echo $! >"$API_PID"
    echo "Started API server (pid $(cat "$API_PID"))."
  fi
}

stop_services() {
  if is_running "$CHAT_PID"; then
    kill "$(cat "$CHAT_PID")"
    rm -f "$CHAT_PID"
    echo "Stopped Chatty automation."
  else
    echo "Chatty automation not running."
  fi

  if is_running "$API_PID"; then
    kill "$(cat "$API_PID")"
    rm -f "$API_PID"
    echo "Stopped API server."
  else
    echo "API server not running."
  fi
}

status_services() {
  if is_running "$CHAT_PID"; then
    echo "Chatty automation running (pid $(cat "$CHAT_PID"))."
  else
    echo "Chatty automation stopped."
  fi

  if is_running "$API_PID"; then
    echo "API server running (pid $(cat "$API_PID"))."
  else
    echo "API server stopped."
  fi
}

case "${1:-}" in
  start)
    start_services
    ;;
  stop)
    stop_services
    ;;
  restart)
    stop_services
    start_services
    ;;
  status)
    status_services
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
