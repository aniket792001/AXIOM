"""Multi-Tenant Hybrid Vector Store for Axiom & SCORE Engine.

Combines Dense Vector Search (Qdrant) + Sparse Keyword Search (BM25Plus)
using Reciprocal Rank Fusion (RRF). Guarantees tenant data isolation.
"""

from collections import defaultdict
import hashlib
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from axiom.config.settings import get_settings
from axiom.core.state import DocumentChunk


def tokenize(text: str) -> List[str]:
    """Tokenize text into alphanumeric and dotted identifiers for BM25."""
    return [t for t in re.findall(r"[a-zA-Z0-9_\.]+", text.lower()) if t]


def _deterministic_mock_embedding(text: str, dim: int = 384) -> List[float]:
    """Generate a deterministic normalized vector for local key-free testing."""
    hash_obj = hashlib.sha256(text.encode("utf-8"))
    raw_bytes = hash_obj.digest()
    vec = []
    for i in range(dim):
        byte_val = raw_bytes[i % len(raw_bytes)]
        vec.append(math.sin(byte_val + i))
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


class HybridVectorStore:
    """Enterprise Hybrid Vector Store with strict tenant isolation."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._qdrant_client: Optional[Any] = None
        self._bm25_indices: Dict[str, Any] = {}
        self._corpus_store: Dict[str, List[DocumentChunk]] = defaultdict(list)
        self._collection_name = self.settings.qdrant_collection
        self._dim = 384
        self._init_qdrant()

    def _init_qdrant(self) -> None:
        """Initialize Qdrant client (remote or local in-memory fallback)."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models

            if self.settings.qdrant_url and self.settings.qdrant_url != "http://localhost:6333":
                self._qdrant_client = QdrantClient(
                    url=self.settings.qdrant_url,
                    api_key=self.settings.qdrant_api_key,
                )
            else:
                self._qdrant_client = QdrantClient(location=":memory:")

            collections = [c.name for c in self._qdrant_client.get_collections().collections]
            if self._collection_name not in collections:
                self._qdrant_client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=models.VectorParams(
                        size=self._dim,
                        distance=models.Distance.COSINE,
                    ),
                )
        except Exception:
            self._qdrant_client = None

    def _get_embedding(self, text: str) -> List[float]:
        """Compute embedding vector using configured provider or mock fallback."""
        if self.settings.gemini_api_key:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                embedder = GoogleGenerativeAIEmbeddings(
                    model=self.settings.embedding_model,
                    google_api_key=self.settings.gemini_api_key,
                )
                return embedder.embed_query(text)
            except Exception:
                pass
        return _deterministic_mock_embedding(text, self._dim)

    def ingest_documents(self, tenant_id: str, chunks: List[DocumentChunk]) -> int:
        """Ingest document chunks into both dense vector store and sparse BM25 index."""
        if not chunks:
            return 0

        self._corpus_store[tenant_id].extend(chunks)

        corpus_texts = [c.content for c in self._corpus_store[tenant_id]]
        tokenized_corpus = [tokenize(doc) for doc in corpus_texts]

        try:
            from rank_bm25 import BM25Plus
            self._bm25_indices[tenant_id] = BM25Plus(tokenized_corpus)
        except ImportError:
            self._bm25_indices[tenant_id] = tokenized_corpus

        if self._qdrant_client:
            from qdrant_client.http import models
            points = []
            for chunk in chunks:
                vector = self._get_embedding(chunk.content)
                point_id = int(hashlib.md5(chunk.id.encode()).hexdigest()[:8], 16)
                payload = {
                    "tenant_id": tenant_id,
                    "chunk_id": chunk.id,
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                }
                points.append(
                    models.PointStruct(id=point_id, vector=vector, payload=payload)
                )

            self._qdrant_client.upsert(
                collection_name=self._collection_name,
                points=points,
            )

        return len(chunks)

    def dense_search(self, tenant_id: str, query: str, top_k: int = 10) -> List[Tuple[DocumentChunk, float]]:
        """Perform dense vector search isolated strictly to the tenant."""
        if not self._qdrant_client:
            return []

        from qdrant_client.http import models

        query_vector = self._get_embedding(query)
        tenant_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="tenant_id",
                    match=models.MatchValue(value=tenant_id),
                )
            ]
        )

        try:
            results = self._qdrant_client.search(
                collection_name=self._collection_name,
                query_vector=query_vector,
                query_filter=tenant_filter,
                limit=top_k,
            )
            hits = []
            for hit in results:
                payload = hit.payload or {}
                chunk = DocumentChunk(
                    id=payload.get("chunk_id", str(hit.id)),
                    content=payload.get("content", ""),
                    metadata=payload.get("metadata", {}),
                    relevance_score=hit.score,
                )
                hits.append((chunk, hit.score))
            return hits
        except Exception:
            return []

    def sparse_search(self, tenant_id: str, query: str, top_k: int = 10) -> List[Tuple[DocumentChunk, float]]:
        """Perform BM25 sparse keyword search isolated strictly to the tenant."""
        tenant_chunks = self._corpus_store.get(tenant_id, [])
        if not tenant_chunks:
            return []

        bm25_index = self._bm25_indices.get(tenant_id)
        if not bm25_index:
            return []

        tokenized_query = tokenize(query)
        if not tokenized_query:
            return []

        if hasattr(bm25_index, "get_scores"):
            scores = bm25_index.get_scores(tokenized_query)
        else:
            scores = [
                sum(1 for token in tokenized_query if token in doc)
                for doc in bm25_index
            ]

        # Calculate matches and filter out non-matching chunks
        scored_chunks = []
        query_set = set(tokenized_query)
        for chunk, score in zip(tenant_chunks, scores):
            chunk_tokens = set(tokenize(chunk.content))
            # Verify that at least one query token exists in chunk
            if query_set.intersection(chunk_tokens):
                scored_chunks.append((chunk, float(score)))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    def hybrid_search(
        self, tenant_id: str, query: str, top_k: int = 5, rrf_k: int = 60
    ) -> List[DocumentChunk]:
        """Perform Hybrid Search with Reciprocal Rank Fusion (RRF)."""
        dense_results = self.dense_search(tenant_id, query, top_k=top_k * 2)
        sparse_results = self.sparse_search(tenant_id, query, top_k=top_k * 2)

        rrf_scores: Dict[str, float] = defaultdict(float)
        chunk_map: Dict[str, DocumentChunk] = {}

        for rank, (chunk, _) in enumerate(dense_results):
            chunk_map[chunk.id] = chunk
            rrf_scores[chunk.id] += 1.0 / (rrf_k + (rank + 1))

        for rank, (chunk, _) in enumerate(sparse_results):
            chunk_map[chunk.id] = chunk
            rrf_scores[chunk.id] += 1.0 / (rrf_k + (rank + 1))

        if not rrf_scores and self._corpus_store.get(tenant_id):
            return self._corpus_store[tenant_id][:top_k]

        sorted_chunk_ids = sorted(
            rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True
        )

        final_chunks: List[DocumentChunk] = []
        for cid in sorted_chunk_ids[:top_k]:
            chunk = chunk_map[cid]
            chunk.relevance_score = rrf_scores[cid]
            final_chunks.append(chunk)

        return final_chunks


_hybrid_store_instance: Optional[HybridVectorStore] = None


def get_vector_store() -> HybridVectorStore:
    """Return singleton instance of the HybridVectorStore."""
    global _hybrid_store_instance
    if _hybrid_store_instance is None:
        _hybrid_store_instance = HybridVectorStore()
    return _hybrid_store_instance
