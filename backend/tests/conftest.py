"""Shared pytest fixtures.

Tests run against a real PostgreSQL database (`schoolprint_test` by
default) rather than SQLite, since the app relies on Postgres-specific
types (UUID, JSONB, native enums).

Each test gets a freshly created/dropped schema (function scope) for full
isolation, since services call `db.commit()` internally which would break
SAVEPOINT-based rollback isolation.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

os.environ.setdefault(
    "SCHOOLPRINT_DATABASE_URL",
    "postgresql+psycopg://schoolprint:schoolprint@localhost:5432/schoolprint_test",
)
os.environ.setdefault("SCHOOLPRINT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("SCHOOLPRINT_COOKIE_SECURE", "false")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

import app.models  # noqa: F401,E402  (registers models on Base.metadata)
from app.api.deps import get_current_user  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.user import UserCreate  # noqa: E402
from app.services.user_service import create_user  # noqa: E402

settings = get_settings()


@pytest.fixture(scope="session")
def _engine():
    engine = create_engine(settings.database_url, future=True)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(_engine) -> Generator[Session, None, None]:
    Base.metadata.drop_all(_engine)
    Base.metadata.create_all(_engine)
    TestSessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(_engine)


@pytest.fixture()
def tmp_storage(monkeypatch: pytest.MonkeyPatch) -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory(prefix="schoolprint-test-") as tmp_dir:
        root = Path(tmp_dir)
        monkeypatch.setattr(settings, "storage_root", root)
        (root / settings.uploads_dirname).mkdir(parents=True, exist_ok=True)
        (root / settings.sliced_dirname).mkdir(parents=True, exist_ok=True)
        (root / settings.previews_dirname).mkdir(parents=True, exist_ok=True)
        (root / settings.backups_dirname).mkdir(parents=True, exist_ok=True)
        yield root


@pytest.fixture()
def fast_dummy_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shrinks the `DummyDriver` simulated print duration so E2E tests
    don't have to sleep for the (20s) production default."""
    monkeypatch.setattr(settings, "dummy_driver_print_duration_seconds", 0.05)


@pytest.fixture()
def fake_slicer(monkeypatch: pytest.MonkeyPatch) -> Path:
    """Points the slicer service at `tests/fixtures/fake_slicer.py` instead
    of a real OrcaSlicer binary, which isn't available in this sandbox."""
    fake_slicer_path = Path(__file__).parent / "fixtures" / "fake_slicer.py"
    monkeypatch.setattr(settings, "slicer_binary_path", str(fake_slicer_path))
    monkeypatch.setattr(settings, "slicer_timeout_seconds", 2)
    return fake_slicer_path


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """A `TestClient` bound to the test DB session, with app startup/shutdown
    lifespan events skipped (no `with` block) so tests fully control state."""

    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_user(db_session: Session) -> User:
    return create_user(
        db_session,
        UserCreate(
            username="admin_test",
            display_name="Test Admin",
            password="adminpass123",
            role=UserRole.ADMIN,
        ),
    )


@pytest.fixture()
def normal_user(db_session: Session) -> User:
    return create_user(
        db_session,
        UserCreate(
            username="user_test",
            display_name="Test User",
            password="userpass123",
            role=UserRole.USER,
            class_name="5a",
        ),
    )


@pytest.fixture(autouse=True)
def _reset_dummy_driver_state() -> None:
    """`DummyDriver` keeps simulated printer state in a module-level dict
    (Section 9.7); clear it between tests so runs don't leak into each
    other."""
    from app.printer_drivers.dummy import reset_all_dummy_state

    reset_all_dummy_state()
    yield
    reset_all_dummy_state()


@pytest.fixture()
def client_as(client: TestClient):
    """Helper to override `get_current_user` with a given user directly,
    bypassing the cookie/JWT login flow for tests that only care about
    role-based behavior."""

    def _as(user: User) -> TestClient:
        app.dependency_overrides[get_current_user] = lambda: user
        return client

    yield _as
    app.dependency_overrides.pop(get_current_user, None)
