from __future__ import annotations

import threading

from sqlalchemy.engine import Engine
from sqlalchemy.schema import MetaData, Table

from .config import resolve_env_vars


class MetadataCache:
    def __init__(self) -> None:
        self._lock: threading.Lock = threading.Lock()
        self._cache: dict[tuple[str, str | None, str], Table] = {}
        self._inflight: dict[tuple[str, str | None, str], threading.Event] = {}

    def get_or_reflect(
        self,
        *,
        engine: Engine,
        url: str,
        schema: str | None,
        table_name: str,
    ) -> Table | None:
        resolved_url = resolve_env_vars(url)
        cache_key = (resolved_url, schema, table_name)

        should_reflect = False
        wait_event: threading.Event | None = None

        with self._lock:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

            wait_event = self._inflight.get(cache_key)
            if wait_event is None:
                wait_event = threading.Event()
                self._inflight[cache_key] = wait_event
                should_reflect = True

        if not should_reflect:
            _ = wait_event.wait()
            with self._lock:
                return self._cache.get(cache_key)

        table: Table | None = None
        try:
            metadata = MetaData()
            metadata.reflect(bind=engine, schema=schema, only=[table_name])

            key = f"{schema}.{table_name}" if schema else table_name
            reflected = metadata.tables.get(key)
            if isinstance(reflected, Table):
                table = reflected

            if table is not None:
                with self._lock:
                    self._cache[cache_key] = table

            return table
        finally:
            with self._lock:
                event = self._inflight.pop(cache_key, None)
                if event is not None:
                    event.set()

    def invalidate(self, *, url: str, schema: str | None, table_name: str) -> None:
        resolved_url = resolve_env_vars(url)
        cache_key = (resolved_url, schema, table_name)
        with self._lock:
            _ = self._cache.pop(cache_key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


_metadata_cache = MetadataCache()


def get_metadata_cache() -> MetadataCache:
    return _metadata_cache
