import unittest

from ADAPTIVE_ORCHESTRATION_ROUTER import (
    AdaptiveOrchestrationRouter,
    Complexity,
    ModelCandidate,
    ModelTier,
    Risk,
)


class AdaptiveRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = AdaptiveOrchestrationRouter()

    def test_narcoguard_release_detects_project_and_requires_verification(self):
        plan = self.router.plan(
            "Fully ship NarcoGuard to production on Vercel and verify the live domain"
        )
        self.assertEqual(plan.project, "narcoguard")
        self.assertEqual(plan.task_type, "deployment")
        self.assertIn(plan.complexity, {Complexity.HIGH, Complexity.STRATEGIC})
        self.assertTrue(plan.require_verification)
        self.assertIn("live-smoke", plan.skills)

    def test_simple_request_uses_small_budget_and_free_model(self):
        plan = self.router.plan("Summarize this short note")
        self.assertEqual(plan.complexity, Complexity.LOW)
        self.assertLessEqual(plan.context_budget_tokens, 4_000)
        self.assertIn(plan.model_tier, {ModelTier.FREE_LOCAL, ModelTier.FREE_CLOUD})
        self.assertEqual(plan.parallel_agents, 1)

    def test_chatty_orchestration_is_strategic(self):
        plan = self.router.plan(
            "Build the Chatty orchestration router with multi-agent delegation "
            "based on token usage and fully ship it"
        )
        self.assertEqual(plan.project, "chatty")
        self.assertEqual(plan.complexity, Complexity.STRATEGIC)
        self.assertGreaterEqual(plan.parallel_agents, 2)
        self.assertTrue(plan.require_verification)

    def test_high_risk_can_use_strong_tier_if_free_unavailable(self):
        models = (
            ModelCandidate(
                "strong", "paid", ModelTier.STRONG_PAID, ("reasoning", "legal"),
                priority=1,
            ),
        )
        router = AdaptiveOrchestrationRouter(models=models)
        plan = router.plan(
            "Prepare a legal filing and verify every citation",
            project="brendan440",
            task_type="research",
            allow_paid=True,
        )
        self.assertEqual(plan.risk, Risk.HIGH)
        self.assertEqual(plan.model_tier, ModelTier.STRONG_PAID)

    def test_unqualified_model_is_not_used_as_fallback(self):
        router = AdaptiveOrchestrationRouter(models=(
            ModelCandidate("quick-only", "local", ModelTier.FREE_LOCAL, ("quick",)),
        ))
        with self.assertRaisesRegex(RuntimeError, "No capable model"):
            router.plan("Analyze this failure", task_type="analysis")

    def test_context_overflow_is_not_used_as_fallback(self):
        router = AdaptiveOrchestrationRouter(models=(
            ModelCandidate("small", "local", ModelTier.FREE_LOCAL,
                           ("coding",), max_context=1000),
        ))
        with self.assertRaisesRegex(RuntimeError, "No capable model"):
            router.plan("Fix this code", task_type="coding")

    def test_paid_fallback_requires_explicit_opt_in(self):
        router = AdaptiveOrchestrationRouter(models=(
            ModelCandidate("paid", "paid", ModelTier.FAST_PAID, ("quick",)),
        ))
        with self.assertRaisesRegex(RuntimeError, "No capable model"):
            router.plan("Hello")
        self.assertEqual(router.plan("Hello", allow_paid=True).provider, "paid")

    def test_provider_failure_can_be_excluded(self):
        plan = self.router.plan(
            "Analyze this code failure",
            unavailable_providers={"ollama", "groq"},
        )
        self.assertNotIn(plan.provider, {"ollama", "groq"})
        self.assertIn("provider_failure", plan.escalation_reasons)


if __name__ == "__main__":
    unittest.main()
