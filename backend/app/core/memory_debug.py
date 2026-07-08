"""
Temporary diagnostic: logs this process's peak resident memory (RSS) at
pipeline stage boundaries. Added specifically to pin down which stage of
GATHER -> NORMALIZE -> REASON is actually responsible for the repeated
OOM kills on Render's 512MB instance -- log timing alone wasn't enough
to tell apart "concurrent fetching" from "embedding" from "LLM calls" as
the real cause, and Render's free-tier Metrics graph is hourly-resolution,
too coarse to see a spike within one ~20s request.

`resource` is POSIX-only (no-op on Windows dev machines, which is fine --
this only needs to run on Render's Linux instance). Remove this module
and its call sites once the actual culprit is confirmed and fixed.
"""
import logging

logger = logging.getLogger(__name__)

try:
    import resource

    def log_memory(label: str) -> None:
        # ru_maxrss is peak RSS in KB on Linux (it's bytes on macOS, but
        # this only matters for Render's Linux instances).
        peak_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        logger.info("[MEM] %s: peak RSS so far = %.1f MB", label, peak_kb / 1024)

except ImportError:
    def log_memory(label: str) -> None:
        pass
