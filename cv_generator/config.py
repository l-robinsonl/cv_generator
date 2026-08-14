"""Supported providers, selectors, and verified standard pricing."""

from decimal import Decimal


COUNTRIES = {
    "US": {
        "label": "United States",
        "candidate": "US-based",
        "location": "city, state, United States",
        "company": "a real company operating in the United States",
    },
    "UK": {
        "label": "United Kingdom",
        "candidate": "UK-based",
        "location": "city, county or region, United Kingdom",
        "company": "a real company operating in the United Kingdom",
    },
}

INDUSTRIES = {
    1: "Healthcare",
    2: "IT and Technology",
    3: "Professional Service and Finance",
    4: "Education",
    5: "Sales and Business Development",
    6: "Marketing and Communications",
    7: "Engineering and Manufacturing",
    8: "Human Resources and Recruitment",
    9: "Retail and Hospitality",
    10: "Construction and Skilled Trades",
}

EXPERIENCE_LEVELS = (
    "Less than 10 years of post-education work experience",
    "More than 10 years of post-education work experience",
)

CAREER_PROGRESSIONS = (
    "Limited progression",
    "Typical progression",
    "Strong progression",
)

OUTPUT_FORMATS = ("pdf", "docx", "txt")

PHONE_NUMBER_MODES = {
    "local": "Country-reserved",
    "demo": "Unique demo numbers",
    "shared_demo": "One shared demo number",
    "mixed": "Mixed batch",
}
DEMO_PHONE_PREFIX = "+210"
DEMO_PHONE_SUFFIX_DIGITS = 9

PROVIDERS = {
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4.1-mini",
    },
    "groq": {
        "label": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
    },
}

# Standard non-batch text prices in USD per one million tokens.
MODEL_PRICING = {
    ("openai", "gpt-4.1-mini"): {
        "input": Decimal("0.40"),
        "cached_input": Decimal("0.10"),
        "output": Decimal("1.60"),
    },
    ("groq", "llama-3.3-70b-versatile"): {
        "input": Decimal("0.59"),
        "cached_input": None,
        "output": Decimal("0.79"),
    },
}

FIRST_NAMES = (
    "Alex", "Avery", "Benjamin", "Brooke", "Cameron", "Charlotte",
    "Daniel", "Diana", "Elliot", "Emily", "Finley", "Freya", "George",
    "Grace", "Harper", "Henry", "Imogen", "Isaac", "James", "Jessica",
    "Kai", "Katherine", "Leo", "Lucy", "Marcus", "Maya", "Nathan",
    "Nicole", "Oliver", "Olivia", "Patrick", "Priya", "Quinn", "Rachel",
    "Robert", "Samuel", "Sofia", "Taylor", "Thomas", "Uma", "Victoria",
    "William", "Xavier", "Yasmin", "Zachary", "Zoe",
)

LAST_NAMES = (
    "Adams", "Ahmed", "Baker", "Brown", "Campbell", "Carter", "Chen",
    "Clarke", "Davies", "Davis", "Edwards", "Evans", "Fisher", "Foster",
    "Garcia", "Green", "Hall", "Harris", "Hughes", "Jackson", "Johnson",
    "Jones", "Khan", "King", "Lee", "Lewis", "Martin", "Miller", "Mitchell",
    "Morgan", "Murphy", "Nelson", "Nguyen", "Patel", "Reed", "Roberts",
    "Robinson", "Scott", "Shah", "Singh", "Smith", "Taylor", "Thomas",
    "Thompson", "Walker", "White", "Williams", "Wilson", "Wright", "Young",
)

MAX_RESUMES = 100
WEB_CONCURRENCY = 2
