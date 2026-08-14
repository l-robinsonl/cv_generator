import re
import threading
import time
import unittest

from cv_generator.api import Completion, TokenUsage
from cv_generator.config import INDUSTRIES, MAX_WEB_CONCURRENCY, WEB_CONCURRENCY
from cv_generator.generator import (
    GenerationOptions,
    ResumeGenerator,
    build_prompt,
    create_plan,
    demo_phone,
    fictional_phone,
    is_demo_phone,
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

    def test_uk_phone_numbers_are_mobile_only_and_never_landlines(self):
        phones = [fictional_phone("UK") for _ in range(200)]
        self.assertTrue(all(phone.startswith("+44 7700 900") for phone in phones))
        self.assertTrue(
            all("01202" not in phone and "+44 1202" not in phone for phone in phones)
        )

    def test_demo_phone_uses_chat_server_demo_range(self):
        for _ in range(100):
            self.assertRegex(demo_phone(), r"^\+210\d{9}$")

    def test_demo_phone_validation_is_strict(self):
        self.assertTrue(is_demo_phone("+210000000000"))
        self.assertFalse(is_demo_phone("+21000000000"))
        self.assertFalse(is_demo_phone("+210 000000000"))
        self.assertFalse(is_demo_phone("210000000000"))

    def test_demo_mode_assigns_unique_demo_numbers_to_entire_batch(self):
        plans = create_plan(
            GenerationOptions(count=20, phone_number_mode="demo")
        )
        phones = [plan.phone for plan in plans]
        self.assertEqual(len(set(phones)), 20)
        self.assertTrue(all(re.fullmatch(r"\+210\d{9}", phone) for phone in phones))

    def test_mixed_mode_assigns_exact_demo_count_and_local_remainder(self):
        plans = create_plan(
            GenerationOptions(
                count=24,
                countries=("UK",),
                phone_number_mode="mixed",
                demo_number_count=7,
            )
        )
        demo_phones = [plan.phone for plan in plans if plan.phone.startswith("+210")]
        local_phones = [plan.phone for plan in plans if not plan.phone.startswith("+210")]
        self.assertEqual(len(demo_phones), 7)
        self.assertEqual(len(local_phones), 17)
        self.assertEqual(len(set(demo_phones)), 7)
        self.assertTrue(all(re.fullmatch(r"\+44 7700 900\d{3}", phone) for phone in local_phones))

    def test_mixed_mode_rejects_demo_count_above_batch_size(self):
        with self.assertRaisesRegex(ValueError, "between 1 and 2"):
            create_plan(
                GenerationOptions(
                    count=3,
                    phone_number_mode="mixed",
                    demo_number_count=3,
                )
            )

    def test_mixed_mode_can_use_one_reserved_country_for_the_remainder(self):
        plans = create_plan(
            GenerationOptions(
                count=20,
                countries=("US", "UK"),
                phone_number_mode="mixed",
                demo_number_count=6,
                reserved_phone_country="UK",
            )
        )
        local_plans = [plan for plan in plans if not plan.phone.startswith("+210")]
        self.assertEqual(len(local_plans), 14)
        self.assertTrue(
            all(re.fullmatch(r"\+44 7700 900\d{3}", plan.phone) for plan in local_plans)
        )
        self.assertEqual({plan.country for plan in plans}, {"US", "UK"})

    def test_mixed_mode_defaults_remainder_to_each_plan_country(self):
        plans = create_plan(
            GenerationOptions(
                count=20,
                countries=("US", "UK"),
                phone_number_mode="mixed",
                demo_number_count=6,
            )
        )
        for plan in plans:
            if plan.phone.startswith("+210"):
                continue
            expected = (
                r"\+44 7700 900\d{3}"
                if plan.country == "UK"
                else r"\+1 \d{3}-555-01\d{2}"
            )
            self.assertRegex(plan.phone, expected)

    def test_reserved_phone_country_must_be_selected(self):
        with self.assertRaisesRegex(ValueError, "one of the selected countries"):
            create_plan(
                GenerationOptions(
                    count=4,
                    countries=("US",),
                    phone_number_mode="mixed",
                    demo_number_count=2,
                    reserved_phone_country="UK",
                )
            )

    def test_uk_prompt_is_explicitly_uk_only(self):
        plan = create_plan(
            GenerationOptions(count=1, countries=("UK",), industry_codes=(5,))
        )[0]
        prompt = build_prompt(plan)
        self.assertIn("UK-based", prompt)
        self.assertIn("United Kingdom", prompt)
        self.assertNotIn("US-based", prompt)
        self.assertIn(f"Phone: {plan.phone}", prompt)

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

    def test_generation_uses_user_selected_concurrency(self):
        client = FakeClient()
        result = ResumeGenerator().generate(
            api_key="unused",
            options=GenerationOptions(
                count=9,
                countries=("UK",),
                industry_codes=(5,),
                output_formats=("txt",),
                concurrency=3,
            ),
            client=client,
        )
        self.assertEqual(result.errors, [])
        self.assertEqual(client.maximum_active, 3)

    def test_concurrency_is_bounded(self):
        with self.assertRaisesRegex(ValueError, f"between 1 and {MAX_WEB_CONCURRENCY}"):
            create_plan(GenerationOptions(concurrency=MAX_WEB_CONCURRENCY + 1))


if __name__ == "__main__":
    unittest.main()
