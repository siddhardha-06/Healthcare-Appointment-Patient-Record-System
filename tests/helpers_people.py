"""Test helpers for patients and doctors (used by several test files)."""
from datetime import datetime

from app.core import clock

MONDAY_8AM = datetime(2026, 11, 2, 8, 0)  # a fixed Monday so slot maths is predictable


def start_clock(at: datetime = MONDAY_8AM) -> datetime:
    clock.set_now(at)
    return at


def patient_body(**overrides):
    body = {"fullName": "Ravi Kumar", "dateOfBirth": "1990-05-14", "gender": "Male", "phone": "9876500001",
            "address": "12 MG Road, Bengaluru", "bloodGroup": "B+", "allergies": "Penicillin",
            "emergencyContactName": "Sita Kumar", "emergencyContactPhone": "9876500099"}
    body.update(overrides)
    return body


def make_patient(client, make_user, **overrides):
    """A registered Patient with a completed profile -> (user, headers, patient_json)."""
    user, headers = make_user("PATIENT")
    overrides.setdefault("phone", user.phone)
    r = client.post("/api/v1/patients/me", headers=headers, json=patient_body(fullName=user.full_name, **overrides))
    assert r.status_code == 201, r.text
    return user, headers, r.json()


def make_doctor(client, make_user, admin_headers, availability=None, specialization="Cardiology",
                name="Dr K Menon", slot_minutes=15):
    """A Doctor account + profile + weekly availability -> (headers, doctor_json)."""
    user, headers = make_user("DOCTOR", full_name=name)
    r = client.post("/api/v1/doctors", headers=admin_headers,
                    json={"userId": user.id, "name": name, "specialization": specialization,
                          "department": specialization, "qualification": "MBBS, MD", "slotMinutes": slot_minutes})
    assert r.status_code == 201, r.text
    doctor = r.json()
    ranges = availability if availability is not None else [
        {"weekday": d, "startTime": "09:00", "endTime": "12:00"} for d in range(0, 6)]
    r = client.put("/api/v1/doctors/me/availability", headers=headers, json=ranges)
    assert r.status_code == 200, r.text
    return headers, doctor
