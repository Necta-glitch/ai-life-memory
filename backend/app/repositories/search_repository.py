from sqlalchemy.orm import Session
from sqlalchemy import select, cast

from app.models.memory import Memory
from pgvector.sqlalchemy import Vector


class SearchRepository:
    def search_by_vector(
        self,
        db: Session,
        query_embedding: list[float],
        user_id: str,
        top_k: int = 10,
    ) -> list[tuple[Memory, float]]:
        """
        Search memories by vector similarity using pgvector cosine distance.
        
        Args:
            db: Database session
            query_embedding: Query vector (1536 dimensions)
            user_id: User ID for isolation
            top_k: Maximum number of results to return
            
        Returns:
            List of (Memory, cosine_distance) tuples, ordered by distance ascending
        """
        # Cast the JSON-stored embedding to pgvector Vector type for cosine_distance operator
        stmt = (
            select(Memory, cast(Memory.embedding, Vector(1536)).cosine_distance(query_embedding).label("distance"))
            .where(Memory.user_id == user_id)
            .where(Memory.embedding.is_not(None))
            .order_by(cast(Memory.embedding, Vector(1536)).cosine_distance(query_embedding))
            .limit(top_k)
        )
        
        results = db.execute(stmt).all()
        return [(row.Memory, row.distance) for row in results]