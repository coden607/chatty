"""Tests for CHATTY_MASTER_ORCHESTRATOR_v2 — framework routing logic.

Only the pure routing/selection layer is exercised; framework clients are
never initialized, so no external services are touched.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CHATTY_MASTER_ORCHESTRATOR_v2 import (  # noqa: E402
    FrameworkRouter,
    MasterOrchestrator,
    TaskResult,
    TaskType,
    UnifiedTask,
)


def make_task(task_type=TaskType.CONTENT_CREATION, **kwargs):
    return UnifiedTask(
        name=kwargs.pop("name", "test task"),
        description=kwargs.pop("description", "do the thing"),
        task_type=task_type,
        **kwargs,
    )


class TestUnifiedTask:
    def test_to_dict_roundtrip(self):
        task = make_task(context={"k": "v"}, priority=2, preferred_framework="crewai")
        d = task.to_dict()
        assert d["task_type"] == "content_creation"
        assert d["context"] == {"k": "v"}
        assert d["priority"] == 2
        assert d["preferred_framework"] == "crewai"


class TestFrameworkSelection:
    @pytest.fixture()
    def router(self):
        return FrameworkRouter()

    def test_preferred_framework_wins(self, router):
        task = make_task(preferred_framework="mcp")
        assert router.select_framework(task) == "mcp"

    def test_task_type_mapping_covers_all_types(self, router):
        for task_type in TaskType:
            if task_type == TaskType.UNKNOWN:
                continue
            assert task_type in router.TASK_FRAMEWORK_MAPPING
            task = make_task(task_type=task_type)
            selected = router.select_framework(task)
            assert selected in router.TASK_FRAMEWORK_MAPPING[task_type]

    def test_first_candidate_selected_without_context(self, router):
        # With no context bonuses, the top-ranked candidate wins.
        task = make_task(task_type=TaskType.CONTENT_CREATION)
        assert router.select_framework(task) == "crewai"

    def test_structured_output_context_boosts_pydantic(self, router):
        task = make_task(
            task_type=TaskType.DATA_ANALYSIS,
            context={"structured_output": True},
        )
        assert router.select_framework(task) == "pydantic_ai"

    def test_code_execution_context_boosts_smolagents(self, router):
        task = make_task(
            task_type=TaskType.CODE_GENERATION,
            context={"code_execution": True},
        )
        assert router.select_framework(task) == "smolagents"

    def test_files_context_boosts_mcp_for_research(self, router):
        task = make_task(task_type=TaskType.RESEARCH, context={"files": True})
        assert router.select_framework(task) == "mcp"

    def test_unknown_type_uses_fallback_mapping(self, router):
        task = make_task(task_type=TaskType.UNKNOWN)
        selected = router.select_framework(task)
        assert selected in ("smolagents", "pydantic_ai")


class TestMasterOrchestratorBasics:
    def test_initialization_is_lazy_and_graceful(self):
        orch = MasterOrchestrator()
        # initialize() must not raise even when framework deps are absent.
        import asyncio

        asyncio.new_event_loop().run_until_complete(orch.initialize())
        assert orch.initialized is True

    def test_execution_history_starts_empty(self):
        orch = MasterOrchestrator()
        assert orch.execution_history == []
