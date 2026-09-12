from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    occurred_at: Optional[datetime] = None

    # These fields are NOT allowed to be updated
    # - id: immutable (database primary key)
    # - user_id: immutable (user isolation - cannot change ownership)
    # - created_at: immutable (record creation timestamp)
    # - source: immutable through update (use create endpoint instead)

    model_config = ConfigDict(from_attributes=True)
