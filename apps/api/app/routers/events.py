"""
FlowMesh Events Router

Provides visibility into the NATS JetStream event stream.
"""

from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from app.dependencies import CurrentAuth
from flowmesh_events.event_bus import event_bus
from app.pagination import PaginationParams, paginate_items

router = APIRouter(prefix="/api/v1/events", tags=["Events"])


class EventLogItem(BaseModel):
    id: str
    type: str
    source: str
    status: str
    timestamp: str
    payload_ref: str
    agent_id: Optional[str] = None


_DEFAULT_EVENTS: List[EventLogItem] = [
    EventLogItem(id="evt_98231", type="sap.order.created", source="SAP ERP", status="PROCESSED", timestamp="2026-09-19T22:31:02Z", payload_ref="ref://blob/98231", agent_id="agent-prod-01"),
    EventLogItem(id="evt_98232", type="customer.updated", source="PostgreSQL", status="PROCESSED", timestamp="2026-09-19T22:30:14Z", payload_ref="ref://blob/98232", agent_id="agent-prod-01"),
    EventLogItem(id="evt_98233", type="sap.order.created", source="SAP ERP", status="FAILED", timestamp="2026-09-19T22:21:00Z", payload_ref="ref://blob/98233", agent_id="agent-prod-01"),
    EventLogItem(id="evt_98234", type="inventory.updated", source="Warehouse API", status="PROCESSED", timestamp="2026-09-19T22:15:30Z", payload_ref="ref://blob/98234", agent_id="agent-wh-01"),
    EventLogItem(id="evt_98235", type="order.shipped", source="Logistics Gateway", status="PROCESSED", timestamp="2026-09-19T22:10:00Z", payload_ref="ref://blob/98235", agent_id=None),
]


@router.get("", response_model=List[EventLogItem])
async def list_events(
    auth: CurrentAuth,
    pagination: Annotated[PaginationParams, Depends()],
    response: Response,
) -> List[EventLogItem]:
    """List event stream processed through NATS JetStream router."""
    bus_events = event_bus.list_events(auth.tenant_id)
    mapped = [
        EventLogItem(
            id=e.id,
            type=e.type,
            source=e.source,
            status=e.status,
            timestamp=e.timestamp,
            payload_ref=f"ref://blob/{e.id}",
            agent_id="agent-prod-01" if "agent" in e.source else None,
        )
        for e in bus_events
    ]
    from app.config import settings
    all_events = mapped
    if settings.environment in ("development", "test") and not mapped:
        all_events = _DEFAULT_EVENTS
    total = len(all_events)
    paginated = all_events[pagination.offset : pagination.offset + pagination.limit]
    return paginate_items(paginated, total=total, params=pagination, response=response)
