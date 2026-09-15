from app.ai.embedding_service import EmbeddingService
from app.repositories.search_repository import SearchRepository
from app.search.schemas import (
    SemanticSearchRequest, 
    SemanticSearchResult, 
    SemanticSearchResponse,
    KeywordSearchRequest,
    KeywordSearchResult,
    KeywordSearchResponse,
    HybridSearchRequest,
    HybridSearchResult,
    HybridSearchResponse,
)
from app.search.reranker import EmbeddingReranker, CrossEncoderReranker, Reranker, NoOpReranker
from app.models.memory import Memory
from app.core.config import RERANKER_TYPE, RERANKER_MODEL
from sqlalchemy import select, func


class SearchService:
    # RRF constant
    RRF_K = 60

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        search_repository: SearchRepository | None = None,
        reranker: Reranker | None = None,
    ):
        self.embedding_service = embedding_service or EmbeddingService()
        self.search_repository = search_repository or SearchRepository()
        
        if reranker is not None:
            self.reranker = reranker
        else:
            self.reranker = self._create_reranker()

    def _create_reranker(self) -> Reranker:
        """Create the appropriate reranker based on configuration."""
        if RERANKER_TYPE == "cross_encoder":
            return CrossEncoderReranker(model_name=RERANKER_MODEL)
        elif RERANKER_TYPE == "embedding":
            return EmbeddingReranker(self.embedding_service)
        elif RERANKER_TYPE == "none":
            return NoOpReranker()
        else:
            # Default to embedding reranker for backward compatibility
            return EmbeddingReranker(self.embedding_service)

    def semantic_search(
        self,
        db,
        request: SemanticSearchRequest,
        user_id: str,
    ) -> SemanticSearchResponse:
        """
        Perform semantic search for a user's memories.
        
        Args:
            db: Database session
            request: Search request with query and top_k
            user_id: User ID for isolation
            
        Returns:
            SemanticSearchResponse with results and metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_service.get_embedding(request.query)
        
        # Search repository
        results = self.search_repository.search_by_vector(
            db=db,
            query_embedding=query_embedding,
            user_id=user_id,
            top_k=request.top_k,
        )
        
        # Convert to response format
        search_results = []
        for memory, distance in results:
            similarity = 1.0 - distance
            search_results.append(SemanticSearchResult(
                id=memory.id,
                user_id=memory.user_id,
                content=memory.content,
                summary=memory.summary,
                topics=memory.topics,
                entities=memory.entities,
                source=memory.source,
                created_at=memory.created_at.isoformat() if memory.created_at else "",
                occurred_at=memory.occurred_at.isoformat() if memory.occurred_at else None,
                similarity=similarity,
            ))
        
        # Count total candidates (memories with embeddings for this user)
        from sqlalchemy import select, func
        total_stmt = select(func.count(Memory.id)).where(
            Memory.user_id == user_id,
            Memory.embedding.is_not(None)
        )
        total_candidates = db.execute(total_stmt).scalar() or 0
        
        return SemanticSearchResponse(
            results=search_results,
            query=request.query,
            total_candidates=total_candidates,
        )

    def keyword_search(
        self,
        db,
        request: KeywordSearchRequest,
        user_id: str,
    ) -> KeywordSearchResponse:
        """
        Perform keyword search for a user's memories using PostgreSQL Full-Text Search.
        
        Args:
            db: Database session
            request: Search request with query and top_k
            user_id: User ID for isolation
            
        Returns:
            KeywordSearchResponse with results and metadata
        """
        # Search repository
        results = self.search_repository.search_by_keyword(
            db=db,
            query=request.query,
            user_id=user_id,
            top_k=request.top_k,
        )
        
        # Convert to response format
        search_results = []
        for memory, keyword_score in results:
            search_results.append(KeywordSearchResult(
                id=memory.id,
                user_id=memory.user_id,
                content=memory.content,
                summary=memory.summary,
                topics=memory.topics,
                entities=memory.entities,
                source=memory.source,
                created_at=memory.created_at.isoformat() if memory.created_at else "",
                occurred_at=memory.occurred_at.isoformat() if memory.occurred_at else None,
                keyword_score=keyword_score,
            ))
        
        # Count total candidates (all memories with matching keywords for this user)
        total_candidates = self.search_repository.count_keyword_candidates(
            db=db,
            query=request.query,
            user_id=user_id,
        )
        
        return KeywordSearchResponse(
            results=search_results,
            query=request.query,
            total_candidates=total_candidates,
        )

    def _get_rrf_scores(
        self,
        semantic_results: list[SemanticSearchResult],
        keyword_results: list[KeywordSearchResult],
        k: int = RRF_K,
    ) -> dict[int, float]:
        """
        Calculate RRF scores from two ranked result lists.
        
        RRF formula: score(d) = sum(1 / (k + rank(d)))
        
        Args:
            semantic_results: List of SemanticSearchResult (rank 1 = index 0)
            keyword_results: List of KeywordSearchResult (rank 1 = index 0)
            k: RRF constant (default 60)
            
        Returns:
            Dictionary mapping memory_id -> RRF score
        """
        rrf_scores: dict[int, float] = {}
        
        # Add semantic search contributions
        for rank, result in enumerate(semantic_results, start=1):
            memory_id = result.id
            if memory_id not in rrf_scores:
                rrf_scores[memory_id] = 0.0
            rrf_scores[memory_id] += 1.0 / (k + rank)
        
        # Add keyword search contributions
        for rank, result in enumerate(keyword_results, start=1):
            memory_id = result.id
            if memory_id not in rrf_scores:
                rrf_scores[memory_id] = 0.0
            rrf_scores[memory_id] += 1.0 / (k + rank)
        
        return rrf_scores

    def hybrid_search(
        self,
        db,
        request: HybridSearchRequest,
        user_id: str,
    ) -> HybridSearchResponse:
        """
        Perform hybrid search using RRF (Reciprocal Rank Fusion) to combine
        semantic and keyword search results.
        
        Args:
            db: Database session
            request: Search request with query and top_k
            user_id: User ID for isolation
            
        Returns:
            HybridSearchResponse with RRF-fused results
        """
        # Use a larger candidate pool for better fusion (retrieve more than top_k)
        # We fetch up to 50 from each to have enough candidates for fusion
        candidate_pool_k = max(request.top_k * 3, 50)
        
        # Execute both searches with larger candidate pool
        semantic_request = SemanticSearchRequest(query=request.query, top_k=candidate_pool_k)
        keyword_request = KeywordSearchRequest(query=request.query, top_k=candidate_pool_k)
        
        semantic_response = self.semantic_search(db, semantic_request, user_id)
        keyword_response = self.keyword_search(db, keyword_request, user_id)
        
        # Calculate RRF scores
        rrf_scores = self._get_rrf_scores(
            semantic_response.results,
            keyword_response.results,
            self.RRF_K,
        )
        
        # Create a lookup for all memory details (from both sources)
        memory_lookup: dict[int, dict] = {}
        for r in semantic_response.results:
            memory_lookup[r.id] = {
                "id": r.id,
                "user_id": r.user_id,
                "content": r.content,
                "summary": r.summary,
                "topics": r.topics,
                "entities": r.entities,
                "source": r.source,
                "created_at": r.created_at,
                "occurred_at": r.occurred_at,
            }
        for r in keyword_response.results:
            if r.id not in memory_lookup:
                memory_lookup[r.id] = {
                    "id": r.id,
                    "user_id": r.user_id,
                    "content": r.content,
                    "summary": r.summary,
                    "topics": r.topics,
                    "entities": r.entities,
                    "source": r.source,
                    "created_at": r.created_at,
                    "occurred_at": r.occurred_at,
                }
        
        # Sort by RRF score descending
        sorted_memory_ids = sorted(rrf_scores.keys(), key=lambda mid: rrf_scores[mid], reverse=True)
        
        # Build final results (limited to top_k)
        final_results = []
        for memory_id in sorted_memory_ids[:request.top_k]:
            mem = memory_lookup[memory_id]
            final_results.append(HybridSearchResult(
                id=mem["id"],
                user_id=mem["user_id"],
                content=mem["content"],
                summary=mem["summary"],
                topics=mem["topics"],
                entities=mem["entities"],
                source=mem["source"],
                created_at=mem["created_at"],
                occurred_at=mem["occurred_at"],
                rrf_score=rrf_scores[memory_id],
            ))
        
        # total_candidates = unique memory IDs in the candidate pool
        all_candidate_ids = set(r.id for r in semantic_response.results) | set(r.id for r in keyword_response.results)
        total_candidates = len(all_candidate_ids)
        
        return HybridSearchResponse(
            results=final_results,
            query=request.query,
            total_candidates=total_candidates,
        )

    def _get_candidate_pool(
        self,
        db,
        request: HybridSearchRequest,
        user_id: str,
    ) -> list[HybridSearchResult]:
        """
        Get a larger candidate pool for reranking.

        Retrieves a larger pool of candidates from both semantic and keyword search,
        combines them with RRF, and returns the full pool (not limited to top_k).
        This ensures the reranker has enough candidates to work with.
        """
        candidate_pool_k = max(request.top_k * 3, 50)

        # Execute both searches with larger candidate pool
        semantic_request = SemanticSearchRequest(query=request.query, top_k=candidate_pool_k)
        keyword_request = KeywordSearchRequest(query=request.query, top_k=candidate_pool_k)

        semantic_response = self.semantic_search(db, semantic_request, user_id)
        keyword_response = self.keyword_search(db, keyword_request, user_id)

        # Calculate RRF scores
        rrf_scores = self._get_rrf_scores(
            semantic_response.results,
            keyword_response.results,
            self.RRF_K,
        )

        # Create a lookup for all memory details (from both sources)
        memory_lookup: dict[int, dict] = {}
        for r in semantic_response.results:
            memory_lookup[r.id] = {
                "id": r.id,
                "user_id": r.user_id,
                "content": r.content,
                "summary": r.summary,
                "topics": r.topics,
                "entities": r.entities,
                "source": r.source,
                "created_at": r.created_at,
                "occurred_at": r.occurred_at,
            }
        for r in keyword_response.results:
            if r.id not in memory_lookup:
                memory_lookup[r.id] = {
                    "id": r.id,
                    "user_id": r.user_id,
                    "content": r.content,
                    "summary": r.summary,
                    "topics": r.topics,
                    "entities": r.entities,
                    "source": r.source,
                    "created_at": r.created_at,
                    "occurred_at": r.occurred_at,
                }

        # Build full candidate pool (not limited to top_k)
        # Fetch embeddings from database for reranking
        all_candidate_ids = set(r.id for r in semantic_response.results) | set(r.id for r in keyword_response.results)
        
        # Fetch embeddings from database in bulk
        from app.models.memory import Memory
        embeddings_map = {}
        if all_candidate_ids:
            embedding_results = db.execute(
                select(Memory.id, Memory.embedding).where(Memory.id.in_(all_candidate_ids))
            ).all()
            embeddings_map = {row.id: row.embedding for row in embedding_results}
        
        candidate_pool = []
        for memory_id in all_candidate_ids:
            mem = memory_lookup[memory_id]
            candidate_pool.append(HybridSearchResult(
                id=mem["id"],
                user_id=mem["user_id"],
                content=mem["content"],
                summary=mem["summary"],
                topics=mem["topics"],
                entities=mem["entities"],
                source=mem["source"],
                created_at=mem["created_at"],
                occurred_at=mem["occurred_at"],
                rrf_score=rrf_scores[memory_id],
                embedding=embeddings_map.get(memory_id),
            ))

        return candidate_pool

    def rerank(
        self,
        query: str,
        results: list[HybridSearchResult],
        top_k: int,
    ) -> list[HybridSearchResult]:
        """
        Rerank results using the configured reranker.

        Args:
            query: The original user query
            results: List of HybridSearchResult to rerank
            top_k: Number of results to return after reranking

        Returns:
            Reranked list of HybridSearchResult
        """
        return self.reranker.rerank(query, results, top_k)

    def hybrid_search_with_rerank(
        self,
        db,
        request: HybridSearchRequest,
        user_id: str,
    ) -> HybridSearchResponse:
        """
        Perform hybrid search with reranking.

        This is the main entry point for the new search flow:
        1. Get candidate pool from hybrid search (semantic + keyword + RRF)
        2. Rerank candidates by embedding similarity
        3. Return top_k reranked results
        """
        # Get candidate pool
        candidate_pool = self._get_candidate_pool(db, request, user_id)

        if not candidate_pool:
            return HybridSearchResponse(
                results=[],
                query=request.query,
                total_candidates=0,
            )

        # Rerank the candidate pool
        reranked_results = self.rerank(request.query, candidate_pool, request.top_k)

        # total_candidates = unique memory IDs in the candidate pool
        total_candidates = len(candidate_pool)

        return HybridSearchResponse(
            results=reranked_results,
            query=request.query,
            total_candidates=total_candidates,
        )