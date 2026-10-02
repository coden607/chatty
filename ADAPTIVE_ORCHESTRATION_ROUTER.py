#!/usr/bin/env python3
"""Adaptive orchestration policy for CHATTY.

This module sits above the existing framework/model routers. It makes a cheap,
deterministic routing decision before expensive model calls:
- detect project/task/risk/complexity
- assign a token/context budget
- choose the cheapest capable execution tier
- select framework/persona/skills
- require verification and define escalation triggers

It deliberately contains no provider SDK calls so it is cheap, testable, and
safe to import from any CHATTY entrypoint.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence
import json
import re


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    STRATEGIC = "strategic"


class Risk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModelTier(str, Enum):
    FREE_LOCAL = "free_local"
    FREE_CLOUD = "free_cloud"
    FAST_PAID = "fast_paid"
    STRONG_PAID = "strong_paid"


@dataclass(frozen=True)
class ModelCandidate:
    name: str
    provider: str
    tier: ModelTier
    strengths: Sequence[str]
    max_context: int = 128_000
    estimated_cost_per_million_input: float = 0.0
    priority: int = 100


DEFAULT_MODELS: Sequence[ModelCandidate] = (
    ModelCandidate("llama3.2", "ollama", ModelTier.FREE_LOCAL,
                   ("quick", "summarization", "coding"), priority=10),
    ModelCandidate("llama-3.1-8b-instant", "groq", ModelTier.FREE_CLOUD,
                   ("quick", "summarization", "coding"), priority=20),
    ModelCandidate("gemini-2.0-flash-lite", "gemini", ModelTier.FREE_CLOUD,
                   ("quick", "summarization"), max_context=1_000_000, priority=21),
    ModelCandidate("qwen/qwen3-coder:free", "openrouter", ModelTier.FREE_CLOUD,
                   ("coding", "analysis"), max_context=262_000, priority=22),
    ModelCandidate("moonshotai/kimi-k2.5", "nvidia", ModelTier.FREE_CLOUD,
                   ("reasoning", "coding", "analysis", "research"),
                   max_context=131_072, priority=23),
    ModelCandidate("fast-paid", "configured", ModelTier.FAST_PAID,
                   ("quick", "coding", "analysis", "research"), priority=50),
    ModelCandidate("strong-paid", "configured", ModelTier.STRONG_PAID,
                   ("reasoning", "coding", "analysis", "research", "legal"),
                   priority=90),
)


PROJECT_KEYWORDS: Dict[str, Sequence[str]] = {
    "narcoguard": ("narcoguard", "guardian", "overdose", "relapse", "stability signal"),
    "airbear": ("airbear", "rickshaw", "tuk-tuk", "72v", "solar ride"),
    "cortese": ("cortese", "missed call", "pizza", "twilio"),
    "brendan440": ("brendan440", "cpl 440", "probation", "vop", "restitution"),
    "nextlaw607": ("nextlaw", "courtlistener", "legal terminal"),
    "chatty": ("chatty", "openclaw", "orchestration", "router", "agent"),
}


TASK_RULES: Sequence[tuple[str, Sequence[str]]] = (
    ("coding", ("code", "implement", "build", "fix", "debug", "repo", "pull request", "ci")),
    ("research", ("research", "investigate", "find sources", "compare evidence", "case law")),
    ("deployment", ("deploy", "ship", "vercel", "production", "release")),
    ("analysis", ("analyze", "analysis", "review", "audit", "diagnose")),
    ("summarization", ("summarize", "recap", "brief")),
    ("quick", ("what is", "where is", "how much", "simple")),
)


@dataclass
class RoutingPlan:
    project: str
    task_type: str
    complexity: Complexity
    risk: Risk
    model_tier: ModelTier
    model: str
    provider: str
    framework: str
    persona: str
    skills: List[str]
    context_budget_tokens: int
    output_budget_tokens: int
    parallel_agents: int
    require_verification: bool
    escalation_reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        data = asdict(self)
        for k in ("complexity", "risk", "model_tier"):
            data[k] = getattr(self, k).value
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


class AdaptiveOrchestrationRouter:
    """Cheap policy router that minimizes token and provider spend."""

    def __init__(self, models: Sequence[ModelCandidate] = DEFAULT_MODELS):
        self.models = tuple(models)

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip().lower())

    def detect_project(self, text: str, explicit: Optional[str] = None) -> str:
        if explicit:
            return explicit.strip().lower()
        t = self._normalize(text)
        scores = {
            project: sum(1 for kw in words if kw in t)
            for project, words in PROJECT_KEYWORDS.items()
        }
        best = max(scores, key=scores.get)
        return best if scores[best] else "general"

    def detect_task_type(self, text: str, explicit: Optional[str] = None) -> str:
        if explicit:
            return explicit.strip().lower()
        t = self._normalize(text)
        for task_type, words in TASK_RULES:
            if any(word in t for word in words):
                return task_type
        return "quick"

    def estimate_complexity(self, text: str, task_type: str) -> Complexity:
        t = self._normalize(text)
        strategic = ("fully ship", "end-to-end", "architecture", "orchestrat", "multi-agent")
        high = ("production", "security", "migration", "cross-repo", "root cause", "legal")
        if any(x in t for x in strategic):
            return Complexity.STRATEGIC
        if task_type in {"deployment", "research"} or any(x in t for x in high):
            return Complexity.HIGH
        if len(t) > 700 or task_type in {"coding", "analysis"}:
            return Complexity.MEDIUM
        return Complexity.LOW

    def estimate_risk(self, text: str, project: str, task_type: str) -> Risk:
        t = self._normalize(text)
        if project in {"brendan440"} or any(
            x in t for x in ("production deploy", "delete", "secrets", "credential", "payment", "legal filing")
        ):
            return Risk.HIGH
        if task_type in {"deployment", "coding"} or project in {"narcoguard", "airbear"}:
            return Risk.MEDIUM
        return Risk.LOW

    @staticmethod
    def budgets(complexity: Complexity) -> tuple[int, int, int]:
        if complexity == Complexity.LOW:
            return 4_000, 800, 1
        if complexity == Complexity.MEDIUM:
            return 12_000, 2_000, 1
        if complexity == Complexity.HIGH:
            return 28_000, 4_000, 2
        return 48_000, 6_000, 3

    @staticmethod
    def framework_for(task_type: str, complexity: Complexity) -> str:
        if complexity in {Complexity.HIGH, Complexity.STRATEGIC}:
            return "archon2" if task_type in {"deployment", "analysis", "research"} else "langgraph_supervisor"
        if task_type == "coding":
            return "openclaw"
        if task_type == "research":
            return "mcp"
        if task_type == "analysis":
            return "pydantic_ai"
        return "smolagents"

    @staticmethod
    def persona_for(project: str, task_type: str) -> str:
        if project == "narcoguard":
            return "NarcoGuard Safety-Conscious Product Engineer"
        if project == "airbear":
            return "AirBear Systems and Full-Stack Engineer"
        if project == "brendan440":
            return "New York Post-Judgment Legal Researcher"
        if project == "cortese":
            return "Cortese Communications Automation Engineer"
        if project == "chatty":
            return "CHATTY Orchestration Engineer"
        return f"{task_type.replace('_', ' ').title()} Specialist"

    @staticmethod
    def skills_for(project: str, task_type: str) -> List[str]:
        skills: List[str] = []
        if task_type == "coding":
            skills += ["repo-inspection", "unit-tests", "ci"]
        elif task_type == "deployment":
            skills += ["repo-inspection", "ci", "deployment", "live-smoke"]
        elif task_type == "research":
            skills += ["source-retrieval", "evidence-check"]
        elif task_type == "analysis":
            skills += ["structured-analysis", "verification"]
        if project != "general":
            skills.append(f"project:{project}")
        return skills

    @staticmethod
    def desired_strength(task_type: str, complexity: Complexity) -> str:
        if task_type == "coding":
            return "coding"
        if task_type == "research":
            return "research"
        if task_type in {"analysis", "deployment"}:
            return "analysis"
        if complexity in {Complexity.HIGH, Complexity.STRATEGIC}:
            return "reasoning"
        return "quick"

    def choose_model(
        self,
        strength: str,
        complexity: Complexity,
        risk: Risk,
        context_budget: int,
        unavailable_providers: Iterable[str] = (),
        allow_paid: bool = False,
    ) -> ModelCandidate:
        unavailable = {p.lower() for p in unavailable_providers}
        eligible = [
            m for m in self.models
            if m.provider.lower() not in unavailable
            and m.max_context >= context_budget
            and (strength in m.strengths or "reasoning" in m.strengths)
        ]
        # Cheapest capable first. Strong paid becomes eligible by policy only
        # for high-risk/strategic work; otherwise free tiers are preferred.
        max_tier = ModelTier.STRONG_PAID if (
            risk == Risk.HIGH or complexity == Complexity.STRATEGIC
        ) else ModelTier.FAST_PAID
        order = {
            ModelTier.FREE_LOCAL: 0,
            ModelTier.FREE_CLOUD: 1,
            ModelTier.FAST_PAID: 2,
            ModelTier.STRONG_PAID: 3,
        }
        eligible = [m for m in eligible if order[m.tier] <= order[max_tier]]
        if not allow_paid:
            eligible = [m for m in eligible if m.tier in {
                ModelTier.FREE_LOCAL, ModelTier.FREE_CLOUD,
            }]
        if not eligible:
            raise RuntimeError(
                "No capable model available within context and paid-fallback policy"
            )
        eligible.sort(key=lambda m: (order[m.tier], m.estimated_cost_per_million_input, m.priority))
        return eligible[0]

    def plan(
        self,
        request: str,
        *,
        project: Optional[str] = None,
        task_type: Optional[str] = None,
        unavailable_providers: Iterable[str] = (),
        allow_paid: bool = False,
    ) -> RoutingPlan:
        detected_project = self.detect_project(request, project)
        detected_task = self.detect_task_type(request, task_type)
        complexity = self.estimate_complexity(request, detected_task)
        risk = self.estimate_risk(request, detected_project, detected_task)
        context_budget, output_budget, parallel_agents = self.budgets(complexity)
        strength = self.desired_strength(detected_task, complexity)
        model = self.choose_model(
            strength, complexity, risk, context_budget, unavailable_providers,
            allow_paid=allow_paid,
        )

        escalation: List[str] = []
        if complexity in {Complexity.HIGH, Complexity.STRATEGIC}:
            escalation.append("verification_failed")
        if risk == Risk.HIGH:
            escalation += ["low_confidence", "unsafe_or_irreversible_action"]
        escalation += ["provider_failure", "context_overflow"]

        return RoutingPlan(
            project=detected_project,
            task_type=detected_task,
            complexity=complexity,
            risk=risk,
            model_tier=model.tier,
            model=model.name,
            provider=model.provider,
            framework=self.framework_for(detected_task, complexity),
            persona=self.persona_for(detected_project, detected_task),
            skills=self.skills_for(detected_project, detected_task),
            context_budget_tokens=context_budget,
            output_budget_tokens=output_budget,
            parallel_agents=parallel_agents,
            require_verification=(risk != Risk.LOW or complexity != Complexity.LOW),
            escalation_reasons=sorted(set(escalation)),
            metadata={
                "policy": "cheapest-capable-first",
                "strength": strength,
                "context_isolation": True,
                "paid_fallback_allowed": allow_paid,
                "execution_verified": False,
            },
        )
