from __future__ import annotations

import math
from typing import Dict, List, Tuple
from flowmesh_search.models import SearchDocument


class SemanticDenseTower:
    """
    Two-Tower Semantic Retrieval component inspired by the Uber Eats Search Pipeline.
    Encodes query text and document fields into high-dimensional sparse/dense vector space
    using character 3-gram and token embeddings, computing cosine similarity for semantic matching.
    """

    def __init__(self, vector_dim: int = 512):
        self.vector_dim = vector_dim
        self._doc_vectors: Dict[str, Dict[int, float]] = {}

    def _text_to_vector(self, text: str) -> Dict[int, float]:
        """Hashes character n-grams and tokens into normalized vector space."""
        if not text:
            return {}

        clean = text.lower().strip()
        vec: Dict[int, float] = {}

        words = clean.split()
        for w in words:
            h = hash(w) % self.vector_dim
            vec[h] = vec.get(h, 0.0) + 1.5

        if len(clean) >= 3:
            for i in range(len(clean) - 2):
                ngram = clean[i:i + 3]
                h = hash(ngram) % self.vector_dim
                vec[h] = vec.get(h, 0.0) + 0.5

        magnitude = math.sqrt(sum(v * v for v in vec.values()))
        if magnitude > 0:
            for k in vec:
                vec[k] /= magnitude

        return vec

    def index_document(self, doc: SearchDocument) -> None:
        """Encodes document attributes (title, description, tags, payload) into vector space."""
        combined_text = f"{doc.title} {doc.description} {' '.join(doc.tags)} {doc.entity_type}"
        self._doc_vectors[doc.id] = self._text_to_vector(combined_text)

    def remove_document(self, doc_id: str) -> None:
        self._doc_vectors.pop(doc_id, None)

    def clear(self) -> None:
        self._doc_vectors.clear()

    def search_semantic(
        self,
        query: str,
        candidate_ids: List[str],
        top_k: int = 50,
    ) -> List[Tuple[str, float]]:
        """
        Calculates cosine similarity between query vector and candidate document vectors.
        Returns list of (doc_id, similarity_score).
        """
        query_vec = self._text_to_vector(query)
        if not query_vec:
            return []

        scored: List[Tuple[str, float]] = []

        for doc_id in candidate_ids:
            doc_vec = self._doc_vectors.get(doc_id)
            if not doc_vec:
                continue

            dot = 0.0
            for k, qv in query_vec.items():
                if k in doc_vec:
                    dot += qv * doc_vec[k]

            if dot > 0.08:
                scored.append((doc_id, round(dot, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
