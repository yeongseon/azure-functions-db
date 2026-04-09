"""Host-level e2e tests for bindings and decorators.

Usage:
    E2E_BASE_URL=http://localhost:7071 pytest tests/e2e/host -v --no-cov

These tests exercise the Function App from ``examples/e2e_app/function_app.py``
against a running ``func start`` host or a deployed Azure Functions app.
"""

from __future__ import annotations

import pytest

from tests.e2e.host.conftest import BASE_URL, SKIP_REASON, _get, _post

pytestmark = pytest.mark.host_e2e


@pytest.mark.skipif(not BASE_URL, reason=SKIP_REASON)
def test_health_returns_200() -> None:
    r = _get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.skipif(not BASE_URL, reason=SKIP_REASON)
def test_output_binding_insert() -> None:
    """POST /api/items should insert via output binding."""
    payload = {"id": 1001, "name": "e2e-widget", "status": "active"}
    r = _post("/api/items", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "e2e-widget"


@pytest.mark.skipif(not BASE_URL, reason=SKIP_REASON)
def test_input_binding_by_pk() -> None:
    """GET /api/items/{id} should fetch by PK via input binding."""
    # Ensure row exists
    _post("/api/items", json={"id": 1002, "name": "e2e-fetch", "status": "active"})
    r = _get("/api/items/1002")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 1002
    assert data["name"] == "e2e-fetch"


@pytest.mark.skipif(not BASE_URL, reason=SKIP_REASON)
def test_input_binding_by_pk_not_found() -> None:
    """GET /api/items/{id} for non-existent row should return 404."""
    r = _get("/api/items/999999")
    assert r.status_code == 404


@pytest.mark.skipif(not BASE_URL, reason=SKIP_REASON)
def test_input_binding_query_mode() -> None:
    """GET /api/items should return rows via query input binding."""
    r = _get("/api/items")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)


@pytest.mark.skipif(not BASE_URL, reason=SKIP_REASON)
def test_inject_reader() -> None:
    """GET /api/reader/{id} should fetch via inject_reader."""
    _post("/api/items", json={"id": 1003, "name": "e2e-reader", "status": "active"})
    r = _get("/api/reader/1003")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 1003


@pytest.mark.skipif(not BASE_URL, reason=SKIP_REASON)
def test_inject_writer() -> None:
    """POST /api/writer should insert via inject_writer."""
    payload = {"id": 1004, "name": "e2e-writer", "status": "active"}
    r = _post("/api/writer", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "e2e-writer"
