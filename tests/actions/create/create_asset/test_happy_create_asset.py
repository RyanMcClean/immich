from collections.abc import Callable
from unittest.mock import MagicMock, patch
from pathlib import Path
import pytest

from tests.helpers import get_config, make_args, get_random_string

from immich_cli.helpers.helpers import compute_file_hash
from immich_cli.actions.create import create_asset

RANDOM_GOOD_FILE = [f"{get_random_string()}.jpg" for x in range(5)]
RANDOM_BAD_FILE = [get_random_string() for x in range(5)]
RANDOM_GOOD_FILES = [[f"{get_random_string()}.jpg" for x in range(5)] for x in range(5)]
RANDOM_BAD_FILES = [[get_random_string() for x in range(5)] for x in range(5)]
RANDOM_GOOD_BAD_FILES = [
    [get_random_string() for x in range(5)]
    + ([f"{get_random_string()}.jpg" for x in range(5)])
    for x in range(5)
]
RANDOM_AUDIO_FILE = [f"{get_random_string()}.mp3" for x in range(5)]

RANDOM_TAGS = [get_random_string() for x in range(5)]

"""
    TODO: Add audio tests
    TODO: Add KeyboardInterrupt tests
"""


@pytest.mark.usefixtures("mock_asset_info", "mock_asset_response")
class TestCreateAssetHappy:

    @pytest.fixture(scope="function")
    def create_files(self, tmp_path, request) -> list[Path]:
        files: list[Path] = (
            [Path(tmp_path / file) for file in request.param]
            if isinstance(request.param, list)
            else [Path(tmp_path / request.param)]
        )
        for x in files:
            Path(x).write_bytes(str(x).encode("utf-8"))
        return files

    @pytest.fixture(scope="function")
    def get_upload_file(self, mock_asset_response) -> Callable:
        def upload_file(path) -> MagicMock:
            return mock_asset_response("created", path)

        return upload_file

    @pytest.fixture(scope="function")
    def get_get_asset_info(self, mock_asset_info) -> Callable:
        def get_asset_info(_asset_response) -> MagicMock:
            return mock_asset_info(compute_file_hash(_asset_response.id))

        return get_asset_info

    @pytest.fixture(scope="function")
    def get_mocked_immich(self, get_get_asset_info, get_upload_file) -> MagicMock:
        immich = MagicMock()
        immich.upload_file.side_effect = get_upload_file
        immich.get_asset_info.side_effect = get_get_asset_info
        immich.get_tags.return_value = []
        immich.get_albums.return_value = []
        return immich

    # region Upload Happy Paths

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_GOOD_FILE,
        indirect=True,
        ids=[f"Create Single Asset - {x}" for x in range(1, len(RANDOM_GOOD_FILE) + 1)],
    )
    def test_create_asset_single(self, caplog, create_files, get_mocked_immich):
        """
        Upload and delete one asset
        """

        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent)), config=get_config()
            )

        for file in create_files:
            assert not file.exists()
        assert (
            f"{len(create_files)} file(s) processed, {len(create_files)} deleted"
            in caplog.text
        )

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_BAD_FILE,
        indirect=True,
        ids=[
            f"Dont Create Invalid Single Asset - {x}"
            for x in range(1, len(RANDOM_BAD_FILE) + 1)
        ],
    )
    def test_dont_create_invalid_asset(self, caplog, create_files, get_mocked_immich):
        """
        Don't upload invalid files
        """
        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(make_args(str(create_files[0].parent)), config=get_config())

        for file in create_files:
            assert file.exists()
        assert "0 file(s) processed, 0 deleted" in caplog.text

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_GOOD_FILES,
        indirect=True,
        ids=[
            f"Create Multiple Assets - {x}"
            for x in range(1, len(RANDOM_GOOD_FILES) + 1)
        ],
    )
    def test_create_asset_multiple(self, caplog, create_files, get_mocked_immich):
        """
        Upload and delete multiple assets
        """
        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent)), config=get_config()
            )

        for file in create_files:
            assert not file.exists()
        assert (
            f"{len(create_files)} file(s) processed, {len(create_files)} deleted"
            in caplog.text
        )

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_BAD_FILES,
        indirect=True,
        ids=[
            f"Dont Create Multiple Invalid Assets - {x}"
            for x in range(1, len(RANDOM_BAD_FILES) + 1)
        ],
    )
    def test_dont_create_invalid_asset_multiple(
        self, caplog, create_files, get_mocked_immich
    ):
        """
        Upload and delete multiple assets
        """
        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent)), config=get_config()
            )

        for file in create_files:
            assert file.exists()
        assert "0 file(s) processed, 0 deleted" in caplog.text

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_GOOD_BAD_FILES,
        indirect=True,
        ids=[
            f"Create Valid and Skip Invalid Assets - {x}"
            for x in range(1, len(RANDOM_GOOD_BAD_FILES) + 1)
        ],
    )
    def test_create_valid_skip_invalid(self, caplog, create_files, get_mocked_immich):
        """
        Upload and delete valid .jpg files, don't upload or delete invalid files
        """
        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent)), config=get_config()
            )

        for file in create_files:
            if ".jpg" in str(file):
                assert not file.exists()
            else:
                assert file.exists()

        assert "5 file(s) processed, 5 deleted" in caplog.text

    # endregion

    # region Upload and tag happy paths

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_GOOD_FILE,
        indirect=True,
        ids=[
            f"Upload and Tag Single Asset - {x}"
            for x in range(1, len(RANDOM_GOOD_FILE) + 1)
        ],
    )
    def test_upload_and_tag_single_asset(self, caplog, create_files, get_mocked_immich):
        """
        Upload and tag a single file
        """

        tag = get_random_string()

        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent), tag=[tag]),
                config=get_config(),
            )

        for file in create_files:
            assert not file.exists()

        assert "1 file(s) processed, 1 deleted" in caplog.text
        assert f"Adding tag ({tag}) to all uploaded files" in caplog.text
        get_mocked_immich.post_tag.assert_called_once_with(tag)
        get_mocked_immich.tag_asset.assert_called_once()
        tagged_assets = get_mocked_immich.tag_asset.call_args[0][1]
        assert len(tagged_assets) == 1

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_GOOD_FILES,
        indirect=True,
        ids=[
            f"Upload and Tag Multiple Assets - {x}"
            for x in range(1, len(RANDOM_GOOD_FILES) + 1)
        ],
    )
    def test_upload_and_tag_multiple_asset(
        self, caplog, create_files, get_mocked_immich
    ):
        """
        Upload and tag a multiple file
        """

        tag = get_random_string()

        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent), tag=[tag]),
                config=get_config(),
            )

        for file in create_files:
            assert not file.exists()

        assert "5 file(s) processed, 5 deleted" in caplog.text
        assert f"Adding tag ({tag}) to all uploaded files" in caplog.text
        get_mocked_immich.post_tag.assert_called_once_with(tag)
        get_mocked_immich.tag_asset.assert_called_once()
        tagged_assets = get_mocked_immich.tag_asset.call_args[0][1]
        assert len(tagged_assets) == 5

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_BAD_FILE,
        indirect=True,
        ids=[
            f"Don't upload or Tag Single Asset - {x}"
            for x in range(1, len(RANDOM_BAD_FILE) + 1)
        ],
    )
    def test_dont_upload_and_tag_single_asset(
        self, caplog, create_files, get_mocked_immich
    ):
        """
        Don't upload or tag a single file
        """

        tag = get_random_string()

        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent), tag=[tag]),
                config=get_config(),
            )

        for file in create_files:
            assert file.exists()

        assert "0 file(s) processed, 0 deleted" in caplog.text
        assert f"Adding tag({tag}) to all uploaded files" not in caplog.text

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_BAD_FILES,
        indirect=True,
        ids=[
            f"Don't upload and Tag Multiple Assets - {x}"
            for x in range(1, len(RANDOM_GOOD_FILES) + 1)
        ],
    )
    def test_dont_upload_and_tag_multiple_asset(
        self, caplog, create_files, get_mocked_immich
    ):
        """
        Don't upload or tag a multiple files
        """

        tag = get_random_string()

        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent), tag=[tag]),
                config=get_config(),
            )

        for file in create_files:
            assert file.exists()

        assert "0 file(s) processed, 0 deleted" in caplog.text
        assert f"Adding tag ({tag}) to all uploaded files" not in caplog.text

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_GOOD_FILE,
        indirect=True,
        ids=[
            f"Upload and Tag Single Asset Multiple tags - {x}"
            for x in range(1, len(RANDOM_GOOD_FILE) + 1)
        ],
    )
    def test_upload_and_tag_single_asset_multiple_tags(
        self, caplog, create_files, get_mocked_immich
    ):
        """
        Upload and tag a single file with multiple tags
        """

        tags = RANDOM_TAGS

        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent), tag=tags),
                config=get_config(),
            )

        for file in create_files:
            assert not file.exists()

        assert "1 file(s) processed, 1 deleted" in caplog.text
        for tag in tags:
            assert f"Adding tag ({tag}) to all uploaded files" in caplog.text
        get_mocked_immich.post_tag.assert_called()
        get_mocked_immich.tag_asset.assert_called()
        tagged_assets = get_mocked_immich.tag_asset.call_args[0][1]
        assert len(tagged_assets) == 1

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_GOOD_FILES,
        indirect=True,
        ids=[
            f"Upload and Tag Multiple Assets Multiple Tags - {x}"
            for x in range(1, len(RANDOM_GOOD_FILES) + 1)
        ],
    )
    def test_upload_and_tag_multiple_asset_multiple_tags(
        self, caplog, create_files, get_mocked_immich
    ):
        """
        Upload and tag a multiple file multiple tags
        """

        tags = RANDOM_TAGS

        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent), tag=tags),
                config=get_config(),
            )

        for file in create_files:
            assert not file.exists()

        assert "5 file(s) processed, 5 deleted" in caplog.text
        for tag in tags:
            assert f"Adding tag ({tag}) to all uploaded files" in caplog.text
        get_mocked_immich.post_tag.assert_called_with(tags[-1])
        get_mocked_immich.tag_asset.assert_called()
        tagged_assets = get_mocked_immich.tag_asset.call_args[0][1]
        assert len(tagged_assets) == 5

    # endregion

    # region Upload and add to album happy paths

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_GOOD_FILE,
        indirect=True,
        ids=[
            f"Upload and Add to Album Single Asset - {x}"
            for x in range(1, len(RANDOM_GOOD_FILE) + 1)
        ],
    )
    def test_upload_and_add_to_album_single_asset(
        self, caplog, create_files, get_mocked_immich
    ):
        """
        Upload and add to album a single file
        """

        album = get_random_string()

        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent), album=album),
                config=get_config(),
            )

        for file in create_files:
            assert not file.exists()

        assert "1 file(s) processed, 1 deleted" in caplog.text
        assert f"Adding all uploaded files to album: '{album}'" in caplog.text
        get_mocked_immich.post_album.assert_called_once_with(album)
        get_mocked_immich.add_asset_to_album.assert_called_once()
        album_asset = get_mocked_immich.add_asset_to_album.call_args[0][1]
        assert len(album_asset) == 1

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_GOOD_FILES,
        indirect=True,
        ids=[
            f"Upload and add to Album Multiple Assets - {x}"
            for x in range(1, len(RANDOM_GOOD_FILES) + 1)
        ],
    )
    def test_upload_and_add_to_album_multiple_asset(
        self, caplog, create_files, get_mocked_immich
    ):
        """
        Upload and add to album multiple files
        """

        album = get_random_string()

        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("DEBUG"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent), album=album),
                config=get_config(),
            )

        for file in create_files:
            assert not file.exists()

        assert "5 file(s) processed, 5 deleted" in caplog.text
        assert f"Adding all uploaded files to album: '{album}'" in caplog.text
        get_mocked_immich.post_album.assert_called_once_with(album)
        get_mocked_immich.add_asset_to_album.assert_called_once()
        album_assets = get_mocked_immich.add_asset_to_album.call_args[0][1]
        assert len(album_assets) == 5

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_BAD_FILE,
        indirect=True,
        ids=[
            f"Don't upload or add asset to album Single Asset - {x}"
            for x in range(1, len(RANDOM_BAD_FILE) + 1)
        ],
    )
    def test_dont_upload_or_add_to_album_single_asset(
        self, caplog, create_files, get_mocked_immich
    ):
        """
        Don't upload or add asset to album a single file
        """

        album = get_random_string()

        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent), album=album),
                config=get_config(),
            )

        for file in create_files:
            assert file.exists()

        assert "0 file(s) processed, 0 deleted" in caplog.text
        assert f"Adding all uploaded files to album: '{album}'" not in caplog.text

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_BAD_FILES,
        indirect=True,
        ids=[
            f"Don't upload or Add to Album Multiple Assets - {x}"
            for x in range(1, len(RANDOM_BAD_FILES) + 1)
        ],
    )
    def test_dont_upload_and_add_to_album_multiple_asset(
        self, caplog, create_files, get_mocked_immich
    ):
        """
        Don't upload or add to Album multiple files
        """

        album = get_random_string()

        with (
            patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
            caplog.at_level("INFO"),
        ):
            create_asset(
                args=make_args(str(create_files[0].parent), album=album),
                config=get_config(),
            )

        for file in create_files:
            assert file.exists()

        assert "0 file(s) processed, 0 deleted" in caplog.text
        assert f"Adding all uploaded files to album: '{album}'" not in caplog.text

    # endregion

    # region KeyboardInterrupt handled properly

    @pytest.mark.parametrize(
        "create_files",
        RANDOM_GOOD_FILES,
        indirect=True,
        ids=[
            f"Raise Keyboard Interrupt - {x}"
            for x in range(1, len(RANDOM_GOOD_FILES) + 1)
        ],
    )
    def test_raise_keyboard_interrupt_error(
        self, caplog, create_files, get_mocked_immich
    ):

        def upload_file(path):
            raise KeyboardInterrupt

        get_mocked_immich.upload_file = upload_file

        with pytest.raises(KeyboardInterrupt):
            with (
                patch("immich_cli.actions.create.Immich", return_value=get_mocked_immich),
                caplog.at_level("INFO"),
            ):
                create_asset(
                    args=make_args(str(create_files[0].parent)), config=get_config()
                )

    # endregion

    # region Upload audio file

    # @pytest.mark.parametrize(
    #     "create_files",
    #     RANDOM_AUDIO_FILE,
    #     indirect=True,
    #     ids=[
    #         f"Upload Single Audio File - {x}"
    #         for x in range(1, len(RANDOM_AUDIO_FILE) + 1)
    #     ],
    # )
    # def test_upload_audio_file(self, caplog, create_files, get_mocked_immich):

    #     with patch(
    #         "immich_cli.actions.create.Immich", return_value=get_mocked_immich
    #     ), caplog.at_level("INFO"):
    #         create_asset(
    #             args=make_args(
    #                 str(create_files[0].parent), convert_audio=True, verbose=False
    #             ),
    #             config=get_config(),
    #         )

    #     assert "test failure" in caplog.text


# endregion
