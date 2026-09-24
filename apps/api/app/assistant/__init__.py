"""
FlowMesh Read-Only AI Incident Assistant (§30)

Reliability-first engineering assistant that inspects logs, distributed traces,
workflow run steps, and circuit breaker metrics to synthesize root-cause analyses.
All diagnostic queries are strictly read-only; remediation actions require
explicit human operator confirmation.
"""

from app.assistant.service import (
    DiagnosticReport,
    RemediationAction,
    IncidentAssistant,
    assistant_service,
)

__all__ = [
    "DiagnosticReport",
    "RemediationAction",
    "IncidentAssistant",
    "assistant_service",
]
