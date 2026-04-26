from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, select

from azure_functions_db.binding.writer import DbWriter
from azure_functions_db.core.errors import WriteError


def _create_users_db(db_path: Path) -> str:
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)
    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(50)),
    )
    metadata.create_all(engine)
    engine.dispose()
    return url


def _row_count(url: str) -> int:
    engine = create_engine(url)
    metadata = MetaData()
    table = Table("users", metadata, autoload_with=engine)
    with engine.connect() as conn:
        rows = conn.execute(select(table)).fetchall()
    engine.dispose()
    return len(rows)


@pytest.fixture
def users_url(tmp_path: Path) -> str:
    return _create_users_db(tmp_path / "users.db")


class TestTransactionCommit:
    def test_transaction_commits_on_success(self, users_url: str) -> None:
        with DbWriter(url=users_url, table="users") as writer:
            with writer.transaction():
                writer.insert(data={"id": 1, "name": "Alice"})
                writer.insert(data={"id": 2, "name": "Bob"})
        assert _row_count(users_url) == 2

    def test_transaction_yields_writer_instance(self, users_url: str) -> None:
        with DbWriter(url=users_url, table="users") as writer:
            with writer.transaction() as tx_writer:
                assert tx_writer is writer
                tx_writer.insert(data={"id": 1, "name": "Alice"})
        assert _row_count(users_url) == 1


class TestTransactionRollback:
    def test_transaction_rolls_back_on_exception(self, users_url: str) -> None:
        with DbWriter(url=users_url, table="users") as writer:
            with pytest.raises(RuntimeError, match="boom"), writer.transaction():
                writer.insert(data={"id": 1, "name": "Alice"})
                raise RuntimeError("boom")
        assert _row_count(users_url) == 0

    def test_transaction_rolls_back_on_write_error(self, users_url: str) -> None:
        with DbWriter(url=users_url, table="users") as writer:
            with pytest.raises(WriteError), writer.transaction():
                writer.insert(data={"id": 1, "name": "Alice"})
                writer.insert(data={"id": 1, "name": "Bob"})
        assert _row_count(users_url) == 0


class TestTransactionNesting:
    def test_nested_transaction_raises(self, users_url: str) -> None:
        with DbWriter(url=users_url, table="users") as writer:
            with writer.transaction():
                with pytest.raises(WriteError, match="nested"):
                    with writer.transaction():
                        pass
        assert _row_count(users_url) == 0

    def test_can_open_new_transaction_after_previous_completes(
        self, users_url: str
    ) -> None:
        with DbWriter(url=users_url, table="users") as writer:
            with writer.transaction():
                writer.insert(data={"id": 1, "name": "Alice"})
            with writer.transaction():
                writer.insert(data={"id": 2, "name": "Bob"})
        assert _row_count(users_url) == 2


class TestTransactionWithMultipleOps:
    def test_insert_update_delete_in_transaction(self, users_url: str) -> None:
        with DbWriter(url=users_url, table="users") as writer:
            with writer.transaction():
                writer.insert(data={"id": 1, "name": "Alice"})
                writer.insert(data={"id": 2, "name": "Bob"})
                writer.update(data={"name": "Alicia"}, pk={"id": 1})
                writer.delete(pk={"id": 2})
        assert _row_count(users_url) == 1
