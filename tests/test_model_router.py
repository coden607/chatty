"""Tests for CHATTY_MODEL_ROUTER — failover, circuit breaker, confidence scoring.

All external provider calls are mocked; no network access.
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CHATTY_MODEL_ROUTER import (  # noqa: E402
    GenerationResult,
    ModelProvider,
    ModelRouter,
    TaskType,
)


@pytest.fixture()
def router():
    r = ModelRouter()
    # Deterministic keys: NVIDIA + OpenRouter configured, rest empty.
    r.api_keys = {
        ModelProvider.NVIDIA: ["test-key"],
        ModelProvider.OPENROUTER: ["test-key"],
        ModelProvider.XAI_GROK: [],
        ModelProvider.OPENAI: [],
        ModelProvider.ANTHROPIC: [],
        ModelProvider.COHERE: [],
        ModelProvider.OLLAMA: ["local"],
    }
    r.retry_delay = 0  # keep tests fast
    return r


# ---------------------------------------------------------------- circuit breaker


class TestCircuitBreaker:
    def test_opens_after_threshold_failures(self, router):
        for _ in range(router.circuit_breaker_threshold):
            router._record_failure(ModelProvider.NVIDIA, "boom")
        status = router.status[ModelProvider.NVIDIA]
        assert status.circuit_breaker_open is True
        assert status.circuit_breaker_reset_time is not None

    def test_does_not_open_below_threshold(self, router):
        router._record_failure(ModelProvider.NVIDIA, "boom")
        assert router.status[ModelProvider.NVIDIA].circuit_breaker_open is False

    def test_blocks_requests_while_open(self, router):
        for _ in range(router.circuit_breaker_threshold):
            router._record_failure(ModelProvider.NVIDIA, "boom")
        assert router._check_circuit_breaker(ModelProvider.NVIDIA) is False

    def test_resets_after_timeout(self, router):
        for _ in range(router.circuit_breaker_threshold):
            router._record_failure(ModelProvider.NVIDIA, "boom")
        # Backdate the reset time into the past.
        router.status[ModelProvider.NVIDIA].circuit_breaker_reset_time = (
            datetime.now() - timedelta(seconds=1)
        )
        assert router._check_circuit_breaker(ModelProvider.NVIDIA) is True
        status = router.status[ModelProvider.NVIDIA]
        assert status.circuit_breaker_open is False
        assert status.consecutive_failures == 0

    def test_success_closes_breaker_and_resets_failures(self, router):
        for _ in range(router.circuit_breaker_threshold):
            router._record_failure(ModelProvider.NVIDIA, "boom")
        router._record_success(ModelProvider.NVIDIA, latency=120.0)
        status = router.status[ModelProvider.NVIDIA]
        assert status.circuit_breaker_open is False
        assert status.consecutive_failures == 0
        assert status.success_count == 1

    def test_latency_moving_average(self, router):
        router._record_success(ModelProvider.NVIDIA, latency=100.0)
        router._record_success(ModelProvider.NVIDIA, latency=200.0)
        # EMA: 100 * 0.9 + 200 * 0.1 = 110
        assert router.status[ModelProvider.NVIDIA].average_latency == pytest.approx(110.0)


# ---------------------------------------------------------------- generate / failover


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


class TestGenerateFailover:
    def test_paid_providers_skipped_without_allow_paid(self, router, monkeypatch):
        called = []

        async def fake_try_generate(provider, **kwargs):
            called.append(provider)
            return "ok"

        monkeypatch.setattr(router, "_try_generate", fake_try_generate)
        result = _run(router.generate("hello", task_type=TaskType.CHAT))
        assert result.success is True
        # NVIDIA is first in cloud priority; paid providers never attempted.
        assert result.provider_used == ModelProvider.NVIDIA
        assert ModelProvider.XAI_GROK not in called
        assert ModelProvider.OPENAI not in called
        assert ModelProvider.ANTHROPIC not in called
        assert ModelProvider.COHERE not in called

    def test_falls_back_to_next_provider_on_failure(self, router, monkeypatch):
        async def fake_try_generate(provider, **kwargs):
            if provider == ModelProvider.NVIDIA:
                raise RuntimeError("nvidia down")
            return "openrouter content"

        monkeypatch.setattr(router, "_try_generate", fake_try_generate)
        result = _run(router.generate("hello"))
        assert result.success is True
        assert result.provider_used == ModelProvider.OPENROUTER
        assert result.fallback_used is True
        assert result.content == "openrouter content"

    def test_failure_when_all_providers_fail(self, router, monkeypatch):
        async def failing(provider, **kwargs):
            raise RuntimeError(f"{provider.value} down")

        monkeypatch.setattr(router, "_try_generate", failing)
        router.retry_delay = 0
        result = _run(router.generate("hello"))
        assert result.success is False
        assert result.error is not None
        # One recorded failure per provider after retries are exhausted.
        assert router.status[ModelProvider.NVIDIA].consecutive_failures == 1
        assert router.status[ModelProvider.OPENROUTER].consecutive_failures == 1

    def test_providers_without_keys_are_skipped(self, router, monkeypatch):
        called = []

        async def fake_try_generate(provider, **kwargs):
            called.append(provider)
            return "ok"

        monkeypatch.setattr(router, "_try_generate", fake_try_generate)
        router.api_keys[ModelProvider.NVIDIA] = []  # no key -> skipped
        result = _run(router.generate("hello"))
        assert result.provider_used == ModelProvider.OPENROUTER
        assert ModelProvider.NVIDIA not in called

    def test_open_circuit_breaker_skips_provider(self, router, monkeypatch):
        async def fake_try_generate(provider, **kwargs):
            return "ok"

        monkeypatch.setattr(router, "_try_generate", fake_try_generate)
        for _ in range(router.circuit_breaker_threshold):
            router._record_failure(ModelProvider.NVIDIA, "boom")
        result = _run(router.generate("hello"))
        assert result.success is True
        assert result.provider_used == ModelProvider.OPENROUTER
        assert result.fallback_used is True


# ---------------------------------------------------------------- model selection / confidence


class TestModelSelection:
    def test_model_preference_falls_back_to_default(self, router):
        name = router._get_model_name(ModelProvider.NVIDIA, "nonexistent-pref")
        assert name == router.PROVIDER_MODELS[ModelProvider.NVIDIA]["default"]

    def test_task_priority_map_covers_all_task_types(self, router):
        for task_type in TaskType:
            assert task_type in router.TASK_PROVIDER_PRIORITY
            assert len(router.TASK_PROVIDER_PRIORITY[task_type]) > 0

    def test_confidence_low_for_empty_content(self, router):
        assert router._calculate_confidence("", ModelProvider.OPENAI) == pytest.approx(0.1)

    def test_confidence_penalizes_hallucination_indicators(self, router):
        clean = router._calculate_confidence("A complete and useful answer about marketing.", ModelProvider.OPENAI)
        shaky = router._calculate_confidence("I'm not sure, but here is an answer.", ModelProvider.OPENAI)
        assert shaky < clean


# ---------------------------------------------------------------- health


class TestHealthCheck:
    def test_all_available_is_excellent(self, router):
        assert router.health_check()["overall_health"] == "excellent"

    def test_degraded_when_half_available(self, router):
        providers = list(ModelProvider)
        for p in providers[: len(providers) // 2]:
            router.status[p].circuit_breaker_open = True
        assert router.health_check()["overall_health"] == "degraded"

    def test_critical_when_most_down(self, router):
        providers = list(ModelProvider)
        for p in providers[: len(providers) - 1]:
            router.status[p].circuit_breaker_open = True
        assert router.health_check()["overall_health"] == "critical"

    def test_down_when_all_down(self, router):
        for p in ModelProvider:
            router.status[p].circuit_breaker_open = True
        assert router.health_check()["overall_health"] == "down"

    def test_get_best_provider_respects_keys_and_breakers(self, router):
        router.api_keys[ModelProvider.NVIDIA] = []
        router.api_keys[ModelProvider.OPENROUTER] = []
        assert router.get_best_provider_for_task(TaskType.CHAT) is None
        router.api_keys[ModelProvider.OPENROUTER] = ["k"]
        for _ in range(router.circuit_breaker_threshold):
            router._record_failure(ModelProvider.OPENROUTER, "x")
        assert router.get_best_provider_for_task(TaskType.CHAT) is None
