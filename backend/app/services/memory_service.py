from sqlalchemy.orm import Session

from app.repositories.memory_repository import MemoryRepository
from app.schemas.memory import MemoryCreate
from app.schemas.memory_update import MemoryUpdate
from app.models.memory import Memory


class MemoryService:
    def __init__(self):
        self.repository = MemoryRepository()

    def create_memory(
        self,
        db: Session,
        memory: MemoryCreate,
        user_id: str,
    ):
        return self.repository.create(
            db=db,
            memory=memory,
            user_id=user_id,
        )

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