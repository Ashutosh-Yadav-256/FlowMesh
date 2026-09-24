import pytest
from datetime import datetime, timezone
from flowmesh_search.engine import FlowMeshSearchEngine
from flowmesh_search.models import SearchDocument
from flowmesh_search.tokenizer import CodeAwareTokenizer
from flowmesh_search.typo import damerau_levenshtein_distance, max_allowed_typos


def test_tokenizer_code_and_natural_language():
    tokenizer = CodeAwareTokenizer()

    tokens = tokenizer.tokenize("RUN-92831")
    assert "run" in tokens
    assert "92831" in tokens
    assert "run-92831" in tokens

    tokens = tokenizer.tokenize("order_processing_pipeline")
    assert "order" in tokens
    assert "processing" in tokens
    assert "pipeline" in tokens

    tokens = tokenizer.tokenize("validateInventory")
    assert "validate" in tokens
    assert "inventory" in tokens


def test_typo_tolerance_rules():
    assert max_allowed_typos(3) == 0
    assert max_allowed_typos(4) == 0
    assert max_allowed_typos(5) == 1
    assert max_allowed_typos(8) == 1
    assert max_allowed_typos(9) == 2

    assert damerau_levenshtein_distance("posgtres", "postgres") == 1
    assert damerau_levenshtein_distance("stipe", "stripe") == 1
    assert damerau_levenshtein_distance("warehouse", "waerhouse") == 1


def test_search_engine_prefix_and_typo():
    engine = FlowMeshSearchEngine()
    tenant_id = "tenant_test"

    doc1 = SearchDocument(
        id="conn_pg_01",
        tenant_id=tenant_id,
        entity_type="connection",
        title="Orders DB (Postgres 16)",
        description="Production PostgreSQL read-write replica",
        tags=["database", "sql"],
        status="HEALTHY",
    )
    doc2 = SearchDocument(
        id="conn_stripe_01",
        tenant_id=tenant_id,
        entity_type="connection",
        title="Stripe Billing Gateway",
        description="Payment processor for customer checkouts",
        tags=["payment", "billing"],
        status="HEALTHY",
    )
    doc3 = SearchDocument(
        id="RUN-92831",
        tenant_id=tenant_id,
        entity_type="run",
        title="Order Processing Execution #92831",
        description="Completed in 412ms without errors",
        tags=["order", "webhook"],
        status="COMPLETED",
        created_at=datetime.now(timezone.utc),
    )

    engine.index_documents(tenant_id, [doc1, doc2, doc3])

    res = engine.search(tenant_id, "postg")
    assert res.total_hits >= 1
    assert res.results[0].id == "conn_pg_01"

    res_code = engine.search(tenant_id, "RUN-92831")
    assert res_code.total_hits >= 1
    assert res_code.results[0].id == "RUN-92831"

    res_typo = engine.search(tenant_id, "stipe")
    assert res_typo.total_hits >= 1
    assert res_typo.results[0].id == "conn_stripe_01"


def test_multi_tenant_isolation_and_clean_slate():
    engine = FlowMeshSearchEngine()

    doc_a = SearchDocument(
        id="wf_01",
        tenant_id="tenant_a",
        entity_type="workflow",
        title="Order Ingestion Workflow",
    )
    engine.index_document("tenant_a", doc_a)

    res_b = engine.search("tenant_b", "order")
    assert res_b.total_hits == 0
    assert len(res_b.results) == 0

    res_a = engine.search("tenant_a", "order")
    assert res_a.total_hits == 1
    assert res_a.results[0].id == "wf_01"


def test_semantic_hybrid_retrieval():
    engine = FlowMeshSearchEngine()
    tenant_id = "tenant_hybrid"

    doc_incident = SearchDocument(
        id="INC-1932",
        tenant_id=tenant_id,
        entity_type="incident",
        title="Warehouse API Gateway Timeout",
        description="HTTP 503 upstream gateway timeout on inventory check step",
        tags=["circuit_breaker", "timeout"],
        status="RECOVERED",
    )
    engine.index_document(tenant_id, doc_incident)

    res = engine.search(tenant_id, "inventory gateway error")
    assert res.total_hits >= 1
    assert res.results[0].id == "INC-1932"
    assert len(res.results[0].highlights) > 0
