"""
Groq client wrapper.

call_groq_structured() validates JSON output against a Pydantic
schema, retrying with the validation error fed back to the model
if it fails -- up to max_retries times. This is the mechanism that
enforces "the analysis must be correct" rather than leaving it
to hope.

Both call_groq() and call_groq_structured() fall back to Gemini
(gemini_service.py) automatically when Groq raises RateLimitError --
Groq's free-tier daily quota (100k tokens/day) gets exhausted by a
single investigation's REASON stage easily, confirmed repeatedly in
practice across multiple accounts. The fallback is silent to every
caller in reasoning_service.py/chat_service.py -- they only ever call
these two functions and never know which provider actually answered.
If GEMINI_API_KEY isn't configured, the original RateLimitError
propagates unchanged (no silent behavior change for anyone who hasn't
set up the fallback).
"""
import json
import logging
from typing import Type, TypeVar
from groq import Groq, RateLimitError, APIConnectionError
from pydantic import BaseModel, ValidationError
from app.core.config import settings
from app.services.network_retry import call_with_dns_retry

logger = logging.getLogger(__name__)
client = Groq(api_key=settings.GROQ_API_KEY)

T = TypeVar("T", bound=BaseModel)


def _raw_call_groq(prompt: str, system: str, max_tokens: int, temperature: float) -> str:
    """No fallback logic here -- both call_groq() and the retry loop
    inside _call_groq_structured() use this directly, so a RateLimitError
    always propagates to whichever OUTER public function the caller
    actually invoked, which picks the right Gemini fallback (plain vs
    schema-enforced). If the retry loop called call_groq() instead, a
    429 mid-retry would get silently caught by call_groq()'s OWN
    fallback and answered by plain (non-schema-enforced) Gemini instead
    of the structured one -- a real bug, not just an inefficiency."""
    def _do_call():
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content

    return call_with_dns_retry(_do_call, exceptions=(APIConnectionError,), label="Groq")


def call_groq(prompt: str, system: str = "You are an expert financial due diligence analyst.",
              max_tokens: int = 4096, temperature: float = 0.2) -> str:
    try:
        return _raw_call_groq(prompt, system, max_tokens, temperature)
    except RateLimitError:
        if not settings.GEMINI_API_KEY:
            raise
        logger.warning("Groq rate-limited -- falling back to Gemini for this call")
        from app.services.gemini_service import call_gemini
        return call_gemini(prompt, system=system, max_tokens=max_tokens, temperature=temperature)


def call_groq_structured(
    prompt: str,
    schema: Type[T],
    system: str = "You are an expert financial due diligence analyst.",
    max_tokens: int = 4096,
    max_retries: int = 3,
) -> T:
    """
    Calls Groq, requires valid JSON matching `schema`, retries with the
    validation error appended to the prompt if it fails. Raises only
    after exhausting retries -- callers should treat that as a hard
    failure for this investigation, not paper over it with defaults.
    """
    try:
        return _call_groq_structured(prompt, schema, system, max_tokens, max_retries)
    except RateLimitError:
        if not settings.GEMINI_API_KEY:
            raise
        logger.warning("Groq rate-limited -- falling back to Gemini for this structured call")
        from app.services.gemini_service import call_gemini_structured
        return call_gemini_structured(prompt, schema, system=system, max_tokens=max_tokens)


def _call_groq_structured(
    prompt: str,
    schema: Type[T],
    system: str,
    max_tokens: int,
    max_retries: int,
) -> T:
    schema_json = json.dumps(schema.model_json_schema(), indent=2)

    full_system = (
        f"{system}\n\n"
        f"You MUST respond with ONLY valid JSON matching this exact schema. "
        f"No markdown code fences, no preamble, no explanation outside the JSON.\n\n"
        f"Schema:\n{schema_json}"
    )

    current_prompt = prompt
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        raw = _raw_call_groq(current_prompt, full_system, max_tokens, 0.1)
        cleaned = _strip_json_fences(raw)

        try:
            data = json.loads(cleaned)
            validated = schema.model_validate(data)
            return validated
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            logger.warning(
                "Structured Groq call failed validation on attempt %d/%d: %s",
                attempt, max_retries, exc,
            )
            current_prompt = (
                f"{prompt}\n\n"
                f"--- IMPORTANT: your previous response was invalid ---\n"
                f"Error: {exc}\n"
                f"Your previous response was:\n{raw[:1500]}\n\n"
                f"Respond again with ONLY valid JSON matching the required schema. "
                f"Fix the error above."
            )

    raise RuntimeError(
        f"Groq structured call failed validation after {max_retries} attempts: {last_error}"
    )


def _strip_json_fences(text: str) -> str:
    """Models sometimes wrap JSON in ```json ... ``` despite instructions not to."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()