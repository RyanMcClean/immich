from __future__ import annotations

from pydantic import BaseModel
from uuid import UUID

from immich_cli.immich_api.enums import AlbumUserRole


class AlbumUserCreateDto(BaseModel):
    role: AlbumUserRole
    userId: UUID
