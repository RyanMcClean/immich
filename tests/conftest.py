# conftest.py

from collections.abc import Callable
from unittest.mock import MagicMock
import pytest

from immich_cli.immich_api.enums import AssetMediaStatus


@pytest.fixture
def mock_asset_response() -> Callable:
    def _mock_asset_response(status: str, path: str) -> MagicMock:
        resp = MagicMock()
        resp.status = AssetMediaStatus(status)
        resp.id = path
        return resp

    return _mock_asset_response


@pytest.fixture
def mock_asset_info() -> Callable:
    def _mock_asset_info(checksum: str, asset_id: str = "id") -> MagicMock:
        info = MagicMock()
        info.checksum = checksum
        info.id = asset_id
        return info

    return _mock_asset_info
