"""
Retry helper scoped specifically to transient DNS/connection failures --
confirmed on this dev machine/network as `[Errno 11001] getaddrinfo
failed` blips (Windows resolver hiccups) that self-resolve within
~15-20s, hitting Supabase, Qdrant, Groq, and Gemini unpredictably. Not
used for rate limits, validation errors, or anything else -- those still
propagate immediately exactly as before.

A blip mid-REASON-stage previously killed the whole investigation and
surfaced "This investigation failed" to the user for something that
would have succeeded on its own a few seconds later.
"""
import logging
import time

logger = logging.getLogger(__name__)


def call_with_dns_retry(fn, *, exceptions, retries=3, base_delay_seconds=5, label="request"):
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except exceptions as exc:
            last_exc = exc
            if attempt == retries:
                break
            delay = base_delay_seconds * attempt
            logger.warning(
                "%s hit a connection error (attempt %d/%d): %s -- retrying in %ds",
                label, attempt, retries, exc, delay,
            )
            time.sleep(delay)
    raise last_exc
