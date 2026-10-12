from __future__ import annotations

from pydantic import BaseModel

from immich_cli.immich_api.enums import AlbumUserRole


class AlbumUserResponseDto(BaseModel):
    role: AlbumUserRole
    user: "UserResponseDto"


from immich_cli.immich_api.dtos import UserResponseDto
