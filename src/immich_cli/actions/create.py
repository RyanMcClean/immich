from argparse import Namespace
import logging
from typing import Any
from concurrent.futures import Future
from time import sleep

import concurrent.futures
from logging import Logger

from requests import Response

from immich_cli.actions.upload_pipeline import (
    FileOutcome,
    finalize_file,
    log_summary,
    upload_and_verify_file,
    verified_assets,
    wrap_audio_file_and_hash,
    delete_verified_assets,
    POSITIVE_STATUSES,
)
from immich_cli.helpers.helpers import list_files_recursive, add_to_album
from immich_cli.helpers.mime_types import get_asset_type, is_supported_type
from immich_cli.immich_api.immich_class import Immich
from immich_cli.immich_api.dtos import (
    TagResponseDto,
    AlbumResponseDto,
    AssetResponseDto,
)

logger: Logger = logging.getLogger(__name__)

#############################################
# Pick action based on user selected object #
#############################################


def create(args: Namespace, config: dict) -> None:
    """Pick a create action based on the user-selected object."""
    if hasattr(args, "object"):
        match args.object:
            case "asset":
                create_asset(args, config)

            case "album":
                create_album()

            case "tag":
                create_tag()

            case _:
                raise ValueError


#######################
# Create/Upload asset #
#######################


def create_asset(args: Namespace, config: dict) -> None:
    """
    Upload every supported file under args.file_path,
    verify each against its server-reported checksum,
    and optionally tag/album/delete on success.
    """
    immich = Immich(config["BASE_URL"], config["API_KEY"])

    tags_to_apply: list[str] = []
    albums_to_add_to: list[str] = []
    tags: list[TagResponseDto] = immich.get_tags()
    albums: list[AlbumResponseDto] = immich.get_albums()
    outcomes: list[FileOutcome] = []

    if hasattr(args, "search_tag") and args.search_tag:
        for search_tag in args.search_tag:
            tags_to_apply = [
                tag.value for tag in tags if search_tag.lower() in tag.value.lower()
            ]
            if len(tags_to_apply) < 1:
                logger.error(f"No tags were found when searching for '{search_tag}'")
                exit(0)

        check: str = ""
        while len(check) < 1 or (check.lower()[0] != "y" and check.lower()[0] != "n"):
            check = input(
                "Search tag was selected\nBefore proceeding confirm the found tag(s) are correct:"
                + f"\n{tags_to_apply}\n(yes/no)\n"
            )
            if check.lower()[0] == "n":
                exit(0)

    if hasattr(args, "search_album") and args.search_album:
        for search_album in args.search_album:
            albums_to_add_to = [
                album.albumName
                for album in albums
                if search_album.lower() in album.albumName.lower()
            ]
            if len(albums_to_add_to) < 1:
                logger.error(
                    f"No albums were found when searching for '{search_album}'"
                )
                exit(0)

        check: str = ""
        while len(check) < 1 or (check.lower()[0] != "y" and check.lower()[0] != "n"):
            check = input(
                "Search album was selected\nBefore proceeding confirm the found album(s) are correct:"
                + f"\n{albums_to_add_to}\n(yes/no)\n"
            )
            if check.lower()[0] == "n":
                exit(0)

    logger.info("Collecting file list")
    files_to_upload: list[str] = list_files_recursive(args.file_path)
    logger.info(f"Total files: {len(files_to_upload)}")

    # wrapped_path -> original_path, and original_path -> hash of the original
    # taken before it was wrapped, so the original can be safely re-verified
    # right before it's deleted.
    audio_originals: dict[str, str] = {}
    audio_original_hashes: dict[str, str] = {}

    if args.convert_audio:
        audio_files: list[str] = [
            x for x in files_to_upload if get_asset_type(x) == "audio"
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            audio_futures: set[Future[Any]] = {
                executor.submit(wrap_audio_file_and_hash, x, args) for x in audio_files
            }

            for finished in concurrent.futures.as_completed(audio_futures):
                wrapped_path, original_path, original_hash = finished.result()
                files_to_upload.append(wrapped_path)
                audio_originals[wrapped_path] = original_path
                audio_original_hashes[original_path] = original_hash

    files_to_upload: list[str] = [x for x in files_to_upload if is_supported_type(x)]

    try:
        for num, file in enumerate(sorted(files_to_upload)):
            logger.info("")
            logger.info(f"{num + 1}/{len(files_to_upload)}")
            outcome: FileOutcome = upload_and_verify_file(immich, file)
            outcome = finalize_file(
                outcome, args, audio_originals, audio_original_hashes, tags, immich
            )
            outcomes.append(outcome)
            sleep(args.delay)

    except KeyboardInterrupt:
        logger.warning("Interrupted; finalizing results gathered so far")
        raise
    finally:
        verified: list[AssetResponseDto] = verified_assets(outcomes)
        if args.album and verified:
            logger.info(f"Adding all uploaded files to album: '{args.album}'")
            _: list[AlbumResponseDto] = add_to_album(
                args.album, albums, verified, immich
            )

        if args.tag and verified:

            for tag_name in args.tag:
                logger.info(f"Adding tag ({tag_name}) to all uploaded files")
                tag: TagResponseDto = immich.post_tag(tag_name)
                _: Response = immich.tag_asset(tag, verified)

        if hasattr(args, "search_tag") and args.search_tag:
            for tag_name in tags_to_apply:
                logger.info(f"Adding tag ({tag_name}) to all uploaded files")
                tag: TagResponseDto = immich.post_tag(tag_name)
                _: Response = immich.tag_asset(tag, verified)

        if hasattr(args, "search_album") and args.search_album:
            for album_name in albums_to_add_to:
                logger.info(f"Adding album ({album_name}) to all uploaded files")
                _: list[AlbumResponseDto] = add_to_album(
                    album_name, albums, verified, immich
                )

        if args.delete:
            logger.info(f"Removing {len([outcome for outcome in outcomes
                            if outcome.status in POSITIVE_STATUSES])} files")
            outcomes = delete_verified_assets(
                outcomes, audio_originals, audio_original_hashes
            )
        log_summary(outcomes)

    logger.info("Finished uploading files")


################
# Create album #
################


# TODO
def create_album():
    raise NotImplementedError


##############
# Create tag #
##############

# TODO


def create_tag():
    raise NotImplementedError
