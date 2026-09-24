"""
FlowMesh Request Body Size and Depth Validation Middleware

Prevents memory exhaustion and deserialization attacks by:
1. Rejecting request bodies larger than MAX_REQUEST_BODY_BYTES (default: 1 MB)
2. Rejecting JSON payloads with nesting depth > MAX_JSON_NESTING_DEPTH (default: 10)
"""

from __future__ import annotations

import json
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


def _check_nesting_depth(obj, current_depth: int = 0, max_depth: int = 10) -> bool:
    """Returns True if nesting depth exceeds max_depth."""
    if current_depth > max_depth:
        return True
    if isinstance(obj, dict):
        for value in obj.values():
            if _check_nesting_depth(value, current_depth + 1, max_depth):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if _check_nesting_depth(item, current_depth + 1, max_depth):
                return True
    return False


class InputValidatorMiddleware(BaseHTTPMiddleware):
    """Validates request body size and JSON nesting depth."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        from app.config import settings

        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.max_request_body_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "PayloadTooLarge",
                        "message": f"Request body exceeds maximum allowed size of {settings.max_request_body_bytes} bytes.",
                    },
                )

            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.body()
                    if len(body) > settings.max_request_body_bytes:
                        return JSONResponse(
                            status_code=413,
                            content={
                                "error": "PayloadTooLarge",
                                "message": f"Request body exceeds maximum allowed size of {settings.max_request_body_bytes} bytes.",
                            },
                        )
                    if body:
                        parsed = json.loads(body)
                        if _check_nesting_depth(parsed, max_depth=settings.max_json_nesting_depth):
                            return JSONResponse(
                                status_code=400,
                                content={
                                    "error": "PayloadTooDeep",
                                    "message": f"JSON nesting depth exceeds maximum of {settings.max_json_nesting_depth} levels.",
                                },
                            )
                except json.JSONDecodeError:
                    pass

        return await call_next(request)
