"""
FlowMesh Error Categorization, Backoff, and Circuit Breaker Exceptions

Classifies execution errors into:
- TRANSIENT: Network timeouts, HTTP 5xx, rate limits, connection resets, deadlocks.
- PERMANENT: Schema errors, HTTP 4xx, authentication failures, missing fields.
- CIRCUIT_OPEN: Fast-fail tripped state to avoid pounding degraded dependencies.
"""

from enum import Enum
import random
from typing import Union, Any, Dict, Optional
from flowmesh_workflow.schema import RetryPolicy


class ErrorCategory(str, Enum):
    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"
    CIRCUIT_OPEN = "CIRCUIT_OPEN"


class CircuitBreakerOpenError(Exception):
    """Raised when attempting an operation against a connection with an OPEN circuit breaker."""
    def __init__(self, connection_id: str, message: Optional[str] = None):
        self.connection_id = connection_id
        super().__init__(message or f"Circuit breaker is OPEN for connection '{connection_id}'. Fast-failing downstream traffic.")


def categorize_error(exc: Union[Exception, str]) -> ErrorCategory:
    """
    Categorizes an exception or error message into TRANSIENT, PERMANENT, or CIRCUIT_OPEN.
    """
    if isinstance(exc, CircuitBreakerOpenError):
        return ErrorCategory.CIRCUIT_OPEN

    err_str = str(exc).lower()

    if "circuit breaker is open" in err_str or "circuit_open" in err_str:
        return ErrorCategory.CIRCUIT_OPEN

    permanent_keywords = [
        "400", "bad request",
        "401", "unauthorized",
        "403", "forbidden",
        "404", "not found",
        "422", "unprocessable",
        "validation error", "schema validation",
        "syntax error", "invalid tag",
        "permission denied", "duplicate key",
        "cycle detected",
    ]
    for kw in permanent_keywords:
        if kw in err_str:
            return ErrorCategory.PERMANENT

    transient_keywords = [
        "500", "internal server error",
        "502", "bad gateway",
        "503", "service unavailable",
        "504", "gateway timeout",
        "429", "rate limit", "too many requests",
        "timeout", "timed out",
        "connection refused", "connection reset",
        "network error", "econnrefused", "socket read timeout",
        "deadlock", "temporary failure", "getaddrinfo failed",
    ]
    for kw in transient_keywords:
        if kw in err_str:
            return ErrorCategory.TRANSIENT

    if isinstance(exc, (TimeoutError, ConnectionError)):
        return ErrorCategory.TRANSIENT

    return ErrorCategory.PERMANENT


def calculate_backoff(attempt: int, policy: Union[RetryPolicy, Dict[str, Any]]) -> float:
    """
    Calculates sleep interval in seconds using exponential backoff and jitter.
    """
    if isinstance(policy, dict):
        backoff_type = policy.get("backoff", "exponential")
        initial_sec = float(policy.get("initial_interval_seconds", 0.5))
        max_sec = float(policy.get("max_interval_seconds", 30.0))
        use_jitter = policy.get("jitter", True)
    else:
        backoff_type = policy.backoff
        initial_sec = policy.initial_interval_seconds
        max_sec = policy.max_interval_seconds
        use_jitter = policy.jitter

    attempt_idx = max(1, attempt)

    if backoff_type == "fixed":
        base_interval = initial_sec
    elif backoff_type == "linear":
        base_interval = min(max_sec, initial_sec * attempt_idx)
    else:
        base_interval = min(max_sec, initial_sec * (2 ** (attempt_idx - 1)))

    if use_jitter and base_interval > 0:

        return round(random.uniform(0.5 * base_interval, base_interval), 3)

    return round(base_interval, 3)
