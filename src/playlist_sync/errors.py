"""Exception hierarchy for playlist-sync.

Adapters translate vendor-specific failures into these exceptions so that the
core never depends on a streaming-service SDK (see ``docs/ARCHITECTURE.md`` §4
and the error conventions in ``AGENTS.md``).
Everything raised by the project derives from :class:`PlaylistSyncError`, which
is meant to be caught only at top-level boundaries (CLI/UI), never silently.

Messages must be user-safe: never include tokens, cookies, request headers or
raw vendor payloads.
"""

from __future__ import annotations

__all__ = [
    "AuthError",
    "AuthExpiredError",
    "AuthTimeoutError",
    "PlaylistSyncError",
    "RateLimitError",
    "RetryableError",
    "ServiceUnavailableError",
    "TrackNotFoundError",
]


class PlaylistSyncError(Exception):
    """Base class for every error raised by playlist-sync."""


class AuthError(PlaylistSyncError):
    """Base class for authentication problems."""


class AuthExpiredError(AuthError):
    """Stored credentials are missing, expired or rejected by the service.

    Raised when a service answers with 401/403; the CLI/UI then asks the user to
    reconnect that service.
    """


class AuthTimeoutError(AuthError):
    """An interactive login did not complete before its timeout."""


class RetryableError(PlaylistSyncError):
    """A transient failure that may succeed when retried.

    ``retry_after`` carries the delay requested by the service (``Retry-After``
    header) in seconds, when known. Retry decorators treat it as a delay hint.
    """

    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class RateLimitError(RetryableError):
    """The service rejected a call because of rate limiting."""


class ServiceUnavailableError(RetryableError):
    """The service is temporarily unavailable (5xx responses, network errors)."""


class TrackNotFoundError(PlaylistSyncError):
    """The requested track is unavailable in the service."""
