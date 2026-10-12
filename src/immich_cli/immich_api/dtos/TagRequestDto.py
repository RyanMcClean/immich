from __future__ import annotations

from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class TagRequestDto(BaseModel):
    color: Optional[str] = None
    name: str
    parentId: Optional[UUID] = None
