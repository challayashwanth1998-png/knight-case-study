"""
AWS Bedrock AI helper using Bedrock API Key authentication.
Drop-in replacement for the Gemini helper — same interface (call_gemini, call_gemini_json).
Uses the Converse API with Amazon Nova Pro.
"""
import os
import re
import time
import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ── Bedrock Config ──────────────────────────────────────────
BEDROCK_REGION = "us-east-1"
MODEL_ID = "amazon.nova-pro-v1:0"
BEDROCK_API_KEY = os.environ.get("BEDROCK_API_KEY", "")
BEDROCK_ENDPOINT = f"https://bedrock-runtime.{BEDROCK_REGION}.amazonaws.com"
MAX_RETRIES = 5
BASE_WAIT = 5

# Amazon Nova Pro pricing (per 1M tokens)
PRICE_INPUT_PER_1M = 0.80
PRICE_OUTPUT_PER_1M = 3.20


# ── Cost Tracking (same interface as gemini.py) ─────────────

@dataclass
class AICallMetrics:
    """Metrics for a single AI API call."""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    step_name: str = ""


@dataclass
class SubmissionAIMetrics:
    """Accumulated AI metrics for an entire submission pipeline."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    total_calls: int = 0
    calls: list = field(default_factory=list)

    def add_call(self, metrics: AICallMetrics):
        self.total_input_tokens += metrics.input_tokens
        self.total_output_tokens += metrics.output_tokens
        self.total_cost_usd += metrics.cost_usd
        self.total_calls += 1
        self.calls.append(metrics)

    def to_dict(self) -> dict:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_calls": self.total_calls,
        }


# Thread-local storage for per-submission metrics
_thread_local = threading.local()


def start_tracking() -> SubmissionAIMetrics:
    """Start tracking AI metrics for the current submission pipeline."""
    metrics = SubmissionAIMetrics()
    _thread_local.metrics = metrics
    return metrics


def get_current_metrics() -> Optional[SubmissionAIMetrics]:
    """Get the current submission's AI metrics."""
    return getattr(_thread_local, "metrics", None)


def _calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate USD cost from token counts."""
    input_cost = (input_tokens / 1_000_000) * PRICE_INPUT_PER_1M
    output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT_PER_1M
    return input_cost + output_cost


# ── Bedrock Converse via API Key ─────────────────────────────

def _call_bedrock_converse(model_id: str, messages: list, system: list,
                            inference_config: dict) -> dict:
    """
    Call Bedrock Converse API using API Key authentication.
    """
    url = f"{BEDROCK_ENDPOINT}/model/{model_id}/converse"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-amz-bedrock-api-key": BEDROCK_API_KEY,
    }

    body = {
        "messages": messages,
        "system": system,
        "inferenceConfig": inference_config,
    }

    response = requests.post(url, headers=headers, json=body, timeout=120)

    if response.status_code != 200:
        error_body = response.text
        raise RuntimeError(
            f"Bedrock API error (HTTP {response.status_code}): {error_body[:300]}"
        )

    return response.json()


# ── API Call Functions (same interface as gemini.py) ─────────

def call_gemini(
    prompt: str,
    model_name: str = MODEL_ID,
    max_retries: int = MAX_RETRIES,
    temperature: float = 0.1,
    json_mode: bool = False,
    step_name: str = "",
) -> str:
    """
    Call AWS Bedrock using the Converse API with API Key auth.
    Function name kept as call_gemini for drop-in compatibility.
    """
    messages = [{"role": "user", "content": [{"text": prompt}]}]

    system_text = "You are an expert insurance underwriting analyst."
    if json_mode:
        system_text += " Always respond with valid JSON only. No markdown, no code fences, no extra text."

    system = [{"text": system_text}]

    inference_config = {
        "maxTokens": 8192,
        "temperature": temperature,
    }

    for attempt in range(1, max_retries + 1):
        try:
            start_time = time.time()

            response = _call_bedrock_converse(
                model_id=model_name,
                messages=messages,
                system=system,
                inference_config=inference_config,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Extract text from Converse response
            text = ""
            output_message = response.get("output", {}).get("message", {})
            for block in output_message.get("content", []):
                if "text" in block:
                    text += block["text"]

            text = _clean_json_fences(text)

            # Extract token counts
            usage = response.get("usage", {})
            input_tokens = usage.get("inputTokens", 0)
            output_tokens = usage.get("outputTokens", 0)
            cost = _calculate_cost(input_tokens, output_tokens)

            # Track metrics
            call_metrics = AICallMetrics(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                latency_ms=latency_ms,
                step_name=step_name,
            )

            submission_metrics = get_current_metrics()
            if submission_metrics:
                submission_metrics.add_call(call_metrics)

            logger.info(
                f"Bedrock [{step_name}]: {input_tokens}+{output_tokens} tokens, "
                f"${cost:.4f}, {latency_ms}ms"
            )

            return text

        except RuntimeError as e:
            error_msg = str(e)
            if "ThrottlingException" in error_msg or "429" in error_msg:
                wait_time = BASE_WAIT * (2 ** (attempt - 1))
                logger.warning(f"Bedrock throttled (attempt {attempt}), waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Bedrock API error (attempt {attempt}): {error_msg}")
                if attempt < max_retries:
                    time.sleep(BASE_WAIT * attempt)
                else:
                    raise
        except Exception as e:
            logger.error(f"Bedrock API error (attempt {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(BASE_WAIT * attempt)
            else:
                raise

    raise RuntimeError(f"Bedrock API failed after {max_retries} retries")


def call_gemini_json(
    prompt: str,
    model_name: str = MODEL_ID,
    max_retries: int = MAX_RETRIES,
    temperature: float = 0.1,
    step_name: str = "",
) -> dict:
    """
    Call Bedrock and parse the response as JSON.
    """
    text = call_gemini(
        prompt=prompt,
        model_name=model_name,
        max_retries=max_retries,
        temperature=temperature,
        json_mode=True,
        step_name=step_name,
    )

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        array_match = re.search(r'\[.*\]', text, re.DOTALL)
        if array_match:
            try:
                return json.loads(array_match.group())
            except json.JSONDecodeError:
                pass

        logger.error(f"Failed to parse JSON from Bedrock response: {text[:200]}")
        return {}


def _clean_json_fences(text: str) -> str:
    """Remove markdown code fences from JSON responses."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()
