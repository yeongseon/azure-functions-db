from __future__ import annotations

from ..core.errors import DbError


class StateStoreError(DbError):
    pass


class LeaseConflictError(StateStoreError):
    pass


class FingerprintMismatchError(StateStoreError):
    pass
