#!/bin/bash
set -euo pipefail

API_BASE="${CHATTY_API_BASE:-http://localhost:8080}"

usage() {
  cat <<'EOF'
Chatty CLI (local terminal control)

Usage:
  ./chatty_cli.sh status
  ./chatty_cli.sh start-autonomy
  ./chatty_cli.sh stop-autonomy
  ./chatty_cli.sh autopilot
  ./chatty_cli.sh wizard
  ./chatty_cli.sh queue-task "Title" [owner] [priority]
  ./chatty_cli.sh plan-campaign "Name" "Channel" "Goal"
  ./chatty_cli.sh create-n8n "Name" ["Description"] ["Trigger"]
  ./chatty_cli.sh prompt-all "Message"
  ./chatty_cli.sh message "Operator note"
  ./chatty_cli.sh feedback "Outcome" score [notes]
  ./chatty_cli.sh ingest-trends "Source" trends.json
  ./chatty_cli.sh okr "Cycle" "Focus1,Focus2,Focus3"
  ./chatty_cli.sh grant "Name" "Deadline"
  ./chatty_cli.sh experiment "Name" "Metric"
  ./chatty_cli.sh pilot-calc devices cost_per_device savings_per_case cases
  ./chatty_cli.sh proposal "Title" [context]
  ./chatty_cli.sh press "Angle"
  ./chatty_cli.sh video "Topic"
  ./chatty_cli.sh refresh-pipelines
  ./chatty_cli.sh workflows
  ./chatty_cli.sh agents
  ./chatty_cli.sh tasks
  ./chatty_cli.sh campaigns

Environment:
  CHATTY_API_BASE=http://localhost:8080
EOF
}

require_arg() {
  if [ -z "${2:-}" ]; then
    echo "Missing required argument: $1" >&2
    exit 1
  fi
}

json_post() {
  local endpoint="$1"
  local payload="$2"
  curl -sS -H "Content-Type: application/json" -d "$payload" "$API_BASE$endpoint"
  echo ""
}

json_escape() {
  ./python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"
}

json_build_kv() {
  local key="$1"
  local value="$2"
  printf '"%s":%s' "$key" "$(json_escape "$value")"
}

require_api() {
  if ! curl -sS "$API_BASE/api/health" >/dev/null; then
    echo "API not reachable at $API_BASE. Start it first." >&2
    exit 1
  fi
}

case "${1:-}" in
  status)
    curl -sS "$API_BASE/api/status"
    echo ""
    ;;
  start-autonomy)
    require_api
    curl -sS -X POST "$API_BASE/api/autonomy/start"
    echo ""
    ;;
  stop-autonomy)
    require_api
    curl -sS -X POST "$API_BASE/api/autonomy/stop"
    echo ""
    ;;
  autopilot)
    require_api
    curl -sS -X POST "$API_BASE/api/autonomy/start" >/dev/null
    json_post "/api/tasks" "{$(json_build_kv "title" "Run NarcoGuard outreach sprint"),$(json_build_kv "owner" "acquisition_engine"),\"priority\":\"high\"}"
    json_post "/api/tasks" "{$(json_build_kv "title" "Generate weekly investor update"),$(json_build_kv "owner" "investor_relations"),\"priority\":\"normal\"}"
    json_post "/api/campaigns" "{$(json_build_kv "name" "NarcoGuard Pilot Launch"),$(json_build_kv "channel" "email"),$(json_build_kv "goal" "pilot signups")}"
    json_post "/api/n8n/workflows" "{$(json_build_kv "name" "NarcoGuard Followup"),$(json_build_kv "description" "Auto follow-up cadence"),$(json_build_kv "trigger" "schedule")}"
    echo "Autopilot configured."
    ;;
  wizard)
    require_api
    read -r -p "Task title: " title
    read -r -p "Owner (default orchestrator): " owner
    read -r -p "Priority (normal/high/urgent): " priority
    read -r -p "Campaign name: " cname
    read -r -p "Campaign channel: " cchannel
    read -r -p "Campaign goal: " cgoal
    read -r -p "Prompt to all agents: " prompt
    owner="${owner:-orchestrator}"
    priority="${priority:-normal}"
    if [ -n "$title" ]; then
      json_post "/api/tasks" "{$(json_build_kv "title" "$title"),$(json_build_kv "owner" "$owner"),\"priority\":\"$priority\"}"
    fi
    if [ -n "$cname" ] && [ -n "$cchannel" ] && [ -n "$cgoal" ]; then
      json_post "/api/campaigns" "{$(json_build_kv "name" "$cname"),$(json_build_kv "channel" "$cchannel"),$(json_build_kv "goal" "$cgoal")}"
    fi
    if [ -n "$prompt" ]; then
      json_post "/api/agents/prompt" "{$(json_build_kv "prompt" "$prompt"),\"targets\":[\"all\"]}"
    fi
    ;;
  queue-task)
    require_arg "Title" "${2:-}"
    title="$2"
    owner="${3:-orchestrator}"
    priority="${4:-normal}"
    json_post "/api/tasks" "{$(json_build_kv "title" "$title"),$(json_build_kv "owner" "$owner"),\"priority\":\"$priority\"}"
    ;;
  plan-campaign)
    require_arg "Name" "${2:-}"
    require_arg "Channel" "${3:-}"
    require_arg "Goal" "${4:-}"
    json_post "/api/campaigns" "{$(json_build_kv "name" "$2"),$(json_build_kv "channel" "$3"),$(json_build_kv "goal" "$4")}"
    ;;
  create-n8n)
    require_arg "Name" "${2:-}"
    desc="${3:-}"
    trigger="${4:-manual}"
    json_post "/api/n8n/workflows" "{$(json_build_kv "name" "$2"),$(json_build_kv "description" "$desc"),$(json_build_kv "trigger" "$trigger")}"
    ;;
  prompt-all)
    require_arg "Message" "${2:-}"
    json_post "/api/agents/prompt" "{$(json_build_kv "prompt" "$2"),\"targets\":[\"all\"]}"
    ;;
  message)
    require_arg "Operator note" "${2:-}"
    json_post "/api/user/messages" "{$(json_build_kv "message" "$2")}"
    ;;
  feedback)
    require_arg "Outcome" "${2:-}"
    require_arg "score" "${3:-}"
    notes="${4:-}"
    json_post "/api/learning/feedback" "{$(json_build_kv "outcome" "$2"),\"score\":$3,$(json_build_kv "notes" "$notes")}"
    ;;
  ingest-trends)
    require_arg "Source" "${2:-}"
    require_arg "trends.json" "${3:-}"
    if [ ! -f "$3" ]; then
      echo "Trend file not found: $3" >&2
      exit 1
    fi
    items_json="$(cat "$3")"
    json_post "/api/trends/ingest" "{\"source\":\"$2\",\"items\":$items_json}"
    ;;
  okr)
    require_arg "Cycle" "${2:-}"
    require_arg "Focus list" "${3:-}"
    focus_items="$(./python3 -c 'import json,sys; print(json.dumps([s.strip() for s in sys.argv[1].split(",") if s.strip()]))' "$3")"
    json_post "/api/okr" "{\"cycle\":\"$2\",\"focus\":$focus_items}"
    ;;
  grant)
    require_arg "Name" "${2:-}"
    require_arg "Deadline" "${3:-}"
    json_post "/api/grants" "{$(json_build_kv "name" "$2"),$(json_build_kv "deadline" "$3")}"
    ;;
  experiment)
    require_arg "Name" "${2:-}"
    require_arg "Metric" "${3:-}"
    json_post "/api/experiments/pricing" "{$(json_build_kv "name" "$2"),$(json_build_kv "hypothesis" "Increase conversion"),$(json_build_kv "metric" "$3")}"
    ;;
  pilot-calc)
    require_arg "devices" "${2:-}"
    require_arg "cost_per_device" "${3:-}"
    require_arg "savings_per_case" "${4:-}"
    require_arg "cases" "${5:-}"
    json_post "/api/pilot/calc" "{\"devices\":$2,\"monthly_cost_per_device\":$3,\"estimated_savings_per_case\":$4,\"estimated_cases_prevented\":$5}"
    ;;
  proposal)
    require_arg "Title" "${2:-}"
    context="${3:-}"
    json_post "/api/proposals/draft" "{$(json_build_kv "title" "$2"),$(json_build_kv "context" "$context")}"
    ;;
  press)
    require_arg "Angle" "${2:-}"
    json_post "/api/press/pitch" "{$(json_build_kv "angle" "$2")}"
    ;;
  video)
    require_arg "Topic" "${2:-}"
    json_post "/api/video/script" "{$(json_build_kv "topic" "$2"),\"length_sec\":90}"
    ;;
  refresh-pipelines)
    require_api
    curl -sS -X POST "$API_BASE/api/pipelines/refresh"
    echo ""
    ;;
  workflows)
    curl -sS "$API_BASE/api/narcoguard/workflows"
    echo ""
    ;;
  agents)
    curl -sS "$API_BASE/api/agents"
    echo ""
    ;;
  tasks)
    curl -sS "$API_BASE/api/tasks"
    echo ""
    ;;
  campaigns)
    curl -sS "$API_BASE/api/campaigns"
    echo ""
    ;;
  *)
    usage
    exit 1
    ;;
esac
