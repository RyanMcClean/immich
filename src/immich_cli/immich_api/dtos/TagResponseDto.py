from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class TagResponseDto(BaseModel):
    color: Optional[str] = None
    createdAt: datetime
    id: UUID
    name: str
    parentId: Optional[str] = None
    updatedAt: datetime
    value: str
