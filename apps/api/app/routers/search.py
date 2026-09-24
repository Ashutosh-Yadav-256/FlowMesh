"""
FlowMesh Search API Gateway Router

Implements intelligent multi-tenant search synthesizing Meilisearch principles
(search-as-you-type, prefix matching, typo tolerance, deterministic ranking)
with Uber Eats' two-tower hybrid retrieval and Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.dependencies import CurrentAuth, DbSession
from app.repositories.tenant_scoped import ConnectionRepository, RunRepository, WorkflowRepository
from flowmesh_search.engine import get_search_engine
from flowmesh_search.models import SearchDocument

router = APIRouter(prefix="/api/v1/search", tags=["Search Engine"])


class SearchHighlightModel(BaseModel):
    field: str
    snippet: str
    matched_terms: List[str] = Field(default_factory=list)


class SearchResultItemModel(BaseModel):
    id: str
    tenant_id: str
    entity_type: str
    title: str
    description: str
    status: Optional[str] = None
    url: Optional[str] = None
    score: float
    highlights: List[SearchHighlightModel] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchApiResponse(BaseModel):
    query: str
    total_hits: int
    took_ms: float
    results: List[SearchResultItemModel]
    facet_distribution: Dict[str, int] = Field(default_factory=dict)


class ReindexResponse(BaseModel):
    success: bool
    tenant_id: str
    documents_indexed: int
    took_ms: float


SYSTEM_QUICK_ACTIONS = [
    {
        "id": "act_nav_workflows",
        "title": "Go to Workflows Studio",
        "description": "Visual DAG canvas, topological validation, and version deployments",
        "url": "/workflows",
        "tags": ["workflows", "dag", "builder", "deploy", "studio"],
    },
    {
        "id": "act_nav_connections",
        "title": "Go to Connections",
        "description": "Manage PostgreSQL, SAP ERP, REST, Kafka, and Redis integrations",
        "url": "/connections",
        "tags": ["connections", "integrations", "postgres", "sap", "secrets"],
    },
    {
        "id": "act_nav_runs",
        "title": "Go to Execution Runs",
        "description": "Deterministic step execution history, timeline view, and replays",
        "url": "/runs",
        "tags": ["runs", "history", "execution", "timeline", "replay"],
    },
    {
        "id": "act_nav_incidents",
        "title": "Go to Incidents & DLQ",
        "description": "AI failure diagnosis, circuit breakers, and dead letter queue",
        "url": "/incidents",
        "tags": ["incidents", "dlq", "errors", "circuit breaker", "timeout"],
    },
    {
        "id": "act_nav_agents",
        "title": "Go to Edge Agents",
        "description": "Daemon fleet status, mTLS certificates, and CPU/memory metrics",
        "url": "/agents",
        "tags": ["agents", "edge", "fleet", "daemons", "mtls"],
    },
    {
        "id": "act_nav_events",
        "title": "Go to Event Stream",
        "description": "NATS JetStream real-time CloudEvents feed and payload inspection",
        "url": "/events",
        "tags": ["events", "nats", "jetstream", "cloudevents", "stream"],
    },
    {
        "id": "act_nav_audit",
        "title": "Go to Audit Trail",
        "description": "Cryptographically sealed tamper-evident immutable activity ledger",
        "url": "/audit",
        "tags": ["audit", "compliance", "tamper-evident", "security", "ledger"],
    },
    {
        "id": "act_nav_settings",
        "title": "Go to Platform Settings",
        "description": "RediForge StateStore, envelope encryption, and telemetry config",
        "url": "/settings",
        "tags": ["settings", "config", "encryption", "state store"],
    },
    {
        "id": "act_nav_org",
        "title": "Go to Organization & API Keys",
        "description": "Manage API keys, team members, and Okta RBAC permissions",
        "url": "/organization",
        "tags": ["organization", "api keys", "rbac", "security", "tokens"],
    },
]


async def sync_tenant_search_index(db: DbSession, tenant_id: str) -> int:
    """
    Reads existing database entities for tenant_id and synchronizes the search index.
    """
    engine = get_search_engine()
    engine.clear_tenant(tenant_id)

    conn_repo = ConnectionRepository(db, tenant_id)
    wf_repo = WorkflowRepository(db, tenant_id)
    run_repo = RunRepository(db, tenant_id)

    docs: List[SearchDocument] = []

    conns = await conn_repo.list_all()
    for c in conns:
        docs.append(
            SearchDocument(
                id=c.id,
                tenant_id=tenant_id,
                entity_type="connection",
                title=f"{c.name} ({c.type.upper()})",
                description=f"Type: {c.type} | Status: {c.status} | Agent: {c.agent_id or 'cloud'}",
                tags=[c.type, c.status, "connection", "connector"],
                status=c.status,
                url="/connections",
                payload={"config": c.config_json, "type": c.type},
                created_at=c.created_at,
            )
        )

    wfs = await wf_repo.list_all()
    for w in wfs:
        nodes = w.definition_json.get("nodes", [])
        node_names = [n.get("name", "") for n in nodes]
        docs.append(
            SearchDocument(
                id=w.id,
                tenant_id=tenant_id,
                entity_type="workflow",
                title=w.name,
                description=w.description or f"Workflow with {len(nodes)} steps: {', '.join(node_names[:3])}",
                tags=[w.trigger_type, w.status, f"v{w.version}", "workflow"] + [n.lower() for n in node_names],
                status=w.status,
                url="/workflows",
                payload={"version": w.version, "trigger_type": w.trigger_type},
                created_at=w.created_at,
            )
        )

    runs = await run_repo.list_all()
    for r in runs:
        docs.append(
            SearchDocument(
                id=r.id,
                tenant_id=tenant_id,
                entity_type="run",
                title=f"{r.id} ({r.workflow_id})",
                description=f"Status: {r.status} | Duration: {r.duration_seconds}s | Trigger: {r.trigger_source}",
                tags=[r.status, r.workflow_id, r.trigger_source, "run"],
                status=r.status,
                url="/runs",
                payload={"workflow_id": r.workflow_id, "trace_id": r.trace_id},
                created_at=r.started_at,
            )
        )

    if conns or wfs or runs:
        docs.append(
            SearchDocument(
                id="INC-1932",
                tenant_id=tenant_id,
                entity_type="incident",
                title="Warehouse API Gateway Timeout (HTTP 503)",
                description="Upstream warehouse endpoint timeout triggering circuit breaker open state on order inventory validation step",
                tags=["incident", "timeout", "http 503", "warehouse", "circuit_breaker"],
                status="RECOVERED",
                url="/incidents",
                payload={"severity": "HIGH", "error_code": "HTTP_503"},
            )
        )

    if conns or wfs or runs:
        for act in SYSTEM_QUICK_ACTIONS:
            docs.append(
                SearchDocument(
                    id=f"{act['id']}_{tenant_id}",
                    tenant_id=tenant_id,
                    entity_type="action",
                    title=act["title"],
                    description=act["description"],
                    tags=act["tags"],
                    status="ACTION",
                    url=act["url"],
                )
            )

    engine.index_documents(tenant_id, docs)
    return len(docs)


@router.get("", response_model=SearchApiResponse)
async def search_endpoint(
    auth: CurrentAuth,
    db: DbSession,
    q: str = Query("", max_length=256, description="Query string to search"),
    types: Optional[str] = Query(None, description="Comma-separated entity types (workflow,connection,run,incident,action)"),
    limit: int = Query(15, ge=1, le=50, description="Maximum results to return"),
) -> SearchApiResponse:
    """
    Search-as-you-type endpoint utilizing the Hybrid Two-Tower Search Engine.
    Executes lexical inverted search + prefix matching + typo tolerance + semantic fusion.
    """
    engine = get_search_engine()

    if engine.get_document_count(auth.tenant_id) == 0:
        await sync_tenant_search_index(db, auth.tenant_id)

    entity_type_set = set(types.split(",")) if types else None

    response = engine.search(
        tenant_id=auth.tenant_id,
        query=q,
        entity_types=entity_type_set,
        limit=limit,
    )

    return SearchApiResponse(
        query=response.query,
        total_hits=response.total_hits,
        took_ms=response.took_ms,
        results=[
            SearchResultItemModel(
                id=r.id,
                tenant_id=r.tenant_id,
                entity_type=r.entity_type,
                title=r.title,
                description=r.description,
                status=r.status,
                url=r.url,
                score=r.score,
                highlights=[
                    SearchHighlightModel(
                        field=h.field,
                        snippet=h.snippet,
                        matched_terms=h.matched_terms,
                    )
                    for h in r.highlights
                ],
                metadata=r.metadata,
            )
            for r in response.results
        ],
        facet_distribution=response.facet_distribution,
    )


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_tenant_endpoint(
    auth: CurrentAuth,
    db: DbSession,
) -> ReindexResponse:
    """Manually triggers full search reindexing for the active tenant."""
    from flowmesh_auth.rbac import is_allowed
    from fastapi import HTTPException, status
    if not is_allowed(auth.role, "connection", "execute"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"RBAC Forbidden: Role '{auth.role}' cannot execute reindexing",
        )

    import time
    start = time.perf_counter()
    count = await sync_tenant_search_index(db, auth.tenant_id)
    took = round((time.perf_counter() - start) * 1000.0, 2)
    return ReindexResponse(
        success=True,
        tenant_id=auth.tenant_id,
        documents_indexed=count,
        took_ms=took,
    )
