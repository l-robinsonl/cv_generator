import re
import threading
import time
import unittest

from cv_generator.api import Completion, TokenUsage
from cv_generator.config import INDUSTRIES, WEB_CONCURRENCY
from cv_generator.generator import (
    GenerationOptions,
    ResumeGenerator,
    build_prompt,
    create_plan,
    fictional_phone,
)


class FakeClient:
    def __init__(self):
        self.total_usage = TokenUsage()
        self._lock = threading.Lock()
        self.maximum_active = 0
        self.active = 0

    def complete(self, prompt):
        with self._lock:
            self.active += 1
            self.maximum_active = max(self.maximum_active, self.active)
        time.sleep(0.01)
        with self._lock:
            self.active -= 1
            self.total_usage.add(TokenUsage(input_tokens=100, output_tokens=200))
        return Completion(
            "# Alex Smith\n\n## Skills\n\n- Communication\n",
            TokenUsage(input_tokens=100, output_tokens=200),
        )


class GeneratorTests(unittest.TestCase):
    def test_all_industry_codes_are_available(self):
        self.assertEqual(list(INDUSTRIES), list(range(1, 11)))
        self.assertEqual(INDUSTRIES[5], "Sales and Business Development")

    def test_uk_only_selection_never_creates_us_plan(self):
        plans = create_plan(
            GenerationOptions(count=30, countries=("UK",), industry_codes=(1, 5))
        )
        self.assertEqual({plan.country for plan in plans}, {"UK"})
        self.assertEqual({plan.industry for plan in plans}, {INDUSTRIES[1], INDUSTRIES[5]})

    def test_balanced_selection_differs_by_no_more_than_one(self):
        plans = create_plan(
            GenerationOptions(
                count=11,
                countries=("US", "UK"),
                industry_codes=(1,),
                output_formats=("pdf", "docx", "txt"),
            )
        )
        country_counts = [sum(plan.country == value for plan in plans) for value in ("US", "UK")]
        format_counts = [
            sum(plan.output_format == value for plan in plans)
            for value in ("pdf", "docx", "txt")
        ]
        self.assertLessEqual(max(country_counts) - min(country_counts), 1)
        self.assertLessEqual(max(format_counts) - min(format_counts), 1)

    def test_phone_numbers_use_reserved_fictional_ranges(self):
        for _ in range(100):
            self.assertRegex(fictional_phone("UK"), r"^\+44 7700 900\d{3}$")
            self.assertRegex(fictional_phone("US"), r"^\+1 \d{3}-555-01\d{2}$")

    def test_uk_prompt_is_explicitly_uk_only(self):
        plan = create_plan(
            GenerationOptions(count=1, countries=("UK",), industry_codes=(5,))
        )[0]
        prompt = build_prompt(plan)
        self.assertIn("UK-based", prompt)
        self.assertIn("United Kingdom", prompt)
        self.assertNotIn("US-based", prompt)

    def test_generation_uses_fixed_bounded_concurrency_and_totals_usage(self):
        client = FakeClient()
        result = ResumeGenerator().generate(
            api_key="unused",
            options=GenerationOptions(
                count=8,
                countries=("UK",),
                industry_codes=(5,),
                output_formats=("txt",),
                flat=True,
            ),
            client=client,
        )
        self.assertEqual(len(result.documents), 8)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.usage.input_tokens, 800)
        self.assertEqual(result.usage.output_tokens, 1600)
        self.assertGreater(client.maximum_active, 1)
        self.assertLessEqual(client.maximum_active, WEB_CONCURRENCY)
        self.assertTrue(all("/" not in item.relative_path for item in result.documents))


if __name__ == "__main__":
    unittest.main()
