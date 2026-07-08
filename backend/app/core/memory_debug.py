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

Uses print(), not logging -- confirmed the hard way that this app never
calls logging.basicConfig() anywhere, so the root logger sits at the
default WARNING level and every plain logger.info() call across the
whole codebase (this one included, originally) was being silently
dropped before it reached any handler. print() goes straight to stdout,
which Render always captures regardless of logging config.
"""
import sys

try:
    import resource

    def log_memory(label: str) -> None:
        # ru_maxrss is peak RSS in KB on Linux (it's bytes on macOS, but
        # this only matters for Render's Linux instances).
        peak_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        print(f"[MEM] {label}: peak RSS so far = {peak_kb / 1024:.1f} MB", flush=True, file=sys.stderr)

except ImportError:
    def log_memory(label: str) -> None:
        pass
