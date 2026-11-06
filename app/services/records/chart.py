from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock, crypto, events
from app.core.database import get_db
from app.core.errors import ApiError
from app.core.roles import Role
from app.core.security import client_ip, require_roles
from app.services.doctors.models import Doctor
from app.services.patients.service import patient_for_user
from app.services.records.access import authorize_chart
from app.services.records.models import Consultation, ConsultationVersion, Prescription
from app.services.records.schemas import ChartOut

router = APIRouter(tags=["records"])


def build_chart(db: Session, patient) -> dict:
    today = clock.now().date()
    dob = patient.date_of_birth
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    allergies = [a.strip() for a in (patient.allergies or "").split(",") if a.strip()]
    doctors = {d.id: d.name for d in db.scalars(select(Doctor))}
    visits = []
    for c in db.scalars(select(Consultation).where(Consultation.patient_id == patient.id).order_by(Consultation.created_at.desc())):
        latest = db.scalar(select(ConsultationVersion).where(ConsultationVersion.consultation_id == c.id,
                                                             ConsultationVersion.version == c.current_version))
        visits.append({"appointment_id": c.appointment_id, "consultation_id": c.id, "date": c.created_at,
                       "doctor": doctors.get(c.doctor_id, "?"), "diagnosis": crypto.decrypt(latest.diagnosis_enc),
                       "version": c.current_version})
    prescriptions = [{"prescription_id": p.id, "date": p.issued_at, "doctor": doctors.get(p.doctor_id, "?"),
                      "items": len(p.items)}
                     for p in db.scalars(select(Prescription).where(Prescription.patient_id == patient.id)
                                         .order_by(Prescription.issued_at.desc()))]
    return {"patient": {"id": patient.id, "mrn": patient.mrn, "name": patient.full_name, "age": age,
                        "gender": patient.gender, "blood_group": patient.blood_group, "allergies": allergies},
            "visits": visits, "prescriptions": prescriptions}


@router.get("/patients/me/records", response_model=ChartOut)
def my_records(request: Request, user=Depends(require_roles(Role.PATIENT)), db: Session = Depends(get_db)):
    """HAP-F-043: a patient's own history, read-only."""
    patient = patient_for_user(db, user.id)
    if patient is None:
        raise ApiError(404, "NOT_FOUND", "Please complete your patient profile first.")
    events.audit(db, user, "READ", "chart", patient.id, client_ip(request))
    db.commit()
    return build_chart(db, patient)


@router.get("/patients/{patient_id}/records", response_model=ChartOut)
def patient_chart(patient_id: int, request: Request, user=Depends(require_roles(Role.DOCTOR, Role.PATIENT)),
                  db: Session = Depends(get_db)):
    """HAP-F-040: allergies first; only for patients with a care relationship. Every view is audited."""
    patient = authorize_chart(db, user, patient_id, request)
    events.audit(db, user, "READ", "chart", patient.id, client_ip(request))
    db.commit()
    return build_chart(db, patient)
