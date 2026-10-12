from __future__ import annotations

from pydantic import BaseModel


class SearchFacetResponseDto(BaseModel):
    counts: list["SearchFacetCountResponseDto"]
    fieldName: str


from immich_cli.immich_api.dtos import SearchFacetCountResponseDto
