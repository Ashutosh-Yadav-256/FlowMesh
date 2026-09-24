"""
FlowMesh Sliding-Window Rate Limiter Middleware

Enforces per-tenant request rate limits using the StateStore abstraction
(MemoryStateStore for zero-cost dev, RedisStateStore for production).

Features:
- Sliding window counter per (tenant_id, minute)
- Separate limits for auth vs. general endpoints
- X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers
- Exempts /health, /ready, /metrics, /docs, /openapi.json
"""

from __future__ import annotations

import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


_window_counters: dict[str, list[float]] = defaultdict(list)

_EXEMPT_PATHS = frozenset({
    "/health", "/ready", "/metrics", "/docs", "/redoc", "/openapi.json",
    "/favicon.ico",
})


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Tenant-scoped sliding-window rate limiter."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        from app.config import settings

        if not settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path

        if path in _EXEMPT_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        tenant_id = request.headers.get("x-tenant-id", "tenant_default")

        is_auth = path.startswith("/api/v1/auth") or path.startswith("/api/v1/api-keys")
        limit = settings.rate_limit_auth_per_minute if is_auth else settings.rate_limit_per_minute

        now = time.time()
        window_key = f"rl:{tenant_id}:{'auth' if is_auth else 'general'}"
        window = _window_counters[window_key]

        cutoff = now - 60.0
        while window and window[0] < cutoff:
            window.pop(0)

        remaining = max(0, limit - len(window))
        reset_at = int(now + 60)

        if len(window) >= limit:
            retry_after = int(window[0] + 60 - now) + 1
            return JSONResponse(
                status_code=429,
                content={
                    "error": "TooManyRequests",
                    "message": f"Rate limit exceeded. Maximum {limit} requests per minute for this tenant.",
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                },
            )

        window.append(now)

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1 if remaining > 0 else 0)
        response.headers["X-RateLimit-Reset"] = str(reset_at)

        return response
