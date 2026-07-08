"""
Gemini client wrapper -- automatic fallback for when Groq's free-tier
daily quota is exhausted (see groq_service.py, which catches Groq's
RateLimitError and calls into this module transparently; nothing in
reasoning_service.py or chat_service.py needs to know this exists).

Uses Gemini's native structured-output support (response_schema +
response_mime_type="application/json") instead of the schema-dumped-
into-prompt-text approach Groq needs -- no manual JSON schema
duplication in the prompt. This constrains the *shape* of the output,
not its length: a real fallback call still truncated mid-JSON when
max_tokens was too small, so call_gemini_structured() still needs its
own retry loop, same as Groq's -- confirmed by that actual failure, not
assumed upfront.
"""
import logging
from typing import Type, TypeVar
import httpx
from google import genai
from google.genai import types
from google.genai.errors import ServerError
from pydantic import BaseModel
from app.core.config import settings
from app.services.network_retry import call_with_dns_retry

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# httpx.TransportError catches DNS/connection blips; ServerError catches
# Gemini's own "503 UNAVAILABLE -- model currently experiencing high
# demand, please try again later" -- confirmed in practice as a genuine,
# textbook-transient failure distinct from a connection-level error, so
# it gets the same retry-with-backoff treatment rather than failing the
# whole investigation on the first hiccup.
_RETRYABLE_GEMINI_EXCEPTIONS = (httpx.TransportError, ServerError)

_client: "genai.Client | None" = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY not configured -- cannot fall back to Gemini. "
                "Get a free key at https://aistudio.google.com/apikey"
            )
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def call_gemini(
    prompt: str,
    system: str = "You are an expert financial due diligence analyst.",
    max_tokens: int = 4096,
    temperature: float = 0.2,
) -> str:
    client = _get_client()

    def _do_call():
        return client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )

    response = call_with_dns_retry(_do_call, exceptions=_RETRYABLE_GEMINI_EXCEPTIONS, label="Gemini")
    return response.text or ""


# Confirmed via the model's own model.output_token_limit -- don't keep
# doubling past what the model can physically return.
_MAX_OUTPUT_TOKENS_CEILING = 60000


def call_gemini_structured(
    prompt: str,
    schema: Type[T],
    system: str = "You are an expert financial due diligence analyst.",
    max_tokens: int = 4096,
    max_retries: int = 5,
) -> T:
    """
    Requires valid JSON matching `schema`. Gemini's response_schema mode
    guarantees the JSON is *shaped* right, but doesn't protect against
    truncation -- confirmed in practice: a real fallback call cut off
    mid-string ("EOF while parsing a string") when max_tokens was too
    small for the actual output, which response_schema does nothing to
    prevent. Retries mirror Groq's approach (error fed back into the
    prompt), but specifically double max_tokens when the finish_reason
    shows truncation rather than treating it like a generic format error.
    max_retries defaults to 5 (not 3, like Groq's) since a genuinely
    large investigation needed 3 doublings to stop truncating in
    practice -- confirmed against the model's real 65536-token output
    limit, so there's room for several doublings before hitting it.
    """
    client = _get_client()
    current_prompt = prompt
    current_max_tokens = max_tokens
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        def _do_call():
            return client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=current_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    max_output_tokens=current_max_tokens,
                    temperature=0.1,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )

        response = call_with_dns_retry(_do_call, exceptions=_RETRYABLE_GEMINI_EXCEPTIONS, label="Gemini")
        truncated = bool(response.candidates) and response.candidates[0].finish_reason == "MAX_TOKENS"

        try:
            if not response.text:
                raise ValueError("empty response text")
            return schema.model_validate_json(response.text)
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Gemini structured call failed validation on attempt %d/%d (truncated=%s): %s",
                attempt, max_retries, truncated, exc,
            )
            if truncated:
                current_max_tokens = min(current_max_tokens * 2, _MAX_OUTPUT_TOKENS_CEILING)
            else:
                current_prompt = (
                    f"{prompt}\n\n"
                    f"--- IMPORTANT: your previous response was invalid ---\n"
                    f"Error: {exc}\n"
                    f"Respond again with ONLY valid JSON matching the required schema."
                )

    raise RuntimeError(
        f"Gemini structured call failed validation after {max_retries} attempts: {last_error}"
    )
