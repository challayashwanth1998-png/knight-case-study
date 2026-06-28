"""
Shared Gemini API helper with automatic rate-limit retry and cost tracking.
Tracks tokens, cost, and latency per call.
"""
import re
import time
import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

# Lazy initialization
_genai = None
_initialized = False

def _ensure_initialized():
    global _genai, _initialized
    if not _initialized:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _genai = genai
        _initialized = True
    return _genai

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 5
BASE_WAIT = 15

# Gemini 2.5 Flash pricing (per 1M tokens)
PRICE_INPUT_PER_1M = 0.15    # $0.15 per 1M input tokens
PRICE_OUTPUT_PER_1M = 0.60   # $0.60 per 1M output tokens


# ── Cost Tracking ──────────────────────────────────────────

@dataclass
class AICallMetrics:
    """Metrics for a single Gemini API call."""
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


def _extract_token_counts(response) -> tuple[int, int]:
    """Extract input/output token counts from Gemini response metadata."""
    try:
        usage = response.usage_metadata
        return (
            getattr(usage, "prompt_token_count", 0) or 0,
            getattr(usage, "candidates_token_count", 0) or 0,
        )
    except Exception:
        return 0, 0


# ── API Call Functions ──────────────────────────────────────

def call_gemini(
    prompt: str,
    model_name: str = DEFAULT_MODEL,
    max_retries: int = MAX_RETRIES,
    temperature: float = 0.1,
    json_mode: bool = False,
    step_name: str = "",
) -> str:
    """
    Call Gemini with automatic retry on rate-limit (429) errors.
    Tracks token usage and cost.
    """
    _ensure_initialized()
    gen_config = {"temperature": temperature}
    if json_mode:
        gen_config["response_mime_type"] = "application/json"

    model = _genai.GenerativeModel(model_name, generation_config=gen_config)

    for attempt in range(1, max_retries + 1):
        try:
            start_time = time.time()
            response = model.generate_content(prompt)
            latency_ms = int((time.time() - start_time) * 1000)

            text = response.text
            text = _clean_json_fences(text)

            # Track metrics
            input_tokens, output_tokens = _extract_token_counts(response)
            cost = _calculate_cost(input_tokens, output_tokens)

            call_metrics = AICallMetrics(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                latency_ms=latency_ms,
                step_name=step_name,
            )

            # Add to submission-level tracker if active
            tracker = get_current_metrics()
            if tracker:
                tracker.add_call(call_metrics)

            logger.info(
                f"Gemini call ({step_name}): "
                f"{input_tokens}in/{output_tokens}out tokens, "
                f"${cost:.5f}, {latency_ms}ms"
            )

            return text
        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower()

            if is_rate_limit and attempt < max_retries:
                wait_time = _parse_retry_delay(err_str, attempt)
                logger.warning(
                    f"Gemini rate limit hit (attempt {attempt}/{max_retries}). "
                    f"Waiting {wait_time}s before retry..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"Gemini API error (attempt {attempt}): {e}")
                if attempt >= max_retries:
                    raise
                time.sleep(BASE_WAIT * attempt)

    raise RuntimeError("Gemini API call failed after all retries")


def call_gemini_json(
    prompt: str,
    model_name: str = DEFAULT_MODEL,
    max_retries: int = MAX_RETRIES,
    temperature: float = 0.1,
    step_name: str = "",
) -> dict | list:
    """
    Call Gemini and parse the response as JSON.
    Handles markdown fences, retries on rate limits AND parse errors.
    """
    text = call_gemini(
        prompt, model_name=model_name, max_retries=max_retries,
        temperature=temperature, json_mode=True, step_name=step_name,
    )

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        cleaned = _extract_json(text)
        if cleaned is not None:
            return cleaned
        logger.error(f"Failed to parse Gemini response as JSON. Response: {text[:500]}")
        raise


def call_gemini_vision_batch(
    prompt: str,
    images: list[tuple[bytes, str, str]],  # [(image_data, mime_type, label), ...]
    model_name: str = DEFAULT_MODEL,
    max_retries: int = MAX_RETRIES,
    temperature: float = 0.1,
    step_name: str = "",
) -> str:
    """
    Call Gemini with MULTIPLE images in a single API call.
    Much faster than individual calls for CDL batches.
    
    Args:
        images: list of (image_bytes, mime_type, label) tuples
    Returns:
        Combined text response for all images
    """
    _ensure_initialized()
    gen_config = {"temperature": temperature}
    model = _genai.GenerativeModel(model_name, generation_config=gen_config)

    # Build multimodal content: prompt + all images
    content_parts = [prompt]
    for image_data, mime_type, label in images:
        content_parts.append(f"\n--- Image: {label} ---")
        content_parts.append({"mime_type": mime_type, "data": image_data})

    for attempt in range(1, max_retries + 1):
        try:
            start_time = time.time()
            response = model.generate_content(content_parts)
            latency_ms = int((time.time() - start_time) * 1000)

            text = response.text
            text = _clean_json_fences(text)

            input_tokens, output_tokens = _extract_token_counts(response)
            cost = _calculate_cost(input_tokens, output_tokens)

            call_metrics = AICallMetrics(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                latency_ms=latency_ms,
                step_name=step_name,
            )
            tracker = get_current_metrics()
            if tracker:
                tracker.add_call(call_metrics)

            logger.info(
                f"Gemini vision BATCH ({step_name}, {len(images)} images): "
                f"{input_tokens}in/{output_tokens}out tokens, "
                f"${cost:.5f}, {latency_ms}ms"
            )
            return text
        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower()
            if is_rate_limit and attempt < max_retries:
                wait_time = _parse_retry_delay(err_str, attempt)
                logger.warning(f"Gemini vision batch rate limit (attempt {attempt}/{max_retries}). Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Gemini vision batch error (attempt {attempt}): {e}")
                if attempt >= max_retries:
                    raise
                time.sleep(BASE_WAIT * attempt)
    raise RuntimeError("Gemini vision batch call failed after all retries")

def call_gemini_vision(
    prompt: str,
    image_data: bytes,
    mime_type: str = "image/png",
    model_name: str = DEFAULT_MODEL,
    max_retries: int = MAX_RETRIES,
    temperature: float = 0.1,
    json_mode: bool = False,
    step_name: str = "",
) -> str:
    """
    Call Gemini with an image + text prompt (multimodal).
    Used for reading driver licenses, inspecting documents with images, etc.
    """
    _ensure_initialized()
    gen_config = {"temperature": temperature}
    if json_mode:
        gen_config["response_mime_type"] = "application/json"

    model = _genai.GenerativeModel(model_name, generation_config=gen_config)

    # Create multimodal content
    image_part = {"mime_type": mime_type, "data": image_data}

    for attempt in range(1, max_retries + 1):
        try:
            start_time = time.time()
            response = model.generate_content([prompt, image_part])
            latency_ms = int((time.time() - start_time) * 1000)

            text = response.text
            text = _clean_json_fences(text)

            input_tokens, output_tokens = _extract_token_counts(response)
            cost = _calculate_cost(input_tokens, output_tokens)

            call_metrics = AICallMetrics(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                latency_ms=latency_ms,
                step_name=step_name,
            )

            tracker = get_current_metrics()
            if tracker:
                tracker.add_call(call_metrics)

            logger.info(
                f"Gemini vision call ({step_name}): "
                f"{input_tokens}in/{output_tokens}out tokens, "
                f"${cost:.5f}, {latency_ms}ms"
            )

            return text
        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower()

            if is_rate_limit and attempt < max_retries:
                wait_time = _parse_retry_delay(err_str, attempt)
                logger.warning(
                    f"Gemini vision rate limit hit (attempt {attempt}/{max_retries}). "
                    f"Waiting {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"Gemini vision API error (attempt {attempt}): {e}")
                if attempt >= max_retries:
                    raise
                time.sleep(BASE_WAIT * attempt)

    raise RuntimeError("Gemini vision API call failed after all retries")


def call_gemini_vision_json(
    prompt: str,
    image_data: bytes,
    mime_type: str = "image/png",
    model_name: str = DEFAULT_MODEL,
    max_retries: int = MAX_RETRIES,
    temperature: float = 0.1,
    step_name: str = "",
) -> dict | list:
    """Call Gemini vision and parse the response as JSON."""
    text = call_gemini_vision(
        prompt, image_data, mime_type=mime_type, model_name=model_name,
        max_retries=max_retries, temperature=temperature,
        json_mode=True, step_name=step_name,
    )

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        cleaned = _extract_json(text)
        if cleaned is not None:
            return cleaned
        logger.error(f"Failed to parse vision response as JSON. Response: {text[:500]}")
        raise


# ── Helpers ──────────────────────────────────────────────────

def _clean_json_fences(text: str) -> str:
    """Remove markdown code fences from JSON responses."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _extract_json(text: str) -> dict | list | None:
    """Try to find and parse JSON from text that might have extra content."""
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    return None


def _parse_retry_delay(error_str: str, attempt: int) -> float:
    """Try to parse the retry delay from a Gemini 429 error message."""
    match = re.search(r"retry in (\d+\.?\d*)", error_str.lower())
    if match:
        return float(match.group(1)) + 2
    return min(BASE_WAIT * (2 ** (attempt - 1)), 120)
