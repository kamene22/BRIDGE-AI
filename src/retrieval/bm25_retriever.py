"""
src/retrieval/bm25_retriever.py — Pure Python BM25 Okapi Sparse Retriever

Implements BM25 Okapi algorithm (k1=1.5, b=0.75) over corpus text chunks.
Preserves chunk ID, document content, metadata, and relative rank.
"""

import math
import re
from typing import List, Dict, Any, Tuple

# Basic English & Legal Stopwords
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were", "will",
    "with", "the", "this", "but", "they", "have", "had", "what", "when", "where", "who"
}


def tokenize(text: str) -> List[str]:
    """Tokenizes text into normalized alphanumeric terms, stripping punctuation."""
    tokens = re.findall(r"\b\w+\b", text.lower())
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_chunks = []
        self.corpus_size = 0
        self.avgdl = 0.0
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        """Indexes a list of chunk dictionaries containing 'id', 'document', 'metadata'."""
        self.doc_chunks = chunks
        self.corpus_size = len(chunks)
        if self.corpus_size == 0:
            return

        self.doc_len = []
        self.doc_freqs = []
        df = {}

        for chunk in chunks:
            text = chunk.get("document", "")
            tokens = tokenize(text)
            self.doc_len.append(len(tokens))

            frequencies = {}
            for t in tokens:
                frequencies[t] = frequencies.get(t, 0) + 1
            self.doc_freqs.append(frequencies)

            for t in set(tokens):
                df[t] = df.get(t, 0) + 1

        self.avgdl = sum(self.doc_len) / float(self.corpus_size) if self.corpus_size > 0 else 1.0

        # Calculate IDF for each token using Lucene/BM25 formula
        self.idf = {}
        for word, freq in df.items():
            idf_val = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))
            self.idf[word] = max(0.0, idf_val)

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Searches BM25 index for query and returns ranked chunks with scores."""
        if not self.doc_chunks or self.corpus_size == 0:
            return []

        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        scores = []
        for idx in range(self.corpus_size):
            score = 0.0
            doc_len = self.doc_len[idx]
            doc_freq = self.doc_freqs[idx]

            for token in q_tokens:
                if token in doc_freq:
                    freq = doc_freq[token]
                    idf = self.idf.get(token, 0.0)
                    num = freq * (self.k1 + 1.0)
                    den = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl))
                    score += idf * (num / den)

            scores.append((score, idx))

        # Sort by score descending
        scores.sort(key=lambda x: x[0], reverse=True)

        results = []
        for rank, (score, idx) in enumerate(scores[:top_k], 1):
            if score <= 0.0:
                continue
            chunk = self.doc_chunks[idx].copy()
            chunk["bm25_score"] = round(score, 4)
            chunk["bm25_rank"] = rank
            results.append(chunk)

        return results
