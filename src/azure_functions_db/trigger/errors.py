from __future__ import annotations

from ..core.errors import DbError


class PollerError(DbError):
    pass


class LeaseAcquireError(PollerError):
    pass


class SourceConfigurationError(PollerError):
    pass


class FetchError(PollerError):
    pass


class HandlerError(PollerError):
    pass


class CommitError(PollerError):
    pass


class LostLeaseError(PollerError):
    pass


class SerializationError(PollerError):
    pass
