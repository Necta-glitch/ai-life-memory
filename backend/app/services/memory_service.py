from sqlalchemy.orm import Session

from app.repositories.memory_repository import MemoryRepository
from app.schemas.memory import MemoryCreate
from app.schemas.memory_update import MemoryUpdate
from app.models.memory import Memory
from app.ai.service import AIService
from app.ai.embedding_service import EmbeddingService
from app.ai.embeddings import build_embedding_input


class MemoryService:
    def __init__(
        self,
        ai_service: AIService | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        self.repository = MemoryRepository()
        self.ai_service = ai_service or AIService()
        self.embedding_service = embedding_service or EmbeddingService()

    def create_memory(
        self,
        db: Session,
        memory: MemoryCreate,
        user_id: str,
    ) -> Memory:
        # Create memory object but don't commit yet
        new_memory = Memory(
            user_id=user_id,
            content=memory.content,
            source=memory.source,
            occurred_at=memory.occurred_at,
        )

        db.add(new_memory)
        db.flush()  # Get ID without committing

        # Process with AI
        ai_result = self.ai_service.process_memory(memory.content)

        # Update with AI results
        new_memory.summary = ai_result.summary
        new_memory.topics = ai_result.topics
        new_memory.entities = ai_result.entities

        # Generate embedding using MVP strategy: content + summary
        embedding_text = build_embedding_input(
            content=memory.content,
            summary=ai_result.summary,
            strategy="content_summary",
        )
        embedding = self.embedding_service.get_embedding(embedding_text)
        new_memory.embedding = embedding

        # Commit everything atomically
        db.commit()
        db.refresh(new_memory)

        return new_memory

    def get_memories(
        self,
        db: Session,
        user_id: str,
    ) -> list[Memory]:
        return self.repository.get_all(
            db=db,
            user_id=user_id,
        )

    def get_memory(
        self,
        db: Session,
        memory_id: int,
        user_id: str,
    ) -> Memory | None:
        return self.repository.get_by_id(
            db=db,
            memory_id=memory_id,
            user_id=user_id,
        )

    def update_memory(
        self,
        db: Session,
        memory_id: int,
        memory_update: MemoryUpdate,
        user_id: str,
    ) -> Memory | None:
        """
        Update a memory by ID.
        
        Returns:
            Updated Memory object, or None if not found
        """
        return self.repository.update(
            db=db,
            memory_id=memory_id,
            memory_update=memory_update,
            user_id=user_id,
        )

    def delete_memory(
        self,
        db: Session,
        memory_id: int,
        user_id: str,
    ) -> bool:
        return self.repository.delete(
            db=db,
            memory_id=memory_id,
            user_id=user_id,
        )