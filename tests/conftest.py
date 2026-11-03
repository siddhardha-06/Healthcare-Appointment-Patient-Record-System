"""Shared pytest fixtures. Every test gets a fresh in-memory database and app."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # fast hashes in tests; TC-SEC-01 checks the real cost
os.environ.setdefault("LOGIN_RATE_PER_MINUTE", "1000")  # the rate-limit test lowers it itself
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-only-0123456789")

from fastapi.testclient import TestClient  # noqa: E402

from app.core import clock  # noqa: E402
from app.core.config import reload_settings  # noqa: E402
from app.core.database import SessionLocal, get_engine  # noqa: E402
from app.main import create_app  # noqa: E402

PASSWORD = "Test@1234"


@pytest.fixture
def app():
    reload_settings()
    application = create_app("sqlite://")
    yield application
    clock.set_now(None)
    get_engine().dispose()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def db(app):
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def make_user(db, client):
    """make_user(role, email=None) -> (user, auth_headers). Creates the account directly and logs in through the API."""
    from app.services.auth.service import create_user

    counter = {"n": 0}

    def _make(role: str, email: str | None = None, full_name: str | None = None, password: str = PASSWORD):
        counter["n"] += 1
        email = email or f"{role.lower()}{counter['n']}@test.local"
        user = create_user(db, email, password, role, full_name or f"Test {role.title()} {counter['n']}", "98765" + f"{counter['n']:05d}")
        db.commit()
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200, resp.text
        return user, {"Authorization": f"Bearer {resp.json()['accessToken']}"}

    return _make
