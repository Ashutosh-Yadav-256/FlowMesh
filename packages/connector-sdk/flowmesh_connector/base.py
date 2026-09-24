"""
FlowMesh Connector SDK - Base Connector Implementation

Provides a structured, production-ready foundation for authoring FlowMesh connectors.
Handles automatic duration tracking, error normalization, 4-point health verification,
and typed dispatch to registered operation handlers.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable, Awaitable, Optional

from flowmesh_connector.protocol import (
    ConnectionSpec,
    TestStepResult,
    TestResult,
    DiscoveryGraph,
    OperationSpec,
    Operation,
    OperationResult,
)

logger = logging.getLogger("flowmesh.connector_sdk")


class BaseConnector(ABC):
    """
    Abstract Base Class for FlowMesh Connectors.
    
    Subclasses implement:
    - `validate_credentials(conn)`
    - `ping_connection(conn)`
    - `check_permissions(conn)`
    - `probe_discovery(conn)`
    - `discover(conn)`
    - `operations()`
    - Individual operation handler methods or register them in `_handlers`.
    """

    type: str = "base"

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[ConnectionSpec, Operation], Awaitable[Any]]] = {}

    def register_handler(
        self, op_name: str, handler: Callable[[ConnectionSpec, Operation], Awaitable[Any]]
    ) -> None:
        """Registers an asynchronous operation handler function."""
        self._handlers[op_name.lower()] = handler

    async def test(self, conn: ConnectionSpec) -> TestResult:
        """
        Standard 4-point health check lifecycle:
        1. Connectivity (Network ping / reachability)
        2. Authentication (Credentials format & cryptographic check)
        3. Permissions (Authorization / scope probe)
        4. Schema / Discovery probe (Ensures metadata introspection works)
        """
        steps: List[TestStepResult] = []

        t0 = time.perf_counter()
        try:
            await self.ping_connection(conn)
            dur = (time.perf_counter() - t0) * 1000
            steps.append(TestStepResult(name="connectivity", status="passed", duration_ms=dur, message="Host is reachable"))
        except Exception as e:
            dur = (time.perf_counter() - t0) * 1000
            steps.append(TestStepResult(name="connectivity", status="failed", duration_ms=dur, message=f"Connection failed: {str(e)}"))
            return TestResult(success=False, steps=steps, error_message=str(e))

        t0 = time.perf_counter()
        try:
            await self.validate_credentials(conn)
            dur = (time.perf_counter() - t0) * 1000
            steps.append(TestStepResult(name="authentication", status="passed", duration_ms=dur, message="Credentials verified"))
        except Exception as e:
            dur = (time.perf_counter() - t0) * 1000
            steps.append(TestStepResult(name="authentication", status="failed", duration_ms=dur, message=f"Auth failed: {str(e)}"))
            return TestResult(success=False, steps=steps, error_message=str(e))

        t0 = time.perf_counter()
        try:
            await self.check_permissions(conn)
            dur = (time.perf_counter() - t0) * 1000
            steps.append(TestStepResult(name="permissions", status="passed", duration_ms=dur, message="Required permissions granted"))
        except Exception as e:
            dur = (time.perf_counter() - t0) * 1000
            steps.append(TestStepResult(name="permissions", status="failed", duration_ms=dur, message=f"Permissions error: {str(e)}"))
            return TestResult(success=False, steps=steps, error_message=str(e))

        t0 = time.perf_counter()
        try:
            await self.probe_discovery(conn)
            dur = (time.perf_counter() - t0) * 1000
            steps.append(TestStepResult(name="discovery", status="passed", duration_ms=dur, message="Metadata schema probe successful"))
        except Exception as e:
            dur = (time.perf_counter() - t0) * 1000
            steps.append(TestStepResult(name="discovery", status="failed", duration_ms=dur, message=f"Discovery failed: {str(e)}"))
            return TestResult(success=False, steps=steps, error_message=str(e))

        return TestResult(success=True, steps=steps)

    @abstractmethod
    async def ping_connection(self, conn: ConnectionSpec) -> None:
        """Pings upstream service."""
        pass

    @abstractmethod
    async def validate_credentials(self, conn: ConnectionSpec) -> None:
        """Verifies authentication credentials."""
        pass

    @abstractmethod
    async def check_permissions(self, conn: ConnectionSpec) -> None:
        """Verifies authorization."""
        pass

    @abstractmethod
    async def probe_discovery(self, conn: ConnectionSpec) -> None:
        """Tests discovery capability."""
        pass

    @abstractmethod
    async def discover(self, conn: ConnectionSpec) -> DiscoveryGraph:
        """Discovers entities, schemas, and relationships."""
        pass

    @abstractmethod
    def operations(self) -> List[OperationSpec]:
        """Lists supported operations and schemas."""
        pass

    async def execute(self, conn: ConnectionSpec, op: Operation) -> OperationResult:
        """Executes an authorized operation with timing and error isolation."""
        t0 = time.perf_counter()
        op_name = op.name.lower()

        handler = self._handlers.get(op_name)
        if not handler:

            method_name = f"op_{op_name}"
            if hasattr(self, method_name):
                handler = getattr(self, method_name)

        if not handler:
            dur = (time.perf_counter() - t0) * 1000
            return OperationResult(
                success=False,
                duration_ms=dur,
                error=f"Unsupported operation '{op.name}' for connector '{self.type}'.",
                records_affected=0
            )

        try:
            data = await handler(conn, op)
            dur = (time.perf_counter() - t0) * 1000
            records = 1 if data is not None else 0
            if isinstance(data, list):
                records = len(data)
            return OperationResult(
                success=True,
                duration_ms=dur,
                data=data,
                records_affected=records
            )
        except Exception as e:
            dur = (time.perf_counter() - t0) * 1000
            logger.error(f"Connector '{self.type}' operation '{op.name}' failed: {e}", exc_info=True)
            return OperationResult(
                success=False,
                duration_ms=dur,
                error=str(e),
                records_affected=0
            )
