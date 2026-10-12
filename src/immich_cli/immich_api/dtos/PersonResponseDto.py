from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PersonResponseDto(BaseModel):
    birthDate: Optional[datetime] = None
    color: Optional[str] = None
    id: str
    isFavorite: Optional[bool]
    isHidden: bool
    name: str
    thumbnailPath: str
    updatedAt: Optional[datetime]
