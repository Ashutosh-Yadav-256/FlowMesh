from __future__ import annotations

from functools import lru_cache
from typing import Tuple


def max_allowed_typos(word_len: int) -> int:
    """
    Meilisearch-compatible typo allowance rules:
    - 0-4 chars: 0 typos
    - 5-8 chars: 1 typo
    - 9+ chars: 2 typos
    """
    if word_len < 5:
        return 0
    elif word_len <= 8:
        return 1
    else:
        return 2


@lru_cache(maxsize=16384)
def damerau_levenshtein_distance(s1: str, s2: str) -> int:
    """
    Computes Damerau-Levenshtein distance between s1 and s2
    supporting insertions, deletions, substitutions, and adjacent transpositions.
    """
    len1, len2 = len(s1), len(s2)
    if s1 == s2:
        return 0
    if len1 == 0:
        return len2
    if len2 == 0:
        return len1

    d = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        d[i][0] = i
    for j in range(len2 + 1):
        d[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1,
                d[i][j - 1] + 1,
                d[i - 1][j - 1] + cost
            )

            if i > 1 and j > 1 and s1[i - 1] == s2[j - 2] and s1[i - 2] == s2[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)

    return d[len1][len2]


def match_with_typo(
    query_term: str,
    indexed_term: str,
    is_prefix: bool = False,
    max_typos: int = 2
) -> Tuple[bool, int, bool]:
    """
    Evaluates whether query_term matches indexed_term under Meilisearch rules.
    Returns: (is_match, typo_count, is_prefix_match)
    """
    q_len = len(query_term)
    allowed_typos = min(max_allowed_typos(q_len), max_typos)

    if query_term == indexed_term:
        return True, 0, False

    if is_prefix and len(indexed_term) >= q_len and indexed_term.startswith(query_term):
        return True, 0, True

    if is_prefix and len(indexed_term) >= q_len:
        prefix_sub = indexed_term[:q_len]
        dist = damerau_levenshtein_distance(query_term, prefix_sub)
        if dist <= allowed_typos:
            return True, dist, True

    dist = damerau_levenshtein_distance(query_term, indexed_term)
    if dist <= allowed_typos:
        return True, dist, False

    return False, 999, False
