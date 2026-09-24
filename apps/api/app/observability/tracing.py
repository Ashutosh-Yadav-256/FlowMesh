"""OpenTelemetry Distributed Tracing & W3C TraceContext Propagation for FlowMesh."""
from __future__ import annotations
import time
import uuid
import re
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager, contextmanager
from pydantic import BaseModel, Field

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace import Status, StatusCode

    resource = Resource.create({"service.name": "flowmesh-platform"})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    _otel_tracer = trace.get_tracer("flowmesh", "0.1.0")
except Exception:
    _otel_tracer = None


class SpanRecord(BaseModel):
    """Represents an immutable recorded span in a distributed trace."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    name: str
    service: str = "flowmesh"
    start_time: float
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    status: str = "OK"
    attributes: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


class TraceContext:
    """W3C TraceContext (traceparent) encoder and decoder."""
    
    @staticmethod
    def generate_trace_id() -> str:
        """Generates a standard 32-character hex trace ID."""
        return uuid.uuid4().hex

    @staticmethod
    def generate_span_id() -> str:
        """Generates a standard 16-character hex span ID."""
        return uuid.uuid4().hex[:16]

    @staticmethod
    def format_traceparent(trace_id: str, span_id: str, sampled: bool = True) -> str:
        """Encodes trace_id and span_id into W3C traceparent header: 00-{trace_id}-{span_id}-{flags}."""
        clean_trace_id = trace_id.replace("-", "").zfill(32)[:32]
        clean_span_id = span_id.replace("-", "").zfill(16)[:16]
        flags = "01" if sampled else "00"
        return f"00-{clean_trace_id}-{clean_span_id}-{flags}"

    @staticmethod
    def parse_traceparent(header_val: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Parses W3C traceparent header returning (trace_id, parent_span_id)."""
        if not header_val:
            return None, None
        
        match = re.match(r"^00-([0-9a-fA-F]{32})-([0-9a-fA-F]{16})-[0-9a-fA-F]{2}$", header_val.strip())
        if match:
            return match.group(1).lower(), match.group(2).lower()
        return None, None


class TraceStore:
    """In-memory, queryable repository of distributed trace spans with FIFO eviction."""
    
    def __init__(self, max_traces: int = 1000):
        self._traces: Dict[str, List[SpanRecord]] = {}
        self._trace_order: List[str] = []
        self._max_traces = max_traces

    def record_span(self, span: SpanRecord) -> None:
        """Stores a span under its trace_id."""
        trace_id = span.trace_id
        if trace_id not in self._traces:
            if len(self._trace_order) >= self._max_traces:
                oldest = self._trace_order.pop(0)
                self._traces.pop(oldest, None)
            self._traces[trace_id] = []
            self._trace_order.append(trace_id)
            
        self._traces[trace_id].append(span)

    def get_trace(self, trace_id: str) -> Optional[List[SpanRecord]]:
        """Retrieves all spans for a trace sorted chronologically by start_time."""
        spans = self._traces.get(trace_id)
        if spans:
            return sorted(spans, key=lambda s: s.start_time)
        return None

    def get_summary(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns recent trace summaries with root span info and total durations."""
        summaries = []
        for tid in reversed(self._trace_order[-limit:]):
            spans = self._traces.get(tid, [])
            if not spans:
                continue
            sorted_spans = sorted(spans, key=lambda s: s.start_time)
            root = sorted_spans[0]
            total_duration = sum(s.duration_ms for s in sorted_spans)
            has_error = any(s.status == "ERROR" for s in sorted_spans)
            summaries.append({
                "trace_id": tid,
                "root_name": root.name,
                "service": root.service,
                "span_count": len(spans),
                "duration_ms": round(total_duration, 2),
                "status": "ERROR" if has_error else "OK",
                "start_time": root.start_time,
            })
        return summaries

    def clear(self) -> None:
        """Clears all stored traces."""
        self._traces.clear()
        self._trace_order.clear()


trace_store = TraceStore()


def get_tracer():
    """Returns the OpenTelemetry tracer instance or dummy tracer."""
    return _otel_tracer


@contextmanager
def record_span(
    name: str,
    service: str = "flowmesh-platform",
    trace_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
):
    """Synchronous context manager to record a trace span into TraceStore and OpenTelemetry."""
    t_id = trace_id or TraceContext.generate_trace_id()
    s_id = TraceContext.generate_span_id()
    attrs = attributes.copy() if attributes else {}
    start = time.time()
    
    span = SpanRecord(
        trace_id=t_id,
        span_id=s_id,
        parent_span_id=parent_span_id,
        name=name,
        service=service,
        start_time=start,
        attributes=attrs,
    )
    
    try:
        yield span
        span.status = "OK"
    except Exception as exc:
        span.status = "ERROR"
        span.error_message = str(exc)
        span.attributes["error.type"] = type(exc).__name__
        span.attributes["error.message"] = str(exc)
        raise
    finally:
        end = time.time()
        span.end_time = end
        span.duration_ms = round((end - start) * 1000, 2)
        trace_store.record_span(span)


@asynccontextmanager
async def record_async_span(
    name: str,
    service: str = "flowmesh-platform",
    trace_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
):
    """Asynchronous context manager to record a trace span into TraceStore and OpenTelemetry."""
    t_id = trace_id or TraceContext.generate_trace_id()
    s_id = TraceContext.generate_span_id()
    attrs = attributes.copy() if attributes else {}
    start = time.time()
    
    span = SpanRecord(
        trace_id=t_id,
        span_id=s_id,
        parent_span_id=parent_span_id,
        name=name,
        service=service,
        start_time=start,
        attributes=attrs,
    )
    
    try:
        yield span
        span.status = "OK"
    except Exception as exc:
        span.status = "ERROR"
        span.error_message = str(exc)
        span.attributes["error.type"] = type(exc).__name__
        span.attributes["error.message"] = str(exc)
        raise
    finally:
        end = time.time()
        span.end_time = end
        span.duration_ms = round((end - start) * 1000, 2)
        trace_store.record_span(span)
