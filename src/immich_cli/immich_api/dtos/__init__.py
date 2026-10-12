# File: immich_cli.immich_api/dtos/__init__.py

"""
DTO package - explicit exports for all DTO classes.

Usage:
    from immich_cli.immich_api.dtos import AssetResponseDto, TagResponseDto
"""

# Non dto dependant
from .TagResponseDto import TagResponseDto
from .AlbumUserCreateDto import AlbumUserCreateDto
from .AssetMediaResponseDto import AssetMediaResponseDto
from .AssetStackResponseDto import AssetStackResponseDto
from .ContributorCountResponseDto import ContributorCountResponseDto
from .ExifResponseDto import ExifResponseDto
from .PersonResponseDto import PersonResponseDto
from .TagRequestDto import TagRequestDto
from .UserResponseDto import UserResponseDto
from .SearchFacetCountResponseDto import SearchFacetCountResponseDto
from .SearchAssetsMetadataRequestDto import SearchAssetsMetadataRequestDto

# Single dto dependant
from .AlbumRequestDto import AlbumRequestDto
from .AlbumUserResponseDto import AlbumUserResponseDto
from .SearchFacetResponseDto import SearchFacetResponseDto

# Multi dto dependant
from .AssetResponseDto import AssetResponseDto
from .AlbumResponseDto import AlbumResponseDto
from .SearchAlbumResponseDto import SearchAlbumResponseDto
from .SearchAssetResponseDto import SearchAssetResponseDto
from .SearchMetadataResponseDto import SearchMetadataResponseDto

# Re-exported for convenience since AssetResponseDto.visibility uses it
from immich_cli.immich_api.enums import AssetVisibility

__all__ = [
    "SearchFacetCountResponseDto",
    "SearchAssetsMetadataRequestDto",
    "SearchFacetResponseDto",
    "AssetMediaResponseDto",
    "AssetResponseDto",
    "AssetStackResponseDto",
    "AlbumRequestDto",
    "AlbumUserResponseDto",
    "AlbumUserCreateDto",
    "AlbumResponseDto",
    "ContributorCountResponseDto",
    "ExifResponseDto",
    "PersonResponseDto",
    "TagResponseDto",
    "TagRequestDto",
    "UserResponseDto",
    "AssetVisibility",
    "SearchAlbumResponseDto",
    "SearchAssetResponseDto",
    "SearchMetadataResponseDto",
]
