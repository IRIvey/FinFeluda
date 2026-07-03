"""
Groq client wrapper.

call_groq_structured() validates JSON output against a Pydantic
schema, retrying with the validation error fed back to the model
if it fails -- up to max_retries times. This is the mechanism that
enforces "the analysis must be correct" rather than leaving it
to hope.
"""
import json
import logging
from typing import Type, TypeVar
from groq import Groq
from pydantic import BaseModel, ValidationError
from app.core.config import settings

logger = logging.getLogger(__name__)
client = Groq(api_key=settings.GROQ_API_KEY)

T = TypeVar("T", bound=BaseModel)


def call_groq(prompt: str, system: str = "You are an expert financial due diligence analyst.",
              max_tokens: int = 4096, temperature: float = 0.2) -> str:
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
        raw = call_groq(current_prompt, system=full_system, max_tokens=max_tokens, temperature=0.1)
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