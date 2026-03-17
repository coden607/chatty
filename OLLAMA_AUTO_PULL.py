#!/usr/bin/env python3
"""
OLLAMA_AUTO_PULL.py - Auto-detect and pull missing Ollama models

When FREE_LLM_ROUTER tries Ollama models that aren't installed,
this module detects the gap and pulls them in the background.

Priority order (smallest → largest):
  1. llama3.2:1b   - 1GB, fastest
  2. llama3.2:3b   - 2GB, good balance
  3. phi3:mini     - 2.3GB, long context
  4. mistral:7b    - 4GB, strong reasoning
  5. codellama:7b  - 4GB, coding tasks
  6. llama3.3:70b  - 43GB, best quality (only if space permits)
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MIN_FREE_GB  = float(os.getenv("OLLAMA_MIN_FREE_GB", "5"))   # don't pull if less free disk


@dataclass
class OllamaModel:
    name: str
    size_gb: float
    priority: int          # lower = pull first
    strengths: List[str] = field(default_factory=list)
    alias: List[str] = field(default_factory=list)


WANTED_MODELS: List[OllamaModel] = [
    OllamaModel("llama3.2:1b",  1.3,  1, ["quick", "fast"],         ["llama3.2"]),
    OllamaModel("llama3.2:3b",  2.0,  2, ["reasoning", "general"],  []),
    OllamaModel("phi3:mini",    2.3,  3, ["long_context", "coding"], ["phi3"]),
    OllamaModel("gemma2:2b",    1.6,  4, ["creative", "quick"],      ["gemma2"]),
    OllamaModel("mistral:7b",   4.1,  5, ["coding", "reasoning"],    ["mistral"]),
    OllamaModel("codellama:7b", 3.8,  6, ["coding"],                 ["codellama"]),
    OllamaModel("llama3.1:8b",  4.7,  7, ["reasoning", "analysis"],  []),
]


class OllamaAutoManager:
    """
    Manages Ollama model availability.
    - Checks which models are installed
    - Auto-pulls missing models (smallest first)
    - Updates FREE_LLM_ROUTER when new models become available
    - Runs as a background daemon
    """

    def __init__(self):
        self._installed: Set[str] = set()
        self._pulling: Set[str] = set()
        self._pull_log: List[Dict] = []
        self._ollama_ok: Optional[bool] = None
        self._log_path = Path("logs/ollama_auto_pull.json")
        self._log_path.parent.mkdir(exist_ok=True)

    # ── Ollama connectivity ────────────────────────────────────

    async def _check_ollama(self) -> bool:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(f"{OLLAMA_BASE}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def list_installed(self) -> Set[str]:
        """Return set of installed model names."""
        if not await self._check_ollama():
            return set()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{OLLAMA_BASE}/api/tags")
                data = r.json()
                names = set()
                for m in data.get("models", []):
                    name = m.get("name", "")
                    names.add(name)
                    # Also add base name (without tag)
                    if ":" in name:
                        names.add(name.split(":")[0])
                self._installed = names
                return names
        except Exception as e:
            logger.debug(f"List installed failed: {e}")
            return set()

    def _is_installed(self, model: OllamaModel) -> bool:
        all_names = {model.name} | set(model.alias)
        return bool(all_names & self._installed)

    # ── Disk space check ───────────────────────────────────────

    def _free_disk_gb(self) -> float:
        try:
            import shutil
            stat = shutil.disk_usage("/")
            return stat.free / (1024 ** 3)
        except Exception:
            return 999.0

    # ── Model pull ─────────────────────────────────────────────

    async def pull_model(self, model_name: str) -> bool:
        """Pull a single model via ollama CLI."""
        if model_name in self._pulling:
            logger.info(f"Already pulling {model_name}")
            return False

        self._pulling.add(model_name)
        logger.info(f"⬇️  Pulling Ollama model: {model_name}")
        t0 = time.time()

        try:
            proc = await asyncio.create_subprocess_exec(
                "ollama", "pull", model_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            elapsed = int(time.time() - t0)

            if proc.returncode == 0:
                logger.info(f"✅ Pulled {model_name} in {elapsed}s")
                self._installed.add(model_name)
                self._log_event(model_name, "success", elapsed)
                return True
            else:
                err = stderr.decode()[:200]
                logger.warning(f"❌ Pull {model_name} failed: {err}")
                self._log_event(model_name, "failed", elapsed, err)
                return False
        except FileNotFoundError:
            logger.warning("ollama CLI not found. Install from https://ollama.com")
            return False
        except Exception as e:
            logger.error(f"Pull error for {model_name}: {e}")
            return False
        finally:
            self._pulling.discard(model_name)

    def _log_event(self, model: str, status: str, elapsed_s: int, error: str = ""):
        entry = {
            "model": model,
            "status": status,
            "elapsed_s": elapsed_s,
            "error": error,
            "ts": datetime.utcnow().isoformat(),
        }
        self._pull_log.append(entry)
        try:
            existing: List[Dict] = []
            if self._log_path.exists():
                existing = json.loads(self._log_path.read_text())
            existing.append(entry)
            self._log_path.write_text(json.dumps(existing[-100:], indent=2))
        except Exception:
            pass

    # ── Auto-pull loop ─────────────────────────────────────────

    async def auto_pull_missing(
        self,
        max_models: int = 3,
        min_priority: int = 5,
    ) -> List[str]:
        """
        Pull missing models up to max_models, ordered by priority.
        Only pulls if enough disk space.
        Returns list of models pulled.
        """
        await self.list_installed()
        free_gb = self._free_disk_gb()
        logger.info(f"💽 Free disk: {free_gb:.1f} GB, installed: {self._installed}")

        if free_gb < MIN_FREE_GB:
            logger.warning(f"⚠️  Only {free_gb:.1f}GB free, skipping auto-pull "
                           f"(need >{MIN_FREE_GB}GB)")
            return []

        pulled = []
        candidates = sorted(
            [m for m in WANTED_MODELS if m.priority <= min_priority
             and not self._is_installed(m)
             and m.size_gb < free_gb - MIN_FREE_GB],
            key=lambda m: m.priority
        )

        for model in candidates[:max_models]:
            success = await self.pull_model(model.name)
            if success:
                pulled.append(model.name)
                free_gb -= model.size_gb   # update estimate
                if free_gb < MIN_FREE_GB:
                    logger.info("Stopping pulls - disk getting low")
                    break

        return pulled

    async def ensure_base_model(self) -> bool:
        """
        Ensure at least one small model is available for YOLO/offline use.
        Returns True if any model is available.
        """
        await self.list_installed()
        if self._installed:
            return True

        # Pull the smallest model
        logger.info("No Ollama models found. Pulling llama3.2:1b as base model...")
        return await self.pull_model("llama3.2:1b")

    # ── Daemon ─────────────────────────────────────────────────

    async def run_daemon(self, check_interval_minutes: int = 30):
        """
        Background daemon: periodically check and pull missing models.
        Also notifies FREE_LLM_ROUTER when models become available.
        """
        logger.info(f"🦙 Ollama auto-pull daemon started (interval={check_interval_minutes}m)")

        while True:
            if await self._check_ollama():
                new_pulls = await self.auto_pull_missing(max_models=2, min_priority=4)
                if new_pulls:
                    logger.info(f"🆕 New Ollama models available: {new_pulls}")
                    # Refresh FREE_LLM_ROUTER's ollama check
                    try:
                        from FREE_LLM_ROUTER import get_router
                        get_router()._ollama_available = None   # force recheck
                    except Exception:
                        pass
            else:
                logger.debug("Ollama not running, skipping check")

            await asyncio.sleep(check_interval_minutes * 60)

    def status(self) -> Dict[str, Any]:
        return {
            "ollama_base":  OLLAMA_BASE,
            "installed":    list(self._installed),
            "currently_pulling": list(self._pulling),
            "free_disk_gb": round(self._free_disk_gb(), 1),
            "pull_log":     self._pull_log[-5:],
            "wanted_models": [
                {"name": m.name, "size_gb": m.size_gb,
                 "installed": self._is_installed(m)}
                for m in WANTED_MODELS
            ],
        }


# ── Module singleton ───────────────────────────────────────────
_manager: Optional[OllamaAutoManager] = None

def get_ollama_manager() -> OllamaAutoManager:
    global _manager
    if _manager is None:
        _manager = OllamaAutoManager()
    return _manager


if __name__ == "__main__":
    async def demo():
        m = OllamaAutoManager()
        installed = await m.list_installed()
        print(f"Installed: {installed}")
        print(f"Free disk: {m._free_disk_gb():.1f} GB")
        print("Status:", json.dumps(m.status(), indent=2))

        if not installed:
            print("\nNo models installed. Pulling base model...")
            await m.ensure_base_model()

    asyncio.run(demo())
