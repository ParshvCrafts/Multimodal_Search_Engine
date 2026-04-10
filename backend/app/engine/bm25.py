import re
from collections import Counter
from typing import Dict, List

import numpy as np

__all__ = ["SimpleBM25"]


class SimpleBM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_tokens: List[List[str]] = []
        self.avg_dl: float = 0
        self.df: Dict[str, int] = {}
        self.n_docs: int = 0

    def fit(self, documents: List[str]):
        self.doc_tokens = [self._tokenize(d) for d in documents]
        self.n_docs = len(self.doc_tokens)
        self.avg_dl = np.mean([len(t) for t in self.doc_tokens]) if self.doc_tokens else 1
        self.df = Counter()
        for tokens in self.doc_tokens:
            for t in set(tokens):
                self.df[t] += 1

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b[a-z]+\b', str(text).lower())

    def score_candidates(self, query: str, candidate_indices: List[int]) -> np.ndarray:
        q_tokens = self._tokenize(query)
        scores = np.zeros(len(candidate_indices), dtype=np.float32)
        for i, doc_idx in enumerate(candidate_indices):
            if doc_idx >= len(self.doc_tokens):
                continue
            doc = self.doc_tokens[doc_idx]
            dl = len(doc)
            tf_doc = Counter(doc)
            s = 0.0
            for qt in q_tokens:
                if qt not in self.df:
                    continue
                tf = tf_doc.get(qt, 0)
                idf = np.log((self.n_docs - self.df[qt] + 0.5) / (self.df[qt] + 0.5) + 1)
                num = tf * (self.k1 + 1)
                den = tf + self.k1 * (1 - self.b + self.b * dl / self.avg_dl)
                s += idf * num / den
            scores[i] = s
        return scores
