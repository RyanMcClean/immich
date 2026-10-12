import requests


class ImmichRequestError(requests.RequestException):
    """Raised for explicit, non-transient Immich API failures (bad status, bad body)."""


class EmptyFileError(ImmichRequestError):
    """Raised when Immich rejects an upload because the server considers the file empty."""
