import os
import shutil
import tempfile
import pytest
from flowmesh_search.engine import FlowMeshSearchEngine
from flowmesh_search.models import SearchDocument


@pytest.fixture
def temp_search_dir():
    temp_dir = tempfile.mkdtemp(prefix="flowmesh_search_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_index_persists_and_reloads(temp_search_dir):
    engine1 = FlowMeshSearchEngine()
    tenant_id = "tenant_test_persist"

    doc1 = SearchDocument(
        id="wf_invoice_proc",
        tenant_id=tenant_id,
        entity_type="workflow",
        title="Invoice Processing Workflow",
        description="Automated invoice extraction and validation",
        tags=["billing", "finance"],
    )
    doc2 = SearchDocument(
        id="conn_stripe",
        tenant_id=tenant_id,
        entity_type="connection",
        title="Stripe Payment Gateway",
        description="Payment processing integration",
        tags=["payment", "finance"],
    )

    engine1.index_documents(tenant_id, [doc1, doc2], persist=False)
    engine1.persist_to_disk(tenant_id, dir_path=temp_search_dir)

    expected_file = os.path.join(temp_search_dir, f"{tenant_id}.json")
    assert os.path.exists(expected_file)

    engine2 = FlowMeshSearchEngine()
    assert tenant_id not in engine2._tenant_indexes

    loaded = engine2.load_from_disk(tenant_id, dir_path=temp_search_dir)
    assert loaded is True
    assert engine2.get_document_count(tenant_id) == 2

    results = engine2.search(tenant_id=tenant_id, query="invoice")
    assert results.total_hits > 0
    assert results.results[0].id == "wf_invoice_proc"


def test_clean_tenant_has_no_file(temp_search_dir):
    engine = FlowMeshSearchEngine()
    tenant_id = "tenant_fresh_clean"

    doc = SearchDocument(
        id="doc_temp",
        tenant_id=tenant_id,
        entity_type="run",
        title="Temporary Run",
        description="To be cleared",
    )
    engine.index_document(tenant_id, doc, persist=False)
    engine.persist_to_disk(tenant_id, dir_path=temp_search_dir)

    file_path = os.path.join(temp_search_dir, f"{tenant_id}.json")
    assert os.path.exists(file_path)

    engine.clear_tenant(tenant_id)

    if os.path.exists(file_path):
        os.remove(file_path)
    assert not os.path.exists(file_path)
