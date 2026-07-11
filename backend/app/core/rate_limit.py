"""Minimal in-memory rate limiter for the login endpoint (Section 15).

A single-process, in-memory limiter is sufficient for the MVP: SchoolPrint
runs as one backend instance on a Raspberry Pi, so there is no need for a
distributed store like Redis. If the deployment ever becomes multi-process,
this should move to a shared backend.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()
        if len(hits) >= self.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts, please wait before trying again.",
            )
        hits.append(now)

    def reset(self, key: str) -> None:
        self._hits.pop(key, None)


login_rate_limiter = InMemoryRateLimiter(max_attempts=10, window_seconds=60)


def client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"
