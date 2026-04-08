from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from .errors import CursorSerializationError
from .types import CursorPart, CursorValue


def serialize_cursor_part(value: object) -> CursorPart:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    msg = f"Unsupported cursor value type: {type(value).__name__}"
    raise TypeError(msg)


def parse_checkpoint_cursor(raw: object) -> CursorValue | None:
    if raw is None or isinstance(raw, (str, int, float, bool)):
        return raw
    if isinstance(raw, tuple):
        return raw
    if isinstance(raw, list):
        return tuple(raw)
    msg = f"Unsupported cursor type in checkpoint: {type(raw).__name__}"
    raise CursorSerializationError(msg)
