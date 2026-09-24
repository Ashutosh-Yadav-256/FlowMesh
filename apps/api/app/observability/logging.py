"""Structured JSON Logging enforcing §8 mandatory fields across FlowMesh."""
from __future__ import annotations
import json
import logging
import time
import sys
from contextvars import ContextVar
from typing import Optional, Dict, Any

current_request_id: ContextVar[Optional[str]] = ContextVar("current_request_id", default=None)
current_tenant_id: ContextVar[Optional[str]] = ContextVar("current_tenant_id", default=None)
current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)
current_trace_id: ContextVar[Optional[str]] = ContextVar("current_trace_id", default=None)
current_span_id: ContextVar[Optional[str]] = ContextVar("current_span_id", default=None)


class FlowMeshJSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON with §8 mandatory enterprise fields."""

    def format(self, record: logging.LogRecord) -> str:

        req_id = getattr(record, "request_id", None) or current_request_id.get() or "req_system"
        t_id = getattr(record, "tenant_id", None) or current_tenant_id.get() or "tenant_default"
        u_id = getattr(record, "user_id", None) or current_user_id.get() or "user_system"
        tr_id = getattr(record, "trace_id", None) or current_trace_id.get() or "tr_none"
        sp_id = getattr(record, "span_id", None) or current_span_id.get() or "sp_none"
        
        agent_id = getattr(record, "agent_id", None) or "agent_none"
        connector_id = getattr(record, "connector_id", None) or "conn_none"
        operation = getattr(record, "operation", None) or record.funcName or "op_unknown"
        result = getattr(record, "result", None) or ("ERROR" if record.levelno >= logging.ERROR else "SUCCESS")

        payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt) or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": req_id,
            "tenant_id": t_id,
            "agent_id": agent_id,
            "user_id": u_id,
            "connector_id": connector_id,
            "operation": operation,
            "result": result,
            "trace_id": tr_id,
            "span_id": sp_id,
            "logger": record.name,
        }

        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            payload["metadata"] = record.extra_data

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


class FlowMeshLogger:
    """Enterprise wrapper providing convenience methods for structured JSON logging."""

    def __init__(self, name: str = "flowmesh"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(FlowMeshJSONFormatter())
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            self.logger.propagate = False

    def info(
        self,
        message: str,
        operation: Optional[str] = None,
        result: str = "SUCCESS",
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        connector_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._log(
            logging.INFO,
            message,
            operation=operation,
            result=result,
            tenant_id=tenant_id,
            agent_id=agent_id,
            connector_id=connector_id,
            extra_data=extra,
        )

    def warning(
        self,
        message: str,
        operation: Optional[str] = None,
        result: str = "WARNING",
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        connector_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._log(
            logging.WARNING,
            message,
            operation=operation,
            result=result,
            tenant_id=tenant_id,
            agent_id=agent_id,
            connector_id=connector_id,
            extra_data=extra,
        )

    def error(
        self,
        message: str,
        operation: Optional[str] = None,
        result: str = "ERROR",
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        connector_id: Optional[str] = None,
        exc_info: bool = False,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._log(
            logging.ERROR,
            message,
            operation=operation,
            result=result,
            tenant_id=tenant_id,
            agent_id=agent_id,
            connector_id=connector_id,
            exc_info=exc_info,
            extra_data=extra,
        )

    def _log(
        self,
        level: int,
        message: str,
        operation: Optional[str] = None,
        result: str = "SUCCESS",
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        connector_id: Optional[str] = None,
        exc_info: bool = False,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        extra_fields = {
            "operation": operation or "op_log",
            "result": result,
            "agent_id": agent_id or "agent_none",
            "connector_id": connector_id or "conn_none",
            "extra_data": extra_data or {},
        }
        if tenant_id:
            extra_fields["tenant_id"] = tenant_id

        self.logger.log(level, message, exc_info=exc_info, extra=extra_fields)


def get_logger(name: str = "flowmesh") -> FlowMeshLogger:
    """Returns a singleton or scoped FlowMeshLogger."""
    return FlowMeshLogger(name)
