from __future__ import annotations

from pydantic import BaseModel
from uuid import UUID


class ContributorCountResponseDto(BaseModel):
    assetCount: int
    userId: UUID
