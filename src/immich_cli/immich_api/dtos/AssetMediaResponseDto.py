from __future__ import annotations

from pydantic import BaseModel
from uuid import UUID

from immich_cli.immich_api.enums import AssetMediaStatus


class AssetMediaResponseDto(BaseModel):
    id: UUID
    status: AssetMediaStatus
