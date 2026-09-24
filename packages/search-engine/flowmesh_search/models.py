from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SearchDocument:
    id: str
    tenant_id: str
    entity_type: str
    title: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    status: Optional[str] = None
    url: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class HighlightSnippet:
    field: str
    snippet: str
    matched_terms: List[str] = field(default_factory=list)


@dataclass
class SearchResultItem:
    id: str
    tenant_id: str
    entity_type: str
    title: str
    description: str
    status: Optional[str] = None
    url: Optional[str] = None
    score: float = 0.0
    highlights: List[HighlightSnippet] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResponse:
    query: str
    total_hits: int
    took_ms: float
    results: List[SearchResultItem]
    facet_distribution: Dict[str, int] = field(default_factory=dict)
