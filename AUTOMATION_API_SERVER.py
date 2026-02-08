#!/usr/bin/env python3
"""
AUTOMATION API SERVER
REST API for controlling and monitoring the complete automation system
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import logging
from datetime import datetime
import json
import os
import re
from pathlib import Path
from leads_storage import get_all_leads, add_lead
from dotenv import load_dotenv

load_dotenv(".env", override=False)
_secrets_file = os.getenv("CHATTY_SECRETS_FILE")
if _secrets_file:
    load_dotenv(os.path.expanduser(_secrets_file), override=False)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CHATTY Automation API",
    description="API for controlling and monitoring complete automation system",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "chatty-automation-api",
    }

app.add_middleware(
    CORSMiddleware,
    # Restrict CORS to localhost/127.0.0.1 for enhanced security
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    """Inject essential security headers into every response"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Basic CSP to prevent common injection attacks
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self' http://localhost:8080 http://127.0.0.1:8080;"
    return response

# Status models
class SystemStatus(BaseModel):
    status: str
    systems_active: int
    total_automations: int
    uptime: float
    revenue_generated: float

class AutomationStatus(BaseModel):
    name: str
    status: str
    modules: int
    features: int

class RevenueStats(BaseModel):
    total: float
    today: float
    this_week: float
    this_month: float
    breakdown: Dict[str, float]

class PromptRequest(BaseModel):
    prompt: str
    targets: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None

class TaskRequest(BaseModel):
    title: str
    owner: Optional[str] = None
    priority: Optional[str] = "normal"
    metadata: Optional[Dict[str, Any]] = None

class UserMessage(BaseModel):
    message: str
    channel: Optional[str] = "operator"
    metadata: Optional[Dict[str, Any]] = None

class CampaignRequest(BaseModel):
    name: str
    channel: str
    goal: str
    owner: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class N8nWorkflowRequest(BaseModel):
    name: str
    description: Optional[str] = None
    trigger: Optional[str] = "manual"
    metadata: Optional[Dict[str, Any]] = None

class LearningFeedback(BaseModel):
    outcome: str
    score: float
    notes: Optional[str] = None

class TrendIngest(BaseModel):
    source: str
    items: List[Dict[str, Any]]

class OkrRequest(BaseModel):
    cycle: str
    focus: List[str]

class GrantRequest(BaseModel):
    name: str
    deadline: str
    value: Optional[str] = None
    notes: Optional[str] = None

class PricingExperimentRequest(BaseModel):
    name: str
    hypothesis: str
    metric: str

class PilotCalcRequest(BaseModel):
    devices: int
    monthly_cost_per_device: float
    estimated_savings_per_case: float
    estimated_cases_prevented: int

class DraftRequest(BaseModel):
    title: str
    context: Optional[str] = None

class PressPitchRequest(BaseModel):
    angle: str
    outlet: Optional[str] = None

class VideoScriptRequest(BaseModel):
    topic: str
    length_sec: Optional[int] = 90

class PartnerBriefRequest(BaseModel):
    partner_type: str
    goal: str

class CrmNoteRequest(BaseModel):
    account: str
    note: str

class MetricIngestRequest(BaseModel):
    metric: str
    value: float

class LeadCaptureRequest(BaseModel):
    email: str
    name: Optional[str] = None
    source: str = "landing_page"
    metadata: Optional[Dict[str, Any]] = None

# Global status
system_status = {
    "running": False,
    "systems": {},
    "total_revenue": 0.0,
    "start_time": None
}

automation_instance: Optional[Any] = None
automation_task: Optional[asyncio.Task] = None
automation_lock = asyncio.Lock()

agents_registry = [
    {"name": "orchestrator", "status": "active", "focus": "routing", "llm": "control", "apis": ["scheduler", "memory"]},
    {"name": "revenue_engine", "status": "active", "focus": "pricing", "llm": "analysis", "apis": ["billing", "crm"]},
    {"name": "acquisition_engine", "status": "active", "focus": "outreach", "llm": "growth", "apis": ["email", "ads"]},
    {"name": "content_engine", "status": "active", "focus": "narratives", "llm": "creative", "apis": ["social", "cms"]},
    {"name": "investor_relations", "status": "active", "focus": "updates", "llm": "strategy", "apis": ["docs", "data-room"]},
    {"name": "partnerships", "status": "active", "focus": "alliances", "llm": "relationship", "apis": ["crm"]},
    {"name": "support_ops", "status": "active", "focus": "support", "llm": "service", "apis": ["ticketing"]}
]

prompt_history: List[Dict[str, Any]] = []
task_queue: List[Dict[str, Any]] = []
collab_feed: List[Dict[str, Any]] = []
user_messages: List[Dict[str, Any]] = []
campaigns: List[Dict[str, Any]] = []
N8N_WORKFLOW_DIR = os.path.join(os.path.dirname(__file__), "n8n_workflows")
n8n_workflows: List[Dict[str, Any]] = []
transparency_log: List[Dict[str, Any]] = []
learning_log: List[Dict[str, Any]] = []
learning_state = {
    "last_update": None,
    "trend": "stable",
    "score_avg": 0.0
}

TREND_DIR = os.path.join(os.path.dirname(__file__), "trend_data")
trend_state = {
    "last_refresh": None,
    "items": [],
    "sources": []
}

okr_state = {
    "current_cycle": "Q1",
    "focus": ["Pilot readiness", "Funding pipeline", "County outreach"],
    "last_rotated": None
}
okr_history: List[Dict[str, Any]] = []

content_briefs: List[Dict[str, Any]] = []
grant_tracker: List[Dict[str, Any]] = []
pricing_experiments: List[Dict[str, Any]] = []
crm_notes: List[Dict[str, Any]] = []
metrics_history: List[Dict[str, Any]] = []
anomaly_log: List[Dict[str, Any]] = []
VIRAL_DIR = Path("generated_content/viral")
VIRAL_LOG = VIRAL_DIR / "experiment_history.jsonl"
INVESTOR_DIR = Path("generated_content/investor")
INVESTOR_METRICS = INVESTOR_DIR / "metrics_snapshot.json"
INVESTOR_OUTREACH = INVESTOR_DIR / "outreach_log.csv"

fail_safe_state = {
    "active": False,
    "error_count": 0,
    "threshold": 5
}

autonomy_state = {
    "running": False,
    "mode": "autopilot",
    "loop_interval_sec": 60,
    "last_tick": None
}

autonomy_settings = {
    "daily_budget": 250.0,
    "risk_guardrails": "conservative",
    "primary_channel": "email",
    "review_window_hours": 4
}

pipelines = {
    "marketing": {
        "name": "NarcoGuard Marketing Pipeline",
        "status": "active",
        "progress": 58,
        "stages": [
            {"name": "Persona refresh", "status": "complete"},
            {"name": "Campaign ideation", "status": "active"},
            {"name": "Asset production", "status": "queued"},
            {"name": "Distribution", "status": "queued"}
        ]
    },
    "revenue": {
        "name": "Revenue Autopilot",
        "status": "active",
        "progress": 41,
        "stages": [
            {"name": "Offer optimization", "status": "active"},
            {"name": "Pricing experiments", "status": "queued"},
            {"name": "Conversion reviews", "status": "queued"}
        ]
    },
    "customer_success": {
        "name": "Customer Success Ops",
        "status": "active",
        "progress": 36,
        "stages": [
            {"name": "Onboarding playbook", "status": "complete"},
            {"name": "Retention workflow", "status": "active"},
            {"name": "Expansion triggers", "status": "queued"}
        ]
    }
}

autonomy_task_handle: Optional[asyncio.Task] = None

narcoguard_workflows = [
    {
        "id": "ng-outreach",
        "name": "Narcoguard Outreach Pipeline",
        "owner": "acquisition_engine",
        "status": "active",
        "progress": 72,
        "last_run": None,
        "steps": [
            {"name": "Target list build", "status": "complete"},
            {"name": "Personalization pass", "status": "active"},
            {"name": "Cadence scheduling", "status": "queued"},
            {"name": "CRM logging", "status": "queued"}
        ]
    },
    {
        "id": "ng-investor",
        "name": "Investor Update Automation",
        "owner": "investor_relations",
        "status": "active",
        "progress": 44,
        "last_run": None,
        "steps": [
            {"name": "Metrics snapshot", "status": "complete"},
            {"name": "Narrative refresh", "status": "active"},
            {"name": "Artifact packaging", "status": "queued"}
        ]
    },
    {
        "id": "ng-content",
        "name": "NarcoGuard Content Engine",
        "owner": "content_engine",
        "status": "active",
        "progress": 61,
        "last_run": None,
        "steps": [
            {"name": "Topic selection", "status": "complete"},
            {"name": "Drafting", "status": "complete"},
            {"name": "Review + polish", "status": "active"},
            {"name": "Distribution queue", "status": "queued"}
        ]
    }
]

def _advance_workflow(workflow: Dict[str, Any]) -> None:
    steps = workflow.get("steps", [])
    active_index = next((i for i, step in enumerate(steps) if step["status"] == "active"), None)

    if active_index is None:
        if all(step["status"] == "complete" for step in steps):
            for step in steps:
                step["status"] = "queued"
            if steps:
                steps[0]["status"] = "active"
        else:
            for step in steps:
                if step["status"] == "queued":
                    step["status"] = "active"
                    break
    else:
        steps[active_index]["status"] = "complete"
        for step in steps[active_index + 1:]:
            if step["status"] == "queued":
                step["status"] = "active"
                break

    workflow["progress"] = min(100, workflow.get("progress", 0) + 7)
    if steps and all(step["status"] == "complete" for step in steps):
        workflow["status"] = "complete"
        workflow["progress"] = 100
        _record_completion("workflow", workflow.get("name", "workflow"), workflow.get("owner", "orchestrator"), "Workflow completed")
    else:
        workflow["status"] = "active"

def _record_collab(event: str, agent: str, detail: str) -> None:
    collab_feed.insert(0, {
        "event": event,
        "agent": agent,
        "detail": detail,
        "timestamp": datetime.now().isoformat()
    })
    collab_feed[:] = collab_feed[:30]

def _record_completion(category: str, name: str, owner: str, detail: str = "") -> None:
    transparency_log.insert(0, {
        "category": category,
        "name": name,
        "owner": owner,
        "detail": detail,
        "timestamp": datetime.now().isoformat()
    })
    transparency_log[:] = transparency_log[:50]

def _record_learning(outcome: str, score: float, notes: str = "") -> None:
    learning_log.insert(0, {
        "outcome": outcome,
        "score": score,
        "notes": notes,
        "timestamp": datetime.now().isoformat()
    })
    learning_log[:] = learning_log[:60]

def _refresh_trends() -> None:
    os.makedirs(TREND_DIR, exist_ok=True)
    trend_files = sorted(
        (f for f in os.listdir(TREND_DIR) if f.endswith(".json")),
        reverse=True
    )
    if not trend_files:
        return
    latest_path = os.path.join(TREND_DIR, trend_files[0])
    try:
        with open(latest_path, "r", encoding="ascii") as handle:
            payload = json.load(handle)
        trend_state["items"] = payload.get("items", [])[:25]
        trend_state["sources"] = payload.get("sources", [])[:10]
        trend_state["last_refresh"] = datetime.now().isoformat()
    except (json.JSONDecodeError, OSError):
        return

def _seed_automation_ideas() -> None:
    if not trend_state["items"]:
        return
    existing_titles = {task["title"] for task in task_queue}
    for item in trend_state["items"][:5]:
        title = f"Trend response: {item.get('title', 'Insight')}"
        if title in existing_titles:
            continue
        task_queue.insert(0, {
            "id": len(task_queue) + 1,
            "title": title,
            "owner": "content_engine",
            "priority": "normal",
            "status": "queued",
            "metadata": {"trend_source": item.get("source", "unknown")},
            "created_at": datetime.now().isoformat()
        })
        _record_collab("trend", "content_engine", f"Queued trend response: {title}")
        existing_titles.add(title)
        if len(task_queue) > 50:
            break

def _seed_content_briefs() -> None:
    if not trend_state["items"]:
        return
    existing_titles = {brief["title"] for brief in content_briefs}
    for item in trend_state["items"][:6]:
        title = f"Content brief: {item.get('title', 'Insight')}"
        if title in existing_titles:
            continue
        content_briefs.insert(0, {
            "title": title,
            "source": item.get("source", "unknown"),
            "status": "draft",
            "created_at": datetime.now().isoformat()
        })
        _record_collab("content", "content_engine", f"Drafted brief: {title}")
        existing_titles.add(title)
        if len(content_briefs) > 40:
            break

def _prioritize_tasks() -> List[Dict[str, Any]]:
    priority_weight = {"urgent": 3, "high": 2, "normal": 1, "low": 0}
    queued = [task for task in task_queue if task["status"] == "queued"]
    return sorted(queued, key=lambda t: priority_weight.get(t.get("priority", "normal"), 1), reverse=True)

def _record_anomaly(metric: str, value: float, baseline: float) -> None:
    anomaly_log.insert(0, {
        "metric": metric,
        "value": value,
        "baseline": baseline,
        "timestamp": datetime.now().isoformat()
    })
    anomaly_log[:] = anomaly_log[:25]

def _archive_stale_tasks(max_age_hours: int = 24) -> None:
    cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
    for task in task_queue:
        created_at = task.get("created_at")
        if not created_at or task.get("status") in {"complete", "archived"}:
            continue
        try:
            created_ts = datetime.fromisoformat(created_at).timestamp()
        except ValueError:
            continue
        if created_ts < cutoff:
            task["status"] = "archived"
            task["updated_at"] = datetime.now().isoformat()
            _record_collab("archive", task["owner"], f"Archived stale task: {task['title']}")

def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "workflow"

def _read_viral_outputs(limit: int = 10, include_content: bool = False) -> List[Dict[str, Any]]:
    outputs: List[Dict[str, Any]] = []
    if not VIRAL_DIR.exists():
        return outputs
    paths = sorted(VIRAL_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in paths[:limit]:
        entry = {
            "file": str(path),
            "name": path.name,
            "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }
        if include_content:
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                content = ""
            entry["content_preview"] = content[:2000]
        outputs.append(entry)
    return outputs

def _read_viral_history(limit: int = 10) -> List[Dict[str, Any]]:
    if not VIRAL_LOG.exists():
        return []
    entries: List[Dict[str, Any]] = []
    try:
        lines = VIRAL_LOG.read_text(encoding="utf-8").splitlines()
    except Exception:
        return entries
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries

def _read_viral_file(name: str) -> Dict[str, Any]:
    if not name:
        raise FileNotFoundError("missing file name")
    safe_name = Path(name).name
    target = (VIRAL_DIR / safe_name).resolve()
    if not str(target).startswith(str(VIRAL_DIR.resolve())):
        raise FileNotFoundError("invalid file path")
    if not target.exists() or not target.is_file():
        raise FileNotFoundError("file not found")
    return {
        "file": str(target),
        "name": target.name,
        "modified_at": datetime.fromtimestamp(target.stat().st_mtime).isoformat(),
        "content": target.read_text(encoding="utf-8"),
    }

def _read_investor_metrics() -> Dict[str, Any]:
    if not INVESTOR_METRICS.exists():
        return {}
    try:
        return json.loads(INVESTOR_METRICS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

def _list_investor_files(prefix: str, limit: int = 10) -> List[Dict[str, Any]]:
    if not INVESTOR_DIR.exists():
        return []
    paths = sorted(
        INVESTOR_DIR.glob(f"{prefix}_*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    payload: List[Dict[str, Any]] = []
    for path in paths[:limit]:
        payload.append(
            {
                "file": str(path),
                "name": path.name,
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            }
        )
    return payload

def _read_investor_file(name: str) -> Dict[str, Any]:
    if not name:
        raise FileNotFoundError("missing file name")
    safe_name = Path(name).name
    target = (INVESTOR_DIR / safe_name).resolve()
    if not str(target).startswith(str(INVESTOR_DIR.resolve())):
        raise FileNotFoundError("invalid file path")
    if not target.exists() or not target.is_file():
        raise FileNotFoundError("file not found")
    return {
        "file": str(target),
        "name": target.name,
        "modified_at": datetime.fromtimestamp(target.stat().st_mtime).isoformat(),
        "content": target.read_text(encoding="utf-8"),
    }

def _read_outreach_log(limit: int = 50) -> List[str]:
    if not INVESTOR_OUTREACH.exists():
        return []
    lines = INVESTOR_OUTREACH.read_text(encoding="utf-8").splitlines()
    return lines[-limit:]

def _sync_system_status_from_instance() -> None:
    if not automation_instance:
        return
    revenue_status = automation_instance.revenue_engine.get_status() if automation_instance.revenue_engine else {}
    acquisition_status = automation_instance.acquisition_engine.get_status() if automation_instance.acquisition_engine else {}
    investor_status = automation_instance.investor_workflows.get_status() if automation_instance.investor_workflows else {}
    viral_status = automation_instance.viral_growth.get_status() if automation_instance.viral_growth else {}
    system_status["total_revenue"] = revenue_status.get("total_revenue", system_status["total_revenue"])
    system_status["systems"] = {
        "complete_automation": {
            "status": "active" if automation_instance.is_running else "stopped",
            "modules": 10,
            "features": 70,
        },
        "revenue_engine": {
            "status": revenue_status.get("status", "unknown"),
            "modules": revenue_status.get("automation_modules", 0),
            "features": len(revenue_status.get("modules", {})),
        },
        "acquisition_engine": {
            "status": acquisition_status.get("status", "unknown"),
            "modules": len(acquisition_status.get("channels", {})),
            "features": acquisition_status.get("total_leads", 0),
        },
        "investor_workflows": {
            "status": investor_status.get("status", "unknown"),
            "modules": 3,
            "features": 4,
        },
        "viral_growth": {
            "status": viral_status.get("status", "unknown"),
            "modules": len(viral_status.get("active_experiments", [])),
            "features": len(viral_status.get("recent_outputs", [])),
        },
    }

async def _launch_automation_system() -> None:
    global automation_instance, automation_task
    from START_COMPLETE_AUTOMATION import ChattyCompleteAutomation

    automation_instance = ChattyCompleteAutomation()
    ok = await automation_instance.initialize()
    if not ok:
        automation_instance = None
        raise RuntimeError("Failed to initialize automation system")
    automation_task = asyncio.create_task(
        automation_instance.start(),
        name="chatty_complete_automation"
    )

def _advance_pipeline(pipeline: Dict[str, Any]) -> None:
    stages = pipeline.get("stages", [])
    active_index = next((i for i, stage in enumerate(stages) if stage["status"] == "active"), None)
    if active_index is None:
        if stages:
            stages[0]["status"] = "active"
    else:
        stages[active_index]["status"] = "complete"
        for stage in stages[active_index + 1:]:
            if stage["status"] == "queued":
                stage["status"] = "active"
                break

    pipeline["progress"] = min(100, pipeline.get("progress", 0) + 6)
    if stages and all(stage["status"] == "complete" for stage in stages):
        pipeline["status"] = "complete"
        pipeline["progress"] = 100
        _record_completion("pipeline", pipeline.get("name", "pipeline"), "orchestrator", "Pipeline completed")

async def _autonomy_loop() -> None:
    while autonomy_state["running"]:
        try:
            now = datetime.now().isoformat()
            autonomy_state["last_tick"] = now

            queued_tasks = _prioritize_tasks()
            if queued_tasks:
                task = queued_tasks[0]
                task["status"] = "active"
                task["updated_at"] = now
                _record_collab("start", task["owner"], f"Started task: {task['title']}")
            else:
                for task in task_queue:
                    if task["status"] == "active":
                        task["status"] = "complete"
                        task["updated_at"] = now
                        _record_collab("complete", task["owner"], f"Completed task: {task['title']}")
                        _record_completion("task", task["title"], task["owner"], "Task completed")
                        break

            for pipeline in pipelines.values():
                if pipeline["status"] != "complete":
                    _advance_pipeline(pipeline)

            _refresh_trends()
            _seed_automation_ideas()
            _seed_content_briefs()
            _archive_stale_tasks()

            if learning_log:
                scores = [entry["score"] for entry in learning_log[:12]]
                avg_score = sum(scores) / len(scores)
                learning_state["score_avg"] = round(avg_score, 2)
                learning_state["last_update"] = now
                if avg_score >= 0.75:
                    autonomy_settings["risk_guardrails"] = "balanced"
                    autonomy_settings["daily_budget"] = min(autonomy_settings["daily_budget"] + 10, 500)
                    learning_state["trend"] = "up"
                elif avg_score <= 0.4:
                    autonomy_settings["risk_guardrails"] = "conservative"
                    autonomy_settings["daily_budget"] = max(autonomy_settings["daily_budget"] - 10, 50)
                    learning_state["trend"] = "down"
                else:
                    learning_state["trend"] = "stable"

            system_status["total_revenue"] += 8.75
            _record_collab("tick", "orchestrator", "Autonomy loop heartbeat")
            fail_safe_state["error_count"] = max(0, fail_safe_state["error_count"] - 1)
        except Exception as exc:
            fail_safe_state["error_count"] += 1
            _record_collab("error", "orchestrator", f"Autonomy error: {exc}")
            if fail_safe_state["error_count"] >= fail_safe_state["threshold"]:
                autonomy_state["running"] = False
                fail_safe_state["active"] = True
                _record_collab("fail_safe", "orchestrator", "Autonomy paused due to errors")
                break
        await asyncio.sleep(autonomy_state["loop_interval_sec"])

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

@app.get("/")
async def root():
    """Serve the landing page"""
    return FileResponse(os.path.join(TEMPLATES_DIR, "landing_page.html"))

@app.get("/landing")
async def landing():
    """Serve the landing page explicitly"""
    return FileResponse(os.path.join(TEMPLATES_DIR, "landing_page.html"))

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "CHATTY Complete Automation API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "status": "/api/status",
            "start": "/api/start",
            "stop": "/api/stop",
            "revenue": "/api/revenue",
            "automations": "/api/automations",
            "leads": "/api/leads",
            "capture-lead": "/api/capture-lead",
            "workflows": "/api/narcoguard/workflows",
            "agents": "/api/agents",
            "tasks": "/api/tasks",
            "collaboration": "/api/agents/collab",
            "messages": "/api/user/messages",
            "autonomy": "/api/autonomy/status",
            "pipelines": "/api/pipelines",
            "campaigns": "/api/campaigns",
            "n8n": "/api/n8n/workflows",
            "transparency": "/api/transparency/report",
            "learning": "/api/learning/report",
            "trends": "/api/trends/status",
            "okrs": "/api/okr",
            "content": "/api/content/briefs",
            "grants": "/api/grants",
            "experiments": "/api/experiments/pricing",
            "crm": "/api/crm/notes",
            "kpi": "/api/kpi/anomalies",
            "viral": "/api/viral/status",
            "investor": "/api/investor/status",
            "investor-weekly": "/api/investor/weekly",
            "investor-narrative": "/api/investor/narrative",
            "investor-metrics": "/api/investor/metrics",
            "investor-outreach": "/api/investor/outreach"
        }
    }

@app.get("/api/status")
async def get_status():
    """Get complete system status"""
    if automation_instance and automation_instance.is_running:
        _sync_system_status_from_instance()
        system_status["running"] = True
    return {
        "status": "running" if system_status["running"] else "stopped",
        "systems_active": len([s for s in system_status["systems"].values() if s.get("status") == "active"]),
        "total_automations": sum(s.get("modules", 0) for s in system_status["systems"].values()),
        "uptime_hours": (datetime.now() - system_status["start_time"]).total_seconds() / 3600 if system_status["start_time"] else 0,
        "revenue_generated": system_status["total_revenue"],
        "systems": system_status["systems"]
    }

@app.post("/api/start")
async def start_systems(background_tasks: BackgroundTasks):
    """Start all automation systems"""
    try:
        async with automation_lock:
            if automation_task and not automation_task.done():
                return {
                    "status": "already_running",
                    "message": "Automation systems already running",
                    "systems": len(system_status["systems"]),
                }
            await _launch_automation_system()
            system_status["running"] = True
            system_status["start_time"] = datetime.now()
            _sync_system_status_from_instance()
            logger.info("🚀 All automation systems started via API")

            return {
                "status": "started",
                "message": "All automation systems started",
                "systems": len(system_status["systems"]),
                "total_automations": sum(s.get("modules", 0) for s in system_status["systems"].values())
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stop")
async def stop_systems():
    """Stop all automation systems"""
    try:
        global automation_instance, automation_task
        async with automation_lock:
            if automation_instance:
                await automation_instance.stop()
            if automation_task and not automation_task.done():
                try:
                    await asyncio.wait_for(automation_task, timeout=10)
                except asyncio.TimeoutError:
                    automation_task.cancel()
            automation_instance = None
            automation_task = None
            system_status["running"] = False
            system_status["systems"] = {}
            system_status["start_time"] = None

            logger.info("🛑 All automation systems stopped via API")

            return {
                "status": "stopped",
                "message": "All automation systems stopped"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/revenue")
async def get_revenue():
    """Get revenue statistics"""
    if automation_instance and automation_instance.revenue_engine:
        revenue_status = automation_instance.revenue_engine.get_status()
        system_status["total_revenue"] = revenue_status.get("total_revenue", system_status["total_revenue"])
    return {
        "total": system_status["total_revenue"],
        "today": system_status["total_revenue"] * 0.1,  # Simulated
        "this_week": system_status["total_revenue"] * 0.3,
        "this_month": system_status["total_revenue"] * 0.7,
        "breakdown": {
            "affiliate": system_status["total_revenue"] * 0.4,
            "subscription": system_status["total_revenue"] * 0.3,
            "referral": system_status["total_revenue"] * 0.2,
            "other": system_status["total_revenue"] * 0.1
        }
    }

@app.get("/api/automations")
async def get_automations():
    """Get all automation systems"""
    automations = [
        {
            "name": "Complete Automation System",
            "status": "active",
            "modules": 8,
            "features": 64,
            "description": "Core automation system with 8 engines"
        },
        {
            "name": "Automated Revenue Engine",
            "status": "active",
            "modules": 8,
            "features": 56,
            "description": "Revenue generation automation"
        },
        {
            "name": "Advanced Automation Modules",
            "status": "active",
            "modules": 12,
            "features": 120,
            "description": "Advanced automation capabilities"
        },
        {
            "name": "Master Automation Orchestrator",
            "status": "active",
            "modules": 1,
            "features": 10,
            "description": "Orchestrates all systems"
        }
    ]
    
    return {
        "total_systems": len(automations),
        "total_modules": sum(a["modules"] for a in automations),
        "total_features": sum(a["features"] for a in automations),
        "automations": automations
    }

@app.get("/api/leads")
async def get_leads():
    """Get all generated leads"""
    leads = get_all_leads()
    return {
        "total": len(leads),
        "new": len([l for l in leads if l.get("status") == "new"]),
        "leads": leads[::-1]  # Most recent first
    }

@app.post("/api/capture-lead")
async def capture_lead(payload: LeadCaptureRequest):
    """Capture a real lead from landing page or other sources"""
    try:
        # Use the leads_storage module to add the lead
        lead = add_lead(
            name=payload.name or payload.email.split('@')[0],
            email=payload.email,
            source=payload.source,
            metadata=payload.metadata or {}
        )
        
        logger.info(f"🎯 REAL LEAD CAPTURED: {payload.email} from {payload.source}")
        _record_collab("lead", "acquisition_engine", f"Captured real lead: {payload.email} ({payload.source})")
        
        return {
            "status": "captured",
            "message": "Lead captured successfully!",
            "lead_id": lead.get("id") if isinstance(lead, dict) else len(get_all_leads()),
            "email": payload.email,
            "source": payload.source
        }
    except Exception as e:
        logger.error(f"Error capturing lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/leads/{lead_id}/convert")
async def convert_lead(lead_id: int):
    """Trigger AI conversion agent for a specific lead"""
    try:
        from AUTOMATED_CUSTOMER_ACQUISITION import acquisition_engine
        result = await acquisition_engine.convert_lead(lead_id)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Error converting lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/narcoguard/workflows")
async def get_narcoguard_workflows():
    """Get NarcoGuard transparent workflow status"""
    return {
        "project": "Narcoguard",
        "workflows": narcoguard_workflows
    }

@app.post("/api/narcoguard/workflows/refresh")
async def refresh_narcoguard_workflows():
    """Refresh and advance workflow telemetry"""
    now = datetime.now().isoformat()
    for workflow in narcoguard_workflows:
        workflow["last_run"] = now
        _advance_workflow(workflow)
    logger.info("🧭 NarcoGuard workflows refreshed")
    return {
        "status": "refreshed",
        "timestamp": now,
        "workflows": narcoguard_workflows
    }

@app.get("/api/agents")
async def get_agents():
    """List available agents"""
    return {
        "total": len(agents_registry),
        "agents": agents_registry
    }

@app.post("/api/agents/prompt")
async def prompt_agents(payload: PromptRequest):
    """Broadcast a prompt to Chatty and agents (mocked)"""
    targets = payload.targets or ["all"]
    if "all" in targets:
        targets = [agent["name"] for agent in agents_registry]

    entry = {
        "prompt": payload.prompt,
        "targets": targets,
        "context": payload.context or {},
        "timestamp": datetime.now().isoformat()
    }
    prompt_history.insert(0, entry)
    prompt_history[:] = prompt_history[:25]

    logger.info("📣 Prompt dispatched to agents: %s", ", ".join(targets))
    _record_collab("prompt", "operator", f"Broadcast prompt to {', '.join(targets)}")
    return {
        "status": "queued",
        "targets": targets,
        "history": prompt_history[:8]
    }

@app.get("/api/autonomy/status")
async def get_autonomy_status():
    """Get autonomy loop status"""
    return {
        "state": autonomy_state,
        "settings": autonomy_settings
    }

@app.post("/api/autonomy/start")
async def start_autonomy():
    """Start the autonomy loop"""
    global autonomy_task_handle
    if autonomy_state["running"]:
        return {"status": "running"}
    autonomy_state["running"] = True
    autonomy_task_handle = asyncio.create_task(_autonomy_loop())
    _record_collab("autonomy", "orchestrator", "Autonomy loop started")
    logger.info("🧠 Autonomy loop started")
    return {"status": "started"}

@app.post("/api/autonomy/stop")
async def stop_autonomy():
    """Stop the autonomy loop"""
    global autonomy_task_handle
    if not autonomy_state["running"]:
        return {"status": "stopped"}
    autonomy_state["running"] = False
    if autonomy_task_handle:
        autonomy_task_handle.cancel()
        autonomy_task_handle = None
    _record_collab("autonomy", "orchestrator", "Autonomy loop stopped")
    logger.info("🛑 Autonomy loop stopped")
    return {"status": "stopped"}

@app.post("/api/autonomy/settings")
async def update_autonomy_settings(payload: Dict[str, Any]):
    """Update autonomy settings"""
    autonomy_settings.update(payload)
    _record_collab("settings", "operator", "Updated autonomy settings")
    return {"status": "updated", "settings": autonomy_settings}

@app.get("/api/pipelines")
async def get_pipelines():
    """Get revenue/marketing pipelines"""
    return {
        "pipelines": list(pipelines.values())
    }

@app.post("/api/pipelines/refresh")
async def refresh_pipelines():
    """Advance pipeline stages"""
    for pipeline in pipelines.values():
        if pipeline["status"] != "complete":
            _advance_pipeline(pipeline)
    _record_collab("pipeline", "orchestrator", "Pipelines advanced")
    return {"status": "refreshed", "pipelines": list(pipelines.values())}

@app.get("/api/viral/status")
async def get_viral_status():
    """Get viral growth status and recent artifacts"""
    outputs = _read_viral_outputs(limit=5, include_content=False)
    history = _read_viral_history(limit=5)
    engine_status = {}
    if automation_instance and automation_instance.viral_growth:
        engine_status = automation_instance.viral_growth.get_status()
    return {
        "status": engine_status.get("status", "active"),
        "active_experiments": engine_status.get("active_experiments", ["hero_story_loop", "ugc_challenge"]),
        "output_directory": str(VIRAL_DIR),
        "recent_outputs": outputs,
        "recent_history": history,
        "last_run": engine_status.get("last_run"),
        "offline_mode": engine_status.get("offline_mode", False),
    }

@app.get("/api/viral/outputs")
async def get_viral_outputs(limit: int = 10, include_content: bool = False):
    """List viral growth output files"""
    outputs = _read_viral_outputs(limit=limit, include_content=include_content)
    return {"outputs": outputs, "count": len(outputs)}

@app.get("/api/viral/output/{name}")
async def get_viral_output(name: str):
    """Fetch a single viral output by filename"""
    try:
        payload = _read_viral_file(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return payload

@app.get("/api/investor/status")
async def get_investor_status():
    """Get investor workflow status and latest artifacts"""
    status = {}
    if automation_instance and automation_instance.investor_workflows:
        status = automation_instance.investor_workflows.get_status()
    weekly = _list_investor_files("weekly_update", limit=3)
    narrative = _list_investor_files("narrative_update", limit=3)
    return {
        "status": status.get("status", "unknown"),
        "last_weekly_update": status.get("last_weekly_update"),
        "last_daily_outreach": status.get("last_daily_outreach"),
        "last_narrative_update": status.get("last_narrative_update"),
        "weekly_updates": weekly,
        "narrative_updates": narrative,
        "metrics_snapshot": _read_investor_metrics(),
    }

@app.get("/api/investor/weekly")
async def list_weekly_updates(limit: int = 10):
    """List weekly investor update files"""
    updates = _list_investor_files("weekly_update", limit=limit)
    return {"updates": updates, "count": len(updates)}

@app.get("/api/investor/weekly/{name}")
async def get_weekly_update(name: str):
    """Fetch a single weekly investor update"""
    try:
        payload = _read_investor_file(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return payload

@app.get("/api/investor/narrative")
async def list_narrative_updates(limit: int = 10):
    """List narrative update files"""
    updates = _list_investor_files("narrative_update", limit=limit)
    return {"updates": updates, "count": len(updates)}

@app.get("/api/investor/narrative/{name}")
async def get_narrative_update(name: str):
    """Fetch a single narrative update"""
    try:
        payload = _read_investor_file(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return payload

@app.get("/api/investor/metrics")
async def get_investor_metrics():
    """Get investor metrics snapshot"""
    return {"metrics": _read_investor_metrics()}

@app.get("/api/investor/outreach")
async def get_investor_outreach(limit: int = 50):
    """Get recent outreach log entries"""
    return {"entries": _read_outreach_log(limit=limit)}

@app.post("/api/investor/refresh")
async def refresh_investor_artifacts():
    """Trigger investor artifact refreshes"""
    if automation_instance and automation_instance.investor_workflows:
        automation_instance.investor_workflows.run_weekly_update_now()
        automation_instance.investor_workflows.run_narrative_update_now()
        automation_instance.investor_workflows.run_daily_outreach_now()
    return {
        "status": "refreshed",
        "weekly_updates": _list_investor_files("weekly_update", limit=1),
        "narrative_updates": _list_investor_files("narrative_update", limit=1),
        "metrics_snapshot": _read_investor_metrics(),
    }

@app.get("/api/campaigns")
async def get_campaigns():
    """Get planned campaigns"""
    return {
        "total": len(campaigns),
        "campaigns": campaigns
    }

@app.post("/api/campaigns")
async def add_campaign(payload: CampaignRequest):
    """Add a campaign plan"""
    campaign = {
        "id": len(campaigns) + 1,
        "name": payload.name,
        "channel": payload.channel,
        "goal": payload.goal,
        "owner": payload.owner or "content_engine",
        "status": "planned",
        "metadata": payload.metadata or {},
        "created_at": datetime.now().isoformat()
    }
    campaigns.insert(0, campaign)
    _record_collab("campaign", campaign["owner"], f"Planned campaign: {campaign['name']}")
    _record_completion("campaign", campaign["name"], campaign["owner"], "Campaign planned")
    logger.info("📣 Campaign planned: %s", campaign["name"])
    return {"status": "planned", "campaign": campaign}

@app.get("/api/n8n/workflows")
async def get_n8n_workflows():
    """List generated n8n workflows"""
    return {
        "total": len(n8n_workflows),
        "workflows": n8n_workflows
    }

@app.post("/api/n8n/workflows")
async def create_n8n_workflow(payload: N8nWorkflowRequest):
    """Create a starter n8n workflow JSON"""
    os.makedirs(N8N_WORKFLOW_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = _slugify(payload.name)
    filename = f"{slug}_{timestamp}.json"
    filepath = os.path.join(N8N_WORKFLOW_DIR, filename)

    workflow = {
        "name": payload.name,
        "nodes": [
            {
                "parameters": {},
                "id": "manual-trigger",
                "name": "Manual Trigger",
                "type": "n8n-nodes-base.manualTrigger",
                "typeVersion": 1,
                "position": [240, 300]
            },
            {
                "parameters": {
                    "functionCode": "return items;"
                },
                "id": "noop",
                "name": "No-op",
                "type": "n8n-nodes-base.function",
                "typeVersion": 2,
                "position": [480, 300]
            }
        ],
        "connections": {
            "Manual Trigger": {
                "main": [[{"node": "No-op", "type": "main", "index": 0}]]
            }
        },
        "settings": {
            "timezone": "UTC"
        },
        "meta": {
            "description": payload.description or "",
            "trigger": payload.trigger or "manual",
            "metadata": payload.metadata or {}
        }
    }

    with open(filepath, "w", encoding="ascii") as handle:
        json.dump(workflow, handle, indent=2)

    entry = {
        "name": payload.name,
        "description": payload.description or "",
        "trigger": payload.trigger or "manual",
        "path": filepath,
        "created_at": datetime.now().isoformat()
    }
    n8n_workflows.insert(0, entry)
    n8n_workflows[:] = n8n_workflows[:50]
    _record_collab("n8n", "orchestrator", f"Created n8n workflow: {payload.name}")
    _record_completion("n8n", payload.name, "orchestrator", "Workflow file created")
    logger.info("🔧 n8n workflow created: %s", filepath)
    return {"status": "created", "workflow": entry}

@app.get("/api/transparency/report")
async def get_transparency_report():
    """Provide a transparency snapshot of completed work"""
    return {
        "generated_at": datetime.now().isoformat(),
        "completed": transparency_log[:20],
        "tasks": task_queue[:10],
        "workflows": narcoguard_workflows,
        "pipelines": list(pipelines.values()),
        "campaigns": campaigns[:10],
        "n8n_workflows": n8n_workflows[:10]
    }

@app.get("/api/learning/report")
async def get_learning_report():
    """Get learning feedback trend"""
    return {
        "state": learning_state,
        "recent_feedback": learning_log[:10]
    }

@app.post("/api/learning/feedback")
async def post_learning_feedback(payload: LearningFeedback):
    """Record learning feedback"""
    score = max(0.0, min(1.0, float(payload.score)))
    _record_learning(payload.outcome, score, payload.notes or "")
    _record_collab("learning", "operator", f"Feedback recorded: {payload.outcome}")
    return {
        "status": "recorded",
        "state": learning_state
    }

@app.get("/api/trends/status")
async def get_trend_status():
    """Get current trend ingestion status"""
    return trend_state

@app.post("/api/trends/ingest")
async def ingest_trends(payload: TrendIngest):
    """Ingest external trend data"""
    os.makedirs(TREND_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"trends_{timestamp}.json"
    path = os.path.join(TREND_DIR, filename)
    record = {
        "sources": [payload.source],
        "items": payload.items
    }
    with open(path, "w", encoding="ascii") as handle:
        json.dump(record, handle, indent=2)
    trend_state["items"] = payload.items[:25]
    trend_state["sources"] = [payload.source]
    trend_state["last_refresh"] = datetime.now().isoformat()
    _record_collab("trend", "orchestrator", f"Ingested trends from {payload.source}")
    return {"status": "ingested", "path": path, "count": len(payload.items)}

@app.get("/api/okr")
async def get_okrs():
    """Get current OKR cycle"""
    return {
        "current": okr_state,
        "history": okr_history[:6]
    }

@app.post("/api/okr")
async def set_okrs(payload: OkrRequest):
    """Set current OKR cycle"""
    okr_state["current_cycle"] = payload.cycle
    okr_state["focus"] = payload.focus
    okr_state["last_rotated"] = datetime.now().isoformat()
    _record_collab("okr", "orchestrator", f"OKRs updated: {payload.cycle}")
    return {"status": "updated", "current": okr_state}

@app.post("/api/okr/rotate")
async def rotate_okrs():
    """Rotate OKRs into history"""
    okr_history.insert(0, {
        "cycle": okr_state["current_cycle"],
        "focus": okr_state["focus"],
        "rotated_at": datetime.now().isoformat()
    })
    okr_history[:] = okr_history[:12]
    okr_state["current_cycle"] = f"Next-{okr_state['current_cycle']}"
    okr_state["focus"] = ["Revenue traction", "Pilot expansion", "Funding momentum"]
    okr_state["last_rotated"] = datetime.now().isoformat()
    _record_collab("okr", "orchestrator", "OKRs rotated")
    return {"status": "rotated", "current": okr_state}

@app.get("/api/content/briefs")
async def get_content_briefs():
    """Get trend-triggered content briefs"""
    return {
        "total": len(content_briefs),
        "briefs": content_briefs[:12]
    }

@app.post("/api/content/briefs/refresh")
async def refresh_content_briefs():
    """Refresh content briefs from trends"""
    _refresh_trends()
    _seed_content_briefs()
    return {"status": "refreshed", "briefs": content_briefs[:12]}

@app.get("/api/grants")
async def get_grants():
    """Get grant tracker entries"""
    return {
        "total": len(grant_tracker),
        "grants": grant_tracker[:12]
    }

@app.post("/api/grants")
async def add_grant(payload: GrantRequest):
    """Add grant to tracker"""
    entry = {
        "name": payload.name,
        "deadline": payload.deadline,
        "value": payload.value or "",
        "notes": payload.notes or "",
        "created_at": datetime.now().isoformat()
    }
    grant_tracker.insert(0, entry)
    _record_collab("grant", "investor_relations", f"Tracked grant: {payload.name}")
    return {"status": "tracked", "grant": entry}

@app.get("/api/experiments/pricing")
async def get_pricing_experiments():
    """Get pricing experiments"""
    return {
        "total": len(pricing_experiments),
        "experiments": pricing_experiments[:10]
    }

@app.post("/api/experiments/pricing")
async def add_pricing_experiment(payload: PricingExperimentRequest):
    """Add pricing experiment"""
    entry = {
        "name": payload.name,
        "hypothesis": payload.hypothesis,
        "metric": payload.metric,
        "status": "planned",
        "created_at": datetime.now().isoformat()
    }
    pricing_experiments.insert(0, entry)
    _record_collab("experiment", "revenue_engine", f"Planned pricing experiment: {payload.name}")
    return {"status": "planned", "experiment": entry}

@app.post("/api/pilot/calc")
async def pilot_calc(payload: PilotCalcRequest):
    """Calculate pilot ROI"""
    monthly_cost = payload.devices * payload.monthly_cost_per_device
    savings = payload.estimated_savings_per_case * payload.estimated_cases_prevented
    roi = (savings - monthly_cost) / monthly_cost if monthly_cost else 0
    return {
        "monthly_cost": round(monthly_cost, 2),
        "estimated_savings": round(savings, 2),
        "roi": round(roi, 2)
    }

@app.post("/api/proposals/draft")
async def draft_proposal(payload: DraftRequest):
    """Generate a proposal draft"""
    try:
        from AUTOMATED_REVENUE_ENGINE import revenue_engine
        system_prompt = "You are a professional grant writer and business developer for NarcoGuard."
        user_prompt = f"""Write a comprehensive proposal draft for: {payload.title}
        
        Context: {payload.context or 'NarcoGuard deployment to reduce overdose deaths.'}
        
        Structure:
        1. Executive Summary
        2. Problem Statement (Opioid Crisis)
        3. Solution (NarcoGuard Automated Watch)
        4. Implementation Plan
        5. Expected Outcomes
        
        Keep it professional, persuasive, and mission-driven."""
        
        draft = await revenue_engine.generate_ai_content(system_prompt, user_prompt)
        return {"draft": draft}
    except Exception as e:
        logger.error(f"Proposal generation failed: {e}")
        return {"draft": f"Error generating proposal: {str(e)}"}

@app.post("/api/investor/weekly")
async def investor_weekly(payload: DraftRequest):
    """Generate an investor weekly update draft"""
    try:
        from AUTOMATED_REVENUE_ENGINE import revenue_engine
        system_prompt = "You are the founder of NarcoGuard writing a weekly update to investors."
        user_prompt = f"""Write a weekly investor update for: {payload.title}
        
        Key Updates: {payload.context or 'Progress on pilots and technology.'}
        
        Structure:
        - 🚀 Key wins & traction
        - 📉 Challenges & risks
        - 🆘 Asks & help needed
        - 📊 Metrics snapshot
        
        Tone: Transparent, ambitious, data-driven."""
        
        draft = await revenue_engine.generate_ai_content(system_prompt, user_prompt)
        return {"draft": draft}
    except Exception as e:
        logger.error(f"Investor update generation failed: {e}")
        return {"draft": f"Error generating update: {str(e)}"}

@app.post("/api/investor/narrative")
async def investor_narrative(payload: DraftRequest):
    """Generate a narrative refresh draft"""
    try:
        from AUTOMATED_REVENUE_ENGINE import revenue_engine
        system_prompt = "You are a strategic communications expert for a MedTech startup."
        user_prompt = f"""Refine the core investor narrative for: {payload.title}
        
        Context/New Evidence: {payload.context or 'Initial pilot success.'}
        
        Output:
        1. One-sentence pitch
        2. The "Why Now" statement
        3. Market Opportunity
        4. Unique Insight
        
        Focus on the urgency of the opioid crisis and the scalability of our AI solution."""
        
        draft = await revenue_engine.generate_ai_content(system_prompt, user_prompt)
        return {"draft": draft}
    except Exception as e:
        logger.error(f"Narrative generation failed: {e}")
        return {"draft": f"Error generating narrative: {str(e)}"}

@app.get("/api/data-room/checklist")
async def data_room_checklist():
    """Get data room checklist"""
    return {
        "items": [
            "One-page brief",
            "Deck PDF",
            "Metrics snapshot",
            "Pilot plan",
            "Risk register",
            "Demo video link"
        ]
    }

@app.post("/api/press/pitch")
async def press_pitch(payload: PressPitchRequest):
    """Generate a press pitch"""
    try:
        from AUTOMATED_REVENUE_ENGINE import revenue_engine
        system_prompt = "You are a PR specialist for NarcoGuard."
        user_prompt = f"""Write a compelling press pitch for: {payload.outlet or 'Tech Media'}
        
        Angle: {payload.angle}
        
        Include:
        - Subject line options
        - The hook (Why this story matters now)
        - Key data points regarding overdose stats
        - Call to action (Interview founder, see demo)
        
        Make it punchy and hard-hitting."""
        
        draft = await revenue_engine.generate_ai_content(system_prompt, user_prompt)
        return {"draft": draft}
    except Exception as e:
        logger.error(f"Pitch generation failed: {e}")
        return {"draft": f"Error generating pitch: {str(e)}"}

@app.post("/api/video/script")
async def video_script(payload: VideoScriptRequest):
    """Generate a short video script"""
    try:
        from AUTOMATED_REVENUE_ENGINE import revenue_engine
        system_prompt = "You are a video producer for social media content."
        user_prompt = f"""Write a video script ({payload.length_sec or 90} seconds) about: {payload.topic}
        
        Format:
        [Visual] | [Audio/Script]
        
        Style: TikTok/Reels style - fast paced, engaging hooks.
        Focus: Saving lives, technology, hope."""
        
        draft = await revenue_engine.generate_ai_content(system_prompt, user_prompt)
        return {"draft": draft}
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        return {"draft": f"Error generating script: {str(e)}"}

@app.post("/api/partner/brief")
async def partner_brief(payload: PartnerBriefRequest):
    """Generate a partner outreach brief"""
    try:
        from AUTOMATED_REVENUE_ENGINE import revenue_engine
        system_prompt = "You are a partnership director for a health tech company."
        user_prompt = f"""Write a partnership proposal brief for: {payload.partner_type}
        
        Goal: {payload.goal}
        
        Include:
        - Mutual benefits
        - Specific pilot proposal
        - Resource requirements
        - Next steps discussion points"""
        
        draft = await revenue_engine.generate_ai_content(system_prompt, user_prompt)
        return {"draft": draft}
    except Exception as e:
        logger.error(f"Brief generation failed: {e}")
        return {"draft": f"Error generating brief: {str(e)}"}

@app.get("/api/crm/notes")
async def get_crm_notes():
    """Get CRM notes"""
    return {"notes": crm_notes[:20]}

@app.post("/api/crm/notes")
async def add_crm_note(payload: CrmNoteRequest):
    """Add a CRM note"""
    entry = {
        "account": payload.account,
        "note": payload.note,
        "timestamp": datetime.now().isoformat()
    }
    crm_notes.insert(0, entry)
    _record_collab("crm", "acquisition_engine", f"Logged CRM note for {payload.account}")
    return {"status": "logged", "note": entry}

@app.post("/api/metrics/ingest")
async def ingest_metric(payload: MetricIngestRequest):
    """Ingest a KPI metric"""
    entry = {
        "metric": payload.metric,
        "value": payload.value,
        "timestamp": datetime.now().isoformat()
    }
    metrics_history.insert(0, entry)
    metrics_history[:] = metrics_history[:50]
    if len(metrics_history) > 5:
        baseline = sum(m["value"] for m in metrics_history[1:6]) / 5
        if baseline and abs(payload.value - baseline) / baseline > 0.35:
            _record_anomaly(payload.metric, payload.value, baseline)
    return {"status": "ingested"}

@app.get("/api/kpi/anomalies")
async def get_kpi_anomalies():
    """Get KPI anomaly log"""
    return {"anomalies": anomaly_log[:10]}

@app.get("/api/weekly/brief")
async def weekly_brief():
    """Get weekly summary brief"""
    completed = transparency_log[:15] # Fetch more logs for context
    events = collab_feed[:15]
    
    try:
        from AUTOMATED_REVENUE_ENGINE import revenue_engine
        
        # Prepare context for AI
        logs_text = "\n".join([f"- {acc.get('action')}: {acc.get('result')} ({acc.get('details')})" for acc in completed])
        events_text = "\n".join([f"- {evt.get('agent')}: {evt.get('event')} - {evt.get('detail')}" for evt in events])
        
        system_prompt = "You are the Chief of Staff for a fully autonomous company."
        user_prompt = f"""Generate a concise, 1-sentence strategic summary of the recent system activity.
        
        Recent Actions:
        {logs_text}
        
        Collaboration Events:
        {events_text}
        
        Focus on progress, autonomy, and key wins. If logs are empty, state that the system is initializing."""
        
        summary = await revenue_engine.generate_ai_content(system_prompt, user_prompt)
        # Keep it brief if AI rambles
        if len(summary) > 200:
            summary = summary[:197] + "..."
            
    except Exception as e:
        logger.error(f"Weekly brief AI generation failed: {e}")
        summary = "Autonomy progressing. (AI Summary temporarily unavailable)"

    body = {
        "completed": completed[:6], # Return fewer items to UI
        "events": events[:6],
        "summary": summary
    }
    return body

@app.get("/api/tasks")
async def get_tasks():
    """Get the autonomy task queue"""
    return {
        "total": len(task_queue),
        "tasks": task_queue
    }

@app.post("/api/tasks")
async def add_task(payload: TaskRequest):
    """Add a task to the autonomy queue"""
    task = {
        "id": len(task_queue) + 1,
        "title": payload.title,
        "owner": payload.owner or "orchestrator",
        "priority": payload.priority or "normal",
        "status": "queued",
        "metadata": payload.metadata or {},
        "created_at": datetime.now().isoformat()
    }
    task_queue.insert(0, task)
    _record_collab("task", task["owner"], f"Queued task: {task['title']}")
    logger.info("🧩 Task queued: %s", task["title"])
    return {
        "status": "queued",
        "task": task
    }

@app.post("/api/tasks/{task_id}/ack")
async def ack_task(task_id: int):
    """Mark a task as active by an agent"""
    for task in task_queue:
        if task["id"] == task_id:
            task["status"] = "active"
            task["updated_at"] = datetime.now().isoformat()
            _record_collab("ack", task["owner"], f"Accepted task: {task['title']}")
            return {"status": "active", "task": task}
    raise HTTPException(status_code=404, detail="Task not found")

@app.get("/api/agents/collab")
async def get_collab_feed():
    """Get the agent collaboration feed"""
    return {
        "total": len(collab_feed),
        "events": collab_feed
    }

@app.post("/api/agents/collab")
async def post_collab_event(payload: Dict[str, Any]):
    """Post a collaboration event"""
    event = payload.get("event", "note")
    agent = payload.get("agent", "orchestrator")
    detail = payload.get("detail", "")
    _record_collab(event, agent, detail)
    logger.info("🤝 Collab event: %s - %s", agent, event)
    return {"status": "recorded"}

@app.get("/api/user/messages")
async def get_user_messages():
    """Get operator messages"""
    return {
        "total": len(user_messages),
        "messages": user_messages[:20]
    }

@app.post("/api/user/messages")
async def post_user_message(payload: UserMessage):
    """Post a user message to the system"""
    entry = {
        "message": payload.message,
        "channel": payload.channel or "operator",
        "metadata": payload.metadata or {},
        "timestamp": datetime.now().isoformat()
    }
    user_messages.insert(0, entry)
    _record_collab("message", "operator", payload.message[:80])
    logger.info("💬 Operator message received")
    return {
        "status": "received",
        "message": entry
    }


@app.get("/api/automations/{automation_name}")
async def get_automation(automation_name: str):
    """Get specific automation system details"""
    automations = {
        "complete_automation": {
            "name": "Complete Automation System",
            "modules": ["Content", "Marketing", "Traffic", "Conversion", "Optimization", "Multi-Channel", "Analytics", "Campaigns"],
            "status": "active"
        },
        "revenue_engine": {
            "name": "Automated Revenue Engine",
            "modules": ["API Integration", "Content", "Social", "Email", "SEO", "Ads", "Conversion", "Optimization"],
            "status": "active"
        },
        "advanced_modules": {
            "name": "Advanced Automation Modules",
            "modules": ["AI Content", "SEO", "Social", "Email Sequences", "Lead Generation", "Retention", "Upsell", "Affiliate", "Market Research", "Competitor Analysis", "Pricing", "Inventory"],
            "status": "active"
        }
    }
    
    if automation_name not in automations:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    return automations[automation_name]

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "systems_running": system_status["running"],
        "systems_count": len(system_status["systems"])
    }

@app.get("/api/metrics")
async def get_metrics():
    """Get performance metrics"""
    return {
        "performance": {
            "uptime_percentage": 100.0,
            "error_rate": 0.0,
            "response_time_ms": 0,
            "throughput": 0
        },
        "revenue": {
            "total": system_status["total_revenue"],
            "growth_rate": 0.0,
            "projected_monthly": 0.0
        },
        "automation": {
            "tasks_completed": 0,
            "tasks_per_hour": 0,
            "success_rate": 100.0
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting CHATTY Automation API Server...")
    print("📍 API available at: http://localhost:8080")
    print("📚 API docs at: http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
