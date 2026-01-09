"""
Rate Limiting Module - Security Enhancement.

Provides rate limiting to protect against abuse with:
    - In-memory rate limiter with configurable limits
    - Per-client/IP request tracking
    - Sliding window algorithm
    - Configurable time windows and request limits
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Callable, Optional

from invoice_mcp_server.shared.logging import get_logger

logger = get_logger(__name__)


class RateLimitResult(Enum):
    ALLOWED = "allowed"
    LIMITED = "limited"
    BLOCKED = "blocked"


@dataclass
class RateLimitConfig:
    requests_per_window: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_REQUESTS", "100")))
    window_seconds: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_WINDOW", "60")))
    burst_limit: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_BURST", "20")))
    block_duration_seconds: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_BLOCK_DURATION", "300")))


@dataclass
class ClientRateInfo:
    request_times: list[float] = field(default_factory=list)
    blocked_until: Optional[float] = None
    violation_count: int = 0


@dataclass
class RateLimitResponse:
    result: RateLimitResult
    remaining: int = 0
    reset_after: float = 0.0
    retry_after: Optional[float] = None
    message: str = ""

    def to_headers(self) -> dict[str, str]:
        headers = {
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_after)),
        }
        if self.retry_after is not None:
            headers["Retry-After"] = str(int(self.retry_after))
        return headers


class RateLimiter:
    def __init__(self, config: Optional[RateLimitConfig] = None) -> None:
        self._config = config or RateLimitConfig()
        self._clients: dict[str, ClientRateInfo] = defaultdict(ClientRateInfo)
        self._lock = Lock()
        self._cleanup_interval = 300
        self._last_cleanup = time.time()

    @property
    def config(self) -> RateLimitConfig:
        return self._config

    def _cleanup_old_entries(self) -> None:
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        cutoff = current_time - self._config.window_seconds * 2
        clients_to_remove = []
        for client_id, info in self._clients.items():
            info.request_times = [t for t in info.request_times if t > cutoff]
            if not info.request_times and (info.blocked_until is None or info.blocked_until < current_time):
                clients_to_remove.append(client_id)
        for client_id in clients_to_remove:
            del self._clients[client_id]
        self._last_cleanup = current_time

    def check_rate_limit(self, client_id: str) -> RateLimitResponse:
        with self._lock:
            self._cleanup_old_entries()
            current_time = time.time()
            client_info = self._clients[client_id]
            if client_info.blocked_until and current_time < client_info.blocked_until:
                retry_after = client_info.blocked_until - current_time
                return RateLimitResponse(
                    result=RateLimitResult.BLOCKED,
                    remaining=0,
                    reset_after=client_info.blocked_until,
                    retry_after=retry_after,
                    message=f"Client blocked for {int(retry_after)} seconds",
                )
            window_start = current_time - self._config.window_seconds
            client_info.request_times = [t for t in client_info.request_times if t > window_start]
            request_count = len(client_info.request_times)
            if request_count >= self._config.requests_per_window:
                client_info.violation_count += 1
                if client_info.violation_count >= 3:
                    client_info.blocked_until = current_time + self._config.block_duration_seconds
                    logger.warning(f"Client {client_id} blocked for repeated rate limit violations")
                    return RateLimitResponse(
                        result=RateLimitResult.BLOCKED,
                        remaining=0,
                        reset_after=client_info.blocked_until,
                        retry_after=float(self._config.block_duration_seconds),
                        message="Client blocked for repeated violations",
                    )
                oldest_request = min(client_info.request_times)
                reset_after = oldest_request + self._config.window_seconds
                retry_after = reset_after - current_time
                logger.info(f"Rate limit exceeded for client {client_id}")
                return RateLimitResponse(
                    result=RateLimitResult.LIMITED,
                    remaining=0,
                    reset_after=reset_after,
                    retry_after=retry_after,
                    message="Rate limit exceeded",
                )
            recent_window = current_time - 1.0
            recent_requests = sum(1 for t in client_info.request_times if t > recent_window)
            if recent_requests >= self._config.burst_limit:
                return RateLimitResponse(
                    result=RateLimitResult.LIMITED,
                    remaining=0,
                    reset_after=current_time + 1.0,
                    retry_after=1.0,
                    message="Burst limit exceeded",
                )
            client_info.request_times.append(current_time)
            remaining = self._config.requests_per_window - len(client_info.request_times)
            if client_info.request_times:
                oldest = min(client_info.request_times)
                reset_after = oldest + self._config.window_seconds
            else:
                reset_after = current_time + self._config.window_seconds
            return RateLimitResponse(
                result=RateLimitResult.ALLOWED,
                remaining=max(0, remaining),
                reset_after=reset_after,
                message="Request allowed",
            )

    def reset_client(self, client_id: str) -> None:
        with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]
                logger.info(f"Reset rate limit for client {client_id}")

    def get_client_status(self, client_id: str) -> dict[str, Any]:
        with self._lock:
            client_info = self._clients.get(client_id)
            if not client_info:
                return {"status": "unknown", "requests": 0, "remaining": self._config.requests_per_window}
            current_time = time.time()
            window_start = current_time - self._config.window_seconds
            recent_requests = [t for t in client_info.request_times if t > window_start]
            return {
                "status": "blocked" if client_info.blocked_until and client_info.blocked_until > current_time else "active",
                "requests": len(recent_requests),
                "remaining": max(0, self._config.requests_per_window - len(recent_requests)),
                "violation_count": client_info.violation_count,
                "blocked_until": client_info.blocked_until,
            }


_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def reset_rate_limiter() -> None:
    global _rate_limiter
    _rate_limiter = None


def rate_limit(get_client_id: Optional[Callable[..., str]] = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        from functools import wraps
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            request = args[0] if args else kwargs.get("request")
            if get_client_id:
                client_id = get_client_id(*args, **kwargs)
            elif hasattr(request, "remote"):
                client_id = request.remote or "unknown"
            elif hasattr(request, "headers"):
                client_id = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP", "unknown"))
            else:
                client_id = "unknown"
            rate_limiter = get_rate_limiter()
            result = rate_limiter.check_rate_limit(client_id)
            if result.result != RateLimitResult.ALLOWED:
                from aiohttp import web
                return web.json_response(
                    {"error": result.message, "retry_after": result.retry_after},
                    status=429,
                    headers=result.to_headers(),
                )
            response = await func(*args, **kwargs)
            if hasattr(response, "headers"):
                for key, value in result.to_headers().items():
                    response.headers[key] = value
            return response
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if get_client_id:
                client_id = get_client_id(*args, **kwargs)
            else:
                client_id = "unknown"
            rate_limiter = get_rate_limiter()
            result = rate_limiter.check_rate_limit(client_id)
            if result.result != RateLimitResult.ALLOWED:
                raise Exception(f"Rate limited: {result.message}")
            return func(*args, **kwargs)
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


async def rate_limit_middleware(request: Any, handler: Callable[..., Any]) -> Any:
    from aiohttp import web
    if request.path == "/health" or request.method == "OPTIONS":
        return await handler(request)
    rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    if not rate_limit_enabled:
        return await handler(request)
    client_id = request.headers.get("X-Forwarded-For", request.headers.get("X-Real-IP", request.remote or "unknown"))
    if "," in client_id:
        client_id = client_id.split(",")[0].strip()
    rate_limiter = get_rate_limiter()
    result = rate_limiter.check_rate_limit(client_id)
    if result.result != RateLimitResult.ALLOWED:
        return web.json_response(
            {"error": result.message, "retry_after": result.retry_after},
            status=429,
            headers=result.to_headers(),
        )
    response = await handler(request)
    for key, value in result.to_headers().items():
        response.headers[key] = value
    return response
