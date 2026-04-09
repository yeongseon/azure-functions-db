"""Shared fixtures for host-level e2e tests.

These tests require a running Azure Functions host (``func start``)
with ``E2E_BASE_URL`` env var pointing to the host root.
"""

from __future__ import annotations

import os
import time

import pytest
import requests

BASE_URL = os.environ.get("E2E_BASE_URL", "").rstrip("/")
SKIP_REASON = "E2E_BASE_URL not set — skipping host e2e tests"


def _get(path: str, **kwargs: object) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=30, **kwargs)  # type: ignore[arg-type]


def _post(path: str, **kwargs: object) -> requests.Response:
    return requests.post(f"{BASE_URL}{path}", timeout=30, **kwargs)  # type: ignore[arg-type]


@pytest.fixture(scope="session", autouse=True)
def warmup() -> None:
    """Retry /api/health until the host is ready (max 2 min)."""
    if not BASE_URL:
        return
    deadline = time.time() + 120
    while time.time() < deadline:
        try:
            r = requests.get(f"{BASE_URL}/api/health", timeout=10)
            if r.status_code < 500:
                return
        except requests.RequestException:
            pass
        time.sleep(3)
    pytest.fail("Warmup failed: /api/health did not respond within 120 s")


@pytest.fixture(scope="session", autouse=True)
def setup_table() -> None:
    """Create the e2e_items table before running tests."""
    if not BASE_URL:
        return
    r = _post("/api/setup")
    assert r.status_code == 200, f"Setup failed: {r.text}"
