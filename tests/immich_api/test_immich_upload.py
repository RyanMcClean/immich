import logging
from unittest.mock import MagicMock, patch
from typing import Any, Generator
from pathlib import Path

import pytest
import requests

from immich_cli.immich_api.exceptions import EmptyFileError, ImmichRequestError
from immich_cli.immich_api.immich_class import Immich
from immich_cli.immich_api.dtos import AssetMediaResponseDto, AssetResponseDto

VALID_ID = "11111111-1111-1111-1111-111111111111"


def make_immich() -> Immich:
    """Construct an Immich instance without hitting the network."""
    immich: Immich = Immich.__new__(Immich)
    immich.baseURL = "http://example.invalid"
    immich.headers = {"Accept": "application/json", "x-api-key": "test"}
    immich.logger = logging.getLogger("test")
    return immich


def ok_upload_response() -> MagicMock:
    response = MagicMock()
    response.ok = True
    response.json.return_value = {"id": VALID_ID, "status": "created"}
    return response


@pytest.fixture(autouse=True)
def no_real_sleep() -> Generator[None, None, Any]:
    with patch("immich_cli.helpers.retry.time.sleep"):
        yield


def test_upload_file_success_returns_asset(tmp_path) -> None:
    file_path: Path = tmp_path / "photo.jpg"
    file_path.write_bytes(b"some bytes")
    immich: Immich = make_immich()

    with patch(
        "immich_cli.immich_api.immich_class.requests.post", return_value=ok_upload_response()
    ) as mock_post:
        asset_response: AssetMediaResponseDto = immich.upload_file(str(file_path))

    assert str(asset_response.id) == VALID_ID
    assert asset_response.status.value == "created"
    assert mock_post.call_count == 1


def test_upload_file_retries_then_succeeds(tmp_path) -> None:
    file_path = tmp_path / "photo.jpg"
    file_path.write_bytes(b"some bytes")
    immich = make_immich()

    with patch(
        "immich_cli.immich_api.immich_class.requests.post",
        side_effect=[
            requests.ConnectionError("blip"),
            requests.ConnectionError("blip"),
            ok_upload_response(),
        ],
    ) as mock_post:
        asset_response: AssetMediaResponseDto = immich.upload_file(str(file_path))

    assert str(asset_response.id) == VALID_ID
    assert mock_post.call_count == 3


def test_upload_file_raises_after_exhausting_retries(tmp_path) -> None:
    file_path: Path = tmp_path / "photo.jpg"
    file_path.write_bytes(b"some bytes")
    immich: Immich = make_immich()

    with patch(
        "immich_cli.immich_api.immich_class.requests.post",
        side_effect=requests.ConnectionError("down"),
    ) as mock_post:
        with pytest.raises(requests.ConnectionError):
            immich.upload_file(str(file_path))

    assert mock_post.call_count == 3


def test_upload_file_empty_file_raises_clear_error(tmp_path) -> None:
    file_path: Path = tmp_path / "empty.jpg"
    file_path.write_bytes(b"")
    immich: Immich = make_immich()

    response = MagicMock()
    response.ok = False
    response.status_code = 400
    response.json.return_value = {"message": "File is empty"}

    with patch(
        "immich_cli.immich_api.immich_class.requests.post", return_value=response
    ) as mock_post:
        with pytest.raises(EmptyFileError):
            immich.upload_file(str(file_path))

    assert mock_post.call_count == 1


def test_upload_file_non_transient_http_error_raises_immediately(tmp_path) -> None:
    file_path: Path = tmp_path / "photo.jpg"
    file_path.write_bytes(b"some bytes")
    immich: Immich = make_immich()

    response = MagicMock()
    response.ok = False
    response.status_code = 500
    response.json.return_value = {"message": "internal error"}

    with patch(
        "immich_cli.immich_api.immich_class.requests.post", return_value=response
    ) as mock_post:
        with pytest.raises(ImmichRequestError):
            immich.upload_file(str(file_path))

    assert mock_post.call_count == 1


def test_get_asset_info_retries_then_succeeds() -> None:
    immich: Immich = make_immich()
    upload_response = MagicMock()
    upload_response.id = VALID_ID

    ok_response = MagicMock()
    ok_response.ok = True
    ok_response.json.return_value = {
        "checksum": "abc123",
        "createdAt": "2024-01-01T00:00:00Z",
        "fileCreatedAt": "2024-01-01T00:00:00Z",
        "fileModifiedAt": "2024-01-01T00:00:00Z",
        "hasMetadata": True,
        "id": VALID_ID,
        "isArchived": False,
        "isEdited": False,
        "isFavorite": False,
        "isOffline": False,
        "isTrashed": False,
        "localDateTime": "2024-01-01T00:00:00Z",
        "originalFileName": "photo.jpg",
        "originalMimeType": "image/jpeg",
        "originalPath": "/photo.jpg",
        "ownerId": "owner",
        "resized": False,
        "updatedAt": "2024-01-01T00:00:00Z",
        "visibility": "timeline",
    }

    with patch(
        "immich_cli.immich_api.immich_class.requests.get",
        side_effect=[requests.Timeout("slow"), ok_response],
    ) as mock_get:
        asset_info: AssetResponseDto = immich.get_asset_info(upload_response)

    assert asset_info.checksum == "abc123"
    assert mock_get.call_count == 2


def test_get_asset_info_raises_after_retries() -> None:
    immich: Immich = make_immich()
    upload_response = MagicMock()
    upload_response.id = VALID_ID

    with patch(
        "immich_cli.immich_api.immich_class.requests.get", side_effect=requests.Timeout("slow")
    ) as mock_get:
        with pytest.raises(requests.Timeout):
            immich.get_asset_info(upload_response)

    assert mock_get.call_count == 3
