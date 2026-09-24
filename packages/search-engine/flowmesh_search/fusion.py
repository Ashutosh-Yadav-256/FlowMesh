from __future__ import annotations

from typing import Dict, List, Tuple


class ReciprocalRankFusion:
    """
    Implements Reciprocal Rank Fusion (RRF) to merge heterogeneous score distributions
    from Lexical (BM25/Prefix/Typo) and Semantic (Two-Tower Vector) retrieval streams.
    """

    def __init__(self, k_constant: int = 60):
        self.k = k_constant

    def fuse(
        self,
        lexical_ranked: List[Tuple[str, float]],
        semantic_ranked: List[Tuple[str, float]],
        weight_lexical: float = 1.0,
        weight_semantic: float = 0.8,
    ) -> List[Tuple[str, float]]:
        """
        Merges ranked streams by summing weighted reciprocal ranks:
        RRF(d) = (w_lex / (k + rank_lex)) + (w_sem / (k + rank_sem))
        """
        rrf_scores: Dict[str, float] = {}

        for rank, (doc_id, _) in enumerate(lexical_ranked, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (weight_lexical / (self.k + rank))

        for rank, (doc_id, _) in enumerate(semantic_ranked, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (weight_semantic / (self.k + rank))

        fused = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
        return fused
