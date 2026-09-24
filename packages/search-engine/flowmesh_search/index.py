from __future__ import annotations

import bisect
from typing import Dict, List, Optional, Set, Tuple
from flowmesh_search.models import SearchDocument
from flowmesh_search.ranking import MatchSignal, MeilisearchRankingEngine
from flowmesh_search.tokenizer import CodeAwareTokenizer
from flowmesh_search.typo import match_with_typo


class InvertedIndex:
    """
    High-performance in-memory Inverted Index supporting:
    - Fast positional postings lookup
    - Prefix searching via sorted vocabulary bisect
    - Meilisearch-compliant typo tolerance
    - Deterministic multi-criteria scoring
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.documents: Dict[str, SearchDocument] = {}

        self.postings: Dict[str, Dict[str, List[Tuple[str, int]]]] = {}
        self.sorted_terms: List[str] = []
        self.tokenizer = CodeAwareTokenizer()
        self.ranker = MeilisearchRankingEngine()

    def add_document(self, doc: SearchDocument) -> None:
        """Indexes a document across all searchable attributes."""
        self.documents[doc.id] = doc

        fields = [
            ("id", doc.id),
            ("title", doc.title),
            ("tags", " ".join(doc.tags)),
            ("description", doc.description or ""),
            ("status", doc.status or ""),
        ]

        for attr_name, attr_val in fields:
            if not attr_val:
                continue
            token_positions = self.tokenizer.tokenize_with_positions(attr_val)
            for token, pos in token_positions:
                if token not in self.postings:
                    self.postings[token] = {}
                    bisect.insort(self.sorted_terms, token)
                if doc.id not in self.postings[token]:
                    self.postings[token][doc.id] = []
                self.postings[token][doc.id].append((attr_name, pos))

    def remove_document(self, doc_id: str) -> None:
        """Removes a document from the inverted index."""
        if doc_id not in self.documents:
            return

        del self.documents[doc_id]

        empty_terms = []
        for term, doc_map in self.postings.items():
            if doc_id in doc_map:
                del doc_map[doc_id]
                if not doc_map:
                    empty_terms.append(term)

        for empty_term in empty_terms:
            del self.postings[empty_term]
            idx = bisect.bisect_left(self.sorted_terms, empty_term)
            if idx < len(self.sorted_terms) and self.sorted_terms[idx] == empty_term:
                del self.sorted_terms[idx]

    def clear(self) -> None:
        """Empties the index completely."""
        self.documents.clear()
        self.postings.clear()
        self.sorted_terms.clear()

    def search_lexical(
        self,
        query: str,
        entity_types: Optional[Set[str]] = None,
        max_candidates: int = 200,
    ) -> List[Tuple[str, float]]:
        """
        Executes lexical inverted search with prefix matching and typo tolerance.
        Returns ranked list of (doc_id, score).
        """
        query_terms = self.tokenizer.tokenize(query)
        if not query_terms:

            docs = list(self.documents.values())
            if entity_types:
                docs = [d for d in docs if d.entity_type in entity_types]
            return [(d.id, 1.0) for d in docs[:max_candidates]]

        candidate_signals: Dict[str, List[MatchSignal]] = {}

        total_terms = len(query_terms)

        for term_idx, q_term in enumerate(query_terms):
            is_last_term = (term_idx == total_terms - 1)
            matching_indexed_terms: List[Tuple[str, int, bool]] = []

            if q_term in self.postings:
                matching_indexed_terms.append((q_term, 0, False))

            if is_last_term and len(q_term) >= 2:

                start_idx = bisect.bisect_left(self.sorted_terms, q_term)
                for i in range(start_idx, len(self.sorted_terms)):
                    cand = self.sorted_terms[i]
                    if cand.startswith(q_term):
                        if cand != q_term:
                            matching_indexed_terms.append((cand, 0, True))
                    else:
                        break

            if len(matching_indexed_terms) < 3 and len(q_term) >= 4:
                for cand in self.sorted_terms:
                    matched, typos, is_p = match_with_typo(q_term, cand, is_prefix=is_last_term)
                    if matched and (cand, typos, is_p) not in matching_indexed_terms:
                        matching_indexed_terms.append((cand, typos, is_p))

            for indexed_term, typos, is_prefix in matching_indexed_terms:
                doc_map = self.postings.get(indexed_term, {})
                for doc_id, occurrences in doc_map.items():

                    doc = self.documents.get(doc_id)
                    if not doc:
                        continue
                    if entity_types and doc.entity_type not in entity_types:
                        continue

                    for attr, pos in occurrences:
                        signal = MatchSignal(
                            query_term=q_term,
                            matched_term=indexed_term,
                            attribute=attr,
                            typo_count=typos,
                            is_prefix=is_prefix,
                            position=pos,
                        )
                        candidate_signals.setdefault(doc_id, []).append(signal)

        scored_candidates: List[Tuple[str, float]] = []
        for doc_id, signals in candidate_signals.items():
            doc = self.documents[doc_id]
            rank_score = self.ranker.compute_candidate_score(
                doc_id=doc_id,
                total_query_terms=total_terms,
                signals=signals,
                created_at=doc.created_at,
            )
            scored_candidates.append((doc_id, rank_score.final_score))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates[:max_candidates]
