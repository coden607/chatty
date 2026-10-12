"""FastAPI routes for the opportunity finder (mounted by AUTOMATION_API_SERVER)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse

from .config import get_settings
from .readiness import readiness
from .store import Store

router = APIRouter()
DASHBOARD = Path(__file__).resolve().parent / "dashboard.html"
_running = {"jobs": False, "prospects": False}


def _store() -> Store:
    return Store(get_settings().db_path)


@router.get("/opportunities")
def opportunities_dashboard():
    return FileResponse(DASHBOARD)


@router.get("/api/opportunities/status")
def status():
    return readiness(get_settings())


@router.get("/api/opportunities/jobs")
def jobs(min_score: int = 0, limit: int = 200):
    rows = _store().list_jobs(min_score=min_score, limit=min(limit, 1000))
    for r in rows:
        r.pop("description", None)
    return {"total": len(rows), "jobs": rows}


@router.get("/api/opportunities/prospects")
def prospects(grade: Optional[str] = None, vertical: Optional[str] = None, limit: int = 500):
    rows = _store().list_prospects(grade=grade, vertical=vertical, limit=min(limit, 5000))
    return {"total": len(rows), "prospects": rows}


@router.get("/api/opportunities/prospects.csv", response_class=PlainTextResponse)
def prospects_csv(grade: Optional[str] = None):
    from .prospects.export import to_csv
    text = to_csv(_store().list_prospects(grade=grade))
    return PlainTextResponse(text, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=cortese_prospects.csv"})


@router.get("/api/opportunities/drafts")
def drafts(limit: int = 100):
    return {"note": "Drafts only. Nothing is ever sent to prospects from this app.", "drafts": _store().list_drafts(limit)}


@router.post("/api/opportunities/run/{kind}")
async def run(kind: str):
    if kind not in _running:
        raise HTTPException(404, "kind must be jobs or prospects")
    if _running[kind]:
        return {"status": "already_running"}
    _running[kind] = True

    def _work():
        try:
            if kind == "jobs":
                from .jobs.finder import find_jobs
                return find_jobs()["summary"]
            from .prospects.finder import find_prospects
            return find_prospects()["summary"]
        finally:
            _running[kind] = False

    summary = await asyncio.to_thread(_work)
    return {"status": "done", "summary": summary}
