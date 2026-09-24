"""
FlowMesh Incident Manager Service
Automated incident detection, timeline correlation, and resolution tracking.
"""

import uuid
import random
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import IncidentRecord
from app.repositories.tenant_scoped import IncidentRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IncidentManager:
    """Manages operational incidents automatically triggered by the Data Plane."""

    def __init__(self, db: AsyncSession, tenant_id: str) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.repo = IncidentRepository(db, tenant_id)

    async def report_circuit_breaker_tripped(
        self,
        connection_id: str,
        workflow_id: str,
        root_cause: str,
        severity: str = "HIGH",
    ) -> IncidentRecord:
        """
        Creates or updates an active incident when a connection's circuit breaker opens.
        """
        now = utc_now()
        now_str = now.strftime("%H:%M:%S")

        existing = await self.repo.get_open_for_connection(connection_id)
        if existing:

            wfs = list(existing.affected_workflows or [])
            if workflow_id not in wfs:
                wfs.append(workflow_id)
                existing.affected_workflows = wfs
            
            await self.repo.add_timeline_event(
                existing.id,
                f"Circuit breaker OPEN for connection '{connection_id}'. Workflow '{workflow_id}' failed fast."
            )
            return existing

        incident_id = f"INC-{random.randint(1000, 9999)}"
        incident = IncidentRecord(
            id=incident_id,
            tenant_id=self.tenant_id,
            title=f"Degraded Connection: {connection_id}",
            severity=severity,
            status="OPEN",
            connection_id=connection_id,
            affected_workflows=[workflow_id],
            root_cause=root_cause,
            timeline=[
                {
                    "timestamp": now_str,
                    "message": f"Circuit breaker OPENED for connection '{connection_id}': {root_cause}",
                }
            ],
            opened_at=now,
        )
        return await self.repo.create(incident)

    async def report_circuit_breaker_recovered(self, connection_id: str) -> Optional[IncidentRecord]:
        """
        Marks an incident as recovered when canary traffic succeeds and circuit closes.
        """
        existing = await self.repo.get_open_for_connection(connection_id)
        if not existing:
            return None

        now = utc_now()
        now_str = now.strftime("%H:%M:%S")

        await self.repo.add_timeline_event(
            existing.id,
            f"Canary probe succeeded. Circuit breaker CLOSED for connection '{connection_id}'. System recovered."
        )
        await self.repo.update_status(existing.id, status="RECOVERED", resolved=True)
        return await self.repo.get_by_id(existing.id)

    async def add_timeline_event(self, incident_id: str, message: str) -> None:
        """Adds a manual or automated timeline log entry."""
        await self.repo.add_timeline_event(incident_id, message)

    async def resolve_incident(self, incident_id: str) -> Optional[IncidentRecord]:
        """Manually resolves an incident."""
        await self.repo.update_status(incident_id, status="RESOLVED", resolved=True)
        return await self.repo.get_by_id(incident_id)
