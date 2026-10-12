from __future__ import annotations

from pydantic import BaseModel


class SearchMetadataResponseDto(BaseModel):
    albums: "SearchAlbumResponseDto"
    assets: "SearchAssetResponseDto"


from immich_cli.immich_api.dtos import SearchAlbumResponseDto, SearchAssetResponseDto
