from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class SearchAssetResponseDto(BaseModel):
    count: int
    facets: list["SearchFacetResponseDto"]
    items: list["AssetResponseDto"]
    nextPage: Optional[str] = None
    total: int  # Deprecated


from immich_cli.immich_api.dtos import SearchFacetResponseDto, AssetResponseDto
