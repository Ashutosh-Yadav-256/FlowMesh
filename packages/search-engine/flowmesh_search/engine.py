from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Set
from flowmesh_search.fusion import ReciprocalRankFusion
from flowmesh_search.index import InvertedIndex
from flowmesh_search.models import HighlightSnippet, SearchDocument, SearchResponse, SearchResultItem
from flowmesh_search.semantic import SemanticDenseTower
from flowmesh_search.tokenizer import CodeAwareTokenizer


class FlowMeshSearchEngine:
    """
    Intelligent Search Engine for FlowMesh Platform.
    Synthesizes Meilisearch's instant search-as-you-type, typo tolerance, and ranking rules
    with Uber Eats' two-tower hybrid retrieval and Reciprocal Rank Fusion (RRF).
    """

    def __init__(self):
        self._tenant_indexes: Dict[str, InvertedIndex] = {}
        self._tenant_semantics: Dict[str, SemanticDenseTower] = {}
        self.fusion = ReciprocalRankFusion(k_constant=60)
        self.tokenizer = CodeAwareTokenizer()

    def _get_or_create_index(self, tenant_id: str, auto_load: bool = True) -> InvertedIndex:
        if tenant_id not in self._tenant_indexes:
            self._tenant_indexes[tenant_id] = InvertedIndex(tenant_id)
            if auto_load:
                self.load_from_disk(tenant_id)
        return self._tenant_indexes[tenant_id]

    def _get_or_create_semantic(self, tenant_id: str) -> SemanticDenseTower:
        if tenant_id not in self._tenant_semantics:
            self._tenant_semantics[tenant_id] = SemanticDenseTower()
        return self._tenant_semantics[tenant_id]

    def persist_to_disk(self, tenant_id: str, dir_path: Optional[str] = None) -> bool:
        """Persists a tenant's documents to disk as JSON."""
        try:
            from app.config import settings
            base_dir = dir_path or getattr(settings, "search_index_path", "./data/search_indexes")
            enabled = getattr(settings, "search_persist_enabled", True)
        except Exception:
            base_dir = dir_path or "./data/search_indexes"
            enabled = True

        if not enabled:
            return False

        idx = self._tenant_indexes.get(tenant_id)
        if not idx:
            return False

        os.makedirs(base_dir, exist_ok=True)
        file_path = os.path.join(base_dir, f"{tenant_id}.json")
        docs_data = []
        for doc in idx.documents.values():
            docs_data.append({
                "id": doc.id,
                "tenant_id": doc.tenant_id,
                "entity_type": doc.entity_type,
                "title": doc.title,
                "description": doc.description,
                "tags": doc.tags,
                "status": doc.status,
                "url": doc.url,
                "payload": doc.payload,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            })
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(docs_data, f, indent=2)
        return True

    def load_from_disk(self, tenant_id: str, dir_path: Optional[str] = None) -> bool:
        """Loads a tenant's documents from disk and populates lexical + semantic indexes."""
        try:
            from app.config import settings
            base_dir = dir_path or getattr(settings, "search_index_path", "./data/search_indexes")
            enabled = getattr(settings, "search_persist_enabled", True)
        except Exception:
            base_dir = dir_path or "./data/search_indexes"
            enabled = True

        if not enabled:
            return False

        file_path = os.path.join(base_dir, f"{tenant_id}.json")
        if not os.path.exists(file_path):
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                docs_data = json.load(f)

            idx = self._get_or_create_index(tenant_id, auto_load=False)
            sem = self._get_or_create_semantic(tenant_id)

            for item in docs_data:
                created_at = datetime.fromisoformat(item["created_at"]) if item.get("created_at") else None
                updated_at = datetime.fromisoformat(item["updated_at"]) if item.get("updated_at") else None
                doc = SearchDocument(
                    id=item["id"],
                    tenant_id=item["tenant_id"],
                    entity_type=item["entity_type"],
                    title=item["title"],
                    description=item.get("description", ""),
                    tags=item.get("tags", []),
                    status=item.get("status"),
                    url=item.get("url"),
                    payload=item.get("payload", {}),
                    created_at=created_at,
                    updated_at=updated_at,
                )
                idx.add_document(doc)
                sem.index_document(doc)
            return True
        except Exception:
            return False

    def index_document(self, tenant_id: str, doc: SearchDocument, persist: bool = True) -> None:
        """Indexes a document in both lexical and semantic towers under tenant isolation."""
        idx = self._get_or_create_index(tenant_id)
        idx.add_document(doc)

        sem = self._get_or_create_semantic(tenant_id)
        sem.index_document(doc)

        if persist:
            self.persist_to_disk(tenant_id)

    def index_documents(self, tenant_id: str, docs: List[SearchDocument], persist: bool = True) -> None:
        for doc in docs:
            self.index_document(tenant_id, doc, persist=False)
        if persist:
            self.persist_to_disk(tenant_id)

    def delete_document(self, tenant_id: str, doc_id: str, persist: bool = True) -> None:
        if tenant_id in self._tenant_indexes:
            self._tenant_indexes[tenant_id].remove_document(doc_id)
        if tenant_id in self._tenant_semantics:
            self._tenant_semantics[tenant_id].remove_document(doc_id)
        if persist:
            self.persist_to_disk(tenant_id)

    def clear_tenant(self, tenant_id: str) -> None:
        """Resets all search indexes for the specified tenant (Clean Slate)."""
        if tenant_id in self._tenant_indexes:
            self._tenant_indexes[tenant_id].clear()
        if tenant_id in self._tenant_semantics:
            self._tenant_semantics[tenant_id].clear()

        try:
            from app.config import settings
            base_dir = getattr(settings, "search_index_path", "./data/search_indexes")
        except Exception:
            base_dir = "./data/search_indexes"

        file_path = os.path.join(base_dir, f"{tenant_id}.json")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    def get_document_count(self, tenant_id: str) -> int:
        if tenant_id not in self._tenant_indexes:

            self.load_from_disk(tenant_id)
            if tenant_id not in self._tenant_indexes:
                return 0
        return len(self._tenant_indexes[tenant_id].documents)

    def _generate_highlights(
        self,
        doc: SearchDocument,
        query_terms: List[str],
    ) -> List[HighlightSnippet]:
        """Generates contextual highlighted snippets with <mark> tags."""
        highlights: List[HighlightSnippet] = []
        if not query_terms:
            return highlights

        fields = [
            ("title", doc.title),
            ("description", doc.description or ""),
            ("id", doc.id),
        ]

        pattern = re.compile(
            r"\b(" + "|".join(re.escape(term) for term in query_terms if len(term) >= 2) + r")\b",
            re.IGNORECASE,
        )

        for field_name, field_val in fields:
            if not field_val:
                continue

            matches = list(pattern.finditer(field_val))
            if matches:

                highlighted = pattern.sub(r"<mark>\1</mark>", field_val)

                snippet = highlighted if len(highlighted) <= 140 else highlighted[:140] + "..."
                matched_words = list({m.group(0).lower() for m in matches})
                highlights.append(
                    HighlightSnippet(
                        field=field_name,
                        snippet=snippet,
                        matched_terms=matched_words,
                    )
                )

        return highlights

    def search(
        self,
        tenant_id: str,
        query: str,
        entity_types: Optional[Set[str]] = None,
        limit: int = 15,
    ) -> SearchResponse:
        """
        Executes hybrid two-tower retrieval with Reciprocal Rank Fusion (RRF)
        and selective hydration for the specified tenant.
        """
        start_time = time.perf_counter()
        clean_query = query.strip()

        if tenant_id not in self._tenant_indexes or not self._tenant_indexes[tenant_id].documents:
            took_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return SearchResponse(
                query=clean_query,
                total_hits=0,
                took_ms=took_ms,
                results=[],
                facet_distribution={},
            )

        index = self._tenant_indexes[tenant_id]
        semantic = self._tenant_semantics.get(tenant_id)

        lexical_ranked = index.search_lexical(
            query=clean_query,
            entity_types=entity_types,
            max_candidates=100,
        )

        semantic_ranked: List[Tuple[str, float]] = []
        if semantic and clean_query:

            candidate_ids = [doc_id for doc_id, _ in lexical_ranked]
            if len(candidate_ids) < 30:

                all_ids = list(index.documents.keys())
                if entity_types:
                    all_ids = [d_id for d_id in all_ids if index.documents[d_id].entity_type in entity_types]
                candidate_ids = list(dict.fromkeys(candidate_ids + all_ids[:50]))

            semantic_ranked = semantic.search_semantic(
                query=clean_query,
                candidate_ids=candidate_ids,
                top_k=50,
            )

        if clean_query and semantic_ranked:
            fused_ranked = self.fusion.fuse(
                lexical_ranked=lexical_ranked,
                semantic_ranked=semantic_ranked,
                weight_lexical=1.0,
                weight_semantic=0.8,
            )
        else:
            fused_ranked = lexical_ranked

        query_terms = self.tokenizer.tokenize(clean_query)
        facet_counts: Dict[str, int] = {}
        hydrated_results: List[SearchResultItem] = []

        for doc_id, score in fused_ranked[:limit]:
            doc = index.documents.get(doc_id)
            if not doc:
                continue

            facet_counts[doc.entity_type] = facet_counts.get(doc.entity_type, 0) + 1
            highlights = self._generate_highlights(doc, query_terms)

            item = SearchResultItem(
                id=doc.id,
                tenant_id=doc.tenant_id,
                entity_type=doc.entity_type,
                title=doc.title,
                description=doc.description,
                status=doc.status,
                url=doc.url or f"/{doc.entity_type}s/{doc.id}",
                score=round(score, 4),
                highlights=highlights,
                metadata=doc.payload,
            )
            hydrated_results.append(item)

        took_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return SearchResponse(
            query=clean_query,
            total_hits=len(fused_ranked),
            took_ms=took_ms,
            results=hydrated_results,
            facet_distribution=facet_counts,
        )


_search_engine_instance: Optional[FlowMeshSearchEngine] = None


def get_search_engine() -> FlowMeshSearchEngine:
    global _search_engine_instance
    if _search_engine_instance is None:
        _search_engine_instance = FlowMeshSearchEngine()
    return _search_engine_instance
