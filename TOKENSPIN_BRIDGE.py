#!/usr/bin/env python3
"""
TOKENSPIN_BRIDGE.py - Python bridge to the tokenspin LLM proxy

tokenspin (at ~/Projects/tokenspin) runs an OpenAI-compatible proxy on port 4141
that handles intelligent LLM provider rotation, token limit tracking, complexity
classification, and failover.

This bridge:
  1. Starts tokenspin if not running
  2. Routes Chatty LLM calls through it (via OpenAI client pointed at port 4141)
  3. Falls back to FREE_LLM_ROUTER if tokenspin is unavailable
  4. Exposes a unified async generate() that either side can use
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

TOKENSPIN_DIR   = Path.home() / "Projects" / "tokenspin"
TOKENSPIN_PORT  = int(os.getenv("TOKENSPIN_PORT", "4141"))
TOKENSPIN_URL   = f"http://localhost:{TOKENSPIN_PORT}/v1"
STARTUP_TIMEOUT = 10   # seconds to wait for tokenspin to start


class TokenspinBridge:
    """
    Unified LLM interface that prefers tokenspin proxy for rotation,
    falls back to FREE_LLM_ROUTER for direct free-model access.
    """

    def __init__(self):
        self._openai_client: Optional[Any] = None
        self._free_router: Optional[Any] = None
        self._tokenspin_ok: Optional[bool] = None
        self._proc: Optional[subprocess.Popen] = None

    # ── tokenspin health check ─────────────────────────────────

    async def _check_tokenspin(self) -> bool:
        """Ping tokenspin proxy health endpoint."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(f"http://localhost:{TOKENSPIN_PORT}/health")
                return r.status_code == 200
        except Exception:
            return False

    async def _start_tokenspin(self) -> bool:
        """Try to start tokenspin proxy if not running."""
        if not TOKENSPIN_DIR.exists():
            logger.debug("tokenspin directory not found, skipping")
            return False

        node_script = TOKENSPIN_DIR / "bin" / "tokenspin"
        if not node_script.exists():
            return False

        try:
            self._proc = subprocess.Popen(
                ["node", str(node_script), "proxy"],
                cwd=str(TOKENSPIN_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait for it to come up
            for _ in range(STARTUP_TIMEOUT * 2):
                await asyncio.sleep(0.5)
                if await self._check_tokenspin():
                    logger.info(f"✅ tokenspin proxy started on port {TOKENSPIN_PORT}")
                    return True
        except Exception as e:
            logger.debug(f"tokenspin start failed: {e}")
        return False

    async def _ensure_tokenspin(self) -> bool:
        if self._tokenspin_ok is not None:
            return self._tokenspin_ok

        # Check if already running
        if await self._check_tokenspin():
            self._tokenspin_ok = True
            logger.info(f"✅ tokenspin proxy available at {TOKENSPIN_URL}")
            return True

        # Try to start it
        started = await self._start_tokenspin()
        self._tokenspin_ok = started
        if not started:
            logger.info("ℹ️  tokenspin not available, using FREE_LLM_ROUTER directly")
        return started

    def _get_openai_client(self) -> Any:
        if self._openai_client is None:
            import openai
            self._openai_client = openai.AsyncOpenAI(
                api_key="tokenspin",   # tokenspin ignores the key
                base_url=TOKENSPIN_URL,
            )
        return self._openai_client

    def _get_free_router(self) -> Any:
        if self._free_router is None:
            from FREE_LLM_ROUTER import get_router
            self._free_router = get_router()
        return self._free_router

    # ── Public API ─────────────────────────────────────────────

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        model: str = "auto",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate a response. Prefers tokenspin proxy, falls back to free router.
        """
        tokenspin_up = await self._ensure_tokenspin()

        if tokenspin_up:
            return await self._generate_via_tokenspin(
                system_prompt, user_prompt, max_tokens, model
            )
        else:
            return await self._generate_via_free_router(
                system_prompt, user_prompt, max_tokens
            )

    async def _generate_via_tokenspin(
        self,
        system: str,
        user: str,
        max_tokens: int,
        model: str = "auto",
    ) -> Dict[str, Any]:
        t0 = time.time()
        try:
            client = self._get_openai_client()
            kwargs: Dict[str, Any] = dict(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            if model != "auto":
                kwargs["model"] = model
            else:
                kwargs["model"] = "auto"   # tokenspin picks best

            response = await client.chat.completions.create(**kwargs)
            text = response.choices[0].message.content or ""
            used_model = response.model or "tokenspin"
            return {
                "text":       text,
                "model":      used_model,
                "provider":   "tokenspin",
                "latency_ms": int((time.time() - t0) * 1000),
            }
        except Exception as e:
            logger.warning(f"tokenspin call failed: {e}, falling back to free router")
            self._tokenspin_ok = False
            return await self._generate_via_free_router(system, user, max_tokens)

    async def _generate_via_free_router(
        self, system: str, user: str, max_tokens: int
    ) -> Dict[str, Any]:
        router = self._get_free_router()
        return await router.generate(system, user, max_tokens)

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
    ):
        """
        Streaming generation via tokenspin proxy.
        Yields text chunks as strings.
        """
        tokenspin_up = await self._ensure_tokenspin()
        if not tokenspin_up:
            # Fallback: yield full response at once
            result = await self._generate_via_free_router(
                system_prompt, user_prompt, max_tokens
            )
            yield result.get("text", "")
            return

        try:
            client = self._get_openai_client()
            async with client.chat.completions.stream(
                model="auto",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                max_tokens=max_tokens,
            ) as stream:
                async for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
        except Exception as e:
            logger.warning(f"Stream failed: {e}")
            result = await self._generate_via_free_router(
                system_prompt, user_prompt, max_tokens
            )
            yield result.get("text", "")

    def status(self) -> Dict[str, Any]:
        return {
            "tokenspin_available": self._tokenspin_ok,
            "tokenspin_url":       TOKENSPIN_URL,
            "tokenspin_dir":       str(TOKENSPIN_DIR),
            "tokenspin_exists":    TOKENSPIN_DIR.exists(),
        }

    async def stop(self):
        """Stop tokenspin if we started it."""
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()


# ── Module singleton ───────────────────────────────────────────
_bridge: Optional[TokenspinBridge] = None

def get_bridge() -> TokenspinBridge:
    global _bridge
    if _bridge is None:
        _bridge = TokenspinBridge()
    return _bridge


async def smart_generate(system: str, user: str, max_tokens: int = 1024) -> str:
    """
    One-liner: generate text using tokenspin (if up) or free LLMs.
    Returns just the text string.
    """
    bridge = get_bridge()
    result = await bridge.generate(system, user, max_tokens)
    return result.get("text", result.get("error", ""))


if __name__ == "__main__":
    async def demo():
        bridge = TokenspinBridge()
        print("Status:", bridge.status())
        result = await bridge.generate(
            "You are a helpful assistant.",
            "Say hello in three words.",
            max_tokens=20,
        )
        print(f"Response ({result.get('provider')}/{result.get('model')}): {result.get('text')}")

    asyncio.run(demo())
