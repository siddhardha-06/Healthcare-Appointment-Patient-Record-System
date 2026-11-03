from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError, not_found
from app.services.patients.models import Patient
from app.services.patients.schemas import PatientIn

PAGE_SIZE = 50


def format_mrn(patient_id: int) -> str:
    return f"HAP-P-{patient_id:06d}"


def find_duplicate(db: Session, phone: str, date_of_birth) -> Patient | None:
    """HAP-F-012: same mobile number and date of birth."""
    return db.scalar(select(Patient).where(Patient.phone == phone, Patient.date_of_birth == date_of_birth))


def create_patient(db: Session, data: PatientIn, user_id: int | None, created_by: int | None, confirm: bool) -> Patient:
    dup = find_duplicate(db, data.phone, data.date_of_birth)
    if dup and not confirm:
        raise ApiError(409, "POSSIBLE_DUPLICATE",
                       f"A patient with this phone and date of birth already exists ({dup.mrn}). "
                       "Send confirm=true to create anyway.")
    patient = Patient(user_id=user_id, created_by=created_by, **data.model_dump())
    db.add(patient)
    db.flush()
    patient.mrn = format_mrn(patient.id)  # unique and never reused: derived from the primary key
    db.commit()
    return patient


def get_patient(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise not_found("Patient")
    return patient


def patient_for_user(db: Session, user_id: int) -> Patient | None:
    return db.scalar(select(Patient).where(Patient.user_id == user_id))


def search(db: Session, q: str | None, page: int):
    """HAP-F-013: name (partial, case-insensitive), MRN or phone; 50 per page."""
    stmt = select(Patient)
    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(Patient.full_name).like(like), Patient.mrn == q.strip().upper(),
                              Patient.phone == q.strip()))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = list(db.scalars(stmt.order_by(Patient.full_name).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)))
    return items, total
