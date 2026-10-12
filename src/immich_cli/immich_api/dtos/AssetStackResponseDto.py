from __future__ import annotations

from pydantic import BaseModel


class AssetStackResponseDto(BaseModel):
    assetCount: int
    id: str
    primaryAssetId: str
