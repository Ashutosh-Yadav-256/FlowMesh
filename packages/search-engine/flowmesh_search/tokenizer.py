from __future__ import annotations

import re
from typing import List, Tuple

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "were", "will", "with"
}

CAMEL_CASE_REGEX = re.compile(r"([a-z])([A-Z])")
WORD_TOKEN_REGEX = re.compile(r"[a-zA-Z0-9_\-\.:]+")


class CodeAwareTokenizer:
    """
    Intelligent tokenizer capable of parsing both natural language text
    and code/identifier symbols (snake_case, camelCase, kebab-case, dotted events).
    """

    def __init__(self, filter_stop_words: bool = True):
        self.filter_stop_words = filter_stop_words

    def tokenize(self, text: str) -> List[str]:
        """Returns ordered list of lowercase normalized tokens."""
        if not text:
            return []

        tokens: List[str] = []
        raw_words = WORD_TOKEN_REGEX.findall(text)

        for word in raw_words:

            clean_word = word.strip(".:-_").lower()
            if not clean_word:
                continue

            if clean_word not in tokens:
                tokens.append(clean_word)

            camel_split = CAMEL_CASE_REGEX.sub(r"\1 \2", word)

            separated = (
                camel_split.replace("_", " ")
                .replace("-", " ")
                .replace(".", " ")
                .replace(":", " ")
                .replace("/", " ")
            )

            sub_tokens = separated.lower().split()
            for sub in sub_tokens:
                sub = sub.strip()
                if not sub:
                    continue
                if self.filter_stop_words and len(sub) > 2 and sub in STOP_WORDS:
                    continue
                if sub not in tokens:
                    tokens.append(sub)

        return tokens

    def tokenize_with_positions(self, text: str) -> List[Tuple[str, int]]:
        """Returns tokens paired with sequential position integers."""
        tokens = self.tokenize(text)
        return [(tok, idx) for idx, tok in enumerate(tokens)]
