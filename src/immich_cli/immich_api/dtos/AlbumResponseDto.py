from __future__ import annotations

from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class AlbumResponseDto(BaseModel):
    albumName: str
    albumThumbnailAssetId: Optional[UUID] = None
    albumUsers: list["AlbumUserResponseDto"]
    assetCount: int
    contributorCounts: Optional[list["ContributorCountResponseDto"]] = None
    createdAt: datetime
    description: str
    endDate: Optional[datetime] = None
    hasSharedLink: bool
    id: UUID
    isActivityEnabled: bool
    lastModifiedAssetTimestamp: Optional[datetime] = None
    order: Optional["AssetOrder"] = None
    shared: bool
    startDate: Optional[datetime] = None
    updatedAt: datetime


from immich_cli.immich_api.dtos import AlbumUserResponseDto, ContributorCountResponseDto

from immich_cli.immich_api.enums import AssetOrder
