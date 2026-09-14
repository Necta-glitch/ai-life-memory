from app.ai.embedding_service import EmbeddingService
from app.repositories.search_repository import SearchRepository
from app.search.schemas import SemanticSearchRequest, SemanticSearchResult, SemanticSearchResponse
from app.models.memory import Memory
from sqlalchemy import select, func


class SearchService:
    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        search_repository: SearchRepository | None = None,
    ):
        self.embedding_service = embedding_service or EmbeddingService()
        self.search_repository = search_repository or SearchRepository()

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