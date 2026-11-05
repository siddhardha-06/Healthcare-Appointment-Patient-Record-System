"""Booking helpers shared by appointment, record and notification tests."""
from datetime import timedelta

from tests.helpers_people import MONDAY_8AM, make_doctor, make_patient, start_clock

NEXT_MONDAY = (MONDAY_8AM + timedelta(days=7)).date().isoformat()


def free_slots(client, headers, doctor_id, day=NEXT_MONDAY):
    r = client.get(f"/api/v1/slots?doctorId={doctor_id}&date={day}", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["slots"]


def book(client, headers, slot_id, reason="Fever for 3 days", **extra):
    return client.post("/api/v1/appointments", headers=headers, json={"slotId": slot_id, "reason": reason, **extra})


def booked_visit(client, make_user, admin_headers=None, day=NEXT_MONDAY):
    """Clock at Monday 08:00, one doctor (Mon–Sat 09–12), one patient with a BOOKED appointment.
    Returns dict with headers and json for doctor, patient and the appointment."""
    start_clock()
    if admin_headers is None:
        _, admin_headers = make_user("ADMIN")
    doc_h, doctor = make_doctor(client, make_user, admin_headers)
    pat_user, pat_h, patient = make_patient(client, make_user)
    slot = free_slots(client, pat_h, doctor["id"], day)[0]
    r = book(client, pat_h, slot["slotId"])
    assert r.status_code == 201, r.text
    return {"admin": admin_headers, "doctor_h": doc_h, "doctor": doctor, "patient_user": pat_user,
            "patient_h": pat_h, "patient": patient, "appointment": r.json()}
