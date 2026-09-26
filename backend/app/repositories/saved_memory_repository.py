from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.saved_memory import SavedMemory
from app.models.memory import Memory


class SavedMemoryRepository:
    def save_memory(
        self,
        db: Session,
        user_id: str,
        memory_id: int,
    ) -> SavedMemory | None:
        """
        Save a memory for the user.
        
        Returns the SavedMemory if created, None if already saved.
        """
        # Check if memory exists and belongs to user
        memory = db.query(Memory).filter(
            Memory.id == memory_id, 
            Memory.user_id == user_id
        ).first()
        
        if memory is None:
            return None
        
        # Check if already saved
        existing = db.query(SavedMemory).filter(
            SavedMemory.user_id == user_id,
            SavedMemory.memory_id == memory_id,
        ).first()
        
        if existing:
            return existing
        
        # Create new saved memory
        saved_memory = SavedMemory(
            user_id=user_id,
            memory_id=memory_id,
        )
        
        db.add(saved_memory)
        db.commit()
        db.refresh(saved_memory)
        
        return saved_memory

    def unsave_memory(
        self,
        db: Session,
        user_id: str,
        memory_id: int,
    ) -> bool:
        """
        Remove a memory from user's saved memories.
        
        Returns True if removed, False if not found.
        """
        saved_memory = db.query(SavedMemory).filter(
            SavedMemory.user_id == user_id,
            SavedMemory.memory_id == memory_id,
        ).first()
        
        if saved_memory is None:
            return False
        
        db.delete(saved_memory)
        db.commit()
        
        return True

    def get_saved_memories(
        self,
        db: Session,
        user_id: str,
    ) -> list[SavedMemory]:
        """
        Get all saved memories for a user, ordered by most recent first.
        """
        return (
            db.query(SavedMemory)
            .filter(SavedMemory.user_id == user_id)
            .order_by(desc(SavedMemory.created_at))
            .all()
        )

    def is_saved(
        self,
        db: Session,
        user_id: str,
        memory_id: int,
    ) -> bool:
        """Check if a memory is saved by the user."""
        return (
            db.query(SavedMemory)
            .filter(
                SavedMemory.user_id == user_id,
                SavedMemory.memory_id == memory_id,
            )
            .first()
        ) is not None