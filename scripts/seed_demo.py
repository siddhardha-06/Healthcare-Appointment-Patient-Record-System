"""Fill a database with demo data for the sprint videos.

    python scripts/seed_demo.py            # uses DATABASE_URL or ./hap.db
    python scripts/seed_demo.py --reset    # delete ./hap.db first

All people and data are made up. Logins printed at the end (password for everyone: Demo@1234).
"""
import sys
from datetime import time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PASSWORD = "Demo@1234"
DOCTORS = [("dr.menon@hap.local", "Dr K Menon", "Cardiology"), ("dr.shah@hap.local", "Dr A Shah", "Paediatrics"),
           ("dr.iyer@hap.local", "Dr S Iyer", "General Medicine")]
PATIENTS = [("asha.rao@hap.local", "Asha Rao", "1992-03-11", "Female", "9876500001", "Penicillin"),
            ("ravi.kumar@hap.local", "Ravi Kumar", "1990-05-14", "Male", "9876500002", ""),
            ("meera.n@hap.local", "Meera N", "1985-12-02", "Female", "9876500003", "Sulfa drugs")]


def main(reset: bool) -> None:
    if reset and (ROOT / "hap.db").exists():
        (ROOT / "hap.db").unlink()
    from app.core import clock
    from app.core.config import settings
    from app.core.database import SessionLocal
    from app.main import create_app
    from app.services.appointments import service as booking
    from app.services.auth.service import create_user, ensure_admin, get_by_email
    from app.services.doctors.models import Availability, Doctor
    from app.services.doctors.service import free_slots, regenerate_slots
    from app.services.patients.models import Patient
    from app.services.patients.service import format_mrn

    create_app()
    with SessionLocal() as db:
        ensure_admin(db)
        if get_by_email(db, "reception@hap.local"):
            print("Demo data already present.")
            return
        create_user(db, "reception@hap.local", PASSWORD, "RECEPTIONIST", "Front Desk")
        doctors = []
        for email, name, spec in DOCTORS:
            u = create_user(db, email, PASSWORD, "DOCTOR", name)
            d = Doctor(user_id=u.id, name=name, specialization=spec, department=spec, qualification="MBBS, MD")
            db.add(d)
            db.flush()
            for wd in range(6):
                db.add(Availability(doctor_id=d.id, weekday=wd, start_time=time(9), end_time=time(13)))
                db.add(Availability(doctor_id=d.id, weekday=wd, start_time=time(15), end_time=time(18)))
            doctors.append(d)
        db.commit()
        for d in doctors:
            regenerate_slots(db, d)
        patients = []
        for email, name, dob, gender, phone, allergies in PATIENTS:
            u = create_user(db, email, PASSWORD, "PATIENT", name, phone)
            from datetime import date
            p = Patient(user_id=u.id, full_name=name, date_of_birth=date.fromisoformat(dob), gender=gender, phone=phone,
                        email=email, allergies=allergies or None, blood_group="O+", created_by=u.id)
            db.add(p)
            db.flush()
            p.mrn = format_mrn(p.id)
            patients.append(p)
        db.commit()
        tomorrow = clock.now().date() + timedelta(days=1)
        if tomorrow.weekday() == 6:
            tomorrow += timedelta(days=1)
        for i, p in enumerate(patients):
            slot = free_slots(db, doctors[0].id, tomorrow)[i]
            booking.book(db, p, slot.id, "Follow-up visit", p.user_id)
    print("Demo data ready. Password for every account:", PASSWORD, "(admin:", settings.admin_password + ")")
    print("  Admin        ", settings.admin_email)
    print("  Receptionist  reception@hap.local")
    for email, name, spec in DOCTORS:
        print(f"  Doctor        {email:24} {name}, {spec}")
    for email, name, *_ in PATIENTS:
        print(f"  Patient       {email:24} {name}")


if __name__ == "__main__":
    main("--reset" in sys.argv)
