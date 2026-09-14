import math
from typing import Protocol

from app.search.schemas import HybridSearchResult


class Reranker(Protocol):
    """Protocol for reranking search results."""

    def rerank(
        self,
        query: str,
        results: list[HybridSearchResult],
        top_k: int,
    ) -> list[HybridSearchResult]:
        """
        Rerank search results by relevance to query.

        Args:
            query: The original user query
            results: List of HybridSearchResult to rerank
            top_k: Number of results to return after reranking

        Returns:
            Reranked list of HybridSearchResult, sorted by rerank_score descending
        """
        ...


class EmbeddingReranker:
    """
    Reranker that uses cosine similarity between query and memory embeddings.

    Uses the existing EmbeddingService to generate query embeddings and reuses
    stored memory embeddings from the database.
    """

    def __init__(self, embedding_service):
        """
        Initialize the reranker.

        Args:
            embedding_service: Instance of EmbeddingService for generating embeddings
        """
        self.embedding_service = embedding_service

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            a: First vector
            b: Second vector

        Returns:
            Cosine similarity score between -1 and 1
        """
        if len(a) != len(b):
            raise ValueError("Vectors must have the same length")

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def rerank(
        self,
        query: str,
        results: list[HybridSearchResult],
        top_k: int,
    ) -> list[HybridSearchResult]:
        """
        Rerank results by cosine similarity between query and memory embeddings.

        Reuses stored memory embeddings from the database. Only generates
        one query embedding per rerank call.

        Args:
            query: The original user query
            results: List of HybridSearchResult to rerank
            top_k: Number of results to return after reranking

        Returns:
            Reranked list of HybridSearchResult with rerank_score added,
            sorted by rerank_score descending
        """
        if not results:
            return []

        # Build query embedding input using the same strategy as memory embeddings
        # Memory embeddings use "content_summary" strategy
        from app.ai.embeddings import build_embedding_input
        query_embedding_text = build_embedding_input(
            content=query,
            summary=query,  # Use query as summary for consistency
            strategy="content_summary",
        )

        # Generate query embedding ONCE
        query_embedding = self.embedding_service.get_embedding(query_embedding_text)

        reranked = []
        for result in results:
            # Get memory embedding from the result
            # The embedding should be available on the memory object
            memory_embedding = getattr(result, 'embedding', None)

            if memory_embedding is not None:
                # Calculate cosine similarity
                rerank_score = self._cosine_similarity(query_embedding, memory_embedding)
            else:
                # If no embedding available, give a neutral score
                rerank_score = 0.0

            # Create a new result with rerank_score
            # We need to add rerank_score to the result
            # Since HybridSearchResult doesn't have rerank_score yet,
            # we'll store it as an attribute or create a new schema
            # For now, let's add it as a dynamic attribute
            result.rerank_score = rerank_score
            reranked.append(result)

        # Sort by rerank_score descending
        reranked.sort(key=lambda r: r.rerank_score, reverse=True)

        return reranked[:top_k]


class NoOpReranker:
    """Reranker that returns results unchanged (for testing or disabling reranking)."""

    def rerank(
        self,
        query: str,
        results: list[HybridSearchResult],
        top_k: int,
    ) -> list[HybridSearchResult]:
        return results[:top_k]