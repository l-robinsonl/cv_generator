from decimal import Decimal
import unittest

from cv_generator.api import TokenUsage, model_cost


class CostTests(unittest.TestCase):
    def test_openai_default_cost_breakdown(self):
        cost = model_cost(
            "openai",
            "gpt-4.1-mini",
            TokenUsage(
                input_tokens=1_000_000,
                cached_input_tokens=200_000,
                output_tokens=500_000,
            ),
        )
        self.assertIsNotNone(cost)
        self.assertEqual(cost.input_cost, Decimal("0.340000"))
        self.assertEqual(cost.cached_input_cost, Decimal("0.020000"))
        self.assertEqual(cost.output_cost, Decimal("0.800000"))
        self.assertEqual(cost.total_cost, Decimal("1.140000"))

    def test_unknown_model_does_not_guess_pricing(self):
        self.assertIsNone(model_cost("groq", "custom-model", TokenUsage(1, 1)))


if __name__ == "__main__":
    unittest.main()
