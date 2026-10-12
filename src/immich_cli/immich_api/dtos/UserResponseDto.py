from __future__ import annotations

from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import Optional


class UserAvatarColor(Enum):
    primary = "primary"
    pink = "pink"
    red = "red"
    yellow = "yellow"
    blue = "blue"
    green = "green"
    purple = "purple"
    orange = "orange"
    gray = "gray"
    amber = "amber"


class UserResponseDto(BaseModel):
    avatarColour: Optional[UserAvatarColor] = None
    email: str
    id: str
    name: str
    profileChangedAt: datetime
    profileImagePath: str
