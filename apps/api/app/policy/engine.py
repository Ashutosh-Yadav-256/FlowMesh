"""
FlowMesh Policy-as-Code Engine

Provides declarative governance and guardrails for workflow definitions
and edge agent command dispatches. Enforces enterprise compliance, secret hygiene,
operational limits, and resilience mandates prior to production deployment.
"""

import re
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("flowmesh.policy")


class PolicySeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class PolicyMode(str, Enum):
    ENFORCE = "ENFORCE"
    AUDIT = "AUDIT"


class PolicyViolation(BaseModel):
    rule_name: str
    severity: PolicySeverity
    node_id: Optional[str] = None
    message: str
    remediation: str


class PolicyEvaluationResult(BaseModel):
    allowed: bool
    mode: PolicyMode
    violations_count: int
    errors_count: int
    warnings_count: int
    violations: List[PolicyViolation] = Field(default_factory=list)
    evaluated_rules_count: int = 0


class PolicyRule(ABC):
    """Abstract base rule for declarative policy verification."""

    name: str = "base_rule"
    description: str = ""
    severity: PolicySeverity = PolicySeverity.ERROR

    @abstractmethod
    def evaluate(self, workflow_def: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[PolicyViolation]:
        """Evaluates the rule against workflow definition dict. Returns list of violations."""
        pass


class MaxTimeoutRule(PolicyRule):
    """Ensures workflow execution timeout does not exceed enterprise ceiling."""

    name = "max_workflow_timeout"
    description = "Workflow execution timeout cannot exceed the organization limit (600s)."
    severity = PolicySeverity.ERROR

    def __init__(self, max_allowed_seconds: int = 600) -> None:
        self.max_allowed_seconds = max_allowed_seconds

    def evaluate(self, workflow_def: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[PolicyViolation]:
        violations = []
        timeout = workflow_def.get("timeout_seconds")
        if timeout is not None and isinstance(timeout, (int, float)) and timeout > self.max_allowed_seconds:
            violations.append(
                PolicyViolation(
                    rule_name=self.name,
                    severity=self.severity,
                    node_id=None,
                    message=f"Configured timeout {timeout}s exceeds organization limit of {self.max_allowed_seconds}s.",
                    remediation=f"Set 'timeout_seconds' <= {self.max_allowed_seconds} or request policy exception.",
                )
            )
        return violations


class MaxRetriesRule(PolicyRule):
    """Ensures individual workflow steps do not configure excessive retry loops."""

    name = "max_step_retries"
    description = "Step retry count must not exceed maximum retry limit (5 retries)."
    severity = PolicySeverity.ERROR

    def __init__(self, max_allowed_retries: int = 5) -> None:
        self.max_allowed_retries = max_allowed_retries

    def evaluate(self, workflow_def: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[PolicyViolation]:
        violations = []
        nodes = workflow_def.get("nodes", [])
        for node in nodes:
            retries = node.get("retry_count") or node.get("max_retries")
            if retries is not None and isinstance(retries, int) and retries > self.max_allowed_retries:
                violations.append(
                    PolicyViolation(
                        rule_name=self.name,
                        severity=self.severity,
                        node_id=node.get("id"),
                        message=f"Node '{node.get('name', node.get('id'))}' specifies {retries} retries, exceeding policy ceiling of {self.max_allowed_retries}.",
                        remediation=f"Reduce retry count to {self.max_allowed_retries} or use circuit breaker fallback.",
                    )
                )
        return violations


class DisallowPlaintextSecretsRule(PolicyRule):
    """Detects hardcoded secrets, tokens, and credentials in step configurations."""

    name = "disallow_plaintext_secrets"
    description = "Hardcoded API keys, bearer tokens, or database passwords are forbidden in workflow definitions."
    severity = PolicySeverity.ERROR

    PATTERNS = [
        re.compile(r"sk_live_[0-9a-zA-Z]{24,}"),
        re.compile(r"ghp_[0-9a-zA-Z]{36}"),
        re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{30,}", re.IGNORECASE),
        re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"),
        re.compile(r"password['\"]\s*:\s*['\"][^'\"]{6,}['\"]", re.IGNORECASE),
    ]

    def evaluate(self, workflow_def: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[PolicyViolation]:
        violations = []
        nodes = workflow_def.get("nodes", [])

        def scan_obj(val: Any, node_id: str) -> None:
            if isinstance(val, str):
                for p in self.PATTERNS:
                    if p.search(val):
                        violations.append(
                            PolicyViolation(
                                rule_name=self.name,
                                severity=self.severity,
                                node_id=node_id,
                                message=f"Potential hardcoded secret or token detected in node '{node_id}'.",
                                remediation="Store secret in FlowMesh Connections or reference via connection credentials binding.",
                            )
                        )
                        break
            elif isinstance(val, dict):
                for k, v in val.items():
                    if k.lower() in ["password", "secret", "api_key", "token"] and isinstance(v, str) and not v.startswith("{{"):
                        if len(v) > 6 and not v.startswith("mock_"):
                            violations.append(
                                PolicyViolation(
                                    rule_name=self.name,
                                    severity=self.severity,
                                    node_id=node_id,
                                    message=f"Hardcoded sensitive key '{k}' found in node parameters.",
                                    remediation="Use Connection Secret binding instead of raw parameter strings.",
                                )
                            )
                    scan_obj(v, node_id)
            elif isinstance(val, list):
                for item in val:
                    scan_obj(item, node_id)

        for node in nodes:
            n_id = node.get("id", "unknown_node")
            scan_obj(node.get("parameters", {}), n_id)
            scan_obj(node.get("config", {}), n_id)

        return violations


class RequireDeadLetterQueueRule(PolicyRule):
    """Enforces that workflows with external HTTP or DB integration steps declare DLQ routing."""

    name = "require_dlq_on_external_operations"
    description = "Workflows performing external I/O must specify DLQ or failure routing."
    severity = PolicySeverity.WARNING

    def evaluate(self, workflow_def: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[PolicyViolation]:
        violations = []
        nodes = workflow_def.get("nodes", [])
        has_external_io = any(
            n.get("type") in ["connector_action", "http_request", "postgres_query", "rest_call"]
            for n in nodes
        )
        has_dlq = workflow_def.get("enable_dlq", True) or workflow_def.get("dlq_topic") is not None

        if has_external_io and not has_dlq:
            violations.append(
                PolicyViolation(
                    rule_name=self.name,
                    severity=self.severity,
                    node_id=None,
                    message="Workflow contains external I/O steps but disables Dead Letter Queue (DLQ) routing.",
                    remediation="Enable DLQ in workflow configuration to ensure poison messages can be replayed.",
                )
            )
        return violations


class AllowedConnectorsRule(PolicyRule):
    """Ensures workflow only uses authorized enterprise connector types."""

    name = "allowed_connector_types"
    description = "Workflows may only invoke approved enterprise connector types."
    severity = PolicySeverity.ERROR

    DEFAULT_ALLOWED = {"postgres", "rest", "stripe", "webhook", "redis", "rediforge", "sap", "sftp"}

    def __init__(self, allowed_types: Optional[set] = None) -> None:
        self.allowed_types = {t.lower() for t in (allowed_types or self.DEFAULT_ALLOWED)}

    def evaluate(self, workflow_def: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[PolicyViolation]:
        violations = []
        nodes = workflow_def.get("nodes", [])
        for node in nodes:
            c_type = node.get("connector_type")
            if c_type and c_type.lower() not in self.allowed_types:
                violations.append(
                    PolicyViolation(
                        rule_name=self.name,
                        severity=self.severity,
                        node_id=node.get("id"),
                        message=f"Connector type '{c_type}' is not on the approved enterprise connector list.",
                        remediation=f"Use one of the approved types: {sorted(list(self.allowed_types))}",
                    )
                )
        return violations


class PolicyEngine:
    """Evaluates policy rules against workflow definitions and execution contexts."""

    def __init__(self, rules: Optional[List[PolicyRule]] = None) -> None:
        self.rules: List[PolicyRule] = rules if rules is not None else [
            MaxTimeoutRule(),
            MaxRetriesRule(),
            DisallowPlaintextSecretsRule(),
            RequireDeadLetterQueueRule(),
            AllowedConnectorsRule(),
        ]

    def add_rule(self, rule: PolicyRule) -> None:
        self.rules.append(rule)

    def evaluate(
        self,
        workflow_def: Dict[str, Any],
        mode: PolicyMode = PolicyMode.ENFORCE,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyEvaluationResult:
        all_violations: List[PolicyViolation] = []
        for rule in self.rules:
            try:
                rule_violations = rule.evaluate(workflow_def, context)
                all_violations.extend(rule_violations)
            except Exception as e:
                logger.error(f"Error evaluating rule '{rule.name}': {e}", exc_info=True)

        errors = [v for v in all_violations if v.severity == PolicySeverity.ERROR]
        warnings = [v for v in all_violations if v.severity == PolicySeverity.WARNING]

        allowed = True
        if mode == PolicyMode.ENFORCE and len(errors) > 0:
            allowed = False

        return PolicyEvaluationResult(
            allowed=allowed,
            mode=mode,
            violations_count=len(all_violations),
            errors_count=len(errors),
            warnings_count=len(warnings),
            violations=all_violations,
            evaluated_rules_count=len(self.rules),
        )


default_policy_engine = PolicyEngine()
