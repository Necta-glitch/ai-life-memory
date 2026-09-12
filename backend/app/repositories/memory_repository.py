from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.schemas.memory import MemoryCreate


class MemoryRepository:
    def create(
        self,
        db: Session,
        memory: MemoryCreate,
        user_id: str,
    ) -> Memory:
        new_memory = Memory(
            user_id=user_id,
            content=memory.content,
            source=memory.source,
            occurred_at=memory.occurred_at,
        )

        db.add(new_memory)
        db.commit()
        db.refresh(new_memory)

        return new_memory

    def get_all(
        self,
        db: Session,
        user_id: str,
    ) -> list[Memory]:
        return db.query(Memory).filter(Memory.user_id == user_id).all()

    def get_by_id(
        self,
        db: Session,
        memory_id: int,
        user_id: str,
    ) -> Memory | None:
        return (
            db.query(Memory)
            .filter(Memory.id == memory_id, Memory.user_id == user_id)
            .first()
        )

    def update(
        self,
        db: Session,
        memory_id: int,
        memory_update,
        user_id: str,
    ) -> Memory | None:
        """
        Update a memory by ID.
        
        Allowed fields: content, occurred_at
        Immutable fields: id, user_id, created_at, source
        """
        # Find the memory
        memory = db.query(Memory).filter(Memory.id == memory_id, Memory.user_id == user_id).first()

        if memory is None:
            return None

        # Only update provided fields
        if memory_update.content is not None:
            memory.content = memory_update.content

        if memory_update.occurred_at is not None:
            memory.occurred_at = memory_update.occurred_at

        db.commit()
        db.refresh(memory)

        return memory

    def delete(
        self,
        db: Session,
        memory_id: int,
        user_id: str,
    ) -> bool:
        """
        Delete a memory by ID.
        
        Returns True if deleted, False if memory not found.
        """
        memory = db.query(Memory).filter(Memory.id == memory_id, Memory.user_id == user_id).first()

        if memory is None:
            return False

        db.delete(memory)
        db.commit()

        return True