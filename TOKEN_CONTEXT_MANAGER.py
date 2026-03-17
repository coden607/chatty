#!/usr/bin/env python3
"""
TOKEN_CONTEXT_MANAGER.py - Token tracking, compression, and LLM handoff

When a provider's token/context limit is near:
  1. Compress the current context (summarize older messages)
  2. Select the best next LLM that can handle the remaining task
  3. Hand off with compressed context + current task
  4. Continue transparently

Also stores conversation contexts to disk so they can be resumed.
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# ── Token limits per provider/model ───────────────────────────
MODEL_TOKEN_LIMITS: Dict[str, int] = {
    # Anthropic
    "claude-sonnet-4-6":           200_000,
    "claude-opus-4-6":             200_000,
    "claude-haiku-4-5-20251001":   200_000,
    # OpenAI
    "gpt-4o":                      128_000,
    "gpt-4o-mini":                 128_000,
    "gpt-3.5-turbo":                16_385,
    # Groq free
    "llama-3.3-70b-versatile":     128_000,
    "llama-3.1-8b-instant":        128_000,
    "mixtral-8x7b-32768":           32_768,
    "gemma2-9b-it":                  8_192,
    # OpenRouter free
    "meta-llama/llama-3.1-8b-instruct:free": 131_072,
    "microsoft/phi-3-mini-128k-instruct:free": 128_000,
    "mistralai/mistral-7b-instruct:free":      32_768,
    "qwen/qwen-2.5-7b-instruct:free":          32_768,
    # xAI
    "grok-2":                      131_072,
    # NVIDIA
    "nvidia/llama-3.1-nemotron-70b-instruct": 128_000,
    # Ollama (local)
    "llama3.2":                    128_000,
    "mistral":                      32_768,
    "phi3":                        128_000,
    # Default
    "default":                      16_000,
}

HANDOFF_THRESHOLD = 0.80   # warn + prepare handoff at 80% usage
COMPRESS_THRESHOLD = 0.70  # start compressing history at 70%


# ─────────────────────────────────────────────────────────────

@dataclass
class Message:
    role: str       # "system" | "user" | "assistant"
    content: str
    tokens: int = 0
    timestamp: float = field(default_factory=time.time)
    compressed: bool = False

    def estimate_tokens(self) -> int:
        return len(self.content) // 4 + 1


@dataclass
class ConversationContext:
    id: str
    model: str
    provider: str
    messages: List[Message] = field(default_factory=list)
    task_description: str = ""
    handoff_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return sum(m.estimate_tokens() for m in self.messages)

    @property
    def token_limit(self) -> int:
        return MODEL_TOKEN_LIMITS.get(self.model, MODEL_TOKEN_LIMITS["default"])

    @property
    def usage_ratio(self) -> float:
        limit = self.token_limit
        return self.total_tokens / limit if limit > 0 else 0.0

    def is_near_limit(self) -> bool:
        return self.usage_ratio >= HANDOFF_THRESHOLD

    def needs_compression(self) -> bool:
        return self.usage_ratio >= COMPRESS_THRESHOLD


# ─────────────────────────────────────────────────────────────

class TokenContextManager:
    """
    Manages conversation contexts across LLM providers.
    Handles token limit monitoring, compression, and handoff.
    """

    CONTEXT_DIR = Path("generated_content/contexts")

    def __init__(self):
        self.CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
        self._contexts: Dict[str, ConversationContext] = {}
        self._compressor_llm: Optional[Any] = None   # injected
        self._router: Optional[Any] = None            # injected

        # tiktoken is loaded lazily on first use to avoid blocking import
        self._tiktoken = None
        self._tiktoken_tried = False

    def inject_router(self, router: Any):
        """Inject the FREE_LLM_ROUTER instance for handoff generation."""
        self._router = router

    # ── Token counting ─────────────────────────────────────────

    def _get_tiktoken(self):
        """Lazy-load tiktoken on first call (it downloads data files on first use)."""
        if not self._tiktoken_tried:
            self._tiktoken_tried = True
            try:
                import tiktoken
                self._tiktoken = tiktoken.get_encoding("cl100k_base")
            except Exception:
                pass
        return self._tiktoken

    def count_tokens(self, text: str) -> int:
        enc = self._get_tiktoken()
        if enc:
            try:
                return len(enc.encode(text))
            except Exception:
                pass
        return len(text) // 4 + 1

    # ── Context lifecycle ──────────────────────────────────────

    def create_context(self, model: str, provider: str,
                       task_description: str = "",
                       context_id: Optional[str] = None) -> ConversationContext:
        cid = context_id or f"ctx_{int(time.time() * 1000)}"
        ctx = ConversationContext(
            id=cid,
            model=model,
            provider=provider,
            task_description=task_description,
        )
        self._contexts[cid] = ctx
        logger.info(f"📝 Created context {cid} → {provider}/{model} "
                    f"(limit: {ctx.token_limit:,} tokens)")
        return ctx

    def add_message(self, ctx: ConversationContext, role: str, content: str) -> int:
        tokens = self.count_tokens(content)
        ctx.messages.append(Message(role=role, content=content, tokens=tokens))
        ctx.last_updated = time.time()
        usage_pct = int(ctx.usage_ratio * 100)
        if ctx.is_near_limit():
            logger.warning(f"⚠️  Context {ctx.id} at {usage_pct}% token limit "
                           f"({ctx.total_tokens:,}/{ctx.token_limit:,})")
        return tokens

    def get_context(self, ctx_id: str) -> Optional[ConversationContext]:
        if ctx_id in self._contexts:
            return self._contexts[ctx_id]
        return self._load_from_disk(ctx_id)

    # ── Context compression ────────────────────────────────────

    async def compress_context(self, ctx: ConversationContext) -> ConversationContext:
        """
        Summarize older messages to free up token space.
        Keeps system prompt + last 4 exchanges intact.
        """
        if len(ctx.messages) <= 6:
            return ctx

        system_msgs = [m for m in ctx.messages if m.role == "system"]
        other_msgs  = [m for m in ctx.messages if m.role != "system"]

        # Keep the last 4 messages fresh
        to_compress = other_msgs[:-4]
        to_keep     = other_msgs[-4:]

        if not to_compress:
            return ctx

        # Build text to summarize
        history_text = "\n".join(
            f"{m.role.upper()}: {m.content}" for m in to_compress
        )
        summary = await self._summarize(history_text, ctx.task_description)

        compressed_msg = Message(
            role="system",
            content=f"[COMPRESSED HISTORY SUMMARY]\n{summary}\n[END SUMMARY]",
            compressed=True,
        )

        ctx.messages = system_msgs + [compressed_msg] + to_keep
        ctx.last_updated = time.time()

        new_pct = int(ctx.usage_ratio * 100)
        logger.info(f"🗜️  Compressed context {ctx.id} → now at {new_pct}% "
                    f"({ctx.total_tokens:,} tokens)")
        return ctx

    async def _summarize(self, text: str, task_context: str) -> str:
        """Use the cheapest/fastest free model to compress history."""
        system = (
            "You are a compression assistant. Summarize the conversation history "
            "concisely, preserving all key facts, decisions, code snippets, and "
            "action items. Be dense and precise, not verbose."
        )
        user = (
            f"Task context: {task_context}\n\n"
            f"Conversation to compress:\n{text[:8000]}\n\n"
            "Write a dense summary that preserves all critical information."
        )

        if self._router:
            from FREE_LLM_ROUTER import TaskType
            result = await self._router.generate(system, user, max_tokens=512,
                                                  task_type=TaskType.SUMMARIZATION)
            return result.get("text", text[:500] + "... [truncated]")

        # Fallback: extract key sentences
        sentences = text.replace("\n", " ").split(". ")
        return ". ".join(sentences[:20]) + "..."

    # ── LLM handoff ────────────────────────────────────────────

    async def handoff(
        self,
        ctx: ConversationContext,
        next_model: Optional[str] = None,
        next_provider: Optional[str] = None,
        reason: str = "token_limit",
    ) -> ConversationContext:
        """
        Create a new context with compressed history and hand off.
        Returns the new context to continue with.
        """
        logger.info(f"🔀 Handing off context {ctx.id} ({reason}) "
                    f"from {ctx.provider}/{ctx.model}")

        # Compress before handoff
        ctx = await self.compress_context(ctx)
        self.save_to_disk(ctx)

        # Pick next model
        if next_model and next_provider:
            new_model    = next_model
            new_provider = next_provider
        else:
            new_model, new_provider = await self._pick_handoff_target(ctx)

        # Build handoff brief
        handoff_summary = self._build_handoff_brief(ctx)

        new_ctx = self.create_context(
            model=new_model,
            provider=new_provider,
            task_description=ctx.task_description,
            context_id=f"{ctx.id}_h{ctx.handoff_count + 1}",
        )
        new_ctx.handoff_count = ctx.handoff_count + 1
        new_ctx.metadata["previous_context_id"] = ctx.id
        new_ctx.metadata["handoff_reason"] = reason

        # Seed new context with handoff brief
        self.add_message(new_ctx, "system",
                         f"You are continuing a task from a previous AI session.\n\n"
                         f"{handoff_summary}")

        logger.info(f"✅ Handoff complete → new context {new_ctx.id} "
                    f"({new_provider}/{new_model})")
        return new_ctx

    def _build_handoff_brief(self, ctx: ConversationContext) -> str:
        lines = [
            f"TASK: {ctx.task_description}",
            f"PREVIOUS MODEL: {ctx.provider}/{ctx.model}",
            f"HANDOFF #: {ctx.handoff_count + 1}",
            "",
            "CONVERSATION CONTEXT:",
        ]
        for m in ctx.messages[-6:]:   # last 3 exchanges
            prefix = "📌 [SUMMARY]" if m.compressed else m.role.upper()
            lines.append(f"{prefix}: {m.content[:800]}")
        lines += ["", "Continue the task seamlessly from where the previous model left off."]
        return "\n".join(lines)

    async def _pick_handoff_target(self, ctx: ConversationContext) -> Tuple[str, str]:
        """Choose the best model for the handoff based on remaining task needs."""
        # Prefer long-context free models
        long_context_models = [
            ("llama-3.3-70b-versatile",                      "groq"),
            ("meta-llama/llama-3.1-8b-instruct:free",         "openrouter"),
            ("microsoft/phi-3-mini-128k-instruct:free",       "openrouter"),
            ("phi3",                                           "ollama"),
        ]
        # Skip current model
        for model_id, provider in long_context_models:
            if model_id != ctx.model:
                return model_id, provider
        return ("meta-llama/llama-3.1-8b-instruct:free", "openrouter")

    # ── Auto-monitor: check and act ───────────────────────────

    async def check_and_manage(self, ctx: ConversationContext) -> ConversationContext:
        """
        Call this after every add_message to auto-compress/handoff.
        Returns the active context (may be a new one after handoff).
        """
        if ctx.is_near_limit():
            ctx = await self.handoff(ctx, reason="token_limit_80pct")
        elif ctx.needs_compression():
            ctx = await self.compress_context(ctx)
        return ctx

    # ── Persistence ────────────────────────────────────────────

    def save_to_disk(self, ctx: ConversationContext):
        path = self.CONTEXT_DIR / f"{ctx.id}.json"
        data = {
            "id": ctx.id,
            "model": ctx.model,
            "provider": ctx.provider,
            "task_description": ctx.task_description,
            "handoff_count": ctx.handoff_count,
            "created_at": ctx.created_at,
            "last_updated": ctx.last_updated,
            "metadata": ctx.metadata,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "tokens": m.tokens,
                    "timestamp": m.timestamp,
                    "compressed": m.compressed,
                }
                for m in ctx.messages
            ],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.debug(f"💾 Saved context {ctx.id}")

    def _load_from_disk(self, ctx_id: str) -> Optional[ConversationContext]:
        path = self.CONTEXT_DIR / f"{ctx_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        ctx = ConversationContext(
            id=data["id"],
            model=data["model"],
            provider=data["provider"],
            task_description=data.get("task_description", ""),
            handoff_count=data.get("handoff_count", 0),
            created_at=data.get("created_at", time.time()),
            last_updated=data.get("last_updated", time.time()),
            metadata=data.get("metadata", {}),
            messages=[
                Message(
                    role=m["role"],
                    content=m["content"],
                    tokens=m.get("tokens", 0),
                    timestamp=m.get("timestamp", time.time()),
                    compressed=m.get("compressed", False),
                )
                for m in data.get("messages", [])
            ],
        )
        self._contexts[ctx_id] = ctx
        return ctx

    def list_contexts(self) -> List[Dict[str, Any]]:
        saved = []
        for path in self.CONTEXT_DIR.glob("*.json"):
            try:
                with open(path) as f:
                    d = json.load(f)
                saved.append({
                    "id": d["id"],
                    "model": d.get("model"),
                    "provider": d.get("provider"),
                    "task": d.get("task_description", "")[:80],
                    "messages": len(d.get("messages", [])),
                    "handoffs": d.get("handoff_count", 0),
                    "updated": datetime.fromtimestamp(
                        d.get("last_updated", 0)
                    ).strftime("%Y-%m-%d %H:%M"),
                })
            except Exception:
                pass
        return sorted(saved, key=lambda x: x["updated"], reverse=True)

    def status_report(self) -> str:
        contexts = self.list_contexts()
        if not contexts:
            return "No saved contexts."
        lines = [f"📋 {len(contexts)} saved contexts:"]
        for c in contexts[:10]:
            lines.append(
                f"  {c['id']}: {c['provider']}/{c['model']} | "
                f"{c['messages']} msgs | handoffs={c['handoffs']} | {c['updated']}"
            )
        return "\n".join(lines)


# ── Module singleton ───────────────────────────────────────────
_manager: Optional[TokenContextManager] = None

def get_manager() -> TokenContextManager:
    global _manager
    if _manager is None:
        _manager = TokenContextManager()
    return _manager


if __name__ == "__main__":
    async def demo():
        from FREE_LLM_ROUTER import FreeLLMRouter
        mgr = get_manager()
        router = FreeLLMRouter()
        mgr.inject_router(router)

        ctx = mgr.create_context("llama-3.1-8b-instant", "groq",
                                 task_description="Write a Python web scraper")
        mgr.add_message(ctx, "user", "Write a basic Python web scraper using httpx.")
        result = await router.generate(
            "You are a Python expert.",
            "Write a basic Python web scraper using httpx.",
            max_tokens=300,
        )
        text = result.get("text", "")
        mgr.add_message(ctx, "assistant", text)
        ctx = await mgr.check_and_manage(ctx)
        mgr.save_to_disk(ctx)
        print(mgr.status_report())

    asyncio.run(demo())
