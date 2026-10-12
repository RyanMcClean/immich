import pytest

from immich_cli.helpers.helpers import list_files_recursive

happy_test_data: list[tuple[str, list[str]]] = [
    (
        "./tests/test_images",
        [
            "./tests/test_images/blurry/6P5A0948.cr2",
            "./tests/test_images/blurry/RY5D0483.cr2",
            "./tests/test_images/in_focus/RY5D0700.cr2",
            "./tests/test_images/in_focus/RY5D0704.cr2",
        ],
    ),
    (
        "./tests/test_images/blurry",
        [
            "./tests/test_images/blurry/6P5A0948.cr2",
            "./tests/test_images/blurry/RY5D0483.cr2",
        ],
    ),
    (
        "./tests/test_images/in_focus",
        [
            "./tests/test_images/in_focus/RY5D0700.cr2",
            "./tests/test_images/in_focus/RY5D0704.cr2",
        ],
    ),
    (
        "./tests/test_images/in_focus/RY5D0704.cr2",
        ["./tests/test_images/in_focus/RY5D0704.cr2"],
    ),
    (
        "./tests/test_images/in_focus/RY5D0700.cr2",
        ["./tests/test_images/in_focus/RY5D0700.cr2"],
    ),
    (
        "./tests/test_images/blurry/6P5A0948.cr2",
        ["./tests/test_images/blurry/6P5A0948.cr2"],
    ),
    (
        "./tests/test_images/blurry/RY5D0483.cr2",
        ["./tests/test_images/blurry/RY5D0483.cr2"],
    ),
]

sad_test_data = ["./random_failure_string", "./Unu/sual/pathing", "thisis@an.email"]


@pytest.mark.parametrize("file_path, expected", happy_test_data)
def test_list_files_recursive_pass(file_path: str, expected: list[str]) -> None:
    file_list: list[str] = list_files_recursive(file_path)
    file_list.sort()
    assert file_list == expected


@pytest.mark.parametrize("file_path", sad_test_data)
def test_list_files_recursive_fail(file_path: str) -> None:
    with pytest.raises(ValueError, match=f"The provide path is invalid: {file_path}"):
        list_files_recursive(file_path)
