from __future__ import annotations

from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SearchAssetsMetadataRequestDto(BaseModel):
    albumIds: Optional[list[UUID]] = None
    checksum: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    createdAfter: Optional[datetime] = None
    createdBefore: Optional[datetime] = None
    description: Optional[str] = None
    encodedVideoPath: Optional[str] = None
    id: Optional[UUID] = None
    isEncoded: Optional[bool] = None
    isFavorite: Optional[bool] = None
    isMotion: Optional[bool] = None
    isNotInAlbum: Optional[bool] = None
    isOffline: Optional[bool] = None
    lensModel: Optional[str] = None
    libraryId: Optional[UUID] = None
    make: Optional[str] = None
    model: Optional[str] = None
    ocr: Optional[str] = None
    order: Optional["AssetOrder"] = None
    originalFilename: Optional[str] = None
    originalPath: Optional[str] = None
    page: Optional[int] = None
    personIds: Optional[UUID] = None
    previewPath: Optional[str] = None
    rating: Optional[int] = None
    size: Optional[int] = None
    state: Optional[str] = None
    tagIds: Optional[list[UUID]] = None
    takenAfter: Optional[datetime] = None
    takenBefore: Optional[datetime] = None
    thumbnailPath: Optional[str] = None
    trashedAfter: Optional[datetime] = None
    trashedBefore: Optional[datetime] = None
    type: Optional["AssetTypeEnum"] = None
    updatedAfter: Optional[datetime] = None
    updatedBefore: Optional[datetime] = None
    visibility: Optional["AssetVisibility"] = None
    withDeleted: Optional[bool] = None
    withExif: Optional[bool] = None
    withPeople: Optional[bool] = None
    withStacked: Optional[bool] = None


from immich_cli.immich_api.enums import AssetOrder, AssetTypeEnum, AssetVisibility
