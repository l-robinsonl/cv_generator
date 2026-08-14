"""Synthetic CV planning, prompting, concurrent generation, and packaging metadata."""

from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import base64
import random
import re
from typing import Callable, List, Optional, Sequence
import uuid

from .api import AIClient, APIRequestError, CostBreakdown, TokenUsage, model_cost
from .config import (
    CAREER_PROGRESSIONS,
    COUNTRIES,
    DEMO_PHONE_PREFIX,
    DEMO_PHONE_SUFFIX_DIGITS,
    EXPERIENCE_LEVELS,
    FIRST_NAMES,
    INDUSTRIES,
    LAST_NAMES,
    MAX_RESUMES,
    OUTPUT_FORMATS,
    PHONE_NUMBER_MODES,
    PROVIDERS,
    WEB_CONCURRENCY,
)
from .documents import MIME_TYPES, render_document


@dataclass(frozen=True)
class ResumePlan:
    country: str
    industry: str
    experience: str
    progression: str
    output_format: str
    first_name: str
    last_name: str
    identifier: str
    phone: str


@dataclass(frozen=True)
class GeneratedDocument:
    relative_path: str
    content: bytes
    mime_type: str


@dataclass
class GenerationOptions:
    provider: str = "openai"
    model: str = "gpt-4.1-mini"
    base_url: Optional[str] = None
    count: int = 10
    countries: Sequence[str] = ("US",)
    industry_codes: Sequence[int] = tuple(INDUSTRIES)
    experience_levels: Sequence[str] = EXPERIENCE_LEVELS
    career_progressions: Sequence[str] = CAREER_PROGRESSIONS
    output_formats: Sequence[str] = OUTPUT_FORMATS
    distribute: bool = True
    flat: bool = False
    phone_number_mode: str = "local"
    demo_number_count: int = 0
    shared_demo_number: Optional[str] = None


@dataclass
class GenerationResult:
    documents: List[GeneratedDocument] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    usage: TokenUsage = field(default_factory=TokenUsage)
    cost: Optional[CostBreakdown] = None


ProgressCallback = Callable[[int, int, str], None]


def fictional_phone(country: str) -> str:
    if country == "UK":
        return f"+44 7700 900{random.randint(0, 999):03d}"
    area_code = random.choice((202, 212, 213, 312, 415, 617, 646, 718))
    return f"+1 {area_code}-555-01{random.randint(0, 99):02d}"


def demo_phone() -> str:
    """Return a number recognized by the chat server's automated demo route."""
    upper_bound = (10 ** DEMO_PHONE_SUFFIX_DIGITS) - 1
    suffix = random.randint(0, upper_bound)
    return f"{DEMO_PHONE_PREFIX}{suffix:0{DEMO_PHONE_SUFFIX_DIGITS}d}"


def is_demo_phone(phone: str) -> bool:
    """Return whether a number belongs to the chat server's demo route."""
    return bool(re.fullmatch(r"\+210\d{9}", phone))


def _balanced(values: Sequence, count: int) -> list:
    values = list(dict.fromkeys(values))
    cycles, remainder = divmod(count, len(values))
    result = values * cycles
    if remainder:
        result.extend(random.sample(values, remainder))
    random.shuffle(result)
    return result


def validate_options(options: GenerationOptions) -> None:
    if not 1 <= options.count <= MAX_RESUMES:
        raise ValueError(f"Count must be between 1 and {MAX_RESUMES}")
    if options.provider not in PROVIDERS:
        raise ValueError("Select a supported provider")
    if not options.model.strip():
        raise ValueError("Model cannot be empty")
    selections = (
        (options.countries, "country"),
        (options.industry_codes, "industry"),
        (options.experience_levels, "experience level"),
        (options.career_progressions, "career progression"),
        (options.output_formats, "output format"),
    )
    for values, label in selections:
        if not values:
            raise ValueError(f"Select at least one {label}")
    if any(country not in COUNTRIES for country in options.countries):
        raise ValueError("Unsupported country selected")
    if any(code not in INDUSTRIES for code in options.industry_codes):
        raise ValueError("Unsupported industry selected")
    if any(value not in EXPERIENCE_LEVELS for value in options.experience_levels):
        raise ValueError("Unsupported experience level selected")
    if any(value not in CAREER_PROGRESSIONS for value in options.career_progressions):
        raise ValueError("Unsupported career progression selected")
    if any(value not in OUTPUT_FORMATS for value in options.output_formats):
        raise ValueError("Unsupported output format selected")
    if options.phone_number_mode not in PHONE_NUMBER_MODES:
        raise ValueError("Select a supported phone-number mode")
    if not 0 <= options.demo_number_count <= options.count:
        raise ValueError(
            f"Demo-number count must be between 0 and the batch size ({options.count})"
        )
    if options.phone_number_mode == "shared_demo" and not is_demo_phone(
        options.shared_demo_number or ""
    ):
        raise ValueError(
            "Shared demo number must be +210 followed by 9 digits "
            "(for example, +210000000000)"
        )


def create_plan(options: GenerationOptions) -> List[ResumePlan]:
    validate_options(options)
    count = options.count
    industries = [INDUSTRIES[code] for code in options.industry_codes]

    if options.distribute:
        countries = _balanced(options.countries, count)
        industry_values = _balanced(industries, count)
        experiences = _balanced(options.experience_levels, count)
        progressions = _balanced(options.career_progressions, count)
        formats = _balanced(options.output_formats, count)
    else:
        countries = [random.choice(options.countries) for _ in range(count)]
        industry_values = [random.choice(industries) for _ in range(count)]
        experiences = [random.choice(options.experience_levels) for _ in range(count)]
        progressions = [random.choice(options.career_progressions) for _ in range(count)]
        formats = [random.choice(options.output_formats) for _ in range(count)]

    name_pairs = [(first, last) for first in FIRST_NAMES for last in LAST_NAMES]
    if count <= len(name_pairs):
        selected_names = random.sample(name_pairs, count)
    else:
        selected_names = [random.choice(name_pairs) for _ in range(count)]

    if options.phone_number_mode == "demo":
        demo_indexes = set(range(count))
    elif options.phone_number_mode == "mixed":
        demo_indexes = set(random.sample(range(count), options.demo_number_count))
    else:
        demo_indexes = set()

    demo_phones = set()

    def unique_demo_phone() -> str:
        phone = demo_phone()
        while phone in demo_phones:
            phone = demo_phone()
        demo_phones.add(phone)
        return phone

    plans = []
    for index in range(count):
        identifier = base64.urlsafe_b64encode(uuid.uuid4().bytes).rstrip(b"=").decode()
        first_name, last_name = selected_names[index]
        phone = (
            options.shared_demo_number or ""
            if options.phone_number_mode == "shared_demo"
            else (
                unique_demo_phone()
                if index in demo_indexes
                else fictional_phone(countries[index])
            )
        )
        plans.append(
            ResumePlan(
                country=countries[index],
                industry=industry_values[index],
                experience=experiences[index],
                progression=progressions[index],
                output_format=formats[index],
                first_name=first_name,
                last_name=last_name,
                identifier=identifier,
                phone=phone,
            )
        )
    return plans


def build_prompt(plan: ResumePlan) -> str:
    country = COUNTRIES[plan.country]
    return f"""Generate a synthetic CV in English for a {country['candidate']} candidate.
The CV must be realistic, logically consistent, and professionally formatted as Markdown.
Return only the CV, with no commentary or code fence.

Personal information
- Full name: {plan.first_name} {plan.last_name}
- Email: testcandidate+{plan.identifier}@daxtra.com
- Location format: {country['location']} (use a real, geographically accurate location)
- Phone: {plan.phone}

Required sections
# {plan.first_name} {plan.last_name}
## Professional Summary
Write a focused 2-3 sentence summary.
## Work History
List jobs in reverse chronological order. Jobs must last 1-5 years, be sequential and
non-overlapping, use realistic titles, and name {country['company']}. Include dates,
responsibilities, and measurable achievements. Match the requested progression and avoid
unexplained demotions.
## Education History
Use realistic institutions and qualifications aligned to the career.
## Skills
Include relevant general competencies, tools, and technologies.

CV requirements
- Country: {country['label']} ({plan.country})
- Industry: {plan.industry}
- Experience: {plan.experience}
- Career progression: {plan.progression}
- Use clear Markdown headings and bullet points.
- Do not invent a different phone number, email address, or candidate name.
"""


def _slug(value: str) -> str:
    return "_".join(value.lower().replace("&", "and").split())


def _relative_path(plan: ResumePlan, flat: bool) -> str:
    filename = f"{plan.identifier}.{plan.output_format}"
    if flat:
        return filename
    return "/".join(
        (
            _slug(plan.industry),
            _slug(plan.experience),
            _slug(plan.progression),
            filename,
        )
    )


class ResumeGenerator:
    """Generate a bounded concurrent batch without persisting keys or CVs."""

    concurrency = WEB_CONCURRENCY

    def generate(
        self,
        api_key: str,
        options: GenerationOptions,
        progress: Optional[ProgressCallback] = None,
        client: Optional[AIClient] = None,
    ) -> GenerationResult:
        plans = create_plan(options)
        client = client or AIClient(
            api_key=api_key,
            provider=options.provider,
            model=options.model,
            base_url=options.base_url,
        )
        result = GenerationResult()
        completed = 0

        def generate_one(plan: ResumePlan) -> GeneratedDocument:
            completion = client.complete(build_prompt(plan))
            data = render_document(
                completion.content, plan.output_format, plan.country
            )
            return GeneratedDocument(
                relative_path=_relative_path(plan, options.flat),
                content=data,
                mime_type=MIME_TYPES[plan.output_format],
            )

        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            future_to_plan = {
                executor.submit(generate_one, plan): plan for plan in plans
            }
            stop_queued_work = False
            for future in as_completed(future_to_plan):
                plan = future_to_plan[future]
                try:
                    document = future.result()
                except CancelledError:
                    result.errors.append(f"Cancelled {plan.identifier}")
                except APIRequestError as error:
                    result.errors.append(str(error))
                    if not stop_queued_work:
                        stop_queued_work = True
                        for pending in future_to_plan:
                            if pending is not future:
                                pending.cancel()
                except Exception as error:
                    result.errors.append(f"{plan.identifier}: {error}")
                else:
                    result.documents.append(document)

                completed += 1
                if progress:
                    progress(completed, len(plans), plan.identifier)

        result.documents.sort(key=lambda item: item.relative_path)
        result.usage = TokenUsage(
            input_tokens=client.total_usage.input_tokens,
            output_tokens=client.total_usage.output_tokens,
            cached_input_tokens=client.total_usage.cached_input_tokens,
        )
        result.cost = model_cost(options.provider, options.model, result.usage)
        return result
