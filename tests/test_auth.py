"""TC-AUTH-01 (HAP-F-001) and TC-AUTH-02 (HAP-F-002, HAP-SR-004), plus HAP-F-003 staff accounts."""
import jwt

from tests.conftest import PASSWORD


def test_tc_auth_01_valid_login_returns_jwt_with_role(client):
    r = client.post("/api/v1/auth/register", json={"email": "asha.rao@test.local", "password": PASSWORD,
                                                    "fullName": "Asha Rao", "phone": "9876500001"})
    assert r.status_code == 201
    r = client.post("/api/v1/auth/login", json={"email": "asha.rao@test.local", "password": PASSWORD})
    assert r.status_code == 200
    token = r.json()["accessToken"]
    claims = jwt.decode(token, options={"verify_signature": False})
    assert claims["role"] == "PATIENT"
    assert claims["exp"] - claims["iat"] == 1800


def test_tc_auth_01_wrong_password_gives_generic_401(client, make_user):
    make_user("PATIENT", email="asha.rao@test.local")
    r = client.post("/api/v1/auth/login", json={"email": "asha.rao@test.local", "password": "Wrong@999"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"
    assert "password is incorrect" in r.json()["error"]["message"].lower()  # does not say which field
    r2 = client.post("/api/v1/auth/login", json={"email": "nobody@test.local", "password": "Wrong@999"})
    assert r2.json() == r.json()


def test_tc_auth_01_staff_cannot_self_register(client):
    r = client.post("/api/v1/auth/register", json={"email": "doc@test.local", "password": PASSWORD,
                                                    "fullName": "Fake Doctor", "role": "DOCTOR"})
    assert r.status_code == 403
    r = client.post("/api/v1/auth/login", json={"email": "doc@test.local", "password": PASSWORD})
    assert r.status_code == 401


def test_register_rejects_weak_password_and_bad_email(client):
    r = client.post("/api/v1/auth/register", json={"email": "x@test.local", "password": "short", "fullName": "X Y"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    r = client.post("/api/v1/auth/register", json={"email": "not-an-email", "password": PASSWORD, "fullName": "X Y"})
    assert r.status_code == 422


def test_duplicate_email_conflict(client, make_user):
    make_user("PATIENT", email="dup@test.local")
    r = client.post("/api/v1/auth/register", json={"email": "dup@test.local", "password": PASSWORD, "fullName": "Dup"})
    assert r.status_code == 409


def test_tc_auth_02_patient_blocked_from_admin_endpoints(client, make_user):
    _, patient = make_user("PATIENT")
    _, admin = make_user("ADMIN")
    for method, url, body in [("get", "/api/v1/admin/users", None),
                              ("post", "/api/v1/admin/users", {"email": "d@test.local", "fullName": "Dr D", "role": "DOCTOR"})]:
        r = getattr(client, method)(url, headers=patient, **({"json": body} if body else {}))
        assert r.status_code == 403
        assert r.json()["error"]["code"] == "FORBIDDEN"
        r = getattr(client, method)(url, headers=admin, **({"json": body} if body else {}))
        assert r.status_code in (200, 201)


def test_missing_or_garbage_token_is_401(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.token"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHENTICATED"


def test_f003_admin_creates_and_deactivates_staff(client, make_user):
    _, admin = make_user("ADMIN")
    r = client.post("/api/v1/admin/users", headers=admin,
                    json={"email": "dr.menon@test.local", "fullName": "Dr K Menon", "role": "DOCTOR"})
    assert r.status_code == 201
    otp = r.json()["oneTimePassword"]
    uid = r.json()["id"]
    r = client.post("/api/v1/auth/login", json={"email": "dr.menon@test.local", "password": otp})
    assert r.status_code == 200 and r.json()["mustChangePassword"] is True
    doctor_headers = {"Authorization": f"Bearer {r.json()['accessToken']}"}
    assert client.patch(f"/api/v1/admin/users/{uid}", headers=admin, json={"isActive": False}).status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": "dr.menon@test.local", "password": otp}).status_code == 403
    assert client.get("/api/v1/auth/me", headers=doctor_headers).status_code == 401


def test_admin_cannot_create_patient_or_admin_via_staff_endpoint(client, make_user):
    _, admin = make_user("ADMIN")
    r = client.post("/api/v1/admin/users", headers=admin, json={"email": "a2@test.local", "fullName": "A Two", "role": "ADMIN"})
    assert r.status_code == 422


def test_change_password(client, make_user):
    _, h = make_user("PATIENT", email="cp@test.local")
    assert client.post("/api/v1/auth/change-password", headers=h,
                       json={"currentPassword": "bad", "newPassword": "New@12345"}).status_code == 401
    assert client.post("/api/v1/auth/change-password", headers=h,
                       json={"currentPassword": PASSWORD, "newPassword": "New@12345"}).status_code == 204
    assert client.post("/api/v1/auth/login", json={"email": "cp@test.local", "password": "New@12345"}).status_code == 200


def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_admin_bootstrap_on_startup(app):
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        r = c.post("/api/v1/auth/login", json={"email": "admin@hap.local", "password": "Admin@1234"})
        assert r.status_code == 200 and r.json()["role"] == "ADMIN"
