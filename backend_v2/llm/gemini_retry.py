"""
Retry helper for transient Gemini API errors (Phase 4.8 stability fix).

Discovered during real paper generation: running several diagram
questions in parallel can legitimately hit Gemini's free-tier rate limit
(429 RESOURCE_EXHAUSTED) or a transient 503 (model overloaded). Without
a retry, these surface as hard failures even though a short wait usually
clears them. This does not redesign anything - it just wraps the existing
call sites with a few bounded retries.
"""

import re
import time

from google.genai import errors

_RETRYABLE_CODES = {429, 503}
_RETRY_DELAY_RE = re.compile(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)")


def _suggested_delay(exc, attempt):
    match = _RETRY_DELAY_RE.search(str(exc))
    if match:
        return float(match.group(1))
    return min(2 ** attempt, 20)


def call_with_retry(fn, *args, max_attempts=3, **kwargs):
    """Call fn(*args, **kwargs), retrying on 429/503 Gemini errors with a
    short backoff. Re-raises the last error if all attempts are exhausted."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return fn(*args, **kwargs)
        except errors.APIError as exc:
            if exc.code not in _RETRYABLE_CODES or attempt == max_attempts - 1:
                raise
            last_exc = exc
            delay = _suggested_delay(exc, attempt)
            print(f"[GEMINI RETRY] {exc.code} on attempt {attempt + 1}/{max_attempts} - retrying in {delay}s")
            time.sleep(delay)
    raise last_exc
