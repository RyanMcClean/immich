from typing import Never, Any

import pytest

from immich_cli.helpers.retry import retry_call


class Transient(Exception):
    pass


class Permanent(Exception):
    pass


def test_succeeds_first_try_never_sleeps():
    sleeps: list[Any] = []
    calls: dict[str, int] = {"n": 0}

    def func() -> str:
        calls["n"] += 1
        return "ok"

    result: str = retry_call(
        func, _retryable_exceptions=(Transient,), _sleep_fn=sleeps.append
    )

    assert result == "ok"
    assert calls["n"] == 1
    assert sleeps == []


def test_retries_then_succeeds() -> None:
    sleeps: list[Any] = []
    calls: dict[str, int] = {"n": 0}

    def func() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise Transient("blip")
        return "ok"

    result: str = retry_call(
        func,
        _retries=3,
        _backoff_seconds=1.0,
        _retryable_exceptions=(Transient,),
        _sleep_fn=sleeps.append,
    )

    assert result == "ok"
    assert calls["n"] == 3
    assert sleeps == [1.0, 2.0]


def test_exhausts_retries_and_raises() -> None:
    sleeps: list[Any] = []
    calls: dict[str, int] = {"n": 0}

    def func() -> Never:
        calls["n"] += 1
        raise Transient("always fails")

    with pytest.raises(Transient):
        retry_call(
            func,
            _retries=3,
            _retryable_exceptions=(Transient,),
            _sleep_fn=sleeps.append,
        )

    assert calls["n"] == 3
    assert len(sleeps) == 2


def test_non_retryable_exception_raises_immediately() -> None:
    sleeps: list[Any] = []
    calls: dict[str, int] = {"n": 0}

    def func() -> Never:
        calls["n"] += 1
        raise Permanent("nope")

    with pytest.raises(Permanent):
        retry_call(
            func,
            _retries=3,
            _retryable_exceptions=(Transient,),
            _sleep_fn=sleeps.append,
        )

    assert calls["n"] == 1
    assert sleeps == []
