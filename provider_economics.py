"""Provider-neutral cost and compatibility gates. Stdlib only; opt-in integration."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_read_tokens: int = 0
    cached_write_tokens: int = 0

    def __post_init__(self):
        if min(self.input_tokens, self.output_tokens, self.cached_read_tokens, self.cached_write_tokens) < 0:
            raise ValueError("negative token count")
        if self.cached_read_tokens + self.cached_write_tokens > self.input_tokens:
            raise ValueError("cache tokens exceed input tokens")

@dataclass(frozen=True)
class Rates:
    input_per_million: float
    output_per_million: float
    cache_read_per_million: float | None = None
    cache_write_per_million: float | None = None

    def __post_init__(self):
        vals = (self.input_per_million, self.output_per_million, self.cache_read_per_million, self.cache_write_per_million)
        if any(v is not None and (v < 0 or v != v or v == float("inf")) for v in vals):
            raise ValueError("invalid pricing")

def estimated_usd(usage: Usage, rates: Rates) -> float:
    """Cached input is part of input_tokens, never double-count it."""
    uncached = usage.input_tokens - usage.cached_read_tokens - usage.cached_write_tokens
    read_rate = rates.cache_read_per_million if rates.cache_read_per_million is not None else rates.input_per_million
    write_rate = rates.cache_write_per_million if rates.cache_write_per_million is not None else rates.input_per_million
    return (uncached * rates.input_per_million + usage.cached_read_tokens * read_rate
            + usage.cached_write_tokens * write_rate + usage.output_tokens * rates.output_per_million) / 1_000_000

def prepare_parameters(parameters: Mapping[str, object], *, supports_sampling: bool = True) -> dict:
    """Return a copy; strip sampling only for adapters that explicitly disallow it."""
    result = dict(parameters)
    if not supports_sampling:
        for name in ("temperature", "top_p", "top_k"):
            result.pop(name, None)
    return result

def fallback_allowed(*, side_effect_started: bool, retries: int, max_retries: int,
                     spent_usd: float, budget_usd: float) -> bool:
    """Fail closed after side effects, retry exhaustion, or budget exhaustion."""
    return (not side_effect_started and 0 <= retries < max_retries
            and 0 <= spent_usd < budget_usd)

def choose_strategy(*, complexity: str, verification_available: bool, budget_usd: float) -> str:
    """Deterministic first-pass policy; provider/model selection stays in existing router."""
    if budget_usd <= 0:
        return "blocked"
    if complexity == "high" and verification_available:
        return "critique"
    if verification_available and complexity in ("medium", "high"):
        return "cascade"
    return "single"
