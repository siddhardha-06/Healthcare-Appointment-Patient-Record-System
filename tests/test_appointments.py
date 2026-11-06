"""TC-APT-01 (F-030, F-031), TC-APT-02 (F-032), TC-APT-03 (F-033, F-034), plus F-035 and leave handling."""
import threading
from datetime import datetime, timedelta

from app.core import clock
from tests.helpers_booking import NEXT_MONDAY, book, booked_visit, free_slots
from tests.helpers_people import MONDAY_8AM, make_doctor, make_patient, start_clock


def test_tc_apt_01_search_shows_free_slots_and_booking_appears_in_schedule(client, make_user):
    start_clock()
    _, admin = make_user("ADMIN")
    doc_h, doctor = make_doctor(client, make_user, admin, specialization="Cardiology")
    make_doctor(client, make_user, admin, specialization="Dermatology", name="Dr S Iyer")
    _, pat_h, _ = make_patient(client, make_user)
    found = client.get("/api/v1/doctors?specialization=Cardiology", headers=pat_h).json()
    assert [d["id"] for d in found] == [doctor["id"]]
    slots = free_slots(client, pat_h, doctor["id"])
    starts = [s["start"] for s in slots]
    assert starts == sorted(starts) and len(slots) == 12
    target = next(s for s in slots if s["start"].endswith("10:15:00"))
    r = book(client, pat_h, target["slotId"], reason="Chest pain on exertion")
    assert r.status_code == 201 and r.json()["status"] == "BOOKED"
    assert target["slotId"] not in [s["slotId"] for s in free_slots(client, pat_h, doctor["id"])]
    sched = client.get(f"/api/v1/appointments?date={NEXT_MONDAY}", headers=doc_h).json()["items"]
    assert len(sched) == 1 and sched[0]["reason"] == "Chest pain on exertion" and sched[0]["patientName"]


def test_slot_search_window_and_past_slots(client, make_user):
    start_clock(MONDAY_8AM.replace(hour=10, minute=7))
    _, admin = make_user("ADMIN")
    _, doctor = make_doctor(client, make_user, admin)
    _, pat_h, _ = make_patient(client, make_user)
    today = free_slots(client, pat_h, doctor["id"], MONDAY_8AM.date().isoformat())
    assert all(s["start"] > "2026-11-02T10:07" for s in today) and len(today) == 7
    assert client.get(f"/api/v1/slots?doctorId={doctor['id']}&date=2026-10-01", headers=pat_h).status_code == 400
    assert client.get(f"/api/v1/slots?doctorId={doctor['id']}&date=2027-01-01", headers=pat_h).status_code == 400
    assert client.get(f"/api/v1/slots?doctorId=999&date={NEXT_MONDAY}", headers=pat_h).status_code == 404


def test_booking_validation(client, make_user):
    v = booked_visit(client, make_user)
    slots = free_slots(client, v["patient_h"], v["doctor"]["id"])
    assert book(client, v["patient_h"], slots[0]["slotId"], reason="hi").status_code == 422
    assert book(client, v["patient_h"], 99999).status_code == 404
    _, no_profile = make_user("PATIENT")
    assert book(client, no_profile, slots[0]["slotId"]).status_code == 404


def test_tc_apt_02_twenty_bookings_of_one_slot_only_one_wins(client, make_user):
    start_clock()
    _, admin = make_user("ADMIN")
    _, doctor = make_doctor(client, make_user, admin)
    patients = [make_patient(client, make_user, phone=f"91{i:08d}")[1] for i in range(20)]
    slot_id = free_slots(client, patients[0], doctor["id"])[0]["slotId"]
    codes = [book(client, h, slot_id).status_code for h in patients]
    assert codes.count(201) == 1 and codes.count(409) == 19


def test_tc_apt_02_concurrent_threads_on_shared_database(tmp_path, make_user):
    """Real concurrency: 20 threads, each with its own DB session, race for the same slot."""
    from app.core.config import reload_settings
    from app.core.database import SessionLocal
    from app.core.errors import ApiError
    from app.main import create_app
    from app.services.appointments import service
    from app.services.appointments.models import Appointment
    from app.services.auth.service import create_user
    from app.services.doctors.models import Doctor, Slot
    from app.services.patients.models import Patient

    reload_settings()
    create_app(f"sqlite:///{tmp_path / 'race.db'}")
    clock.set_now(MONDAY_8AM)
    with SessionLocal() as db:
        du = create_user(db, "race.doc@test.local", "Test@1234", "DOCTOR", "Dr Race")
        doc = Doctor(user_id=du.id, name="Dr Race", specialization="GP", department="GP", qualification="MBBS")
        db.add(doc)
        db.flush()
        slot = Slot(doctor_id=doc.id, start=MONDAY_8AM + timedelta(days=1), end=MONDAY_8AM + timedelta(days=1, minutes=15))
        db.add(slot)
        pats = [Patient(full_name=f"P{i}", date_of_birth=datetime(1990, 1, 1).date(), gender="Male", phone=f"90{i:08d}")
                for i in range(20)]
        db.add_all(pats)
        db.commit()
        slot_id, patient_ids = slot.id, [p.id for p in pats]

    results, barrier = [], threading.Barrier(20)

    def attempt(pid):
        with SessionLocal() as s:
            barrier.wait()
            try:
                service.book(s, s.get(Patient, pid), slot_id, "Race test", 0)
                results.append("ok")
            except ApiError as e:
                results.append(e.code)

    threads = [threading.Thread(target=attempt, args=(pid,)) for pid in patient_ids]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert results.count("ok") == 1 and results.count("SLOT_TAKEN") == 19
    with SessionLocal() as db:
        assert db.query(Appointment).filter(Appointment.slot_id == slot_id, Appointment.status == "BOOKED").count() == 1


def test_unique_index_is_the_final_guard(db, client, make_user):
    import pytest
    from sqlalchemy.exc import IntegrityError
    from app.services.appointments.models import Appointment
    v = booked_visit(client, make_user)
    a = v["appointment"]
    db.add(Appointment(slot_id=a["slotId"], patient_id=a["patientId"], doctor_id=a["doctorId"],
                       start=datetime.fromisoformat(a["start"]), end=datetime.fromisoformat(a["end"]),
                       reason="sneaky second booking", status="BOOKED", created_by=0))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_tc_apt_02_patient_overlap_with_another_doctor(client, make_user):
    v = booked_visit(client, make_user)
    other_h, other = make_doctor(client, make_user, v["admin"], name="Dr A Shah", specialization="ENT")
    same_time = next(s for s in free_slots(client, v["patient_h"], other["id"]) if s["start"] == v["appointment"]["start"])
    r = book(client, v["patient_h"], same_time["slotId"])
    assert r.status_code == 409 and r.json()["error"]["code"] == "PATIENT_OVERLAP"


def test_tc_apt_03_cancel_window_and_slot_freed(client, make_user):
    v = booked_visit(client, make_user)
    appt, pat_h = v["appointment"], v["patient_h"]
    # 3 hours before: allowed, slot FREE again
    clock.set_now(datetime.fromisoformat(appt["start"]) - timedelta(hours=3))
    r = client.delete(f"/api/v1/appointments/{appt['id']}", headers=pat_h)
    assert r.status_code == 200 and r.json()["status"] == "CANCELLED"
    assert appt["slotId"] in [s["slotId"] for s in free_slots(client, pat_h, v["doctor"]["id"])]
    # a second appointment, 1 h 50 min before: blocked
    second = book(client, pat_h, free_slots(client, pat_h, v["doctor"]["id"])[-1]["slotId"]).json()
    clock.set_now(datetime.fromisoformat(second["start"]) - timedelta(hours=1, minutes=50))
    r = client.delete(f"/api/v1/appointments/{second['id']}", headers=pat_h)
    assert r.status_code == 409 and r.json()["error"]["code"] == "CHANGE_WINDOW_CLOSED"
    assert client.get(f"/api/v1/appointments/{second['id']}", headers=pat_h).json()["status"] == "BOOKED"


def test_tc_apt_03_status_transitions(client, make_user):
    v = booked_visit(client, make_user)
    _, rec_h = make_user("RECEPTIONIST")
    aid = v["appointment"]["id"]
    url = f"/api/v1/appointments/{aid}/status"
    assert client.patch(url, headers=v["patient_h"], json={"status": "CHECKED_IN"}).status_code == 403
    assert client.patch(url, headers=rec_h, json={"status": "COMPLETED"}).status_code == 403  # wrong role
    assert client.patch(url, headers=rec_h, json={"status": "CHECKED_IN"}).json()["status"] == "CHECKED_IN"
    r = client.patch(url, headers=rec_h, json={"status": "CHECKED_IN"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"
    assert client.patch(url, headers=v["doctor_h"], json={"status": "COMPLETED"}).json()["status"] == "COMPLETED"
    assert client.delete(f"/api/v1/appointments/{aid}", headers=rec_h).status_code == 409   # COMPLETED -> cancel
    assert client.patch(url, headers=rec_h, json={"status": "NO_SHOW"}).status_code == 409
    assert client.patch(url, headers=rec_h, json={"status": "BOOKED"}).status_code == 422


def test_tc_apt_03_automatic_no_show(client, make_user, db):
    from app.services.appointments.service import mark_no_shows
    v = booked_visit(client, make_user)
    end = datetime.fromisoformat(v["appointment"]["end"])
    assert mark_no_shows(db, end + timedelta(minutes=29)) == 0
    assert mark_no_shows(db, end + timedelta(minutes=31)) == 1
    assert client.get(f"/api/v1/appointments/{v['appointment']['id']}", headers=v["patient_h"]).json()["status"] == "NO_SHOW"


def test_reschedule(client, make_user):
    v = booked_visit(client, make_user)
    pat_h, appt = v["patient_h"], v["appointment"]
    new = free_slots(client, pat_h, v["doctor"]["id"])[3]
    r = client.patch(f"/api/v1/appointments/{appt['id']}/reschedule", headers=pat_h, json={"newSlotId": new["slotId"]})
    assert r.status_code == 200 and r.json()["slotId"] == new["slotId"]
    assert appt["slotId"] in [s["slotId"] for s in free_slots(client, pat_h, v["doctor"]["id"])]
    r = client.patch(f"/api/v1/appointments/{appt['id']}/reschedule", headers=pat_h, json={"newSlotId": new["slotId"]})
    assert r.status_code == 409 and r.json()["error"]["code"] == "SLOT_TAKEN"
    clock.set_now(datetime.fromisoformat(new["start"]) - timedelta(minutes=30))
    other = free_slots(client, pat_h, v["doctor"]["id"])[-1]
    r = client.patch(f"/api/v1/appointments/{appt['id']}/reschedule", headers=pat_h, json={"newSlotId": other["slotId"]})
    assert r.status_code == 409 and r.json()["error"]["code"] == "CHANGE_WINDOW_CLOSED"


def test_f035_receptionist_books_and_changes_for_patient(client, make_user):
    v = booked_visit(client, make_user)
    _, rec_h = make_user("RECEPTIONIST")
    _, _, walk_in = make_patient(client, make_user, phone="9000011111")
    slot = free_slots(client, rec_h, v["doctor"]["id"])[1]
    assert book(client, rec_h, slot["slotId"]).status_code == 422  # patientId required
    r = book(client, rec_h, slot["slotId"], patientId=walk_in["id"])
    assert r.status_code == 201 and r.json()["createdBy"] != r.json()["patientId"]
    # receptionist may cancel inside the 2-hour window
    clock.set_now(datetime.fromisoformat(r.json()["start"]) - timedelta(minutes=30))
    assert client.delete(f"/api/v1/appointments/{r.json()['id']}", headers=rec_h).status_code == 200
    # a patient cannot book for someone else
    other = free_slots(client, v["patient_h"], v["doctor"]["id"])[2]
    assert book(client, v["patient_h"], other["slotId"], patientId=walk_in["id"]).status_code == 403


def test_record_level_access_to_appointments(client, make_user):
    v = booked_visit(client, make_user)
    _, other_h, other = make_patient(client, make_user, phone="9000022222")
    aid = v["appointment"]["id"]
    assert client.get(f"/api/v1/appointments/{aid}", headers=other_h).status_code == 403
    assert client.get(f"/api/v1/appointments?patientId={v['patient']['id']}", headers=other_h).status_code == 403
    assert client.get("/api/v1/appointments", headers=other_h).json()["total"] == 0
    other_doc_h, _ = make_doctor(client, make_user, v["admin"], name="Dr B Rao")
    assert client.get(f"/api/v1/appointments/{aid}", headers=other_doc_h).status_code == 403
    assert client.get(f"/api/v1/appointments?doctorId={v['doctor']['id']}", headers=other_doc_h).status_code == 403
    assert client.get("/api/v1/appointments?status=booked", headers=v["admin"]).json()["total"] == 1


def test_doctor_leave_flags_booked_appointments(client, make_user):
    from app.core import events
    v = booked_visit(client, make_user)
    seen = []
    h = events.subscribe("appointment.leave_affected")(lambda appointment, **_: seen.append(appointment.id))
    try:
        client.post("/api/v1/doctors/me/leave", headers=v["doctor_h"], json={"day": NEXT_MONDAY})
    finally:
        events._handlers["appointment.leave_affected"].remove(h)
    assert seen == [v["appointment"]["id"]]
    flagged = client.get("/api/v1/appointments?needsReschedule=true", headers=v["admin"]).json()["items"]
    assert [a["id"] for a in flagged] == [v["appointment"]["id"]]
    assert client.get(f"/api/v1/appointments/{v['appointment']['id']}", headers=v["patient_h"]).json()["status"] == "BOOKED"


def test_no_show_job_is_registered_and_runs(client, make_user):
    v = booked_visit(client, make_user)
    clock.set_now(datetime.fromisoformat(v["appointment"]["end"]) + timedelta(minutes=31))
    r = client.post("/api/v1/admin/jobs/no-shows/run", headers=v["admin"])
    assert r.status_code == 200 and r.json()["processed"] == 1
