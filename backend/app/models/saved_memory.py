from datetime import datetime, UTC
from sqlalchemy import DateTime, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SavedMemory(Base):
    __tablename__ = "saved_memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    memory_id: Mapped[int] = mapped_column(
        ForeignKey("memories.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    # Relationship to Memory model
    memory: Mapped["Memory"] = relationship("Memory", lazy="joined")

    # Unique constraint to prevent duplicate saves by same user
    __table_args__ = (
        UniqueConstraint("user_id", "memory_id", name="uq_user_memory"),
        Index("ix_saved_memories_user_created_at", "user_id", "created_at"),
    )