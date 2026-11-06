"""TC-DOC-01 (HAP-F-021, F-022) plus HAP-F-020 doctor profiles."""
from datetime import date, datetime, time, timedelta

from app.core import events
from tests.helpers_people import MONDAY_8AM, make_doctor, start_clock

NEXT_MONDAY = (MONDAY_8AM + timedelta(days=7)).date().isoformat()


def test_tc_doc_01_availability_generates_exact_slots(client, make_user):
    start_clock()
    _, admin = make_user("ADMIN")
    doc_h, _ = make_doctor(client, make_user, admin, availability=[{"weekday": 0, "startTime": "09:00", "endTime": "12:00"}])
    slots = client.get(f"/api/v1/doctors/me/slots?day={NEXT_MONDAY}", headers=doc_h).json()
    assert len(slots) == 12
    assert slots[0]["start"].endswith("09:00:00") and slots[-1]["start"].endswith("11:45:00")
    assert all(s["status"] == "FREE" for s in slots)
    # a slot every Monday inside the 30-day window, none on Tuesday
    for week in range(5):
        day = (MONDAY_8AM + timedelta(days=7 * week)).date().isoformat()
        assert len(client.get(f"/api/v1/doctors/me/slots?day={day}", headers=doc_h).json()) == 12
    tuesday = (MONDAY_8AM + timedelta(days=1)).date().isoformat()
    assert client.get(f"/api/v1/doctors/me/slots?day={tuesday}", headers=doc_h).json() == []


def test_overlapping_availability_rejected(client, make_user):
    start_clock()
    _, admin = make_user("ADMIN")
    doc_h, _ = make_doctor(client, make_user, admin, availability=[])
    r = client.put("/api/v1/doctors/me/availability", headers=doc_h,
                   json=[{"weekday": 0, "startTime": "09:00", "endTime": "12:00"},
                         {"weekday": 0, "startTime": "11:00", "endTime": "13:00"}])
    assert r.status_code == 422
    r = client.put("/api/v1/doctors/me/availability", headers=doc_h,
                   json=[{"weekday": 0, "startTime": "12:00", "endTime": "09:00"}])
    assert r.status_code == 422


def test_tc_doc_01_leave_blocks_slots_and_announces_affected_period(client, make_user):
    start_clock()
    _, admin = make_user("ADMIN")
    doc_h, doctor = make_doctor(client, make_user, admin, availability=[{"weekday": 0, "startTime": "09:00", "endTime": "12:00"}])
    seen = []
    handler = events.subscribe("doctor.leave")(lambda **kw: seen.append((kw["doctor"].id, kw["start"], kw["end"])))
    try:
        r = client.post("/api/v1/doctors/me/leave", headers=doc_h, json={"day": NEXT_MONDAY})
    finally:
        events._handlers["doctor.leave"].remove(handler)
    assert r.status_code == 200 and r.json()["blockedSlots"] == 12
    slots = client.get(f"/api/v1/doctors/me/slots?day={NEXT_MONDAY}", headers=doc_h).json()
    assert {s["status"] for s in slots} == {"BLOCKED"}
    assert seen and seen[0][0] == doctor["id"] and seen[0][1].date().isoformat() == NEXT_MONDAY
    # regeneration keeps the leave day blocked
    assert client.post("/api/v1/admin/doctors/regenerate-slots", headers=admin).status_code == 200
    slots = client.get(f"/api/v1/doctors/me/slots?day={NEXT_MONDAY}", headers=doc_h).json()
    assert {s["status"] for s in slots} == {"BLOCKED"}


def test_partial_leave_and_past_leave(client, make_user):
    start_clock()
    _, admin = make_user("ADMIN")
    doc_h, _ = make_doctor(client, make_user, admin, availability=[{"weekday": 0, "startTime": "09:00", "endTime": "12:00"}])
    r = client.post("/api/v1/doctors/me/leave", headers=doc_h, json={"day": NEXT_MONDAY, "startTime": "09:00", "endTime": "10:00"})
    assert r.json()["blockedSlots"] == 4
    assert client.post("/api/v1/doctors/me/leave", headers=doc_h, json={"day": "2026-10-01"}).status_code == 422


def test_f020_admin_manages_doctor_profiles(client, make_user):
    _, admin = make_user("ADMIN")
    _, patient = make_user("PATIENT")
    doc_user, _ = make_user("DOCTOR")
    body = {"userId": doc_user.id, "name": "Dr A Shah", "specialization": "Paediatrics", "department": "Paediatrics",
            "qualification": "MBBS", "slotMinutes": 25}
    assert client.post("/api/v1/doctors", headers=admin, json=body).status_code == 422  # 25 not allowed
    body["slotMinutes"] = 20
    assert client.post("/api/v1/doctors", headers=patient, json=body).status_code == 403
    r = client.post("/api/v1/doctors", headers=admin, json=body)
    assert r.status_code == 201
    assert client.post("/api/v1/doctors", headers=admin, json=body).status_code == 409
    not_doctor, _ = make_user("RECEPTIONIST")
    assert client.post("/api/v1/doctors", headers=admin, json={**body, "userId": not_doctor.id}).status_code == 422
    did = r.json()["id"]
    assert client.patch(f"/api/v1/doctors/{did}", headers=admin, json={"slotMinutes": 30}).json()["slotMinutes"] == 30
    found = client.get("/api/v1/doctors?specialization=paediatrics", headers=patient).json()
    assert [d["name"] for d in found] == ["Dr A Shah"]
    assert client.get("/api/v1/doctors?name=shah", headers=patient).json()[0]["id"] == did
    client.patch(f"/api/v1/doctors/{did}", headers=admin, json={"isActive": False})
    assert client.get("/api/v1/doctors?name=shah", headers=patient).json() == []
    assert client.get(f"/api/v1/doctors/{did}", headers=patient).status_code == 200
    assert client.get("/api/v1/doctors/9999", headers=patient).status_code == 404


def test_doctor_without_profile_gets_404(client, make_user):
    _, doc_h = make_user("DOCTOR")
    assert client.get("/api/v1/doctors/me", headers=doc_h).status_code == 404


def test_changing_availability_removes_free_but_keeps_booked_slots(client, make_user, db):
    from app.services.doctors.models import Slot
    start_clock()
    _, admin = make_user("ADMIN")
    doc_h, doctor = make_doctor(client, make_user, admin, availability=[{"weekday": 0, "startTime": "09:00", "endTime": "10:00"}])
    first = db.query(Slot).filter(Slot.doctor_id == doctor["id"]).order_by(Slot.start).first()
    first.status = "BOOKED"
    db.commit()
    client.put("/api/v1/doctors/me/availability", headers=doc_h, json=[{"weekday": 1, "startTime": "09:00", "endTime": "10:00"}])
    db.expire_all()
    remaining = db.query(Slot).filter(Slot.doctor_id == doctor["id"]).all()
    assert any(s.id == first.id and s.status == "BOOKED" for s in remaining)
    assert all(s.start.weekday() == 1 or s.status == "BOOKED" for s in remaining)
    assert client.get("/api/v1/doctors/me/availability", headers=doc_h).json()[0]["weekday"] == 1


def test_nightly_slot_generation_job(client, make_user, db):
    from app.services.doctors.models import Slot
    start_clock()
    _, admin = make_user("ADMIN")
    _, doctor = make_doctor(client, make_user, admin, availability=[{"weekday": 0, "startTime": "09:00", "endTime": "10:00"}])
    before = db.query(Slot).count()
    start_clock(MONDAY_8AM + timedelta(days=7))  # a week later the window has moved on
    r = client.post("/api/v1/admin/jobs/slot-generation/run", headers=admin)
    assert r.status_code == 200 and r.json()["processed"] == 4 and db.query(Slot).count() == before + 4
