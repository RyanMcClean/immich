from argparse import Namespace
import logging
from logging import Logger

from immich_cli.immich_api.immich_class import Immich
from immich_cli.immich_api.dtos import (
    AlbumResponseDto,
    SearchAssetsMetadataRequestDto,
    SearchAssetResponseDto,
    SearchMetadataResponseDto,
)

logger: Logger = logging.getLogger(__name__)


def download(args: Namespace, config: dict) -> None:
    """Pick a download action based on the user-selected object/type."""
    match args.object:
        case "asset":

            match args.type:
                case "single":
                    pass  # TODO: not yet implemented

                case "album":
                    download_album(args, config)

        case _:
            pass


def download_album(args: Namespace, config: dict) -> None:
    """Downloads all assets from an album

    Args:
        args (Namespace): Program args
        config (dict): Program config
    """
    immich = Immich(config["BASE_URL"], config["API_KEY"])

    albums: list[AlbumResponseDto] = immich.get_albums()

    logger.debug(albums)

    selected_album: AlbumResponseDto = next(
        album for album in albums if args.name == album.albumName
    )

    search_query = SearchAssetsMetadataRequestDto(albumIds=[selected_album.id])

    search_result: SearchMetadataResponseDto = immich.search_metadata(search_query)

    asset_results: SearchAssetResponseDto = search_result.assets

    logger.debug(asset_results.model_dump())

    while asset_results.nextPage:
        logger.info(f"Downloading asset list, page {asset_results.nextPage}")
        search_query = SearchAssetsMetadataRequestDto(
            albumIds=[selected_album.id], page=int(asset_results.nextPage)
        )
        logger.debug(search_query.model_dump())
        search_result: SearchMetadataResponseDto = immich.search_metadata(search_query)

        asset_results.items.extend(search_result.assets.items)
        asset_results.nextPage: str | None = search_result.assets.nextPage  # type: ignore[misc]

    for asset in asset_results.items:
        if immich.download_asset(asset, f"{args.output}{args.name}/"):
            logger.info("File downloaded")
        else:
            logger.error(f"Error downloading file: {asset.id}")

    logger.info(f"Finished downloading: {len(asset_results.items)} assets")
