#!/usr/bin/env python3
"""
Integration tests — verify core engines initialise in offline mode,
YouTube learner and OpenClaw are importable, and fake data generation
has been removed.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Force offline mode so no live API calls are made during tests
os.environ["CHATTY_OFFLINE_MODE"] = "true"
os.environ["CHATTY_USE_FREE_LLM_ONLY"] = "true"

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest


# ── helpers ─────────────────────────────────────────────────────────────────

def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Phase 1 : Critical bug fixes verified at import time ───────────────────

class TestCriticalBugs:
    """Verify Phase-1 fixes didn't regress."""

    def test_revenue_engine_method_name(self):
        from AUTOMATED_REVENUE_ENGINE import AutomatedRevenueEngine
        engine = AutomatedRevenueEngine()
        assert hasattr(engine, "reset_llm_failure"), "reset_llm_failure (singular) must exist"

    def test_start_automation_log_path_relative(self):
        """Log path must NOT contain a hard-coded /home/coden809/CHATTY."""
        source = Path("START_COMPLETE_AUTOMATION.py").read_text()
        assert "/home/coden809/CHATTY/" not in source

    def test_viral_growth_await(self):
        """generate_ai_content calls in VIRAL_GROWTH_ENGINE must be awaited."""
        source = Path("VIRAL_GROWTH_ENGINE.py").read_text()
        # Every call should have 'await' before it
        import re
        calls = re.findall(r"(?:await\s+)?self\.revenue_engine\.generate_ai_content", source)
        for call in calls:
            assert call.startswith("await"), f"Missing await: {call}"

    def test_real_openclaw_imports(self):
        """REAL_OPENCLAW_AGENTZERO must import sys and time."""
        source = Path("REAL_OPENCLAW_AGENTZERO.py").read_text()
        assert "import sys" in source
        assert "import time" in source

    def test_youtube_transcript_api_in_requirements(self):
        reqs = Path("requirements.txt").read_text()
        assert "youtube-transcript-api" in reqs


# ── Phase 2 : YouTube learner ──────────────────────────────────────────────

class TestYouTubeLearner:

    def test_fixed_learner_importable(self):
        from FIXED_YOUTUBE_LEARNER import FixedYouTubeLearner
        learner = FixedYouTubeLearner()
        assert learner is not None

    def test_fixed_learner_has_persistence(self):
        from FIXED_YOUTUBE_LEARNER import FixedYouTubeLearner
        learner = FixedYouTubeLearner()
        assert hasattr(learner, "_save_learning")
        assert hasattr(learner, "learnings_path")

    def test_fixed_learner_has_continuous_learning(self):
        from FIXED_YOUTUBE_LEARNER import FixedYouTubeLearner
        learner = FixedYouTubeLearner()
        assert hasattr(learner, "start_continuous_learning")

    def test_cole_medin_learner_importable(self):
        from COLE_MEDIN_CHANNEL_LEARNER import ColeMedinChannelLearner
        learner = ColeMedinChannelLearner()
        assert learner is not None

    def test_parse_json_response(self):
        from FIXED_YOUTUBE_LEARNER import FixedYouTubeLearner
        learner = FixedYouTubeLearner()
        # Markdown-fenced JSON
        result = learner._parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}
        # Raw JSON
        result = learner._parse_json_response('{"a": 1}')
        assert result == {"a": 1}
        # Surrounding text
        result = learner._parse_json_response('Here is the result: {"b": 2} done')
        assert result == {"b": 2}

    def test_deprecated_files_marked(self):
        for name in [
            "youtube_learning_system.py",
            "YOUTUBE_LEARNING_INTEGRATION.py",
            "REAL_YOUTUBE_LEARNER.py",
            "FUNCTIONAL_YOUTUBE_LEARNER.py",
        ]:
            content = Path(name).read_text()
            assert "DEPRECATED" in content, f"{name} should be marked DEPRECATED"


# ── Phase 3 : OpenClaw ─────────────────────────────────────────────────────

class TestOpenClaw:

    def test_openclaw_imports_cleanly(self):
        from openclaw_integration import MultiLLMRouter, AutonomousLearningSystem
        router = MultiLLMRouter()
        system = AutonomousLearningSystem()
        assert router is not None
        assert system is not None

    def test_openclaw_no_broken_imports(self):
        """openclaw_integration must NOT import from server or learning_system."""
        source = Path("openclaw_integration.py").read_text()
        assert "from server import" not in source
        assert "from learning_system import" not in source


# ── Phase 4 : No fake data generation ──────────────────────────────────────

class TestNoFakeData:

    def test_search_methods_return_empty(self):
        from AUTOMATED_CUSTOMER_ACQUISITION import AutomatedCustomerAcquisition as CustomerAcquisitionEngine
        engine = CustomerAcquisitionEngine()
        assert _run(engine._search_public_health_organizations("opioid")) == []
        assert _run(engine._search_academic_institutions("opioid")) == []
        assert _run(engine._search_nonprofit_organizations("opioid")) == []

    def test_social_discovery_returns_zero(self):
        from AUTOMATED_CUSTOMER_ACQUISITION import AutomatedCustomerAcquisition as CustomerAcquisitionEngine
        engine = CustomerAcquisitionEngine()
        assert _run(engine._automate_social_prospect_discovery()) == 0

    def test_publishers_do_not_claim_success(self):
        source = Path("AUTOMATED_CUSTOMER_ACQUISITION.py").read_text()
        # The old log messages said "Published to ..." implying success
        assert 'Published to blog' not in source
        assert 'Published to Medium' not in source
        assert 'Published to LinkedIn' not in source


# ── Phase 5 : Error handling ───────────────────────────────────────────────

class TestErrorHandling:

    def test_no_bare_except_in_modified_files(self):
        import re
        files = [
            "openclaw_integration.py",
            "FIXED_YOUTUBE_LEARNER.py",
            "SELF_IMPROVING_AGENTS.py",
            "AUTOMATED_CUSTOMER_ACQUISITION.py",
            "AUTOMATED_REVENUE_ENGINE.py",
            "START_COMPLETE_AUTOMATION.py",
            "VIRAL_GROWTH_ENGINE.py",
            "REAL_OPENCLAW_AGENTZERO.py",
            "COLE_MEDIN_CHANNEL_LEARNER.py",
        ]
        for fname in files:
            content = Path(fname).read_text()
            for i, line in enumerate(content.splitlines(), 1):
                if re.search(r"except\s*:", line) and "except Exception" not in line and "except (" not in line:
                    pytest.fail(f"Bare except: in {fname}:{i}: {line.strip()}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
