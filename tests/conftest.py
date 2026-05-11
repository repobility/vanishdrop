"""Pytest fixtures shared across the suite."""

import contextlib
import importlib
import os
import shutil
import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_client(tmp_path):
    """Spin up a fresh FastAPI app rooted in a temp dir.

    Each test gets its own SQLite DB and blob directory, so cases are
    isolated and the suite can run in parallel without state leaks.
    """
    work = tmp_path / "vanishdrop-test"
    work.mkdir()

    # The app module hard-codes ROOT off __file__, so we point at a temp
    # directory by editing module-level constants after import.
    if "app.main" in sys.modules:
        importlib.reload(sys.modules["app.main"])
    from app import main as app_module

    app_module.BLOBS_DIR = work / "blobs"
    app_module.BLOBS_DIR.mkdir(parents=True, exist_ok=True)
    app_module.DB_PATH = work / "test.db"

    # Drop any pre-existing connection state.
    with contextlib.suppress(FileNotFoundError):
        os.unlink(app_module.DB_PATH)

    client = TestClient(app_module.app)
    yield client, app_module
    client.close()
    shutil.rmtree(work, ignore_errors=True)
