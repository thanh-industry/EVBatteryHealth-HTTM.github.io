from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app import db  # noqa: E402
from app.tests.fixtures.bundle_factory import make_small_bundle  # noqa: E402


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test_app.db"
    db.init_db(db_path=path)
    return path


@pytest.fixture(scope="session")
def small_bundle() -> dict:
    """A structurally-valid, genuinely-fitted small bundle. Session scoped
    since fitting it, while fast, is unnecessary to repeat per test."""
    return make_small_bundle()
