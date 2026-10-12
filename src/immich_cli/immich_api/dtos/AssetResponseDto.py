from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

from typing import Optional


class AssetResponseDto(BaseModel):

    # Required fields
    checksum: str
    createdAt: datetime
    fileCreatedAt: datetime
    fileModifiedAt: datetime
    hasMetadata: bool
    id: UUID
    isArchived: bool
    isEdited: bool
    isFavorite: bool
    isOffline: bool
    isTrashed: bool
    localDateTime: datetime
    originalFileName: str
    originalMimeType: str
    originalPath: str
    ownerId: str
    resized: bool  # Deprecated
    updatedAt: datetime
    visibility: "AssetVisibility"

    # Optional fields
    owner: Optional["UserResponseDto"] = None
    stack: Optional["AssetStackResponseDto"] = None
    people: Optional[list["PersonResponseDto"]] = None
    exifInfo: Optional["ExifResponseDto"] = None
    duplicateId: Optional[UUID] = None
    duration: Optional[int] = None
    height: Optional[int] = None
    libraryId: Optional[UUID] = None
    livePhotoVideoId: Optional[str] = None
    thumbHash: Optional[str] = None
    width: Optional[int] = None


from immich_cli.immich_api.dtos import (
    ExifResponseDto,
    UserResponseDto,
    PersonResponseDto,
    AssetStackResponseDto,
)

from immich_cli.immich_api.enums import AssetVisibility
