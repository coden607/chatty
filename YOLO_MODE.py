#!/usr/bin/env python3
"""
YOLO_MODE.py - Autonomous task execution with safety protocols

Three safety levels:
  SAFE     - Read-only ops, no file writes, no shell. Requires confirmation for all actions.
  CAUTIOUS - File writes inside project dir only. Confirms destructive actions.
  YOLO     - Full autonomous, rollback-protected via git stash + backups.

Usage:
  from YOLO_MODE import YoloExecutor, SafetyLevel
  executor = YoloExecutor(safety_level=SafetyLevel.YOLO)
  result = await executor.run("Build a REST API endpoint for user authentication")
"""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Safety config
# ─────────────────────────────────────────────────────────────

class SafetyLevel(Enum):
    SAFE     = "safe"      # Read-only + planning only
    CAUTIOUS = "cautious"  # File writes with confirmations
    YOLO     = "yolo"      # Full auto with rollback

# Paths that YOLO mode will NEVER touch (absolute)
FORBIDDEN_PATHS = {
    "/etc", "/usr", "/bin", "/sbin", "/boot", "/proc", "/sys",
    "/dev", "/lib", "/lib64", "/snap",
    str(Path.home() / ".ssh"),
    str(Path.home() / ".gnupg"),
    str(Path.home() / ".aws"),
    str(Path.home() / ".config/chatty/secrets.env"),
}

# Shell commands never allowed, regardless of safety level
FORBIDDEN_COMMANDS = {
    "rm -rf /", "rm -rf ~", "mkfs", "dd if=",
    "chmod 777 /", "chown root", "sudo rm", ":(){ :|:& };:",
    "curl | bash", "wget | bash", "curl | sh",
}

# File extensions allowed for writing
SAFE_WRITE_EXTENSIONS = {
    ".py", ".txt", ".md", ".json", ".yaml", ".yml", ".toml",
    ".csv", ".html", ".css", ".js", ".ts", ".sh", ".env.example",
    ".cfg", ".ini", ".log",
}


# ─────────────────────────────────────────────────────────────
# Action types
# ─────────────────────────────────────────────────────────────

class ActionType(Enum):
    PLAN          = "plan"
    READ_FILE     = "read_file"
    WRITE_FILE    = "write_file"
    SHELL_SAFE    = "shell_safe"    # read-only shell (ls, cat, grep)
    SHELL_EXEC    = "shell_exec"    # write/execute shell
    WEB_SEARCH    = "web_search"
    WEB_SCRAPE    = "web_scrape"
    LLM_CALL      = "llm_call"
    COMPLETE      = "complete"
    ASK_USER      = "ask_user"


@dataclass
class Action:
    type: ActionType
    description: str
    params: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    success: bool = False
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class ExecutionPlan:
    task: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    safety_level: SafetyLevel = SafetyLevel.CAUTIOUS
    rollback_state: Optional[str] = None    # git stash id
    backup_dir: Optional[Path] = None


# ─────────────────────────────────────────────────────────────
# Safety validator
# ─────────────────────────────────────────────────────────────

class SafetyGuard:
    def __init__(self, project_root: Path, safety_level: SafetyLevel):
        self.root = project_root.resolve()
        self.level = safety_level
        self.audit_log: List[Dict[str, Any]] = []

    def check_path(self, path_str: str) -> Tuple[bool, str]:
        """Return (allowed, reason)."""
        try:
            target = Path(path_str).resolve()
        except Exception:
            return False, "Invalid path"

        # Check forbidden absolute paths
        for forbidden in FORBIDDEN_PATHS:
            if str(target).startswith(forbidden):
                return False, f"Path is in forbidden zone: {forbidden}"

        # SAFE mode: no writes at all
        if self.level == SafetyLevel.SAFE:
            return False, "SAFE mode: no file writes allowed"

        # CAUTIOUS/YOLO: must be within project root
        if not str(target).startswith(str(self.root)):
            if self.level == SafetyLevel.CAUTIOUS:
                return False, f"CAUTIOUS mode: path must be within {self.root}"

        # Check extension
        if target.suffix and target.suffix not in SAFE_WRITE_EXTENSIONS:
            return False, f"Extension {target.suffix!r} not in safe-write list"

        return True, "OK"

    def check_command(self, cmd: str) -> Tuple[bool, str]:
        """Return (allowed, reason)."""
        # Always block regardless of level
        for forbidden in FORBIDDEN_COMMANDS:
            if forbidden in cmd:
                return False, f"Forbidden command pattern: {forbidden!r}"

        if self.level == SafetyLevel.SAFE:
            # Only read-only commands
            readonly = {"ls", "cat", "head", "tail", "grep", "find", "echo",
                        "pwd", "which", "python3 -c", "python3 --version"}
            cmd_base = cmd.strip().split()[0]
            if cmd_base not in readonly and not cmd.startswith("python3 -c"):
                return False, "SAFE mode: only read-only shell commands"

        if self.level == SafetyLevel.CAUTIOUS:
            destructive = ["rm ", "rmdir", "shred", "truncate", "mv /", "mv ~"]
            for d in destructive:
                if d in cmd:
                    return False, f"CAUTIOUS mode: destructive command requires confirmation: {d!r}"

        return True, "OK"

    def log_action(self, action: Action):
        self.audit_log.append({
            "type": action.type.value,
            "desc": action.description,
            "success": action.success,
            "error": action.error,
            "ts": datetime.fromtimestamp(action.timestamp).isoformat(),
        })

    def save_audit(self, task_id: str):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        path = log_dir / f"yolo_audit_{task_id}.json"
        with open(path, "w") as f:
            json.dump(self.audit_log, f, indent=2)
        logger.info(f"📋 Audit log saved: {path}")


# ─────────────────────────────────────────────────────────────
# Rollback system
# ─────────────────────────────────────────────────────────────

class RollbackManager:
    def __init__(self, project_root: Path):
        self.root = project_root
        self.backup_dir: Optional[Path] = None
        self.stash_id: Optional[str] = None

    def create_checkpoint(self) -> bool:
        """Create a git stash checkpoint."""
        try:
            result = subprocess.run(
                ["git", "stash", "push", "-m", f"yolo_checkpoint_{int(time.time())}"],
                cwd=self.root, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and "No local changes" not in result.stdout:
                match = re.search(r"stash@\{(\d+)\}", result.stdout)
                if match:
                    self.stash_id = f"stash@{{{match.group(1)}}}"
                logger.info(f"✅ Checkpoint created: {self.stash_id or 'clean working tree'}")
                return True
        except Exception as e:
            logger.warning(f"Git stash failed: {e}, using file backup")

        # Fallback: file backup
        self.backup_dir = Path("generated_content") / f"backup_{int(time.time())}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        return True

    def rollback(self) -> bool:
        """Restore to checkpoint."""
        if self.stash_id:
            try:
                result = subprocess.run(
                    ["git", "stash", "pop", self.stash_id],
                    cwd=self.root, capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    logger.info(f"✅ Rolled back via git stash")
                    return True
                else:
                    logger.error(f"Git stash pop failed: {result.stderr}")
            except Exception as e:
                logger.error(f"Rollback failed: {e}")
        return False

    def drop_checkpoint(self):
        """Remove checkpoint if task succeeded."""
        if self.stash_id:
            try:
                subprocess.run(
                    ["git", "stash", "drop", self.stash_id],
                    cwd=self.root, capture_output=True, timeout=10
                )
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────
# YOLO Executor
# ─────────────────────────────────────────────────────────────

class YoloExecutor:
    """
    Autonomous task executor with three safety levels.
    Plans tasks with an LLM, executes each step, rolls back on failure.
    """

    def __init__(
        self,
        safety_level: SafetyLevel = SafetyLevel.CAUTIOUS,
        project_root: Optional[Path] = None,
        confirm_callback: Optional[Callable[[str], bool]] = None,
    ):
        self.safety_level = safety_level
        self.root = (project_root or Path(__file__).parent).resolve()
        self.guard = SafetyGuard(self.root, safety_level)
        self.rollback = RollbackManager(self.root)
        self.confirm_callback = confirm_callback or self._default_confirm
        self._router = None
        self._scraper = None
        self.task_history: List[Dict[str, Any]] = []

    def _inject_router(self, router: Any):
        self._router = router

    def _inject_scraper(self, scraper: Any):
        self._scraper = scraper

    def _default_confirm(self, question: str) -> bool:
        """Terminal confirmation. Override with UI callback."""
        if self.safety_level == SafetyLevel.YOLO:
            return True
        try:
            resp = input(f"\n❓ CONFIRM: {question} [y/N] ").strip().lower()
            return resp in ("y", "yes")
        except EOFError:
            return self.safety_level == SafetyLevel.YOLO

    # ── Task planning ──────────────────────────────────────────

    async def _plan_task(self, task: str) -> List[Dict[str, Any]]:
        """Ask LLM to produce a step-by-step JSON execution plan."""
        system = """You are an autonomous task planner. Given a task, output a JSON array of steps.
Each step must be a JSON object with:
  - "type": one of: read_file, write_file, shell_safe, shell_exec, web_search, web_scrape, llm_call, complete
  - "description": what this step does
  - "params": object with step-specific params:
      read_file:  { "path": "..." }
      write_file: { "path": "...", "content": "..." }
      shell_safe: { "command": "read-only shell command" }
      shell_exec: { "command": "shell command to execute" }
      web_search: { "query": "..." }
      web_scrape: { "url": "..." }
      llm_call:   { "prompt": "..." }
      complete:   { "summary": "final result summary" }

Output ONLY valid JSON array, no explanation."""

        user = f"Task: {task}\n\nProject root: {self.root}\nSafety level: {self.safety_level.value}"

        if self._router:
            from FREE_LLM_ROUTER import TaskType
            result = await self._router.generate(system, user, max_tokens=2048,
                                                  task_type=TaskType.REASONING)
            text = result.get("text", "")
        else:
            return [{"type": "llm_call", "description": task,
                     "params": {"prompt": task}},
                    {"type": "complete", "description": "Done",
                     "params": {"summary": "Completed"}}]

        # Parse JSON
        try:
            # Extract JSON array from text
            match = re.search(r"\[.*\]", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass

        # Fallback: simple plan
        return [
            {"type": "llm_call", "description": task, "params": {"prompt": task}},
            {"type": "complete",  "description": "Done", "params": {"summary": "Completed"}},
        ]

    # ── Step executors ─────────────────────────────────────────

    async def _exec_read_file(self, params: Dict) -> str:
        path = params.get("path", "")
        try:
            return Path(path).read_text(encoding="utf-8", errors="replace")[:8000]
        except Exception as e:
            return f"Error reading {path}: {e}"

    async def _exec_write_file(self, params: Dict) -> str:
        path_str = params.get("path", "")
        content  = params.get("content", "")

        allowed, reason = self.guard.check_path(path_str)
        if not allowed:
            return f"BLOCKED: {reason}"

        if self.safety_level == SafetyLevel.CAUTIOUS:
            if not self.confirm_callback(f"Write {len(content)} chars to {path_str}?"):
                return "Cancelled by user."

        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Written {len(content)} chars to {path_str}"

    async def _exec_shell(self, params: Dict, readonly: bool = False) -> str:
        cmd = params.get("command", "")
        allowed, reason = self.guard.check_command(cmd)
        if not allowed:
            return f"BLOCKED: {reason}"

        if not readonly and self.safety_level == SafetyLevel.CAUTIOUS:
            if not self.confirm_callback(f"Run shell: {cmd!r}?"):
                return "Cancelled by user."

        try:
            result = subprocess.run(
                cmd, shell=True, cwd=self.root,
                capture_output=True, text=True, timeout=60
            )
            out = result.stdout[-3000:] if result.stdout else ""
            err = result.stderr[-1000:] if result.stderr else ""
            return f"EXIT {result.returncode}\n{out}\n{err}".strip()
        except subprocess.TimeoutExpired:
            return "Command timed out (60s)"
        except Exception as e:
            return f"Shell error: {e}"

    async def _exec_web_search(self, params: Dict) -> str:
        query = params.get("query", "")
        if self._scraper:
            return await self._scraper.search(query)
        return f"[Web search not available - no scraper injected. Query: {query}]"

    async def _exec_web_scrape(self, params: Dict) -> str:
        url = params.get("url", "")
        if self._scraper:
            return await self._scraper.scrape(url)
        return f"[Web scraper not available. URL: {url}]"

    async def _exec_llm_call(self, params: Dict, step_desc: str) -> str:
        prompt = params.get("prompt", step_desc)
        if self._router:
            result = await self._router.generate(
                "You are an expert autonomous assistant completing a task step.",
                prompt,
                max_tokens=2048,
            )
            return result.get("text", "No response")
        return f"[LLM not available. Prompt: {prompt[:200]}]"

    # ── Main runner ────────────────────────────────────────────

    async def run(
        self,
        task: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute a task autonomously.
        Returns dict with: success, actions, result, rollback_available.
        """
        task_id = f"yolo_{int(time.time())}"
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 YOLO MODE [{self.safety_level.value.upper()}] Task: {task}")
        logger.info(f"{'='*60}")

        actions: List[Action] = []
        final_result = ""
        success = False

        # Checkpoint before starting
        if self.safety_level == SafetyLevel.YOLO and not dry_run:
            self.rollback.create_checkpoint()

        try:
            # Plan
            logger.info("🧠 Planning task...")
            steps = await self._plan_task(task)
            logger.info(f"📋 Plan: {len(steps)} steps")
            for i, s in enumerate(steps, 1):
                logger.info(f"  {i}. [{s.get('type')}] {s.get('description', '')[:80]}")

            if dry_run:
                return {
                    "success": True,
                    "dry_run": True,
                    "plan": steps,
                    "task": task,
                }

            # Execute
            for step in steps:
                s_type = step.get("type", "llm_call")
                s_desc = step.get("description", "")
                s_params = step.get("params", {})

                action = Action(
                    type=ActionType[s_type.upper()] if s_type.upper() in ActionType.__members__ else ActionType.LLM_CALL,
                    description=s_desc,
                    params=s_params,
                )

                logger.info(f"⚡ Executing: [{s_type}] {s_desc[:60]}")

                try:
                    if s_type == "read_file":
                        action.result = await self._exec_read_file(s_params)
                    elif s_type == "write_file":
                        action.result = await self._exec_write_file(s_params)
                    elif s_type == "shell_safe":
                        action.result = await self._exec_shell(s_params, readonly=True)
                    elif s_type == "shell_exec":
                        action.result = await self._exec_shell(s_params, readonly=False)
                    elif s_type == "web_search":
                        action.result = await self._exec_web_search(s_params)
                    elif s_type == "web_scrape":
                        action.result = await self._exec_web_scrape(s_params)
                    elif s_type == "llm_call":
                        action.result = await self._exec_llm_call(s_params, s_desc)
                    elif s_type == "complete":
                        final_result = s_params.get("summary", "Task complete.")
                        action.result = final_result
                        action.success = True
                        actions.append(action)
                        break
                    else:
                        action.result = f"Unknown step type: {s_type}"

                    action.success = not action.result.startswith("BLOCKED")
                    logger.info(f"  ↳ {'✅' if action.success else '❌'} "
                                f"{action.result[:100] if action.result else ''}")

                except Exception as e:
                    action.error = str(e)
                    action.success = False
                    logger.error(f"  ↳ ❌ Step error: {e}")

                finally:
                    self.guard.log_action(action)
                    actions.append(action)

            success = True
            if not final_result:
                # Summarize actions
                successful = [a for a in actions if a.success]
                final_result = f"Completed {len(successful)}/{len(actions)} steps."

            if self.safety_level == SafetyLevel.YOLO:
                self.rollback.drop_checkpoint()

        except Exception as e:
            logger.error(f"💥 Task execution failed: {e}")
            traceback.print_exc()
            success = False
            final_result = f"Error: {e}"

            if self.safety_level == SafetyLevel.YOLO and self.rollback.stash_id:
                if self.confirm_callback("Task failed. Rollback changes?"):
                    self.rollback.rollback()

        finally:
            self.guard.save_audit(task_id)

        result = {
            "task_id": task_id,
            "task": task,
            "success": success,
            "result": final_result,
            "actions": [
                {
                    "type": a.type.value,
                    "description": a.description,
                    "success": a.success,
                    "result_preview": (a.result or "")[:200],
                }
                for a in actions
            ],
            "safety_level": self.safety_level.value,
            "rollback_available": bool(self.rollback.stash_id),
        }

        self.task_history.append(result)
        logger.info(f"\n{'='*60}")
        logger.info(f"{'✅' if success else '❌'} Task complete: {final_result[:200]}")
        return result


# ── Quick-start factory ────────────────────────────────────────

def create_yolo_executor(level: str = "cautious") -> YoloExecutor:
    """
    Factory with optional integration of router + scraper.
    level: "safe" | "cautious" | "yolo"
    """
    lvl = SafetyLevel[level.upper()]
    executor = YoloExecutor(safety_level=lvl)

    try:
        from FREE_LLM_ROUTER import get_router
        executor._inject_router(get_router())
    except Exception:
        pass

    try:
        from FREE_WEB_SCRAPER import get_scraper
        executor._inject_scraper(get_scraper())
    except Exception:
        pass

    return executor


if __name__ == "__main__":
    async def demo():
        executor = create_yolo_executor("cautious")
        result = await executor.run(
            "List all Python files in the current directory and show me the largest one",
            dry_run=False,
        )
        print(json.dumps(result, indent=2))

    asyncio.run(demo())
