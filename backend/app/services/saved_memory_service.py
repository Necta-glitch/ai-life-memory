from sqlalchemy.orm import Session

from app.repositories.saved_memory_repository import SavedMemoryRepository
from app.models.saved_memory import SavedMemory
from app.models.memory import Memory


class SavedMemoryService:
    def __init__(self):
        self.repository = SavedMemoryRepository()

    def save_memory(
        self,
        db: Session,
        user_id: str,
        memory_id: int,
    ) -> SavedMemory | None:
        """
        Save a memory for the user.
        
        Returns the SavedMemory if successful, None if memory not found or doesn't belong to user.
        """
        # Verify memory exists and belongs to user
        memory = db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == user_id,
        ).first()
        
        if memory is None:
            return None
        
        return self.repository.save_memory(db=db, user_id=user_id, memory_id=memory_id)

    def unsave_memory(
        self,
        db: Session,
        user_id: str,
        memory_id: int,
    ) -> bool:
        """
        Remove a memory from user's saved memories.
        
        Returns True if removed, False if not saved.
        """
        # Verify memory exists and belongs to user
        memory = db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == user_id,
        ).first()
        
        if memory is None:
            return False
        
        return self.repository.unsave_memory(db=db, user_id=user_id, memory_id=memory_id)

    def get_saved_memories(
        self,
        db: Session,
        user_id: str,
    ) -> list[SavedMemory]:
        """
        Get all saved memories for a user with their memory data.
        """
        return self.repository.get_saved_memories(db=db, user_id=user_id)

    def is_saved(
        self,
        db: Session,
        user_id: str,
        memory_id: int,
    ) -> bool:
        """Check if a memory is saved by the user."""
        return self.repository.is_saved(db=db, user_id=user_id, memory_id=memory_id)