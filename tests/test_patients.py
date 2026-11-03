"""TC-PAT-01 (HAP-F-010, F-011) plus HAP-F-012 duplicate warning and HAP-F-013 search."""
import re

from tests.helpers_people import patient_body


def test_tc_pat_01_receptionist_registers_patient_and_mrn_is_generated(client, make_user):
    _, reception = make_user("RECEPTIONIST")
    r = client.post("/api/v1/patients", headers=reception, json=patient_body())
    assert r.status_code == 201
    assert re.fullmatch(r"HAP-P-\d{6}", r.json()["mrn"])


def test_tc_pat_01_missing_mandatory_field_is_422(client, make_user):
    _, reception = make_user("RECEPTIONIST")
    body = patient_body()
    del body["dateOfBirth"]
    r = client.post("/api/v1/patients", headers=reception, json=body)
    assert r.status_code == 422
    assert "dateOfBirth" in r.json()["error"]["message"]
    assert client.get("/api/v1/patients", headers=reception).json()["total"] == 0


def test_future_date_of_birth_rejected(client, make_user):
    _, reception = make_user("RECEPTIONIST")
    r = client.post("/api/v1/patients", headers=reception, json=patient_body(dateOfBirth="2999-01-01"))
    assert r.status_code == 422


def test_tc_pat_01_patient_edits_own_phone_but_not_mrn_or_dob(client, make_user):
    _, h = make_user("PATIENT")
    assert client.post("/api/v1/patients/me", headers=h, json=patient_body()).status_code == 201
    r = client.patch("/api/v1/patients/me", headers=h, json={"phone": "9876500002"})
    assert r.status_code == 200
    assert client.get("/api/v1/patients/me", headers=h).json()["phone"] == "9876500002"
    for change in ({"mrn": "HAP-P-999999"}, {"dateOfBirth": "1991-01-01"}):
        r = client.patch("/api/v1/patients/me", headers=h, json=change)
        assert r.status_code == 403
    me = client.get("/api/v1/patients/me", headers=h).json()
    assert me["dateOfBirth"] == "1990-05-14" and me["mrn"].startswith("HAP-P-")


def test_patient_cannot_create_two_profiles(client, make_user):
    _, h = make_user("PATIENT")
    assert client.post("/api/v1/patients/me", headers=h, json=patient_body()).status_code == 201
    assert client.post("/api/v1/patients/me", headers=h, json=patient_body(phone="9000000000")).status_code == 409


def test_mrns_are_unique(client, make_user):
    _, reception = make_user("RECEPTIONIST")
    mrns = {client.post("/api/v1/patients", headers=reception,
                        json=patient_body(phone=f"9{i:09d}")).json()["mrn"] for i in range(25)}
    assert len(mrns) == 25


def test_f012_duplicate_warning_then_confirm(client, make_user):
    _, reception = make_user("RECEPTIONIST")
    first = client.post("/api/v1/patients", headers=reception, json=patient_body()).json()
    r = client.post("/api/v1/patients", headers=reception, json=patient_body(fullName="R Kumar"))
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "POSSIBLE_DUPLICATE" and first["mrn"] in r.json()["error"]["message"]
    r = client.post("/api/v1/patients?confirm=true", headers=reception, json=patient_body(fullName="R Kumar"))
    assert r.status_code == 201


def test_f013_search_by_name_mrn_phone_and_role_check(client, make_user):
    _, reception = make_user("RECEPTIONIST")
    _, patient = make_user("PATIENT")
    p = client.post("/api/v1/patients", headers=reception, json=patient_body(fullName="Asha Rao", phone="9123456780")).json()
    client.post("/api/v1/patients", headers=reception, json=patient_body(fullName="Ravi Kumar", phone="9123456781"))
    assert [x["mrn"] for x in client.get("/api/v1/patients?q=asha", headers=reception).json()["items"]] == [p["mrn"]]
    assert client.get(f"/api/v1/patients?q={p['mrn']}", headers=reception).json()["total"] == 1
    assert client.get("/api/v1/patients?q=9123456781", headers=reception).json()["items"][0]["fullName"] == "Ravi Kumar"
    assert client.get("/api/v1/patients?q=asha", headers=patient).status_code == 403


def test_only_admin_corrects_date_of_birth(client, make_user):
    _, reception = make_user("RECEPTIONIST")
    _, admin = make_user("ADMIN")
    p = client.post("/api/v1/patients", headers=reception, json=patient_body()).json()
    assert client.patch(f"/api/v1/patients/{p['id']}", headers=reception, json={"dateOfBirth": "1990-05-15"}).status_code == 403
    assert client.patch(f"/api/v1/patients/{p['id']}", headers=admin, json={"dateOfBirth": "1990-05-15"}).status_code == 200
    assert client.patch(f"/api/v1/patients/{p['id']}", headers=admin, json={"mrn": "X"}).status_code == 403
    assert client.get("/api/v1/patients/99999", headers=admin).status_code == 404
