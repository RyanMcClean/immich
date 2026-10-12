from __future__ import annotations

from pydantic import BaseModel


class SearchAlbumResponseDto(BaseModel):
    count: int
    facets: list["SearchFacetResponseDto"]
    items: list["AlbumResponseDto"]
    total: int


from immich_cli.immich_api.dtos import AlbumResponseDto, SearchFacetResponseDto
