from __future__ import annotations

from azure_functions_db.core.types import SourceDescriptor
from azure_functions_db.trigger.normalizers import default_normalizer, make_normalizer


def _descriptor() -> SourceDescriptor:
    return SourceDescriptor(kind="sqlalchemy", name="orders", fingerprint="fp_orders")


def test_default_normalizer_produces_upsert() -> None:
    event = default_normalizer({"id": 1}, _descriptor())
    assert event.op == "upsert"  # noqa: S101


def test_default_normalizer_cursor_is_none() -> None:
    event = default_normalizer({"id": 1}, _descriptor())
    assert event.cursor is None  # noqa: S101


def test_default_normalizer_pk_is_empty_dict() -> None:
    event = default_normalizer({"id": 1}, _descriptor())
    assert event.pk == {}  # noqa: S101


def test_default_normalizer_after_contains_full_record() -> None:
    record = {"id": 1, "name": "Alice", "updated_at": 100}
    event = default_normalizer(record, _descriptor())
    assert event.after == record  # noqa: S101


def test_default_normalizer_event_id_is_nonempty_string() -> None:
    event = default_normalizer({"id": 1}, _descriptor())
    assert isinstance(event.event_id, str)  # noqa: S101
    assert event.event_id != ""  # noqa: S101


def test_default_normalizer_before_is_none() -> None:
    event = default_normalizer({"id": 1}, _descriptor())
    assert event.before is None  # noqa: S101


def test_make_normalizer_extracts_cursor_value() -> None:
    event = make_normalizer(cursor_column="updated_at", pk_columns=["id"])(
        {"id": 1, "updated_at": 100},
        _descriptor(),
    )
    assert event.cursor == (100, 1)  # noqa: S101


def test_make_normalizer_extracts_pk_dict() -> None:
    event = make_normalizer(cursor_column="updated_at", pk_columns=["id", "tenant_id"])(
        {"id": 1, "tenant_id": 2, "updated_at": 100},
        _descriptor(),
    )
    assert event.pk == {"id": 1, "tenant_id": 2}  # noqa: S101


def test_make_normalizer_composite_cursor_is_tuple() -> None:
    event = make_normalizer(cursor_column="updated_at", pk_columns=["id", "tenant_id"])(
        {"id": 1, "tenant_id": 2, "updated_at": 100},
        _descriptor(),
    )
    assert event.cursor == (100, 1, 2)  # noqa: S101


def test_make_normalizer_missing_cursor_column_raises_key_error() -> None:
    normalizer = make_normalizer(cursor_column="updated_at", pk_columns=["id"])
    try:
        normalizer({"id": 1}, _descriptor())
    except KeyError as exc:
        assert exc.args == ("updated_at",)  # noqa: S101
    else:
        msg = "Expected KeyError for missing cursor column"
        raise AssertionError(msg)


def test_make_normalizer_missing_pk_column_raises_key_error() -> None:
    normalizer = make_normalizer(cursor_column="updated_at", pk_columns=["id", "tenant_id"])
    try:
        normalizer({"id": 1, "updated_at": 100}, _descriptor())
    except KeyError as exc:
        assert exc.args == ("tenant_id",)  # noqa: S101
    else:
        msg = "Expected KeyError for missing pk column"
        raise AssertionError(msg)
