import unittest
from provider_economics import Usage, Rates, estimated_usd, prepare_parameters, fallback_allowed, choose_strategy

class ProviderEconomicsTests(unittest.TestCase):
    def test_cached_input_not_double_counted(self):
        self.assertAlmostEqual(estimated_usd(Usage(1000, 500, 300, 100), Rates(2, 8, .2, 3)), .00656)
    def test_invalid_cache_accounting(self):
        with self.assertRaises(ValueError):
            Usage(10, 0, 11)
    def test_sampling_compatibility(self):
        p = {"temperature": 0.2, "top_p": .8, "top_k": 10, "max_tokens": 100}
        self.assertEqual(prepare_parameters(p, supports_sampling=False), {"max_tokens": 100})
        self.assertIn("temperature", p)
    def test_no_retry_after_side_effect(self):
        self.assertFalse(fallback_allowed(side_effect_started=True, retries=0, max_retries=2, spent_usd=0, budget_usd=1))
    def test_budget_guard(self):
        self.assertFalse(fallback_allowed(side_effect_started=False, retries=0, max_retries=2, spent_usd=1, budget_usd=1))
    def test_strategy(self):
        self.assertEqual(choose_strategy(complexity="high", verification_available=True, budget_usd=1), "critique")

if __name__ == "__main__":
    unittest.main()
