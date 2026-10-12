from __future__ import annotations

from pydantic import BaseModel


class SearchFacetCountResponseDto(BaseModel):
    count: int
    value: str
