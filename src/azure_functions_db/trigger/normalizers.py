from __future__ import annotations

from collections.abc import Callable
import logging
import uuid

from azure_functions_db.core.types import CursorPart, CursorValue, SourceDescriptor
from azure_functions_db.trigger.events import RowChange

logger = logging.getLogger(__name__)

RawRecord = dict[str, object]
EventNormalizer = Callable[[RawRecord, SourceDescriptor], RowChange]


def _cursor_part(value: object) -> CursorPart:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    msg = f"Unsupported cursor value type: {type(value).__name__}"
    raise TypeError(msg)


def default_normalizer(record: RawRecord, descriptor: SourceDescriptor) -> RowChange:
    return RowChange(
        event_id=uuid.uuid4().hex,
        op="upsert",
        source=descriptor,
        cursor=None,
        pk={},
        before=None,
        after=dict(record),
        metadata={},
    )


def make_normalizer(*, cursor_column: str, pk_columns: list[str]) -> EventNormalizer:
    def normalizer(record: RawRecord, descriptor: SourceDescriptor) -> RowChange:
        cursor_val = _cursor_part(record[cursor_column])
        pk = {column: record[column] for column in pk_columns}
        cursor_parts = [cursor_val]
        cursor_parts.extend(_cursor_part(record[column]) for column in pk_columns)
        cursor: CursorValue = tuple(cursor_parts)
        return RowChange(
            event_id=uuid.uuid4().hex,
            op="upsert",
            source=descriptor,
            cursor=cursor,
            pk=pk,
            before=None,
            after=dict(record),
            metadata={},
        )

    return normalizer
