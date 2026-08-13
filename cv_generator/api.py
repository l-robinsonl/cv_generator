"""Thread-safe client, usage accounting, retries, and cost estimates."""

from dataclasses import dataclass
from decimal import Decimal
import time
from threading import Lock
from typing import Optional

import requests

from .config import MODEL_PRICING, PROVIDERS


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, other: "TokenUsage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cached_input_tokens += other.cached_input_tokens


@dataclass(frozen=True)
class Completion:
    content: str
    usage: TokenUsage


@dataclass(frozen=True)
class CostBreakdown:
    input_cost: Decimal
    output_cost: Decimal
    cached_input_cost: Decimal

    @property
    def total_cost(self) -> Decimal:
        return self.input_cost + self.output_cost


class APIRequestError(RuntimeError):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def model_cost(provider: str, model: str, usage: TokenUsage) -> Optional[CostBreakdown]:
    pricing = MODEL_PRICING.get((provider, model))
    if pricing is None and provider == "openai" and model.startswith("gpt-4.1-mini-"):
        pricing = MODEL_PRICING[("openai", "gpt-4.1-mini")]
    if pricing is None:
        return None

    cached = min(usage.cached_input_tokens, usage.input_tokens)
    uncached = usage.input_tokens - cached
    input_rate = pricing["input"]
    cached_rate = pricing["cached_input"] or input_rate
    million = Decimal("1000000")
    cached_cost = Decimal(cached) * cached_rate / million
    input_cost = Decimal(uncached) * input_rate / million + cached_cost
    output_cost = Decimal(usage.output_tokens) * pricing["output"] / million
    return CostBreakdown(input_cost, output_cost, cached_cost)


class AIClient:
    def __init__(
        self,
        api_key: str,
        provider: str,
        model: str,
        base_url: Optional[str] = None,
    ):
        if provider not in PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
        if not api_key.strip():
            raise ValueError("An API key is required")
        if not model.strip():
            raise ValueError("A model is required")

        self.api_key = api_key.strip()
        self.provider = provider
        self.model = model.strip()
        self.base_url = (base_url or PROVIDERS[provider]["base_url"]).rstrip("/")
        self.total_usage = TokenUsage()
        self._usage_lock = Lock()

    @staticmethod
    def _error_details(response: requests.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            return (response.text or response.reason or "Unknown API error").strip()
        error = body.get("error", body) if isinstance(body, dict) else body
        if isinstance(error, dict):
            message = error.get("message") or error.get("code") or str(error)
            metadata = [error.get("type"), error.get("code")]
            metadata = [item for item in metadata if item and item != message]
            return f"{message} ({', '.join(metadata)})" if metadata else str(message)
        return str(error)

    def complete(self, prompt: str) -> Completion:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1800,
        }

        retryable = {429, 500, 502, 503, 504}
        response = None
        for attempt in range(3):
            try:
                response = requests.post(
                    url, headers=headers, json=payload, timeout=90
                )
                response.raise_for_status()
                break
            except requests.HTTPError as error:
                response = error.response
                status = response.status_code if response is not None else None
                if status in retryable and attempt < 2:
                    retry_after = response.headers.get("retry-after", "")
                    try:
                        delay = min(max(float(retry_after), 0), 10)
                    except ValueError:
                        delay = 2 ** attempt
                    time.sleep(delay)
                    continue
                details = self._error_details(response) if response is not None else str(error)
                request_id = response.headers.get("x-request-id") if response is not None else None
                suffix = f" [request ID: {request_id}]" if request_id else ""
                raise APIRequestError(
                    f"HTTP {status or 'unknown'} for model '{self.model}': "
                    f"{details}{suffix}",
                    status,
                ) from error
            except requests.RequestException as error:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise APIRequestError(
                    f"Could not reach the provider after 3 attempts: {error}"
                ) from error

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise RuntimeError("The provider returned an invalid completion response") from error
        if not content:
            raise RuntimeError("The provider returned an empty completion")

        raw_usage = data.get("usage", {})
        prompt_details = raw_usage.get("prompt_tokens_details") or {}
        usage = TokenUsage(
            input_tokens=int(
                raw_usage.get("prompt_tokens", raw_usage.get("input_tokens", 0)) or 0
            ),
            output_tokens=int(
                raw_usage.get("completion_tokens", raw_usage.get("output_tokens", 0)) or 0
            ),
            cached_input_tokens=int(prompt_details.get("cached_tokens", 0) or 0),
        )
        with self._usage_lock:
            self.total_usage.add(usage)
        return Completion(content, usage)
