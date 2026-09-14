from sqlalchemy.orm import Session
from sqlalchemy import select, cast, func, text

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

    def search_by_keyword(
        self,
        db: Session,
        query: str,
        user_id: str,
        top_k: int = 10,
    ) -> list[tuple[Memory, float]]:
        """
        Search memories by keyword using PostgreSQL Full-Text Search.
        
        Args:
            db: Database session
            query: Search query text
            user_id: User ID for isolation
            top_k: Maximum number of results to return
            
        Returns:
            List of (Memory, ts_rank_score) tuples, ordered by rank descending
        """
        # Create tsquery from user input - websearch_to_tsquery handles natural language queries safely
        tsquery = func.websearch_to_tsquery('simple', query)
        
        # Create tsvector from content and summary fields
        # Coalesce handles NULL values
        tsvector = func.to_tsvector('simple', func.coalesce(Memory.content, '') + ' ' + func.coalesce(Memory.summary, ''))
        
        # Calculate rank using ts_rank
        rank = func.ts_rank(tsvector, tsquery).label('keyword_score')
        
        stmt = (
            select(Memory, rank)
            .where(Memory.user_id == user_id)
            .where(tsvector.op('@@')(tsquery))  # Match condition
            .order_by(rank.desc())
            .limit(top_k)
        )
        
        results = db.execute(stmt).all()
        return [(row.Memory, row.keyword_score) for row in results]

    def count_keyword_candidates(
        self,
        db: Session,
        query: str,
        user_id: str,
    ) -> int:
        """
        Count total memories matching the keyword query for a user.
        
        Args:
            db: Database session
            query: Search query text
            user_id: User ID for isolation
            
        Returns:
            Total count of matching memories
        """
        tsquery = func.websearch_to_tsquery('simple', query)
        tsvector = func.to_tsvector('simple', func.coalesce(Memory.content, '') + ' ' + func.coalesce(Memory.summary, ''))
        
        stmt = select(func.count(Memory.id)).where(
            Memory.user_id == user_id,
            tsvector.op('@@')(tsquery)
        )
        return db.execute(stmt).scalar() or 0