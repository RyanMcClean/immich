from argparse import Namespace
import pytest

import immich_cli.actions.create as create
from tests.helpers import make_args, get_config


def test_create_asset(tmp_path, capsys):

    def create_asset(args: Namespace, config: dict) -> None:
        print(True)

    create.create_asset = create_asset

    create.create(args=make_args(str(tmp_path), object="asset"), config=get_config())
    captured = capsys.readouterr()

    assert "True" in captured.out


def test_create_album(tmp_path):

    with pytest.raises(NotImplementedError):
        create.create(
            args=make_args(str(tmp_path), object="album"), config=get_config()
        )


def test_create_tag(tmp_path):

    with pytest.raises(NotImplementedError):
        create.create(args=make_args(str(tmp_path), object="tag"), config=get_config())
