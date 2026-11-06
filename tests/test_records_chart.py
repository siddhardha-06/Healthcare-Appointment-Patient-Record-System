"""TC-MR-03 (HAP-F-040, HAP-SR-004, HAP-SR-007) and the Audit Log."""
import pytest

from app.services.audit.models import AppendOnlyError, AuditLogEntry
from tests.helpers_booking import booked_visit
from tests.helpers_people import make_doctor, make_patient


def test_tc_mr_03_treating_doctor_reads_chart_allergies_first(client, make_user, db):
    v = booked_visit(client, make_user)
    r = client.get(f"/api/v1/patients/{v['patient']['id']}/records", headers=v["doctor_h"])
    assert r.status_code == 200
    body = r.json()
    assert list(body)[0] == "patient" and body["patient"]["allergies"] == ["Penicillin"]
    assert body["patient"]["mrn"] == v["patient"]["mrn"]
    entries = db.query(AuditLogEntry).filter(AuditLogEntry.record_type == "chart", AuditLogEntry.record_id == v["patient"]["id"]).all()
    assert [(e.action, e.record_type, e.role) for e in entries] == [("READ", "chart", "DOCTOR")]
    assert entries[0].ip and entries[0].timestamp and entries[0].user_id


def test_tc_mr_03_other_doctor_denied_and_logged(client, make_user, db):
    v = booked_visit(client, make_user)
    stranger_h, _ = make_doctor(client, make_user, v["admin"], name="Dr A Shah")
    r = client.get(f"/api/v1/patients/{v['patient']['id']}/records", headers=stranger_h)
    assert r.status_code == 403 and r.json()["error"]["code"] == "NO_CARE_RELATIONSHIP"
    assert "Ravi" not in r.text and "Penicillin" not in r.text
    denied = db.query(AuditLogEntry).filter(AuditLogEntry.action == "DENIED").all()
    assert len(denied) == 1 and denied[0].record_id == v["patient"]["id"] and denied[0].role == "DOCTOR"


def test_tc_mr_03_audit_rows_cannot_be_changed_or_deleted(client, make_user, db):
    v = booked_visit(client, make_user)
    client.get(f"/api/v1/patients/{v['patient']['id']}/records", headers=v["doctor_h"])
    entry = db.query(AuditLogEntry).first()
    entry.detail = "tampered"
    with pytest.raises(AppendOnlyError):
        db.commit()
    db.rollback()
    with pytest.raises(AppendOnlyError):
        db.delete(db.query(AuditLogEntry).first())
        db.commit()
    db.rollback()


def test_patient_sees_only_own_chart(client, make_user):
    v = booked_visit(client, make_user)
    _, other_h, other = make_patient(client, make_user, phone="9000033333")
    assert client.get(f"/api/v1/patients/{v['patient']['id']}/records", headers=other_h).status_code == 403
    assert client.get(f"/api/v1/patients/{other['id']}/records", headers=other_h).status_code == 200
    mine = client.get("/api/v1/patients/me/records", headers=v["patient_h"])
    assert mine.status_code == 200 and mine.json()["visits"] == []
    _, rec_h = make_user("RECEPTIONIST")
    assert client.get(f"/api/v1/patients/{v['patient']['id']}/records", headers=rec_h).status_code == 403
    _, no_profile = make_user("PATIENT")
    assert client.get("/api/v1/patients/me/records", headers=no_profile).status_code == 404


def test_admin_reads_audit_log(client, make_user):
    v = booked_visit(client, make_user)
    client.get(f"/api/v1/patients/{v['patient']['id']}/records", headers=v["doctor_h"])
    rows = client.get("/api/v1/admin/audit?recordType=chart", headers=v["admin"]).json()
    assert rows and rows[0]["action"] == "READ"
    assert client.get("/api/v1/admin/audit?action=admin", headers=v["admin"]).json()  # doctor profile creation
    assert client.get("/api/v1/admin/audit", headers=v["doctor_h"]).status_code == 403
