from argparse import Namespace
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import logging
import os
from logging import Logger
import concurrent.futures

import requests

from immich_cli.helpers.helpers import (
    compute_file_hash,
    wrap_audio_file,
    tag_blurry_images,
)
from immich_cli.immich_api.enums import AssetMediaStatus
from immich_cli.immich_api.exceptions import EmptyFileError
from immich_cli.immich_api.immich_class import Immich
from immich_cli.immich_api.dtos import (
    AssetResponseDto,
    TagResponseDto,
    AssetMediaResponseDto,
)

logger: Logger = logging.getLogger(__name__)


class FileStatus(Enum):
    UPLOADED_VERIFIED = "uploaded_verified"
    DUPLICATE = "duplicate"
    HASH_MISMATCH = "hash_mismatch"
    EMPTY_FILE = "empty_file"
    UPLOAD_FAILED = "upload_failed"
    VERIFY_FAILED = "verify_failed"
    DELETE_FAILED = "delete_failed"


# The only statuses eligible for deletion, tagging, or being added to an album.
POSITIVE_STATUSES = (FileStatus.UPLOADED_VERIFIED, FileStatus.DUPLICATE)

# Statuses that mean the file was left on disk and needs the user's attention.
NEEDS_ATTENTION_STATUSES = (
    FileStatus.HASH_MISMATCH,
    FileStatus.EMPTY_FILE,
    FileStatus.UPLOAD_FAILED,
    FileStatus.VERIFY_FAILED,
    FileStatus.DELETE_FAILED,
)


@dataclass
class AudioOriginalOutcome:
    path: str
    deleted: bool
    skipped_reason: str | None = None


@dataclass
class FileOutcome:
    file: str
    status: FileStatus
    asset_info: AssetResponseDto | None = None
    local_checksum: str | None = None
    deleted: bool = False
    audio_original: AudioOriginalOutcome | None = None
    error: str | None = None


def wrap_audio_file_and_hash(file_path: str, args: Namespace) -> tuple[str, str, str]:
    """Hash the original before wrapping it so its integrity can be re-checked later.

    Returns:
        (wrapped_path, original_path, original_pre_wrap_hash)
    """
    original_hash: str = compute_file_hash(file_path)
    wrapped_path: str = wrap_audio_file(file_path, args)
    return wrapped_path, file_path, original_hash


def upload_and_verify_file(immich: Immich, file: str) -> FileOutcome:
    """Upload one file and verify its checksum.

    Never deletes or tags anything, and never lets an exception escape for an
    expected failure mode — every branch returns a FileOutcome with the file
    left on disk.
    """
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    try:
        local_hash_future = executor.submit(compute_file_hash, file)
    except OSError as exc:
        logger.error(f"{file}: could not read file to hash: {exc}")
        return FileOutcome(file=file, status=FileStatus.UPLOAD_FAILED, error=str(exc))

    try:
        asset_response: AssetMediaResponseDto = immich.upload_file(file)
    except EmptyFileError as exc:
        logger.warning(f"{file}: server reports empty file; file preserved, skipping")
        return FileOutcome(
            file=file,
            status=FileStatus.EMPTY_FILE,
            local_checksum=local_hash_future.result(),
            error=str(exc),
        )
    except requests.RequestException as exc:
        logger.error(f"{file}: upload failed, file preserved: {exc}")
        return FileOutcome(
            file=file,
            status=FileStatus.UPLOAD_FAILED,
            local_checksum=local_hash_future.result(),
            error=str(exc),
        )

    try:
        asset_info: AssetResponseDto = immich.get_asset_info(asset_response)
    except requests.RequestException as exc:
        logger.error(f"{file}: could not verify upload, file preserved: {exc}")
        return FileOutcome(
            file=file,
            status=FileStatus.VERIFY_FAILED,
            local_checksum=local_hash_future.result(),
            error=str(exc),
        )

    if local_hash_future.result() != asset_info.checksum:
        logger.error(
            f"{file}: checksum mismatch (local={local_hash_future.result()}, "
            + f"server={asset_info.checksum}); "
            "file preserved"
        )
        return FileOutcome(
            file=file,
            status=FileStatus.HASH_MISMATCH,
            asset_info=asset_info,
            local_checksum=local_hash_future.result(),
        )

    status: FileStatus = (
        FileStatus.DUPLICATE
        if asset_response.status == AssetMediaStatus.duplicate
        else FileStatus.UPLOADED_VERIFIED
    )
    logger.info(
        f"File was {asset_response.status.value}"
        if status is FileStatus.UPLOADED_VERIFIED
        else f"File is a {asset_response.status.value}"
    )
    logger.debug(f"{file}: checksum verified ({status.value})")
    return FileOutcome(
        file=file,
        status=status,
        asset_info=asset_info,
        local_checksum=local_hash_future.result(),
    )


def delete_audio_original_if_safe(
    original_path: str, pre_wrap_hash: str | None
) -> AudioOriginalOutcome:
    """Re-hash the original right before deleting it, and only delete if it's
    byte-identical to what it was when it was wrapped.

    This does NOT prove the wrapped derivative is a lossless copy of the original
    (that guarantee comes from ffmpeg's exit code and Immich's checksum of the
    wrapped file) — it only guarantees the original itself wasn't corrupted,
    truncated, or modified during this run before it's removed.
    """
    if pre_wrap_hash is None:
        return AudioOriginalOutcome(
            path=original_path,
            deleted=False,
            skipped_reason="no pre-wrap hash recorded",
        )

    try:
        current_hash: str = compute_file_hash(original_path)
    except OSError as exc:
        return AudioOriginalOutcome(
            path=original_path,
            deleted=False,
            skipped_reason=f"could not re-hash: {exc}",
        )

    if current_hash != pre_wrap_hash:
        logger.error(
            f"{original_path}: changed since it was wrapped; NOT deleting original"
        )
        return AudioOriginalOutcome(
            path=original_path, deleted=False, skipped_reason="hash changed since wrap"
        )

    try:
        os.remove(original_path)
    except OSError as exc:
        return AudioOriginalOutcome(
            path=original_path, deleted=False, skipped_reason=f"delete failed: {exc}"
        )

    logger.info(
        f"Removed original audio source (verified unmodified since wrap): {original_path}"
    )
    return AudioOriginalOutcome(path=original_path, deleted=True)


def finalize_file(
    outcome: FileOutcome,
    args: Namespace,
    audio_originals: dict[str, str],
    audio_original_hashes: dict[str, str],
    tags: list[TagResponseDto],
    immich: Immich,
) -> FileOutcome:
    """Apply blur-tagging and deletion.

    Deletion invariant: never runs unless outcome.status is a positive checksum
    match — this is the only place in the pipeline that calls os.remove on an
    uploaded file.
    """
    if outcome.status not in POSITIVE_STATUSES:
        return outcome

    if args.tag_blurry:
        try:
            asset_list: list[AssetResponseDto] = (
                [outcome.asset_info] if outcome.asset_info else []
            )
            tag_blurry_images(tags, outcome.file, asset_list, immich)
        except Exception as exc:
            logger.error(f"{outcome.file}: blur-tagging failed (non-fatal): {exc}")

    return outcome


def delete_verified_assets(
    outcomes: list[FileOutcome],
    audio_originals: dict[str, str],
    audio_original_hashes: dict[str, str],
) -> list[FileOutcome]:
    for outcome in [
        o
        for o in outcomes
        if o.status in POSITIVE_STATUSES and o.asset_info is not None
    ]:
        try:
            logger.debug(f"Removing {os.path.basename(outcome.file)}")
            os.remove(outcome.file)
            outcome.deleted = True
        except OSError as exc:
            logger.error(f"{outcome.file}: verified but delete failed: {exc}")
            outcome.status = FileStatus.DELETE_FAILED
            outcome.error = str(exc)

        original_path: str | None = audio_originals.get(outcome.file)
        if original_path:
            outcome.audio_original = delete_audio_original_if_safe(
                original_path, audio_original_hashes.get(original_path)
            )
    return outcomes


def verified_assets(outcomes: list[FileOutcome]) -> list[AssetResponseDto]:
    return [
        o.asset_info
        for o in outcomes
        if o.status in POSITIVE_STATUSES and o.asset_info is not None
    ]


def summarize_outcomes(
    outcomes: list[FileOutcome],
) -> dict[FileStatus, list[FileOutcome]]:
    grouped: dict[FileStatus, list[FileOutcome]] = defaultdict(list)
    for outcome in outcomes:
        grouped[outcome.status].append(outcome)
    return grouped


def log_summary(outcomes: list[FileOutcome]) -> None:
    grouped: dict[FileStatus, list[FileOutcome]] = summarize_outcomes(outcomes)
    deleted: int = sum(1 for o in outcomes if o.deleted)
    logger.info(
        f"Upload run summary: {len(outcomes)} file(s) processed, {deleted} deleted"
    )
    for status, files in grouped.items():
        logger.info(f"  {status.value}: {len(files)}")

    needs_attention: list[FileOutcome] = [
        o for o in outcomes if o.status in NEEDS_ATTENTION_STATUSES
    ]
    if needs_attention:
        logger.warning(
            f"{len(needs_attention)} file(s) preserved on disk and need attention:"
        )
        for o in needs_attention:
            logger.warning(f"  {o.file}: {o.status.value} ({o.error})")
