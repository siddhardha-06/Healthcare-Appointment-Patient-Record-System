"""TC-SEC-01 (HAP-SR-001, SR-005), TC-SEC-02 (HAP-SR-002, SR-004) and hardening checks (SAD 3.9)."""
import time

import jwt

from app.core import clock
from app.core.config import settings
from tests.conftest import PASSWORD
from tests.helpers_people import make_patient


def test_tc_sec_01_password_stored_as_bcrypt_cost_12(client, db, monkeypatch, caplog):
    from app.services.auth.models import User
    monkeypatch.setattr(settings, "bcrypt_rounds", 12)
    r = client.post("/api/v1/auth/register", json={"email": "lock.test@test.local", "password": PASSWORD, "fullName": "Lock Test"})
    assert r.status_code == 201 and PASSWORD not in r.text
    stored = db.query(User).filter_by(email="lock.test@test.local").one().password_hash
    assert stored.startswith("$2b$12$") and len(stored) == 60
    assert PASSWORD not in caplog.text


def test_tc_sec_01_lockout_after_five_failures_for_15_minutes(client, make_user):
    from datetime import datetime, timedelta
    make_user("PATIENT", email="lock.test@test.local")
    clock.set_now(datetime(2026, 11, 2, 10, 0))
    for _ in range(5):
        assert client.post("/api/v1/auth/login", json={"email": "lock.test@test.local", "password": "Bad@0000"}).status_code == 401
    r = client.post("/api/v1/auth/login", json={"email": "lock.test@test.local", "password": PASSWORD})
    assert r.status_code == 423 and r.json()["error"]["code"] == "ACCOUNT_LOCKED"
    clock.set_now(datetime(2026, 11, 2, 10, 15, 1))
    assert client.post("/api/v1/auth/login", json={"email": "lock.test@test.local", "password": PASSWORD}).status_code == 200
    # counter was reset: 4 more failures do not lock
    for _ in range(4):
        client.post("/api/v1/auth/login", json={"email": "lock.test@test.local", "password": "Bad@0000"})
    assert client.post("/api/v1/auth/login", json={"email": "lock.test@test.local", "password": PASSWORD}).status_code == 200


def test_tc_sec_02_expired_and_forged_tokens_rejected(client, make_user):
    user, headers = make_user("PATIENT")
    good = headers["Authorization"].split()[1]
    claims = jwt.decode(good, settings.jwt_secret, algorithms=["HS256"])
    expired = jwt.encode({**claims, "exp": int(time.time()) - 60}, settings.jwt_secret, algorithm="HS256")
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "TOKEN_EXPIRED"
    head, payload, sig = good.split(".")
    forged_payload = jwt.utils.base64url_encode(jwt.api_jws.json.dumps({**claims, "role": "ADMIN"}).encode()).decode()
    for token in (f"{head}.{forged_payload}.{sig}",
                  jwt.encode({**claims, "role": "ADMIN"}, "wrong-key-wrong-key-wrong-key-123", algorithm="HS256"),
                  jwt.encode({**claims, "role": "ADMIN"}, None, algorithm="none")):
        r = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHENTICATED"


def test_tc_sec_02_patient_a_cannot_read_patient_b(client, make_user):
    from tests.helpers_booking import booked_visit
    v = booked_visit(client, make_user)
    _, a_h, a = make_patient(client, make_user, phone="9000055555")
    assert client.get(f"/api/v1/patients/{a['id']}/records", headers=a_h).status_code == 200
    r = client.get(f"/api/v1/patients/{v['patient']['id']}/records", headers=a_h)
    assert r.status_code == 403 and v["patient"]["fullName"] not in r.text
    assert client.get(f"/api/v1/appointments/{v['appointment']['id']}", headers=a_h).status_code == 403


def test_role_in_request_body_is_ignored(client):
    r = client.post("/api/v1/auth/register", json={"email": "sneaky@test.local", "password": PASSWORD,
                                                    "fullName": "Sneaky", "role": "ADMIN"})
    assert r.status_code == 403


def test_login_rate_limit_returns_429(client, monkeypatch):
    monkeypatch.setattr(settings, "login_rate_per_minute", 10)
    codes = [client.post("/api/v1/auth/login", json={"email": f"x{i}@test.local", "password": "Bad@0000"}).status_code
             for i in range(12)]
    assert codes[:10] == [401] * 10 and codes[10:] == [429, 429]


def test_security_headers_present(client):
    r = client.get("/api/v1/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff" and r.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in r.headers["Content-Security-Policy"]


def test_https_redirect_when_forced(client, monkeypatch):
    monkeypatch.setenv("FORCE_HTTPS", "1")
    r = client.get("/api/v1/health", follow_redirects=False)
    assert r.status_code == 301 and r.headers["location"].startswith("https://")


def test_sql_injection_in_search_is_harmless(client, make_user):
    _, rec_h = make_user("RECEPTIONIST")
    r = client.get("/api/v1/patients?q=' OR 1=1 --", headers=rec_h)
    assert r.status_code == 200 and r.json()["total"] == 0


def test_errors_do_not_leak_internals(client, make_user):
    _, h = make_user("PATIENT")
    r = client.get("/api/v1/appointments/not-a-number", headers=h)
    assert r.status_code == 422 and "Traceback" not in r.text and "sqlalchemy" not in r.text.lower()
