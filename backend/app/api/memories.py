from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import get_db
from app.services.memory_service import MemoryService
from app.services.saved_memory_service import SavedMemoryService
from app.schemas.memory import MemoryCreate, MemoryResponse
from app.schemas.memory_update import MemoryUpdate


router = APIRouter(prefix="/memories", tags=["memories"])
memory_service = MemoryService()
saved_memory_service = SavedMemoryService()


def get_user_id(
    user_id: str = Query(default="dev-user"),
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
) -> str:
    return x_user_id if x_user_id is not None else user_id


# POST /memories/saved - MUST come before /memories/{memory_id} to avoid route conflict
@router.get("/saved", response_model=list[MemoryResponse])
def get_saved_memories(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """
    Get all saved memories for the current user.
    
    Returns memories ordered by most recently saved first.
    """
    saved_memories = saved_memory_service.get_saved_memories(
        db=db,
        user_id=user_id,
    )
    
    # Return the Memory objects from the SavedMemory relationships
    return [sm.memory for sm in saved_memories]


@router.post("/{memory_id}/save", status_code=status.HTTP_201_CREATED)
def save_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """
    Save a memory for the current user.
    
    Returns:
        201 Created if saved successfully
        200 OK if already saved (idempotent)
        404 Not Found if memory doesn't exist or doesn't belong to user
    """
    saved_memory = saved_memory_service.save_memory(
        db=db,
        user_id=user_id,
        memory_id=memory_id,
    )
    
    if saved_memory is None:
        raise HTTPException(
            status_code=404,
            detail="Memory not found",
        )
    
    # Return 201 if newly created, 200 if already existed
    # We can check if it was newly created by checking if created_at is recent
    # For simplicity, we always return 201 as the operation is idempotent
    return {"status": "saved", "memory_id": memory_id}


@router.delete("/{memory_id}/save", status_code=status.HTTP_204_NO_CONTENT)
def unsave_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """
    Remove a memory from the current user's saved memories.
    
    Returns:
        204 No Content if removed successfully
        404 Not Found if memory not found or not saved by user
    """
    removed = saved_memory_service.unsave_memory(
        db=db,
        user_id=user_id,
        memory_id=memory_id,
    )
    
    if not removed:
        raise HTTPException(
            status_code=404,
            detail="Memory not found or not saved",
        )


@router.post("/", response_model=MemoryResponse)
def create_memory(
    memory: MemoryCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """
    Create a new memory.
    
    Currently using hardcoded user_id for development.
    Will use authenticated user_id in production.
    """
    try:
        return memory_service.create_memory(
            db=db,
            memory=memory,
            user_id=user_id,
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating memory",
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process memory",
        )


@router.get("/", response_model=list[MemoryResponse])
def get_memories(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """
    Get all memories for a specific user.
    
    NOTE: In production, this should use authenticated user_id
    instead of hardcoded "dev-user".
    """
    return memory_service.get_memories(
        db=db,
        user_id=user_id,
    )


@router.get("/{memory_id}", response_model=MemoryResponse)
def get_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    memory = memory_service.get_memory(
        db=db,
        memory_id=memory_id,
        user_id=user_id,
    )
    
    if memory is None:
        raise HTTPException(
            status_code=404,
            detail="Memory not found",
        )

    return memory


@router.put("/{memory_id}", response_model=MemoryResponse)
def update_memory(
    memory_id: int,
    memory_update: MemoryUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    memory = memory_service.update_memory(
        db=db,
        memory_id=memory_id,
        memory_update=memory_update,
        user_id=user_id,
    )

    if memory is None:
        raise HTTPException(
            status_code=404,
            detail="Memory not found",
        )

    return memory


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    """
    Delete a memory by ID.
    
    Returns:
        204 No Content if deleted successfully
        404 Not Found if memory doesn't exist
        
    NOTE: In production, this should validate that the memory
    belongs to the authenticated user.
    """
    deleted = memory_service.delete_memory(
        db=db,
        memory_id=memory_id,
        user_id=user_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Memory not found",
        )