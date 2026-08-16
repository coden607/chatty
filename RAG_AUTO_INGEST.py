#!/usr/bin/env python3
"""
RAG_AUTO_INGEST.py - Automatic file watcher for real-time RAG updates

Uses watchdog to monitor directories for new/modified files.
When a file changes, it's automatically re-chunked and re-embedded
into CHATTY_RAG's ChromaDB store.

Monitored by default:
  - Current project directory (.py, .md, .json, .yaml, .txt)
  - generated_content/ (outputs from automation engines)
  - Any additional directories you add via add_watch()

Debounced: rapid saves trigger only one re-ingest (1s debounce).
"""

import asyncio
import logging
import os
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Any, Dict, List, Optional, Set

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

WATCH_EXTENSIONS = {".py", ".md", ".txt", ".json", ".yaml", ".yml",
                    ".toml", ".rst", ".csv", ".ini", ".cfg"}
IGNORE_DIRS      = {".git", "__pycache__", "chroma_db", "node_modules",
                    ".venv", "venv", ".env", "logs", "n8n_workflows"}
DEBOUNCE_SECS    = 2.0
MAX_FILE_SIZE_MB = 5.0


# ─────────────────────────────────────────────────────────────
# Dependency check
# ─────────────────────────────────────────────────────────────

try:
    from watchdog.observers import Observer
    from watchdog.events import (FileSystemEventHandler, FileCreatedEvent,
                                  FileModifiedEvent, FileMovedEvent,
                                  FileDeletedEvent)
    WATCHDOG_OK = True
except ImportError:
    WATCHDOG_OK = False
    logger.info("watchdog not installed: pip install watchdog")
    # Stub classes so the module still imports
    class FileSystemEventHandler:
        pass


# ─────────────────────────────────────────────────────────────
# Event handler
# ─────────────────────────────────────────────────────────────

class RAGFileHandler(FileSystemEventHandler):
    """
    Watchdog handler that queues file changes for debounced ingestion.
    """

    def __init__(self, ingestor: "RAGAutoIngestor"):
        super().__init__()
        self._ingestor = ingestor

    def _should_process(self, path: str) -> bool:
        p = Path(path)
        # Extension filter
        if p.suffix not in WATCH_EXTENSIONS:
            return False
        # Ignore certain dirs
        parts = set(p.parts)
        if parts & IGNORE_DIRS:
            return False
        # Size limit
        try:
            if p.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                return False
        except Exception:
            return False
        return True

    def on_created(self, event):
        if not event.is_directory and self._should_process(event.src_path):
            self._ingestor.queue_file(event.src_path, "created")

    def on_modified(self, event):
        if not event.is_directory and self._should_process(event.src_path):
            self._ingestor.queue_file(event.src_path, "modified")

    def on_moved(self, event):
        if not event.is_directory and self._should_process(event.dest_path):
            self._ingestor.queue_file(event.dest_path, "moved")


# ─────────────────────────────────────────────────────────────
# Auto-ingestor
# ─────────────────────────────────────────────────────────────

class RAGAutoIngestor:
    """
    Watches directories and auto-ingests changed files into CHATTY_RAG.
    """

    def __init__(self, rag=None):
        self._rag = rag
        self._queue: Dict[str, float] = {}    # path → queued_at timestamp
        self._processed: Set[str]     = set() # paths processed this session
        self._observer: Optional[Any] = None
        self._running = False
        self._stats = defaultdict(int)
        self._watched_dirs: List[Path] = []

        if not WATCHDOG_OK:
            logger.warning("watchdog not available — install with: pip install watchdog")

    def _get_rag(self):
        if self._rag is None:
            from CHATTY_RAG import get_rag
            self._rag = get_rag()
        return self._rag

    def _should_process_path(self, path: str | Path) -> bool:
        p = Path(path)
        if p.suffix not in WATCH_EXTENSIONS:
            return False
        if any(part in IGNORE_DIRS for part in p.parts):
            return False
        try:
            if p.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                return False
        except Exception:
            return False
        return True

    # ── Watch management ───────────────────────────────────────

    def add_watch(self, directory: str | Path, recursive: bool = True):
        """Add a directory to watch."""
        path = Path(directory).resolve()
        if not path.exists():
            logger.warning(f"Watch directory does not exist: {path}")
            return
        if path in self._watched_dirs:
            return
        self._watched_dirs.append(path)
        logger.info(f"👁️  Watching: {path} (recursive={recursive})")

        if self._observer and self._running:
            handler = RAGFileHandler(self)
            self._observer.schedule(handler, str(path), recursive=recursive)

    # ── File queue (debounce) ──────────────────────────────────

    def queue_file(self, path: str, event_type: str = "modified"):
        """Queue a file for ingestion with debounce."""
        abs_path = str(Path(path).resolve())
        now = time.time()
        was_queued = abs_path in self._queue
        self._queue[abs_path] = now
        if not was_queued:
            logger.debug(f"📋 Queued [{event_type}]: {Path(abs_path).name}")

    # ── Ingest loop ────────────────────────────────────────────

    async def _process_queue(self):
        """Drain the debounce queue and ingest ready files."""
        now = time.time()
        ready = [p for p, t in list(self._queue.items())
                 if now - t >= DEBOUNCE_SECS]

        rag = self._get_rag()
        for path in ready:
            del self._queue[path]
            try:
                p = Path(path)
                if not p.exists():
                    continue
                n = rag.ingest_file(p)
                self._processed.add(path)
                self._stats["ingested"] += 1
                self._stats["chunks_total"] += n
                logger.info(f"🔄 Auto-ingested {p.name}: {n} chunks")
            except Exception as e:
                self._stats["errors"] += 1
                logger.warning(f"Auto-ingest failed for {path}: {e}")

    # ── Bulk initial ingest ────────────────────────────────────

    async def initial_ingest(self, directories: Optional[List[Path]] = None):
        """
        On startup, ingest all existing files in watched directories.
        Skips files already in ChromaDB (by checking modification time).
        """
        dirs = directories or self._watched_dirs
        rag = self._get_rag()
        total = 0

        for directory in dirs:
            logger.info(f"🚀 Initial ingest: {directory}")
            try:
                for path in directory.rglob("*"):
                    if not path.is_file() or not self._should_process_path(path):
                        continue
                    total += rag.ingest_file(path)
                    await asyncio.sleep(0)
            except Exception as e:
                logger.warning(f"Initial ingest failed for {directory}: {e}")

        logger.info(f"✅ Initial ingest complete: {total} total chunks")
        self._stats["initial_chunks"] = total
        return total

    # ── Main runner ────────────────────────────────────────────

    async def start(self, initial_ingest: bool = True,
                    poll_interval: float = 1.0):
        """
        Start the file watcher and processing loop.
        Pass initial_ingest=True to ingest existing files on startup.
        """
        if not WATCHDOG_OK:
            logger.warning("watchdog not available, running polling fallback")
            await self._polling_fallback(poll_interval)
            return

        if not self._watched_dirs:
            # Default: watch the project root and generated_content
            project_root = Path(__file__).parent
            self.add_watch(project_root)
            self.add_watch(project_root / "generated_content")

        if initial_ingest:
            await self.initial_ingest()

        self._observer = Observer()
        handler = RAGFileHandler(self)
        for directory in self._watched_dirs:
            self._observer.schedule(handler, str(directory), recursive=True)

        self._observer.start()
        self._running = True
        logger.info(f"👁️  RAG auto-ingest watching {len(self._watched_dirs)} directories")

        try:
            while self._running:
                await self._process_queue()
                await asyncio.sleep(poll_interval)
        except asyncio.CancelledError:
            pass
        finally:
            self._observer.stop()
            self._observer.join()
            self._running = False
            logger.info("RAG auto-ingest stopped")

    async def _polling_fallback(self, interval: float = 5.0):
        """
        Fallback when watchdog is unavailable:
        Poll directories every N seconds for mtime changes.
        """
        logger.info("🔄 RAG auto-ingest: polling fallback mode")
        seen_mtimes: Dict[str, float] = {}

        while self._running:
            for directory in self._watched_dirs:
                for ext in WATCH_EXTENSIONS:
                    for p in Path(directory).rglob(f"*{ext}"):
                        if not self._should_process_path(p):
                            continue
                        try:
                            mtime = p.stat().st_mtime
                            if seen_mtimes.get(str(p)) != mtime:
                                seen_mtimes[str(p)] = mtime
                                self.queue_file(str(p), "modified")
                        except Exception:
                            pass

            await self._process_queue()
            await asyncio.sleep(interval)

    def stop(self):
        self._running = False

    def status(self) -> Dict[str, Any]:
        return {
            "running":        self._running,
            "watchdog":       WATCHDOG_OK,
            "watched_dirs":   [str(d) for d in self._watched_dirs],
            "queue_size":     len(self._queue),
            "files_processed": len(self._processed),
            "stats":          dict(self._stats),
            "rag_status":     self._get_rag().status() if self._rag else {},
        }


# ── Module singleton ───────────────────────────────────────────
_ingestor: Optional[RAGAutoIngestor] = None

def get_ingestor(rag=None) -> RAGAutoIngestor:
    global _ingestor
    if _ingestor is None:
        _ingestor = RAGAutoIngestor(rag=rag)
    return _ingestor


if __name__ == "__main__":
    async def demo():
        from CHATTY_RAG import get_rag
        rag = get_rag()
        ingestor = RAGAutoIngestor(rag=rag)

        # Watch just the generated_content directory for demo
        ingestor.add_watch("generated_content", recursive=False)
        ingestor._running = True

        print("Status:", ingestor.status())
        print("Starting 30s watch demo...")
        print("(Create or modify a .txt file in generated_content/ to see it ingest)")

        try:
            await asyncio.wait_for(ingestor.start(initial_ingest=False), timeout=30)
        except asyncio.TimeoutError:
            pass

        print("Final status:", ingestor.status())

    asyncio.run(demo())
