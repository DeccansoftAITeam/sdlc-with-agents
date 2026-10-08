"""Sliding-window rate limits (TD-001/AC-8; TM-002 credential stuffing, TM-013 scripted signups).

In-process and per replica: good enough for one API replica (v1). With several replicas
the effective limit multiplies; move the buckets to Postgres or Redis before scaling out
(noted for M10).
"""

import math
import threading
import time
from collections import deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import problem

_buckets: dict[str, deque[float]] = {}
MAX_KEYS = 100_000  # bound memory: oldest keys are evicted first (dicts keep insertion order)
_lock = threading.Lock()


class RateLimited(Exception):
    def __init__(self, retry_after: float) -> None:
        self.retry_after = max(1, math.ceil(retry_after))


def _window(key: str, window_s: float, now: float) -> deque[float]:
    q = _buckets.get(key)
    if q is None:
        while len(_buckets) >= MAX_KEYS:
            del _buckets[next(iter(_buckets))]
        q = _buckets[key] = deque()
    while q and q[0] <= now - window_s:
        q.popleft()
    return q


def _prune(key: str) -> None:
    q = _buckets.get(key)
    if q is not None and not q:
        del _buckets[key]


def check(key: str, limit: int, window_s: float) -> None:
    """Raise RateLimited if `key` already has `limit` events in the window (doesn't count this call)."""
    now = time.monotonic()
    with _lock:
        q = _window(key, window_s, now)
        if len(q) >= limit:
            raise RateLimited(q[0] + window_s - now)
        _prune(key)


def record(key: str, window_s: float) -> None:
    now = time.monotonic()
    with _lock:
        _window(key, window_s, now).append(now)


def hit(key: str, limit: int, window_s: float) -> None:
    """Count this event atomically, refusing it if the limit is already reached."""
    now = time.monotonic()
    with _lock:
        q = _window(key, window_s, now)
        if len(q) >= limit:
            raise RateLimited(q[0] + window_s - now)
        q.append(now)


def forget_last(key: str) -> None:
    """Undo the most recent hit (e.g. a login attempt that turned out to succeed)."""
    with _lock:
        q = _buckets.get(key)
        if q:
            q.pop()
        _prune(key)


def reset() -> None:
    with _lock:
        _buckets.clear()


def install(app: FastAPI) -> None:
    @app.exception_handler(RateLimited)
    async def _rate_limited(_: Request, exc: RateLimited) -> JSONResponse:
        response = problem(429, "Too Many Requests", "Too many attempts. Try again later.")
        response.headers["Retry-After"] = str(exc.retry_after)
        return response
