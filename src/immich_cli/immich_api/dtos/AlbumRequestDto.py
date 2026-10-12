from __future__ import annotations

from pydantic import BaseModel
from uuid import UUID

from immich_cli.immich_api.dtos import AlbumUserCreateDto


class AlbumRequestDto(BaseModel):
    albumName: str
    albumUsers: list[AlbumUserCreateDto]
    assetIds: list[UUID]
    description: str
