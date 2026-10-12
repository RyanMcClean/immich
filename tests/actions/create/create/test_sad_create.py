import pytest

import immich_cli.actions.create as create
from tests.helpers import make_args, get_config, get_random_string


@pytest.mark.parametrize("_", range(1, 11), ids=lambda x: f"Iteration {x}")
def test_raise_error(tmp_path, _):
    with pytest.raises(ValueError):
        create.create(
            make_args(str(tmp_path), object=get_random_string()), get_config()
        )
