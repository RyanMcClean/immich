from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class ExifResponseDto(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None
    dateTimeOriginal: Optional[datetime] = None
    description: Optional[str] = None
    exifImageHeight: Optional[int] = None
    exifImageWidth: Optional[int] = None
    exposureTime: Optional[str] = None
    fNumber: Optional[float] = None
    fileSizeInByte: Optional[int] = None
    focalLength: Optional[float] = None
    iso: Optional[int] = None
    latitude: Optional[float] = None
    lensModel: Optional[str] = None
    longitude: Optional[float] = None
    make: Optional[str] = None
    model: Optional[str] = None
    modifyDate: Optional[datetime] = None
    orientation: Optional[str] = None
    projectionType: Optional[str] = None
    rating: Optional[int] = None
    state: Optional[str] = None
    timeZone: Optional[str] = None
