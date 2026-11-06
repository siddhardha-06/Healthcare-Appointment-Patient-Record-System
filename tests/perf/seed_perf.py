"""TC-PERF-01 data set: 500 doctors, 10,000 patients, 50,000 appointments (HAP-NF-002).

    DATABASE_URL=sqlite:///./perf.db python tests/perf/seed_perf.py
Then start the server on the same DATABASE_URL and run tests/perf/locustfile.py.
"""
import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

N_DOCTORS, N_PATIENTS, N_APPOINTMENTS = 500, 10_000, 50_000
PASSWORD = "Perf@1234"


def main():
    from sqlalchemy import insert

    from app.core.database import SessionLocal
    from app.core.security import hash_password
    from app.main import create_app
    from app.services.appointments.models import Appointment
    from app.services.auth.models import User
    from app.services.doctors.models import Doctor, Slot
    from app.services.patients.models import Patient

    create_app()
    pw = hash_password(PASSWORD)
    rnd = random.Random(13)
    with SessionLocal() as db:
        db.execute(insert(User), [{"email": f"perf.doc{i}@hap.local", "password_hash": pw, "role": "DOCTOR",
                                   "full_name": f"Dr Perf {i}", "is_active": True} for i in range(N_DOCTORS)] +
                   [{"email": f"perf.pat{i}@hap.local", "password_hash": pw, "role": "PATIENT",
                     "full_name": f"Patient {i}", "is_active": True} for i in range(N_PATIENTS)])
        users = {u.email: u.id for u in db.query(User).filter(User.email.like("perf.%"))}
        db.execute(insert(Doctor), [{"user_id": users[f"perf.doc{i}@hap.local"], "name": f"Dr Perf {i}",
                                     "specialization": rnd.choice(["Cardiology", "ENT", "Paediatrics", "Dermatology"]),
                                     "department": "OPD", "qualification": "MBBS", "slot_minutes": 15, "is_active": True}
                                    for i in range(N_DOCTORS)])
        db.execute(insert(Patient), [{"user_id": users[f"perf.pat{i}@hap.local"], "mrn": f"HAP-P-{900000 + i:06d}",
                                      "full_name": f"Patient {i}", "date_of_birth": date(1980, 1, 1) + timedelta(days=i % 9000),
                                      "gender": "Other", "phone": f"8{i:09d}"} for i in range(N_PATIENTS)])
        doctor_ids = [d.id for d in db.query(Doctor.id)]
        patient_ids = [p.id for p in db.query(Patient.id)]
        start_day = date.today() - timedelta(days=60)
        slots = []
        for did in doctor_ids:
            for k in range(N_APPOINTMENTS // N_DOCTORS):
                day = start_day + timedelta(days=k // 8)
                s = datetime.combine(day, time(9)) + timedelta(minutes=15 * (k % 8))
                slots.append({"doctor_id": did, "start": s, "end": s + timedelta(minutes=15), "status": "BOOKED"})
        db.execute(insert(Slot), slots)
        rows = db.query(Slot.id, Slot.doctor_id, Slot.start, Slot.end).all()
        db.execute(insert(Appointment), [{"slot_id": sid, "patient_id": rnd.choice(patient_ids), "doctor_id": did,
                                          "start": s, "end": e, "reason": "Perf data", "status": "COMPLETED",
                                          "created_by": 0} for sid, did, s, e in rows])
        db.commit()
    print(f"Seeded {N_DOCTORS} doctors, {N_PATIENTS} patients, {len(rows)} appointments. Password: {PASSWORD}")


if __name__ == "__main__":
    main()
