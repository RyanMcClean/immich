from typing import Any
from argparse import Namespace
import random
import string


def make_args(file_path, **overrides) -> Namespace:
    defaults: dict[str, Any | bool | None] = dict(
        file_path=file_path,
        delete=True,
        tag_blurry=False,
        convert_audio=False,
        album=None,
        tag=None,
        delay=0,
    )
    defaults.update(overrides)
    return Namespace(**defaults)


def get_config(**overrides) -> dict:
    defaults: dict[str, str] = {"BASE_URL": "http://x", "API_KEY": "k"}
    defaults.update(**overrides)
    return defaults


def get_random_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))
