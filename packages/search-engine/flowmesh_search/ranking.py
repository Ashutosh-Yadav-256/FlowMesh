from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

ATTRIBUTE_WEIGHTS: Dict[str, float] = {
    "id": 100.0,
    "title": 85.0,
    "tags": 65.0,
    "description": 45.0,
    "payload": 25.0,
}


@dataclass
class MatchSignal:
    query_term: str
    matched_term: str
    attribute: str
    typo_count: int
    is_prefix: bool
    position: int


@dataclass
class CandidateRankScore:
    doc_id: str
    matched_words: int = 0
    total_typos: int = 0
    min_proximity: int = 9999
    max_attribute_weight: float = 0.0
    exactness_score: float = 0.0
    recency_bonus: float = 0.0
    final_score: float = 0.0
    signals: List[MatchSignal] = field(default_factory=list)


class MeilisearchRankingEngine:
    """
    Implements Meilisearch's deterministic multi-criteria bucket sort & scoring:
    1. Words (coverage)
    2. Typo count (minimal edit distance)
    3. Proximity (inter-term distance)
    4. Attribute Rank (field hierarchy)
    5. Exactness (exact vs prefix/typo)
    6. Recency (temporal decay)
    """

    def compute_candidate_score(
        self,
        doc_id: str,
        total_query_terms: int,
        signals: List[MatchSignal],
        created_at: Optional[datetime] = None,
    ) -> CandidateRankScore:
        score = CandidateRankScore(doc_id=doc_id, signals=signals)
        if not signals:
            return score

        unique_matched_query_terms = len({s.query_term for s in signals})
        score.matched_words = unique_matched_query_terms
        words_ratio = unique_matched_query_terms / max(1, total_query_terms)

        term_min_typos: Dict[str, int] = {}
        for s in signals:
            if s.query_term not in term_min_typos or s.typo_count < term_min_typos[s.query_term]:
                term_min_typos[s.query_term] = s.typo_count
        total_typos = sum(term_min_typos.values())
        score.total_typos = total_typos
        typo_multiplier = max(0.2, 1.0 - (total_typos * 0.25))

        positions_by_attr: Dict[str, List[int]] = {}
        for s in signals:
            positions_by_attr.setdefault(s.attribute, []).append(s.position)

        min_prox = 9999
        for attr, pos_list in positions_by_attr.items():
            if len(pos_list) > 1:
                sorted_pos = sorted(pos_list)
                for i in range(len(sorted_pos) - 1):
                    dist = sorted_pos[i + 1] - sorted_pos[i]
                    if dist < min_prox:
                        min_prox = dist
            elif len(signals) == 1:
                min_prox = 1

        score.min_proximity = min_prox
        proximity_bonus = 1.0 / max(1, min_prox)

        max_attr_weight = max((ATTRIBUTE_WEIGHTS.get(s.attribute, 20.0) for s in signals), default=20.0)
        score.max_attribute_weight = max_attr_weight

        exact_matches = sum(1 for s in signals if s.typo_count == 0 and not s.is_prefix)
        score.exactness_score = exact_matches / max(1, len(signals))

        recency = 0.0
        if created_at:
            now = datetime.now(timezone.utc)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            delta_days = max(0.0, (now - created_at).total_seconds() / 86400.0)
            recency = math.exp(-delta_days / 14.0) * 10.0
        score.recency_bonus = recency

        composite = (
            (words_ratio * 1000.0)
            + (max_attr_weight * 5.0)
            + (score.exactness_score * 50.0)
            + (proximity_bonus * 20.0)
            + recency
        ) * typo_multiplier

        score.final_score = round(composite, 3)
        return score
