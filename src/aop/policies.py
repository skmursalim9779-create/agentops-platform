"""Gateway guardrails: PII redaction, rate limiting, loop detection, budgets."""
import hashlib
import re
import threading
import time
from collections import defaultdict, deque

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CARD = re.compile(r"\b(?:\d[ -]?){13,16}\b")
PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[ -]?)?(?:\(\d{2,4}\)|\d{2,4})[ -]?\d{3,4}[ -]?\d{3,4}(?!\d)")


def redact(text):
    """Return (redacted_text, number_of_redactions)."""
    count = 0
    for label, pattern in (("EMAIL", EMAIL), ("CARD", CARD), ("PHONE", PHONE)):
        text, n = pattern.subn(f"[REDACTED_{label}]", text)
        count += n
    return text, count


def contains_pii(text):
    return any(
        p.search(text or "")
        for p in (EMAIL, CARD, PHONE)
    )


class TokenBucket:
    """Per-key token bucket. capacity requests, refilled at `per_minute`."""

    def __init__(self, per_minute=120, capacity=None):
        self.rate = per_minute / 60.0
        self.capacity = capacity or per_minute
        self._state = {}
        self._lock = threading.Lock()

    def allow(self, key):
        now = time.monotonic()
        with self._lock:
            tokens, last = self._state.get(key, (self.capacity, now))
            tokens = min(self.capacity, tokens + (now - last) * self.rate)
            if tokens >= 1:
                self._state[key] = (tokens - 1, now)
                return True
            self._state[key] = (tokens, now)
            return False


class LoopDetector:
    """Flags a session that sends the same prompt `threshold` times within `window` seconds."""

    def __init__(self, threshold=5, window=120):
        self.threshold, self.window = threshold, window
        self._seen = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, session, prompt):
        digest = hashlib.sha1(prompt.encode("utf-8", "ignore")).hexdigest()
        now = time.monotonic()
        with self._lock:
            q = self._seen[(session, digest)]
            q.append(now)
            while q and now - q[0] > self.window:
                q.popleft()
            return len(q) >= self.threshold
