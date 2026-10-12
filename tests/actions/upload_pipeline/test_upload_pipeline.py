# from argparse import Namespace
# from unittest.mock import MagicMock
# from pathlib import Path
# from typing import Never
# from datetime import datetime
# from uuid import UUID

# import requests

# from immich_cli.actions.upload_pipeline import (
#     FileOutcome,
#     FileStatus,
#     delete_audio_original_if_safe,
#     summarize_outcomes,
#     upload_and_verify_file,
#     verified_assets,
#     delete_verified_assets, AudioOriginalOutcome
# )
# from tests.conftest import mock_asset_info, mock_asset_response
# from immich_cli.helpers.helpers import compute_file_hash
# from immich_cli.immich_api.exceptions import EmptyFileError
# from immich_cli.immich_api.dtos import AssetResponseDto
# from immich_cli.immich_api.enums import AssetVisibility

# def test_hash_match_uploads_and_verifies(tmp_path) -> None:
#     file_path: Path = tmp_path / "a.jpg"
#     file_path.write_bytes(b"hello world")

#     immich = MagicMock()
#     immich.upload_file.return_value = mock_asset_response("created")

#     local_hash: str = compute_file_hash(str(file_path))
#     immich.get_asset_info.return_value = mock_asset_info(local_hash)

#     outcome: FileOutcome = upload_and_verify_file(immich, str(file_path))

#     assert outcome.status is FileStatus.UPLOADED_VERIFIED
#     assert outcome.local_checksum == local_hash


# def test_hash_mismatch_preserves_file(tmp_path) -> None:
#     file_path: Path = tmp_path / "a.jpg"
#     file_path.write_bytes(b"hello world")

#     immich = MagicMock()
#     immich.upload_file.return_value = mock_asset_response("created")
#     immich.get_asset_info.return_value = mock_asset_info("wrong-checksum")

#     outcome: FileOutcome = upload_and_verify_file(immich, str(file_path))

#     assert outcome.status is FileStatus.HASH_MISMATCH
#     assert file_path.exists()


# def test_upload_error_preserves_file(tmp_path) -> None:
#     file_path: Path = tmp_path / "a.jpg"
#     file_path.write_bytes(b"hello world")

#     immich = MagicMock()
#     immich.upload_file.side_effect = requests.RequestException("boom")

#     outcome: FileOutcome = upload_and_verify_file(immich, str(file_path))

#     assert outcome.status is FileStatus.UPLOAD_FAILED
#     assert file_path.exists()


# def test_verify_error_preserves_file(tmp_path) -> None:
#     file_path: Path = tmp_path / "a.jpg"
#     file_path.write_bytes(b"hello world")

#     immich = MagicMock()
#     immich.upload_file.return_value = mock_asset_response("created")
#     immich.get_asset_info.side_effect = requests.RequestException("boom")

#     outcome: FileOutcome = upload_and_verify_file(immich, str(file_path))

#     assert outcome.status is FileStatus.VERIFY_FAILED
#     assert file_path.exists()


# def test_empty_file_preserves_file(tmp_path) -> None:
#     file_path = tmp_path / "empty.jpg"
#     file_path.write_bytes(b"")

#     immich = MagicMock()
#     immich.upload_file.side_effect = EmptyFileError("empty")

#     outcome: FileOutcome = upload_and_verify_file(immich, str(file_path))

#     assert outcome.status is FileStatus.EMPTY_FILE
#     assert file_path.exists()


# def test_duplicate_status_is_still_eligible_for_deletion(tmp_path) -> None:
#     file_path: Path = tmp_path / "a.jpg"
#     file_path.write_bytes(b"hello world")

#     immich = MagicMock()
#     immich.upload_file.return_value = mock_asset_response("duplicate")

#     local_hash: str = compute_file_hash(str(file_path))
#     immich.get_asset_info.return_value = mock_asset_info(local_hash)

#     outcome: list[FileOutcome] = [upload_and_verify_file(immich, str(file_path))]
#     assert outcome[0].status is FileStatus.DUPLICATE

#     delete_verified_assets(outcome, {}, {})
#     assert not file_path.exists()


# def test_finalize_deletes_only_on_positive_status(tmp_path) -> None:
#     file_path = tmp_path / "a.jpg"
#     file_path.write_bytes(b"hello world")

#     outcome: list[FileOutcome] = [FileOutcome(file=str(file_path), status=FileStatus.HASH_MISMATCH)]
#     delete_verified_assets(outcome, {}, {})

#     assert file_path.exists()
#     assert not outcome[0].deleted


# def test_finalize_marks_delete_failed_on_os_error(tmp_path, monkeypatch) -> None:
#     import immich_cli.actions.upload_pipeline as pipeline

#     file_path: Path = tmp_path / "a.jpg"
#     file_path.write_bytes(b"hello world")

#     def raise_permission_error(_path) -> Never:
#         raise PermissionError("no")

#     monkeypatch.setattr(pipeline.os, "remove", raise_permission_error)

#     outcome: list[FileOutcome] = [
#         FileOutcome(file=str(file_path),
#         status=FileStatus.UPLOADED_VERIFIED,
#         asset_info=AssetResponseDto(
#                 checksum="000",
#                 createdAt=datetime.now(),
#                 fileCreatedAt=datetime.now(),
#                 fileModifiedAt=datetime.now(),
#                 hasMetadata=False,
#                 id=UUID(int=1234567891234567),
#                 isArchived=False,
#                 isEdited=False,
#                 isFavorite=False,
#                 isOffline=False,
#                 isTrashed=False,
#                 localDateTime=datetime.now(),
#                 originalFileName="test",
#                 originalMimeType="test",
#                 originalPath="test",
#                 ownerId="test",
#                 resized=False,
#                 updatedAt=datetime.now(),
#                 visibility=AssetVisibility.timeline
#             )
#         )
#     ]
#     result: list[FileOutcome] = delete_verified_assets(outcome, {}, {})

#     assert result[0].status is FileStatus.DELETE_FAILED
#     assert not result[0].deleted
#     assert file_path.exists()


# def test_verified_assets_excludes_negative_outcomes() -> None:
#     good = FileOutcome(file="good", status=FileStatus.UPLOADED_VERIFIED, asset_info=mock_asset_info("x"))
#     bad = FileOutcome(file="bad", status=FileStatus.HASH_MISMATCH, asset_info=mock_asset_info("y"))

#     result: list[AssetResponseDto] = verified_assets([good, bad])

#     assert result == [good.asset_info]


# def test_audio_original_deleted_when_unchanged(tmp_path) -> None:
#     original: Path = tmp_path / "song.wav"
#     original.write_bytes(b"audio bytes")

#     pre_wrap_hash: str = compute_file_hash(str(original))

#     outcome: AudioOriginalOutcome = delete_audio_original_if_safe(str(original), pre_wrap_hash)

#     assert outcome.deleted
#     assert not original.exists()


# def test_audio_original_preserved_when_changed_since_wrap(tmp_path) -> None:
#     original: Path = tmp_path / "song.wav"
#     original.write_bytes(b"audio bytes")

#     stale_hash = "not-the-real-hash"

#     outcome: AudioOriginalOutcome = delete_audio_original_if_safe(str(original), stale_hash)

#     assert not outcome.deleted
#     assert outcome.skipped_reason == "hash changed since wrap"
#     assert original.exists()


# def test_summarize_outcomes_groups_by_status() -> None:
#     outcomes: list[FileOutcome] = [
#         FileOutcome(file="a", status=FileStatus.UPLOADED_VERIFIED),
#         FileOutcome(file="b", status=FileStatus.UPLOADED_VERIFIED),
#         FileOutcome(file="c", status=FileStatus.HASH_MISMATCH),
#     ]

#     grouped: dict[FileStatus, list[FileOutcome]] = summarize_outcomes(outcomes)

#     assert len(grouped[FileStatus.UPLOADED_VERIFIED]) == 2
#     assert len(grouped[FileStatus.HASH_MISMATCH]) == 1
