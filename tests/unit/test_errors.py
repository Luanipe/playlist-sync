"""Tests for the project exception hierarchy (AGENTS.md, docs/ARCHITECTURE.md §4)."""

from __future__ import annotations

import pytest

from playlist_sync import errors

# Every public exception except the root base, including intermediate bases.
ERROR_TYPES = [
    errors.AuthError,
    errors.AuthExpiredError,
    errors.AuthTimeoutError,
    errors.RateLimitError,
    errors.RetryableError,
    errors.ServiceUnavailableError,
    errors.TrackNotFoundError,
]

RETRYABLE_ERRORS = [errors.RateLimitError, errors.ServiceUnavailableError]


def test_base_error_derives_from_exception() -> None:
    assert issubclass(errors.PlaylistSyncError, Exception)


@pytest.mark.parametrize("error_type", ERROR_TYPES, ids=lambda cls: cls.__name__)
def test_every_error_derives_from_base(error_type: type[errors.PlaylistSyncError]) -> None:
    assert issubclass(error_type, errors.PlaylistSyncError)


@pytest.mark.parametrize("error_type", ERROR_TYPES, ids=lambda cls: cls.__name__)
def test_error_message_is_preserved(error_type: type[errors.PlaylistSyncError]) -> None:
    with pytest.raises(error_type, match="something went wrong"):
        raise error_type("something went wrong")


def test_documented_exceptions_are_exported() -> None:
    expected = {
        "AuthExpiredError",
        "RateLimitError",
        "ServiceUnavailableError",
        "TrackNotFoundError",
    }
    assert expected <= set(errors.__all__)


def test_all_defined_errors_are_exported() -> None:
    defined = {
        name
        for name, value in vars(errors).items()
        if isinstance(value, type)
        and issubclass(value, errors.PlaylistSyncError)
        and value.__module__ == errors.__name__
    }
    assert set(errors.__all__) == defined


def test_auth_errors_share_a_base() -> None:
    assert issubclass(errors.AuthExpiredError, errors.AuthError)
    assert issubclass(errors.AuthTimeoutError, errors.AuthError)
    assert not issubclass(errors.TrackNotFoundError, errors.AuthError)


@pytest.mark.parametrize(
    "error_type",
    [errors.AuthExpiredError, errors.AuthTimeoutError],
    ids=lambda cls: cls.__name__,
)
def test_auth_errors_are_never_retryable(
    error_type: type[errors.AuthError],
) -> None:
    # docs/ARCHITECTURE.md §6: never retry on expired credentials.
    assert not issubclass(error_type, errors.RetryableError)


def test_all_errors_can_be_caught_as_project_error() -> None:
    with pytest.raises(errors.PlaylistSyncError):
        raise errors.AuthExpiredError("reconnect the service")


@pytest.mark.parametrize("error_type", RETRYABLE_ERRORS, ids=lambda cls: cls.__name__)
def test_retryable_errors_are_retryable(error_type: type[errors.RetryableError]) -> None:
    assert issubclass(error_type, errors.RetryableError)


@pytest.mark.parametrize("error_type", RETRYABLE_ERRORS, ids=lambda cls: cls.__name__)
def test_retry_after_is_carried(error_type: type[errors.RetryableError]) -> None:
    error = error_type("slow down", retry_after=12.5)
    assert error.retry_after == 12.5


@pytest.mark.parametrize("error_type", RETRYABLE_ERRORS, ids=lambda cls: cls.__name__)
def test_retry_after_defaults_to_none(error_type: type[errors.RetryableError]) -> None:
    assert error_type("slow down").retry_after is None


def test_retry_after_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        errors.RateLimitError("slow down", 3)  # type: ignore[call-arg]
