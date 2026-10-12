from argparse import Namespace
import os
import subprocess
import logging
from logging import Logger
import hashlib
import base64
from subprocess import CompletedProcess

from immich_cli.blurry_image_detection.blurry_detect import is_blurry
from immich_cli.immich_api.immich_class import Immich
from immich_cli.immich_api.dtos import (
    AssetResponseDto,
    AssetMediaResponseDto,
    AlbumResponseDto,
    TagResponseDto,
)

logger: Logger = logging.getLogger(__name__)

BLURRY_TAGS: list[str] = [
    "Probably Blurry",
    "Likely Blurry",
    "Maybe Blurry",
    "Likely Not Blurry",
    "Probably Not Blurry",
]

# (variance threshold, tag to apply when variance exceeds it), checked in order;
# falls through to "Probably Blurry" if none match.
BLUR_VARIANCE_THRESHOLDS: list[tuple[int, str]] = [
    (80, "Probably Not Blurry"),
    (60, "Likely Not Blurry"),
    (40, "Maybe Blurry"),
    (20, "Likely Blurry"),
]


def list_files_recursive(path=".") -> list[str]:
    """Generate a list from all of the file, and sub-directories from the file path given

    Args:
        path (str, optional): Path to files you want to list. Defaults to '.'.

    Returns:
        list[str]: A list of all the files in the directory and sub-directories
    """
    to_return: list[str] = []
    if os.path.isdir(path):
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                to_return.extend(list_files_recursive(full_path))
            else:
                to_return.append(full_path)
    elif os.path.isfile(path):
        to_return: list[str] = [path]
    else:
        raise ValueError(f"The provide path is invalid: {path}")

    return to_return


def tag_blurry_images(
    tags: list[TagResponseDto],
    file: str,
    asset_info: list[AssetResponseDto] | list[AssetMediaResponseDto],
    immich: Immich,
) -> list[TagResponseDto]:
    """Tag blurry images, currently another WIP

    Args:
        tags (list[TagResponseDto]): A list of tags on the Immich server
        file (str): The file to tag
        asset_info (AssetResponseDto | AssetMediaResponseDto): The asset model that is being tagged
        immich (Immich): Immich class

    Returns:
        list[TagResponseDto]: Returns an updated list of tags, in-case tags were created in this run
    """
    for blurry_tag in BLURRY_TAGS:
        if not any(blurry_tag == tag.name for tag in tags):
            tag: TagResponseDto = immich.post_tag(blurry_tag)
            tags.append(tag)

    variance: int = is_blurry(file)

    tag_name = "Probably Blurry"
    for threshold, candidate_tag_name in BLUR_VARIANCE_THRESHOLDS:
        if variance > threshold:
            tag_name = candidate_tag_name
            break

    logger.info(f"Adding tag '{tag_name}' to {file}")
    tag = next(x for x in tags if x.name == tag_name)
    immich.tag_asset(tag, asset_info)

    return tags


def add_to_album(
    album: str,
    albums: list[AlbumResponseDto],
    asset_info: list[AssetResponseDto] | list[AssetMediaResponseDto],
    immich: Immich,
) -> list[AlbumResponseDto]:
    """Adds asset(s) to an album

    Args:
        album (str): Album name to add assets to
        albums (list[AlbumResponseDto]): List of album models from Immich server
        asset_info (list[AssetResponseDto] | list[AssetMediaResponseDto]): Asset model
        immich (Immich): Immich class

    Returns:
        list[AlbumResponseDto]: Returns a list of albums, in-case an album has been created via this function
    """
    album_response: AlbumResponseDto | None = None

    logger.info(f"Tagging {len([asset for asset in asset_info])} assets")

    if not any(
        album.lower().strip() == existing_album.albumName.lower().strip()
        for existing_album in albums
    ):
        album_response = immich.post_album(album)
        albums.append(album_response)

    if album_response is None:
        album_response = next(
            x for x in albums if x.albumName.lower().strip() == album.lower().strip()
        )

    immich.add_asset_to_album(album_response, asset_info)
    return albums


def wrap_audio_file(file_path: str, args: Namespace) -> str:
    """Use ffmpeg to wrap audio files in an mp4 container so it can be uploaded to immich

    Args:
        file_path (str): file path to audio file

    Returns:
        str: file path to wrapped audio file
    """

    file_name: str = file_path.split("/")[-1]
    logger.info(f"Wrapping audio file: {file_name}")

    if ".wma" not in file_path and ".wav" not in file_path:
        codec = "copy"
    elif ".mid" in file_path:
        logger.info(f"{file_path} is a midi file, cannot be converted")
        return ""
    else:
        codec = "aac"

    process: CompletedProcess[bytes] = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error" if not args.verbose else "info",
            "-nostdin",
            "-y",
            "-i",
            f"{file_path}",
            "-map",
            "0:a",
            "-c:a",
            codec,
            "-c:v",
            codec,
            "-map_metadata",
            "0:g",
            "-movflags",
            "use_metadata_tags",
            f"{file_path}.mp4",
        ]
    )

    if process.returncode != 0:
        logger.error("ffmpeg failed")
        logger.error(f"{process.stderr}")
        subprocess.run(["stty", "sane"])
        raise SystemExit(1)

    logger.info(f"Finished wrapping audio file: {file_name}")

    return f"{file_path}.mp4"


def compute_file_hash(file_path: str, algo: str = "sha1") -> str:
    """Compute sha1 hash of file, in keeping with how immich hashes files

    Args:
        file_path (str): Path to file to hash
        algo (str, optional): hashing algorithm Defaults to "sha1".

    Returns:
        str: base64-encoded digest of the file's contents
    """

    hash_func = hashlib.new(algo)

    logger.debug("Starting hash")

    with open(file_path, "rb") as file:
        while chunk := file.read(8192):
            hash_func.update(chunk)

    logger.debug("Finished hash")

    return_var: str = base64.b64encode(hash_func.digest()).decode("utf-8")
    return return_var
