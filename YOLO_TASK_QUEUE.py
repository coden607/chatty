#!/usr/bin/env python3
"""
YOLO_TASK_QUEUE.py - Persistent async task queue for YOLO_MODE

Features:
  - SQLite-backed persistence (survives restarts)
  - Priority queuing (1=critical, 5=low)
  - Retry with exponential backoff (max 3 attempts)
  - Job dependencies (task B waits for task A)
  - Status polling via job ID
  - Concurrency control (N workers)
  - Dead letter queue for permanently failed tasks

Queue lives at: generated_content/yolo_task_queue.db
"""

import asyncio
import json
import logging
import sqlite3
import time
import traceback
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)

DB_PATH   = Path("generated_content/yolo_task_queue.db")
MAX_RETRY = 3
BACKOFF   = [30, 120, 600]   # seconds between retries: 30s, 2m, 10m


class JobStatus(Enum):
    PENDING    = "pending"
    RUNNING    = "running"
    COMPLETED  = "completed"
    FAILED     = "failed"
    RETRYING   = "retrying"
    DEAD       = "dead"         # exhausted all retries
    CANCELLED  = "cancelled"
    WAITING    = "waiting"      # waiting on dependency


@dataclass
class Job:
    id: str
    task: str
    safety_level: str = "cautious"
    priority: int = 3              # 1=high, 5=low
    status: JobStatus = JobStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 0
    max_attempts: int = MAX_RETRY
    retry_after: float = 0.0
    depends_on: Optional[str] = None   # job ID this must wait for
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Job":
        return cls(
            id=row["id"],
            task=row["task"],
            safety_level=row["safety_level"],
            priority=row["priority"],
            status=JobStatus(row["status"]),
            result=row["result"],
            error=row["error"],
            attempts=row["attempts"],
            max_attempts=row["max_attempts"],
            retry_after=row["retry_after"],
            depends_on=row["depends_on"],
            metadata=json.loads(row["metadata"] or "{}"),
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )


# ─────────────────────────────────────────────────────────────
# SQLite store
# ─────────────────────────────────────────────────────────────

class TaskDB:
    def __init__(self, path: Path = DB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id          TEXT PRIMARY KEY,
                    task        TEXT NOT NULL,
                    safety_level TEXT DEFAULT 'cautious',
                    priority    INTEGER DEFAULT 3,
                    status      TEXT DEFAULT 'pending',
                    result      TEXT,
                    error       TEXT,
                    attempts    INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 3,
                    retry_after REAL DEFAULT 0,
                    depends_on  TEXT,
                    metadata    TEXT DEFAULT '{}',
                    created_at  REAL,
                    started_at  REAL,
                    completed_at REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON jobs(priority, created_at)")

    def insert(self, job: Job):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO jobs
                (id, task, safety_level, priority, status, result, error,
                 attempts, max_attempts, retry_after, depends_on, metadata,
                 created_at, started_at, completed_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                job.id, job.task, job.safety_level, job.priority,
                job.status.value, job.result, job.error,
                job.attempts, job.max_attempts, job.retry_after,
                job.depends_on, json.dumps(job.metadata),
                job.created_at, job.started_at, job.completed_at,
            ))

    def update(self, job: Job):
        self.insert(job)

    def get(self, job_id: str) -> Optional[Job]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            return Job.from_row(row) if row else None

    def next_ready(self) -> Optional[Job]:
        """Get highest-priority pending/retrying job that's ready to run."""
        now = time.time()
        with self._conn() as conn:
            row = conn.execute("""
                SELECT * FROM jobs
                WHERE status IN ('pending','retrying')
                  AND retry_after <= ?
                  AND (depends_on IS NULL OR depends_on IN (
                      SELECT id FROM jobs WHERE status='completed'
                  ))
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
            """, (now,)).fetchone()
            return Job.from_row(row) if row else None

    def list_jobs(self, status: Optional[str] = None,
                  limit: int = 50) -> List[Job]:
        with self._conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE status=? ORDER BY created_at DESC LIMIT ?",
                    (status, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [Job.from_row(r) for r in rows]

    def cancel(self, job_id: str) -> bool:
        with self._conn() as conn:
            result = conn.execute("""
                UPDATE jobs SET status='cancelled'
                WHERE id=? AND status IN ('pending','retrying','waiting')
            """, (job_id,))
            return result.rowcount > 0

    def stats(self) -> Dict[str, int]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM jobs GROUP BY status"
            ).fetchall()
            return {r["status"]: r["cnt"] for r in rows}


# ─────────────────────────────────────────────────────────────
# Queue worker
# ─────────────────────────────────────────────────────────────

class YoloTaskQueue:
    """
    Persistent task queue that runs YOLO_MODE tasks asynchronously.
    Workers pick up jobs, execute them, handle retries.
    """

    def __init__(self, workers: int = 2):
        self.db = TaskDB()
        self._workers = workers
        self._running = False
        self._active_jobs: Dict[str, asyncio.Task] = {}
        self._executor = None   # YOLO_MODE executor, injected or built lazily

    def _get_executor(self, safety_level: str):
        from YOLO_MODE import create_yolo_executor
        return create_yolo_executor(safety_level)

    # ── Public API ─────────────────────────────────────────────

    def enqueue(
        self,
        task: str,
        safety_level: str = "cautious",
        priority: int = 3,
        depends_on: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_attempts: int = MAX_RETRY,
    ) -> str:
        """Add a task to the queue. Returns job_id."""
        job = Job(
            id=str(uuid.uuid4()),
            task=task,
            safety_level=safety_level,
            priority=priority,
            depends_on=depends_on,
            metadata=metadata or {},
            max_attempts=max_attempts,
        )
        if depends_on:
            job.status = JobStatus.WAITING
        self.db.insert(job)
        logger.info(f"📥 Queued job {job.id[:8]} (priority={priority}): {task[:60]}")
        return job.id

    def enqueue_chain(self, tasks: List[str],
                       safety_level: str = "cautious") -> List[str]:
        """Enqueue a list of tasks in sequence (each depends on previous)."""
        ids = []
        prev_id = None
        for i, task in enumerate(tasks):
            job_id = self.enqueue(
                task, safety_level,
                priority=3,
                depends_on=prev_id,
            )
            ids.append(job_id)
            prev_id = job_id
        return ids

    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self.db.get(job_id)
        if not job:
            return None
        d = job.to_dict()
        # Add human-readable timing
        if job.started_at:
            d["duration_s"] = round(
                (job.completed_at or time.time()) - job.started_at, 1
            )
        return d

    def cancel(self, job_id: str) -> bool:
        return self.db.cancel(job_id)

    def queue_stats(self) -> Dict[str, Any]:
        stats = self.db.stats()
        return {
            "stats": stats,
            "total": sum(stats.values()),
            "active_workers": len(self._active_jobs),
            "max_workers": self._workers,
        }

    def recent_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        return [j.to_dict() for j in self.db.list_jobs(limit=limit)]

    # ── Job execution ──────────────────────────────────────────

    async def _execute_job(self, job: Job):
        """Run a single job with YOLO_MODE executor."""
        job.status = JobStatus.RUNNING
        job.started_at = time.time()
        job.attempts += 1
        self.db.update(job)
        logger.info(f"▶️  Running job {job.id[:8]}: {job.task[:60]}")

        try:
            executor = self._get_executor(job.safety_level)
            result = await executor.run(job.task)
            job.status   = JobStatus.COMPLETED
            job.result   = json.dumps(result.get("result", ""))[:2000]
            job.completed_at = time.time()
            elapsed = round(job.completed_at - job.started_at, 1)
            logger.info(f"✅ Job {job.id[:8]} done in {elapsed}s: {job.result[:80]}")

        except Exception as e:
            job.error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()[-500:]}"
            logger.error(f"❌ Job {job.id[:8]} error: {e}")

            if job.attempts < job.max_attempts:
                backoff = BACKOFF[min(job.attempts - 1, len(BACKOFF) - 1)]
                job.status      = JobStatus.RETRYING
                job.retry_after = time.time() + backoff
                logger.info(f"🔄 Retry {job.attempts}/{job.max_attempts} "
                            f"for {job.id[:8]} in {backoff}s")
            else:
                job.status       = JobStatus.DEAD
                job.completed_at = time.time()
                logger.warning(f"💀 Job {job.id[:8]} exhausted retries")

        finally:
            self.db.update(job)
            self._active_jobs.pop(job.id, None)

    # ── Worker loop ────────────────────────────────────────────

    async def _worker(self, worker_id: int):
        """Single worker coroutine - polls for ready jobs."""
        logger.debug(f"Worker {worker_id} started")
        while self._running:
            # Don't exceed concurrency limit
            if len(self._active_jobs) >= self._workers:
                await asyncio.sleep(1)
                continue

            job = self.db.next_ready()
            if job and job.id not in self._active_jobs:
                task = asyncio.create_task(self._execute_job(job))
                self._active_jobs[job.id] = task
            else:
                await asyncio.sleep(2)   # poll interval

    async def start(self):
        """Start worker pool. Call this as an async task."""
        self._running = True
        logger.info(f"🚀 YOLO Task Queue started ({self._workers} workers)")
        pending_count = len(self.db.list_jobs("pending")) + len(self.db.list_jobs("retrying"))
        if pending_count:
            logger.info(f"📋 {pending_count} pending/retrying jobs in queue")

        workers = [asyncio.create_task(self._worker(i)) for i in range(self._workers)]
        try:
            await asyncio.gather(*workers)
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            logger.info("YOLO Task Queue stopped")

    def stop(self):
        self._running = False


# ── Module singleton ───────────────────────────────────────────
_queue: Optional[YoloTaskQueue] = None

def get_queue(workers: int = 2) -> YoloTaskQueue:
    global _queue
    if _queue is None:
        _queue = YoloTaskQueue(workers=workers)
    return _queue


if __name__ == "__main__":
    async def demo():
        q = YoloTaskQueue(workers=1)
        print("Queue stats:", q.queue_stats())

        # Enqueue a safe demo task
        job_id = q.enqueue(
            "List all Python files in the current directory",
            safety_level="safe",
            priority=1,
        )
        print(f"Enqueued job: {job_id[:8]}")

        # Run queue for 30 seconds
        task = asyncio.create_task(q.start())
        await asyncio.sleep(30)
        q.stop()
        task.cancel()

        status = q.get_status(job_id)
        print(f"Job status: {status['status']}")
        print(f"Result: {status.get('result', '')[:200]}")

    asyncio.run(demo())
