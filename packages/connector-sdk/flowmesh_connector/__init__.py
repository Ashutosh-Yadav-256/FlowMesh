"""
FlowMesh Connector SDK
"""

from flowmesh_connector.protocol import (
    Connector,
    ConnectionSpec,
    DiscoveryGraph,
    TableInfo,
    ColumnInfo,
    OperationSpec,
    Operation,
    OperationResult,
    TestResult,
    TestStepResult,
)
from flowmesh_connector.base import BaseConnector
from connectors.stripe.connector import StripeConnector
from flowmesh_connector.registry import (
    ConnectorRegistry,
    registry,
    get_connector,
    register_connector,
)

__all__ = [
    "Connector",
    "ConnectionSpec",
    "DiscoveryGraph",
    "TableInfo",
    "ColumnInfo",
    "OperationSpec",
    "Operation",
    "OperationResult",
    "TestResult",
    "TestStepResult",
    "BaseConnector",
    "StripeConnector",
    "ConnectorRegistry",
    "registry",
    "get_connector",
    "register_connector",
]
