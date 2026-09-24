"""
FlowMesh Connector Protocol Specification (Frozen Core Contract)

The engine only ever interacts with this protocol. It must not know whether
an execution occurs in a cloud worker or inside a customer network via an Edge Agent.
"""

from typing import Protocol, List, Dict, Any, Optional, runtime_checkable
from pydantic import BaseModel, Field


class ConnectionSpec(BaseModel):
    id: str
    tenant_id: str
    type: str
    name: str
    config: Dict[str, Any]
    credentials: Optional[Dict[str, Any]] = None
    agent_id: Optional[str] = None


class TestStepResult(BaseModel):
    name: str
    status: str
    duration_ms: float
    message: str


class TestResult(BaseModel):
    success: bool
    steps: List[TestStepResult]
    error_message: Optional[str] = None


TestResult.__test__ = False
TestStepResult.__test__ = False


class ColumnInfo(BaseModel):
    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False


class TableInfo(BaseModel):
    schema_name: str
    table_name: str
    columns: List[ColumnInfo]


class DiscoveryGraph(BaseModel):
    entities: List[TableInfo] = Field(default_factory=list)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OperationSpec(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


class Operation(BaseModel):
    id: str
    name: str
    parameters: Dict[str, Any]


class OperationResult(BaseModel):
    success: bool
    duration_ms: float
    data: Optional[Any] = None
    error: Optional[str] = None
    records_affected: int = 0


@runtime_checkable
class Connector(Protocol):
    """Authoritative, frozen Connector Protocol implemented across all connectors."""
    type: str

    async def test(self, conn: ConnectionSpec) -> TestResult:
        """Runs the four-point health & auth check: connectivity, auth, permissions, discovery."""
        ...

    async def discover(self, conn: ConnectionSpec) -> DiscoveryGraph:
        """Discovers entities, schemas, tables, and relationships."""
        ...

    async def execute(self, conn: ConnectionSpec, op: Operation) -> OperationResult:
        """Executes an authorized connector operation."""
        ...

    def operations(self) -> List[OperationSpec]:
        """Enumerates operations supported by this connector."""
        ...
