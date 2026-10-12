#! ../venv/bin/python
# region Imports
from typing import Any
from os import stat_result
from io import BufferedReader

import requests
from requests import Response
from requests_toolbelt.multipart.encoder import MultipartEncoder
import io
from tqdm import tqdm

import os
from datetime import datetime, timezone
import logging
from logging import Logger

from immich_cli.immich_api.dtos import (
    AssetMediaResponseDto,
    AssetResponseDto,
    AlbumResponseDto,
    TagResponseDto,
    UserResponseDto,
    SearchAssetsMetadataRequestDto,
    SearchMetadataResponseDto,
)
from immich_cli.immich_api.exceptions import EmptyFileError, ImmichRequestError
from immich_cli.helpers.retry import retry_call

# endregion


# region Immich class init
class Immich:
    baseURL: str = ""
    apiKey: str = ""
    logger: logging.Logger
    headers: dict[Any, Any] = {}
    current_user: UserResponseDto

    def __init__(self, baseURL: str, apiKey: str):
        """Init function, tests api string, and logs current user

        Args:
            baseURL (str): base URL to immich server
            apiKey (str): api key to immich

        Raises:
            ValueError: If the api key is wrong
        """
        self.logger: Logger = logging.getLogger(__name__)
        self.logger.debug(f"Base URL: {baseURL}")
        self.baseURL: str = baseURL
        self.apiKey: str = apiKey

        if not self._check_api_key():
            raise ValueError(f"{self.apiKey}.\nInvalid api key")
        else:
            self.headers: dict[Any, Any] = {
                "Accept": "application/json",
                "x-api-key": self.apiKey,
            }

        self._get_current_user()

        self.logger.debug(f"Current user: {self.current_user.name}")

    # endregion
    # region Private Functions

    def _check_api_key(self) -> bool:
        """
        Get the api_key endpoint to ensure the api key is working
        """
        headers: dict[str, str] = {
            "Accept": "application/json",
            "x-api-key": self.apiKey,
        }

        response: Response = requests.get(f"{self.baseURL}/api-keys", headers=headers)

        return response.ok

    def _get_current_user(self) -> None:
        """
        Get the currently authenticated user and store it on self.current_user
        """
        user_result: Response = requests.get(
            f"{self.baseURL}/users/me", headers=self.headers
        )

        if user_result.ok:
            self.current_user = UserResponseDto(**user_result.json())

    # endregion
    # region Public Functions

    def get_albums(self) -> list[AlbumResponseDto]:
        """
        Get a list of all the albums already created
        """

        response: Response = requests.get(
            f"{self.baseURL}/albums", headers=self.headers
        )

        if response.ok:
            self.logger.debug(response.text)
            albums: list[AlbumResponseDto] = [
                AlbumResponseDto(**album) for album in response.json()
            ]
            return albums
        else:
            raise ImmichRequestError(f"Failed to get albums: {response.text}")

    def post_album(
        self,
        album_name: str,
        assets: list[AssetResponseDto] | list[AssetMediaResponseDto] | None = None,
        album_users: str | None = None,
        description: str | None = None,
    ) -> AlbumResponseDto:
        """Create a new album

        Returns:
            requests.Response: response from post request
        """

        data: dict[str, str] = {
            "albumName": album_name,
        }

        response: Response = requests.post(
            f"{self.baseURL}/albums", headers=self.headers, json=data
        )

        if response.ok:
            self.logger.debug(response.text)
            album_response = AlbumResponseDto(**response.json())
            return album_response
        else:
            raise ImmichRequestError(
                f"Failed to create album '{album_name}': {response.text}"
            )

    def add_asset_to_album(
        self,
        album_response: AlbumResponseDto,
        asset_info: list[AssetResponseDto] | list[AssetMediaResponseDto],
    ) -> requests.Response:
        """Add a single asset to an album

        Args:
            album_response (AlbumResponseDto): Album to add assets to
            asset_info (list[AssetResponseDto] | list[AssetMediaResponseDto]):
                                                                    Assets to add to the album
        Returns:
            requests.Response: response from put request
        """

        data: dict[str, list[str]] = {"ids": [str(asset.id) for asset in asset_info]}

        response: Response = requests.put(
            f"{self.baseURL}/albums/{str(album_response.id)}/assets",
            headers=self.headers,
            json=data,
        )

        if not response.ok:
            self.logger.error(f"{response.text}")
            exit(1)

        return response

    def get_tags(self) -> list[TagResponseDto]:
        """
        Get a list of all tags already created
        """

        response: Response = requests.get(f"{self.baseURL}/tags", headers=self.headers)

        asset_response_dto: list[TagResponseDto] = [
            TagResponseDto(**tag) for tag in response.json()
        ]

        return asset_response_dto

    def post_tag(self, name: str) -> TagResponseDto:
        """Create a new tag, or return a tag if the tag already exists

        Args:
            name (str): Name of the tag to create

        Returns:
            TagResponseDto: The newly created tag
        """

        data: dict[str, Any] = {"name": name}

        response: Response = requests.post(
            f"{self.baseURL}/tags", headers=self.headers, data=data
        )

        if response.ok:
            self.logger.debug(response.text)
            tag = TagResponseDto(**response.json())
        elif response.json()["message"] == "A tag with that name already exists":
            tag: TagResponseDto = next(
                tag for tag in self.get_tags() if tag.name == name
            )
        else:
            self.logger.debug(response.status_code)
            raise ImmichRequestError(f"Failed to create tag '{name}': {response.text}")

        return tag

    def tag_asset(
        self,
        tag: TagResponseDto,
        asset_list: list[AssetResponseDto] | list[AssetMediaResponseDto],
    ) -> requests.Response:
        """Applies the specified tag to the specified asset

        Args:
            tag (TagResponseDto): Tag to apply
            asset_list (list[AssetResponseDto | AssetMediaResponseDto]): Assets to tag

        Returns:
            requests.Response: response from put request
        """

        data: dict[str, list[str]] = {
            "ids": [str(asset.id) for asset in asset_list],
        }

        self.logger.info(f"Tagging {len([asset for asset in asset_list])} assets")

        response: Response = requests.put(
            f"{self.baseURL}/tags/{tag.id}/assets", headers=self.headers, json=data
        )

        if response.ok:
            self.logger.debug(response.text)
        else:
            self.logger.error(response)
            raise ImmichRequestError(f"Failed to tag asset(s): {response.text}")

        return response

    def get_asset_info(
        self, asset_upload_response: AssetMediaResponseDto
    ) -> AssetResponseDto:
        """Get detailed information about asset

        Returns:
            AssetResponseDto: Detailed information about the asset
        """

        asset_response: Response = retry_call(
            requests.get,
            f"{self.baseURL}/assets/{asset_upload_response.id}",
            headers=self.headers,
            _retries=3,
            _retryable_exceptions=(requests.ConnectionError, requests.Timeout),
        )

        if asset_response.ok:
            asset_response_dto = AssetResponseDto(**asset_response.json())
            return asset_response_dto
        else:
            self.logger.error(
                f"Failed to get asset info for {asset_upload_response.id}: "
                + f"{asset_response.text}"
            )
            raise ImmichRequestError(
                f"get_asset_info failed for {asset_upload_response.id}: {asset_response.text}"
            )

    class ProgressFile:
        """Simple wrapper that tracks reads"""

        def __init__(self, file_path, total_size, desc=None):
            self.file: io.BufferedReader = open(file_path, "rb")
            self.buffered: BufferedReader[BufferedReader[Any]] = io.BufferedReader(
                self.file, buffer_size=6 * 1024 * 1024
            )
            self.total = total_size
            self.current = 0
            self.desc: Any | str = os.path.basename(desc) if desc else "Uploading"

            self.pbar: tqdm = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=self.desc,
            )

        def __getattr__(self, name):
            # Delegate all other methods to the underlying BufferedReader
            return getattr(self.buffered, name)

        def read(self, size=-1) -> bytes:
            data: bytes = self.buffered.read(size if size != -1 else -1)
            if data:
                self.current += len(data)
                self.pbar.update(len(data))
            return data

        def close(self) -> None:
            self.pbar.close()
            self.buffered.close()

    def upload_file(self, file: str) -> AssetMediaResponseDto:
        """
            Upload a single file to Immich

        Returns:
            AssetMediaResponseDto: The created (or duplicate) asset's id and status

        Raises:
            EmptyFileError: If Immich rejects the file as empty
            ImmichRequestError: If Immich rejects the upload for any other reason
        """
        stats: stat_result = os.stat(file)
        file_size: int = stats.st_size
        self.logger.info(f"Uploading {file} ({file_size / (1024**3):.2f} GB)")

        data: dict[str, str] = {
            "fileCreatedAt": datetime.fromtimestamp(
                stats.st_mtime, tz=timezone.utc
            ).isoformat(),
            "fileModifiedAt": datetime.fromtimestamp(
                stats.st_mtime, tz=timezone.utc
            ).isoformat(),
            "isFavorite": "false",
        }

        def _attempt() -> Response:
            # Rebuilt from scratch on every attempt: a partially-read multipart
            # stream can't be resubmitted on retry.
            progress_file: Immich.ProgressFile = self.ProgressFile(
                file, file_size, file
            )
            encoder: MultipartEncoder = MultipartEncoder(
                fields={
                    **data,
                    "assetData": (
                        os.path.basename(file),
                        progress_file,
                        "application/octet-stream",
                    ),
                }
            )
            try:
                return requests.post(
                    f"{self.baseURL}/assets",
                    headers={
                        **self.headers,
                        "Content-Type": encoder.content_type,
                    },
                    data=encoder,
                    timeout=1800,
                )
            finally:
                progress_file.close()

        response: Response = retry_call(
            _attempt,
            _retries=3,
            _retryable_exceptions=(requests.ConnectionError, requests.Timeout),
        )

        if response.ok:
            self.logger.debug(f"Uploaded {file}")
            self.logger.debug(f"{response.json()}")
            return AssetMediaResponseDto(**response.json())

        try:
            error_body = response.json()
        except ValueError:
            error_body = response.text

        if (
            isinstance(error_body, dict)
            and error_body.get("message") == "File is empty"
        ):
            self.logger.warning(
                f"{file}: server reports file is empty, skipping upload"
            )
            raise EmptyFileError(f"{file} is empty")

        self.logger.error(f"Failed to upload {file}")
        self.logger.error(f"{error_body}")
        raise ImmichRequestError(f"Upload failed for {file}: {error_body}")

    def download_asset(self, asset: AssetResponseDto, output_dir: str) -> bool:
        """Download an asset's original file to output_dir

        Args:
            asset (AssetResponseDto): Asset to download
            output_dir (str): Directory to write the downloaded file into

        Returns:
            bool: True if the file was downloaded successfully, False otherwise
        """
        asset_download: Response = requests.get(
            f"{self.baseURL}/assets/{asset.id}/original",
            headers=self.headers,
            stream=True,
        )
        asset_download.raw.decode_content = False

        os.makedirs(output_dir, exist_ok=True)

        total_size = int(asset_download.headers.get("content-length", 0))
        block_size = 8192

        if asset_download.ok:
            with tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=asset.originalFileName,
            ) as progress_bar:
                with open(f"{output_dir}{asset.originalFileName}", "wb") as file:
                    for chunk in asset_download.iter_content(chunk_size=block_size):
                        progress_bar.update(len(chunk))
                        file.write(chunk)

            if os.path.exists(f"{output_dir}/{asset.originalFileName}"):
                self.logger.info(f"Created file: {output_dir}/{asset.originalFileName}")
                return True

        return False

    def search_metadata(
        self, search_query: SearchAssetsMetadataRequestDto
    ) -> SearchMetadataResponseDto:
        """Search asset metadata

        Args:
            search_query (SearchAssetsMetadataRequestDto): Search parameters

        Returns:
            SearchMetadataResponseDto: Search results
        """
        search_result_model: SearchMetadataResponseDto
        search_results: Response = requests.post(
            f"{self.baseURL}/search/metadata",
            headers=self.headers,
            json=search_query.model_dump(exclude_none=True, mode="json"),
        )

        if search_results.ok:
            self.logger.debug(search_results.text)
            if search_query.albumIds:
                search_result_model: SearchMetadataResponseDto = (
                    SearchMetadataResponseDto(**search_results.json())
                )

                return search_result_model

        self.logger.error("Search did not work")
        raise ImmichRequestError(f"Search metadata failed: {search_results.text}")


# endregion
