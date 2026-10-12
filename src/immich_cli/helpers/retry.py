import logging
import time
from typing import Callable, ParamSpec, TypeVar, Any
from logging import Logger

logger: Logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def retry_call(
    func: Callable[P, T],
    *args: Any,
    _retries: int = 3,
    _backoff_seconds: float = 2.0,
    _retryable_exceptions: tuple[type[BaseException], ...] = (),
    _sleep_fn: Callable[[float], None] | None = None,
    **kwargs: Any,
) -> T:
    """Call func(*args, **kwargs), retrying on _retryable_exceptions with linear backoff.

    Re-raises the final exception if all attempts are exhausted. Exceptions not in
    _retryable_exceptions propagate immediately on first occurrence.
    """
    sleep_fn: Callable[[float], None] = (
        _sleep_fn if _sleep_fn is not None else time.sleep
    )
    last_exc: BaseException | None = None
    for attempt in range(1, _retries + 1):
        try:
            return func(*args, **kwargs)
        except _retryable_exceptions as exc:
            last_exc = exc
            logger.warning(
                f"Attempt {attempt}/{_retries} failed for "
                f"{getattr(func, '__name__', func)}: {exc}"
            )
            if attempt < _retries:
                sleep_fn(_backoff_seconds * attempt)
    assert last_exc is not None
    raise last_exc
