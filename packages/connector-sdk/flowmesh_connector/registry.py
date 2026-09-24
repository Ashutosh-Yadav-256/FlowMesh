"""
FlowMesh Connector Registry

Provides a centralized factory registry for looking up and registering connectors
conforming to the frozen Connector Protocol.
"""

from typing import Dict, Optional, List, Type
from flowmesh_connector.protocol import Connector
from connectors.postgres.connector import PostgresConnector
from connectors.rest.connector import RestConnector
from connectors.stripe.connector import StripeConnector


class ConnectorRegistry:
    """Registry maintaining available connector implementations."""

    def __init__(self) -> None:
        self._connectors: Dict[str, Connector] = {}

        self.register("postgres", PostgresConnector())
        self.register("rest", RestConnector())
        self.register("stripe", StripeConnector())

    def register(self, conn_type: str, connector: Connector) -> None:
        """Registers a connector implementation for a specific connection type."""
        self._connectors[conn_type.lower()] = connector

    def get(self, conn_type: str) -> Optional[Connector]:
        """Looks up a connector by type. Falls back to rest/postgres or returns None."""
        return self._connectors.get(conn_type.lower())

    def list_types(self) -> List[str]:
        """Returns all registered connector types."""
        return list(self._connectors.keys())


registry = ConnectorRegistry()


def get_connector(conn_type: str) -> Optional[Connector]:
    """Convenience helper to retrieve a registered connector."""
    return registry.get(conn_type)


def register_connector(conn_type: str, connector: Connector) -> None:
    """Convenience helper to register a connector."""
    registry.register(conn_type, connector)
