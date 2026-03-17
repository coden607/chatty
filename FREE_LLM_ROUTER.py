#!/usr/bin/env python3
"""
FREE_LLM_ROUTER.py - Intelligent routing to free LLM providers

Priority order (best free models first):
  1. NVIDIA Build API - Kimi K2.5 (free tier, very capable reasoning model)
  2. Google Gemini    - gemini-2.0-flash (free tier, 1M context)
  3. Groq            - llama-3.3-70b, mixtral (fast inference, free tier)
  4. OpenRouter      - many free :free models
  5. Ollama          - fully local, unlimited
  6. HuggingFace     - Inference API free tier

Environment variables:
  NVIDIA_API_KEY        - NVIDIA Build API key (free at build.nvidia.com)
  GOOGLE_API_KEY        - Google AI Studio key (free at aistudio.google.com)
  GROQ_API_KEY          - Groq API key (free at console.groq.com)
  OPENROUTER_API_KEY    - OpenRouter key (free tier models)
  HUGGINGFACE_API_KEY   - HuggingFace token
  OLLAMA_BASE_URL       - Ollama server (default http://localhost:11434)
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
load_dotenv()

_secrets_file = os.getenv("CHATTY_SECRETS_FILE")
if _secrets_file:
    load_dotenv(os.path.expanduser(_secrets_file), override=False)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Task types for routing decisions
# ─────────────────────────────────────────────────────────────

class TaskType(Enum):
    CODING        = "coding"
    REASONING     = "reasoning"
    CREATIVE      = "creative"
    SUMMARIZATION = "summarization"
    ANALYSIS      = "analysis"
    QUICK         = "quick"
    LONG_CONTEXT  = "long_context"


# ─────────────────────────────────────────────────────────────
# Model definitions
# ─────────────────────────────────────────────────────────────

@dataclass
class ModelSpec:
    id: str
    provider: str
    context_tokens: int
    tokens_per_min: int        # rate limit (0 = unlimited)
    strengths: List[TaskType]
    cost_per_1k: float = 0.0   # 0.0 = free
    requires_key: str = ""
    priority: int = 5          # lower = higher priority


FREE_MODELS: List[ModelSpec] = [
    # ── NVIDIA Build API (Kimi K2.5) - best free reasoning model ──
    ModelSpec("moonshotai/kimi-k2.5", "nvidia", 131_072, 0,
              [TaskType.REASONING, TaskType.CODING, TaskType.ANALYSIS,
               TaskType.LONG_CONTEXT, TaskType.CREATIVE],
              requires_key="NVIDIA_API_KEY", priority=1),

    # ── Google Gemini free tier ───────────────────────────────────
    ModelSpec("gemini-2.0-flash",          "gemini", 1_048_576, 0,
              [TaskType.REASONING, TaskType.ANALYSIS, TaskType.LONG_CONTEXT,
               TaskType.CODING, TaskType.CREATIVE],
              requires_key="GOOGLE_API_KEY", priority=2),
    ModelSpec("gemini-2.0-flash-lite",     "gemini",   1_048_576, 0,
              [TaskType.QUICK, TaskType.SUMMARIZATION],
              requires_key="GOOGLE_API_KEY", priority=2),
    ModelSpec("gemini-1.5-flash",          "gemini",   1_048_576, 0,
              [TaskType.LONG_CONTEXT, TaskType.SUMMARIZATION],
              requires_key="GOOGLE_API_KEY", priority=3),

    # ── Groq (fast inference) ─────────────────────────────────────
    ModelSpec("llama-3.3-70b-versatile",   "groq", 128_000, 6_000,
              [TaskType.REASONING, TaskType.ANALYSIS, TaskType.CREATIVE],
              requires_key="GROQ_API_KEY", priority=3),
    ModelSpec("llama-3.1-8b-instant",      "groq", 128_000, 20_000,
              [TaskType.QUICK, TaskType.SUMMARIZATION, TaskType.CODING],
              requires_key="GROQ_API_KEY", priority=3),
    ModelSpec("mixtral-8x7b-32768",        "groq",  32_000,  5_000,
              [TaskType.REASONING, TaskType.CODING],
              requires_key="GROQ_API_KEY", priority=3),
    ModelSpec("gemma2-9b-it",              "groq",   8_192, 15_000,
              [TaskType.QUICK, TaskType.CREATIVE],
              requires_key="GROQ_API_KEY", priority=4),

    # ── OpenRouter free models (:free) ────────────────────────────
    ModelSpec("meta-llama/llama-3.3-70b-instruct:free",      "openrouter", 131_072, 0,
              [TaskType.REASONING, TaskType.ANALYSIS, TaskType.CREATIVE],
              requires_key="OPENROUTER_API_KEY", priority=4),
    ModelSpec("meta-llama/llama-3.1-8b-instruct:free",       "openrouter", 131_072, 0,
              [TaskType.QUICK, TaskType.SUMMARIZATION, TaskType.CODING],
              requires_key="OPENROUTER_API_KEY", priority=4),
    ModelSpec("google/gemma-3-9b-it:free",                   "openrouter",   8_192, 0,
              [TaskType.QUICK, TaskType.CREATIVE],
              requires_key="OPENROUTER_API_KEY", priority=4),
    ModelSpec("microsoft/phi-4-mini-instruct:free",          "openrouter", 131_072, 0,
              [TaskType.LONG_CONTEXT, TaskType.SUMMARIZATION, TaskType.CODING],
              requires_key="OPENROUTER_API_KEY", priority=4),
    ModelSpec("mistralai/mistral-7b-instruct:free",          "openrouter",  32_768, 0,
              [TaskType.CODING, TaskType.REASONING],
              requires_key="OPENROUTER_API_KEY", priority=4),
    ModelSpec("qwen/qwen3-8b:free",                          "openrouter",  40_000, 0,
              [TaskType.CODING, TaskType.ANALYSIS],
              requires_key="OPENROUTER_API_KEY", priority=4),

    # ── Ollama (fully local, unlimited) ──────────────────────────
    ModelSpec("llama3.2",   "ollama", 128_000, 0,
              [TaskType.REASONING, TaskType.CODING], priority=5),
    ModelSpec("mistral",    "ollama",  32_768, 0,
              [TaskType.CODING, TaskType.ANALYSIS], priority=5),
    ModelSpec("phi4",       "ollama", 131_072, 0,
              [TaskType.LONG_CONTEXT, TaskType.SUMMARIZATION], priority=5),
    ModelSpec("codellama",  "ollama",  16_384, 0,
              [TaskType.CODING], priority=5),
    ModelSpec("gemma2:2b",  "ollama",   8_192, 0,
              [TaskType.QUICK], priority=6),

    # ── HuggingFace Inference API ─────────────────────────────────
    ModelSpec("HuggingFaceH4/zephyr-7b-beta", "huggingface", 4_096, 0,
              [TaskType.CREATIVE, TaskType.QUICK],
              requires_key="HUGGINGFACE_API_KEY", priority=6),
]


# ─────────────────────────────────────────────────────────────
# Rate limit tracker
# ─────────────────────────────────────────────────────────────

@dataclass
class ProviderState:
    tokens_used_this_minute: int = 0
    requests_this_minute: int = 0
    minute_start: float = field(default_factory=time.time)
    consecutive_errors: int = 0
    last_error_time: float = 0.0
    cooldown_until: float = 0.0

    def reset_if_new_minute(self):
        if time.time() - self.minute_start >= 60:
            self.tokens_used_this_minute = 0
            self.requests_this_minute = 0
            self.minute_start = time.time()

    def is_cooled_down(self) -> bool:
        return time.time() >= self.cooldown_until

    def record_error(self):
        self.consecutive_errors += 1
        self.last_error_time = time.time()
        backoff = min(300, 30 * self.consecutive_errors)
        self.cooldown_until = time.time() + backoff

    def record_success(self):
        self.consecutive_errors = 0
        self.cooldown_until = 0.0


# ─────────────────────────────────────────────────────────────
# Provider clients
# ─────────────────────────────────────────────────────────────

class FreeLLMRouter:
    """
    Routes LLM requests to the best available free provider.
    Priority: NVIDIA Kimi K2.5 > Gemini > Groq > OpenRouter > Ollama > HuggingFace
    """

    def __init__(self):
        self.nvidia_key      = os.getenv("NVIDIA_API_KEY", "")
        self.google_key      = os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
        self.groq_key        = os.getenv("GROQ_API_KEY", "")
        self.openrouter_key  = os.getenv("OPENROUTER_API_KEY", "")
        self.hf_key          = os.getenv("HUGGINGFACE_API_KEY", "")
        self.ollama_base     = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        self._states: Dict[str, ProviderState] = {}
        self._available_models: List[ModelSpec] = []
        self._ollama_available: Optional[bool] = None

        self._init_available_models()

        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)
        self._log_file = log_path / "free_llm_router.jsonl"

    def _init_available_models(self):
        key_map = {
            "nvidia":      self.nvidia_key,
            "gemini":      self.google_key,
            "groq":        self.groq_key,
            "openrouter":  self.openrouter_key,
            "huggingface": self.hf_key,
            "ollama":      "local",
        }
        for model in FREE_MODELS:
            if model.provider == "ollama":
                self._available_models.append(model)
            elif key_map.get(model.provider):
                self._available_models.append(model)

        configured = [m.provider for m in self._available_models]
        logger.info(f"Free LLM providers available: {sorted(set(configured))}")
        if not self._available_models:
            logger.warning(
                "No free LLM providers configured. "
                "Set NVIDIA_API_KEY, GOOGLE_API_KEY, or GROQ_API_KEY."
            )

    def _state(self, provider: str) -> ProviderState:
        if provider not in self._states:
            self._states[provider] = ProviderState()
        return self._states[provider]

    async def _ollama_ok(self) -> bool:
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(f"{self.ollama_base}/api/tags")
                self._ollama_available = r.status_code == 200
        except Exception:
            self._ollama_available = False
        return self._ollama_available

    def _infer_task_type(self, system_prompt: str, user_prompt: str) -> TaskType:
        text = (system_prompt + " " + user_prompt).lower()
        if any(w in text for w in ["write code", "python", "javascript", "function",
                                    "debug", "implement", "script", "def ", "class "]):
            return TaskType.CODING
        if any(w in text for w in ["summarize", "tldr", "summary", "brief", "condense"]):
            return TaskType.SUMMARIZATION
        if any(w in text for w in ["analyze", "analysis", "evaluate", "assess", "compare"]):
            return TaskType.ANALYSIS
        if any(w in text for w in ["story", "creative", "poem", "blog", "content", "write"]):
            return TaskType.CREATIVE
        if len(user_prompt) > 4000:
            return TaskType.LONG_CONTEXT
        if len(user_prompt) < 200:
            return TaskType.QUICK
        return TaskType.REASONING

    def _score_model(self, model: ModelSpec, task: TaskType,
                     needed_tokens: int, state: ProviderState) -> float:
        if not state.is_cooled_down():
            return -1.0
        if model.context_tokens < needed_tokens:
            return -1.0

        state.reset_if_new_minute()
        if model.tokens_per_min > 0:
            remaining = model.tokens_per_min - state.tokens_used_this_minute
            if remaining < needed_tokens:
                return -1.0

        # Base score inversely proportional to priority number
        score = 20.0 - model.priority * 2

        if task in model.strengths:
            score += 5.0
        if task == TaskType.LONG_CONTEXT:
            score += model.context_tokens / 200_000
        # Provider bonuses for speed
        if model.provider == "groq":
            score += 1.5
        if model.provider == "nvidia":
            score += 2.0   # Kimi K2.5 is excellent
        if model.provider == "gemini":
            score += 1.8
        if model.provider == "ollama":
            score += 0.5   # Local = private, but slower
        # Penalise consecutive errors
        score -= state.consecutive_errors * 2
        return score

    async def _select_model(self, task: TaskType, needed_tokens: int,
                            exclude: Optional[List[str]] = None) -> Optional[ModelSpec]:
        ollama_ok = await self._ollama_ok()
        exclude = exclude or []
        best_score, best_model = -1.0, None
        for model in self._available_models:
            if model.id in exclude:
                continue
            if model.provider == "ollama" and not ollama_ok:
                continue
            state = self._state(model.provider)
            score = self._score_model(model, task, needed_tokens, state)
            if score > best_score:
                best_score, best_model = score, model
        return best_model

    # ── Provider call implementations ─────────────────────────

    async def _call_nvidia(self, model: ModelSpec, system: str, user: str,
                           max_tokens: int) -> str:
        """NVIDIA Build API - hosts Kimi K2.5 and other premium models."""
        import httpx
        headers = {
            "Authorization": f"Bearer {self.nvidia_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        payload = {
            "model": model.id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers=headers, json=payload,
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]

    async def _call_gemini(self, model: ModelSpec, system: str, user: str,
                           max_tokens: int) -> str:
        """Google Gemini via google-generativeai SDK."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.google_key)
            combined_prompt = f"{system}\n\n{user}" if system else user
            genai_model = genai.GenerativeModel(model.id)
            response = await asyncio.to_thread(
                genai_model.generate_content,
                combined_prompt,
                generation_config={"max_output_tokens": max_tokens},
            )
            return response.text
        except ImportError:
            # Fallback: use REST API directly
            import httpx
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model.id}:generateContent?key={self.google_key}"
            )
            payload = {
                "contents": [{"parts": [{"text": f"{system}\n\n{user}" if system else user}]}],
                "generationConfig": {"maxOutputTokens": max_tokens},
            }
            async with httpx.AsyncClient(timeout=90) as c:
                r = await c.post(url, json=payload)
                r.raise_for_status()
                data = r.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_groq(self, model: ModelSpec, system: str, user: str,
                         max_tokens: int) -> str:
        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=self.groq_key)
        except ImportError:
            import openai
            client = openai.AsyncOpenAI(
                api_key=self.groq_key,
                base_url="https://api.groq.com/openai/v1"
            )
        response = await client.chat.completions.create(
            model=model.id,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content

    async def _call_openrouter(self, model: ModelSpec, system: str, user: str,
                               max_tokens: int) -> str:
        import openai
        client = openai.AsyncOpenAI(
            api_key=self.openrouter_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://chatty.ai",
                "X-Title": "Chatty AI Platform",
            },
        )
        response = await client.chat.completions.create(
            model=model.id,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content

    async def _call_ollama(self, model: ModelSpec, system: str, user: str,
                           max_tokens: int) -> str:
        import httpx
        payload = {
            "model": model.id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(f"{self.ollama_base}/api/chat", json=payload)
            r.raise_for_status()
            return r.json()["message"]["content"]

    async def _call_huggingface(self, model: ModelSpec, system: str, user: str,
                                max_tokens: int) -> str:
        import httpx
        prompt = f"<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>\n"
        headers = {"Authorization": f"Bearer {self.hf_key}"}
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}}
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                f"https://api-inference.huggingface.co/models/{model.id}",
                headers=headers, json=payload
            )
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                text = data[0].get("generated_text", "")
                if "<|assistant|>" in text:
                    text = text.split("<|assistant|>")[-1].strip()
                return text
            return str(data)

    async def _dispatch(self, model: ModelSpec, system: str, user: str,
                        max_tokens: int) -> str:
        dispatch = {
            "nvidia":      self._call_nvidia,
            "gemini":      self._call_gemini,
            "groq":        self._call_groq,
            "openrouter":  self._call_openrouter,
            "ollama":      self._call_ollama,
            "huggingface": self._call_huggingface,
        }
        fn = dispatch.get(model.provider)
        if fn is None:
            raise ValueError(f"Unknown provider: {model.provider}")
        return await fn(model, system, user, max_tokens)

    # ── Public API ─────────────────────────────────────────────

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        task_type: Optional[TaskType] = None,
        force_model: Optional[str] = None,
        tried: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate using the best available free model.
        Returns dict: {text, model, provider, tokens_estimated, latency_ms, task_type}
        """
        tried = tried or []
        estimated_input = (len(system_prompt) + len(user_prompt)) // 4
        needed_tokens = estimated_input + max_tokens

        if task_type is None:
            task_type = self._infer_task_type(system_prompt, user_prompt)

        if force_model:
            model = next((m for m in self._available_models if m.id == force_model), None)
        else:
            model = await self._select_model(task_type, needed_tokens, exclude=tried)

        if model is None:
            return {
                "text": "",
                "error": "No free LLM providers available. Configure at least one API key.",
                "model": None,
                "provider": None,
            }

        state = self._state(model.provider)
        t0 = time.time()
        try:
            text = await self._dispatch(model, system_prompt, user_prompt, max_tokens)
            latency = int((time.time() - t0) * 1000)
            state.record_success()
            state.tokens_used_this_minute += needed_tokens
            state.requests_this_minute += 1

            result = {
                "text": text,
                "model": model.id,
                "provider": model.provider,
                "tokens_estimated": needed_tokens,
                "latency_ms": latency,
                "task_type": task_type.value,
            }
            self._log(result)
            logger.debug(f"Generated via {model.provider}/{model.id} in {latency}ms")
            return result

        except Exception as e:
            state.record_error()
            logger.warning(f"❌ {model.provider}/{model.id} failed: {e}")
            tried.append(model.id)
            if len(tried) < 6:
                return await self.generate(
                    system_prompt, user_prompt, max_tokens, task_type, tried=tried
                )
            return {"text": "", "error": str(e), "model": model.id, "provider": model.provider}

    def _log(self, result: Dict[str, Any]):
        try:
            with open(self._log_file, "a") as f:
                f.write(json.dumps({**result, "ts": datetime.utcnow().isoformat()}) + "\n")
        except Exception:
            pass

    def status(self) -> Dict[str, Any]:
        out = {}
        for provider, state in self._states.items():
            state.reset_if_new_minute()
            out[provider] = {
                "available": state.is_cooled_down(),
                "tokens_used_this_min": state.tokens_used_this_minute,
                "errors": state.consecutive_errors,
                "cooldown_until": state.cooldown_until,
            }
        return out

    def available_models(self) -> List[str]:
        return [f"{m.provider}/{m.id}" for m in self._available_models]


# ── Module-level singleton ─────────────────────────────────────
_router: Optional[FreeLLMRouter] = None

def get_router() -> FreeLLMRouter:
    global _router
    if _router is None:
        _router = FreeLLMRouter()
    return _router


async def free_generate(system: str, user: str, max_tokens: int = 1024,
                        task_type: Optional[TaskType] = None) -> str:
    """Convenience wrapper — returns just the text string."""
    result = await get_router().generate(system, user, max_tokens, task_type)
    return result.get("text", result.get("error", ""))


if __name__ == "__main__":
    async def main():
        router = FreeLLMRouter()
        print("Available models:", router.available_models())
        result = await router.generate(
            "You are a helpful assistant.",
            "What is 2+2? Reply in one sentence.",
            max_tokens=50,
        )
        print(f"Response from {result.get('provider')}/{result.get('model')}:")
        print(result.get("text"))

    asyncio.run(main())
