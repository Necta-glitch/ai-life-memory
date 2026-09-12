from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class MemoryCreate(BaseModel):
    content: str
    source: str = "text"
    occurred_at: datetime | None = None


class MemoryResponse(BaseModel):
    id: int
    user_id: str
    content: str
    summary: str | None = None
    topics: list[Any] | None = None
    entities: list[Any] | None = None
    source: str
    created_at: datetime
    occurred_at: datetime | None

    model_config = ConfigDict(from_attributes=True)