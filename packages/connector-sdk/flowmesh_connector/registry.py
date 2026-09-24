"""
FlowMesh Connector Registry
Provides a centralized factory registry for looking up and registering connectors
conforming to the frozen Connector Protocol.
"""

from typing import Dict, Optional, List, Type
from flowmesh_connector.protocol import Connector


class ConnectorRegistry:
    """Registry maintaining available connector implementations."""

    def __init__(self) -> None:
        self._connectors: Dict[str, Connector] = {}
        self._defaults_loaded: bool = False

    def _ensure_defaults(self) -> None:
        """Lazily registers built-in connectors to prevent circular module initialization."""
        if self._defaults_loaded:
            return
        self._defaults_loaded = True

        try:
            from connectors.postgres.connector import PostgresConnector
            self.register("postgres", PostgresConnector())
        except Exception:
            pass

        try:
            from connectors.rest.connector import RestConnector
            self.register("rest", RestConnector())
        except Exception:
            pass

        try:
            from connectors.stripe.connector import StripeConnector
            self.register("stripe", StripeConnector())
        except Exception:
            pass

        try:
            from connectors.servicenow.connector import ServiceNowConnector
            self.register("servicenow", ServiceNowConnector())
        except Exception:
            pass

        try:
            from connectors.active_directory.connector import ActiveDirectoryConnector
            self.register("active_directory", ActiveDirectoryConnector())
        except Exception:
            pass

        try:
            from connectors.windows_admin.connector import WindowsAdminConnector
            self.register("windows_admin", WindowsAdminConnector())
        except Exception:
            pass

        try:
            from connectors.ssh.connector import SshParamikoConnector
            self.register("ssh", SshParamikoConnector())
        except Exception:
            pass

        try:
            from connectors.ansible.connector import AnsibleConnector
            self.register("ansible", AnsibleConnector())
        except Exception:
            pass

        try:
            from connectors.azure_automation.connector import AzureAutomationConnector
            self.register("azure_automation", AzureAutomationConnector())
        except Exception:
            pass

        try:
            from connectors.power_platform.connector import PowerPlatformConnector
            self.register("power_platform", PowerPlatformConnector())
        except Exception:
            pass

    def register(self, conn_type: str, connector: Connector) -> None:
        """Registers a connector implementation for a specific connection type."""
        self._connectors[conn_type.lower()] = connector

    def get(self, conn_type: str) -> Optional[Connector]:
        """Looks up a connector by type. Falls back to rest/postgres or returns None."""
        self._ensure_defaults()
        return self._connectors.get(conn_type.lower())

    def list_types(self) -> List[str]:
        """Returns all registered connector types."""
        self._ensure_defaults()
        return list(self._connectors.keys())


registry = ConnectorRegistry()


def get_connector(conn_type: str) -> Optional[Connector]:
    """Convenience helper to retrieve a registered connector."""
    return registry.get(conn_type)


def register_connector(conn_type: str, connector: Connector) -> None:
    """Convenience helper to register a connector."""
    registry.register(conn_type, connector)
