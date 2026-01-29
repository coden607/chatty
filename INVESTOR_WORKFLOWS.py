#!/usr/bin/env python3
"""
INVESTOR WORKFLOWS
Internal automation loops for investor updates and outreach cadence.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

OUTREACH_LOG_HEADER = "timestamp,investor,stage,status,notes\n"


def _ensure_outreach_log(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(OUTREACH_LOG_HEADER, encoding="utf-8")


def log_outreach_event(path: Path, investor: str, stage: str, status: str, notes: str):
    _ensure_outreach_log(path)
    now = datetime.now(timezone.utc).isoformat()
    line = f"{now},{investor},{stage},{status},{notes}\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)


class InvestorWorkflows:
    """Automated investor workflows (no external API calls)."""

    def __init__(self):
        self.is_running = False
        self.status = "stopped"
        self.last_weekly_update = None
        self.last_daily_outreach = None
        self.last_narrative_update = None

        self.base_dir = Path("generated_content") / "investor"
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.weekly_interval = int(os.getenv("INVESTOR_WEEKLY_INTERVAL_SECONDS", 60 * 60 * 24 * 7))
        self.daily_interval = int(os.getenv("INVESTOR_DAILY_INTERVAL_SECONDS", 60 * 60 * 24))
        self.biweekly_interval = int(os.getenv("INVESTOR_BIWEEKLY_INTERVAL_SECONDS", 60 * 60 * 24 * 14))

        self.outreach_log = self.base_dir / "outreach_log.csv"
        _ensure_outreach_log(self.outreach_log)

    async def initialize(self):
        """Prepare local artifacts and folders."""
        self.status = "ready"

    async def start(self):
        """Start background workflow loops."""
        self.is_running = True
        self.status = "active"

        weekly_task = asyncio.create_task(self._weekly_update_loop())
        daily_task = asyncio.create_task(self._daily_outreach_loop())
        biweekly_task = asyncio.create_task(self._biweekly_narrative_loop())

        await asyncio.gather(weekly_task, daily_task, biweekly_task)

    async def stop(self):
        """Stop all loops gracefully."""
        self.is_running = False
        self.status = "stopped"

    def get_status(self):
        return {
            "status": self.status,
            "last_weekly_update": self.last_weekly_update,
            "last_daily_outreach": self.last_daily_outreach,
            "last_narrative_update": self.last_narrative_update,
        }

    def run_weekly_update_now(self):
        self._write_weekly_update()

    def run_daily_outreach_now(self):
        self._write_daily_outreach()

    def run_narrative_update_now(self):
        self._write_narrative_update()

    async def _weekly_update_loop(self):
        while self.is_running:
            self._write_weekly_update()
            await asyncio.sleep(self.weekly_interval)

    async def _daily_outreach_loop(self):
        while self.is_running:
            self._write_daily_outreach()
            await asyncio.sleep(self.daily_interval)

    async def _biweekly_narrative_loop(self):
        while self.is_running:
            self._write_narrative_update()
            await asyncio.sleep(self.biweekly_interval)

    def _write_weekly_update(self):
        now = datetime.now(timezone.utc)
        self.last_weekly_update = now.isoformat()
        filename = self.base_dir / f"weekly_update_{now.strftime('%Y%m%d')}.md"
        content = "\n".join(
            [
                "# Weekly Investor Update",
                f"Date (UTC): {now.isoformat()}",
                "",
                "## Metrics Snapshot",
                "- MRR:",
                "- CAC:",
                "- LTV:",
                "- Churn:",
                "- Runway:",
                "",
                "## Product Progress",
                "-",
                "",
                "## Risks and Mitigations",
                "-",
                "",
                "## Asks",
                "-",
                "",
            ]
        )
        filename.write_text(content, encoding="utf-8")
        self._write_metrics_snapshot(now)

    def _write_daily_outreach(self):
        now = datetime.now(timezone.utc)
        self.last_daily_outreach = now.isoformat()
        targets = [f"Investor_{idx:02d}" for idx in range(1, 11)]
        for investor in targets:
            log_outreach_event(
                self.outreach_log,
                investor=investor,
                stage="Day 0 intro",
                status="queued",
                notes="Automated daily outreach target"
            )

    def _write_narrative_update(self):
        now = datetime.now(timezone.utc)
        self.last_narrative_update = now.isoformat()
        filename = self.base_dir / f"narrative_update_{now.strftime('%Y%m%d')}.md"
        content = "\n".join(
            [
                "# Fundraising Narrative Update",
                f"Date (UTC): {now.isoformat()}",
                "",
                "## Traction Proof",
                "-",
                "",
                "## Customer Evidence",
                "-",
                "",
                "## Product Differentiation",
                "-",
                "",
                "## Objections and Responses",
                "-",
                "",
            ]
        )
        filename.write_text(content, encoding="utf-8")

    def _write_metrics_snapshot(self, now):
        snapshot = {
            "timestamp": now.isoformat(),
            "mrr": None,
            "cac": None,
            "ltv": None,
            "churn": None,
            "runway": None,
        }
        filename = self.base_dir / "metrics_snapshot.json"
        filename.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
