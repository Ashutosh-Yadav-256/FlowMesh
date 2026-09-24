"""Telemetry and Structured Logging Middleware for FastAPI.
Extracts W3C traceparent, measures durations, records Prometheus metrics, and emits §8 structured JSON logs.
"""
from __future__ import annotations
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.observability.tracing import TraceContext, record_span, trace_store
from app.observability.metrics import flowmesh_http_requests_total
from app.observability.logging import (
    current_trace_id,
    current_span_id,
    current_request_id,
    current_tenant_id,
    get_logger,
)

logger = get_logger("flowmesh.ingress")


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Intercepts all HTTP requests to propagate trace context, record metrics, and log structured records."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        
        is_health_or_metric = path in ("/health", "/metrics", "/ready")
        
        incoming_tp = request.headers.get("traceparent")
        trace_id, parent_span_id = TraceContext.parse_traceparent(incoming_tp)
        if not trace_id:
            trace_id = TraceContext.generate_trace_id()
            
        span_id = TraceContext.generate_span_id()
        request_id = request.headers.get("x-request-id") or f"req_{uuid.uuid4().hex[:12]}"
        
        tenant_id = request.headers.get("x-tenant-id", "tenant_default")

        tok_trace = current_trace_id.set(trace_id)
        tok_span = current_span_id.set(span_id)
        tok_req = current_request_id.set(request_id)
        tok_ten = current_tenant_id.set(tenant_id)

        start_time = time.time()
        status_code = 500

        try:
            with record_span(
                name=f"{request.method} {path}",
                service="flowmesh-api",
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                attributes={
                    "http.method": request.method,
                    "http.path": path,
                    "http.client_ip": request.client.host if request.client else "unknown",
                    "request_id": request_id,
                    "tenant_id": tenant_id,
                },
            ) as span:
                response = await call_next(request)
                status_code = response.status_code
                span.attributes["http.status_code"] = status_code
                
                response.headers["x-trace-id"] = trace_id
                response.headers["traceparent"] = TraceContext.format_traceparent(trace_id, span_id)
                return response

        except Exception as exc:
            status_code = 500
            logger.error(
                message=f"HTTP {request.method} {path} unhandled exception: {str(exc)}",
                operation=f"http.{request.method.lower()}",
                result="ERROR",
                tenant_id=tenant_id,
                exc_info=True,
            )
            raise
        finally:
            duration_s = time.time() - start_time
            
            flowmesh_http_requests_total.labels(
                method=request.method,
                endpoint=path,
                status=str(status_code),
            ).inc()

            if not is_health_or_metric:
                log_level = logger.info if status_code < 400 else logger.error
                log_level(
                    message=f"{request.method} {path} responded {status_code} in {round(duration_s * 1000, 2)}ms",
                    operation=f"http.{request.method.lower()}",
                    result="SUCCESS" if status_code < 400 else "ERROR",
                    tenant_id=tenant_id,
                    extra={
                        "http_status": status_code,
                        "duration_ms": round(duration_s * 1000, 2),
                        "path": path,
                    },
                )

            current_trace_id.reset(tok_trace)
            current_span_id.reset(tok_span)
            current_request_id.reset(tok_req)
            current_tenant_id.reset(tok_ten)
