from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
CursorPart: TypeAlias = JsonScalar
CursorValue: TypeAlias = CursorPart | tuple[CursorPart, ...]
RawRecord: TypeAlias = dict[str, object]
Row: TypeAlias = RawRecord
RowDict: TypeAlias = dict[str, object]


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceDescriptor:
    name: str
    kind: str
    fingerprint: str
