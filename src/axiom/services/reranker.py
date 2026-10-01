"""Cross-Encoder Re-Ranking Service for Axiom & SCORE Engine.

Refines hybrid retrieval candidates using token-level cross-attention.
Filters false positives and prioritizes high-precision contractual clauses.
"""

import re
from typing import List
from axiom.config.settings import get_settings
from axiom.core.state import DocumentChunk


class RerankerService:
    """Enterprise Re-ranking Service supporting Cohere and local cross-scorer."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def rerank(self, query: str, chunks: List[DocumentChunk], top_k: int = 5) -> List[DocumentChunk]:
        """Re-rank candidate chunks down to top_k highest precision chunks."""
        if not chunks:
            return []

        # 1. Use Cohere Cross-Encoder if API key and enabled
        if self.settings.reranker_enabled and self.settings.cohere_api_key:
            try:
                import cohere
                co = cohere.ClientV2(api_key=self.settings.cohere_api_key)
                docs_payload = [c.content for c in chunks]
                response = co.rerank(
                    model="rerank-v3.5",
                    query=query,
                    documents=docs_payload,
                    top_n=top_k,
                )
                reranked_chunks: List[DocumentChunk] = []
                for item in response.results:
                    original_chunk = chunks[item.index]
                    original_chunk.relevance_score = item.relevance_score
                    reranked_chunks.append(original_chunk)
                return reranked_chunks
            except Exception:
                pass  # Fallback to local heuristic re-ranker on API failure

        # 2. Local Cross-Scorer (exact phrase, numeric & keyword density)
        query_lower = query.lower()
        query_tokens = set(re.findall(r"[a-zA-Z0-9_\.]+", query_lower))

        scored_chunks = []
        for chunk in chunks:
            content_lower = chunk.content.lower()
            content_tokens = set(re.findall(r"[a-zA-Z0-9_\.]+", content_lower))

            # Metric 1: Token overlap
            overlap = len(query_tokens.intersection(content_tokens)) / max(len(query_tokens), 1)

            # Metric 2: Exact clause / query substring match
            exact_bonus = 0.5 if query_lower in content_lower else 0.0

            # Metric 3: Amendment / addendum keyword boost
            amendment_bonus = 0.4 if any(w in content_lower for w in ["addendum", "amendment", "supersedes", "amended"]) else 0.0

            score = overlap + exact_bonus + amendment_bonus
            chunk.relevance_score = score
            scored_chunks.append((chunk, score))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, _ in scored_chunks[:top_k]]


_reranker_instance = None


def get_reranker() -> RerankerService:
    """Return singleton instance of RerankerService."""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = RerankerService()
    return _reranker_instance
