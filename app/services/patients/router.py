from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core import events
from app.core.database import get_db
from app.core.errors import ApiError
from app.core.roles import Role
from app.core.security import client_ip, require_roles
from app.services.patients import service
from app.services.patients.schemas import PatientIn, PatientList, PatientOut, PatientUpdate

router = APIRouter(tags=["patients"])
STAFF = (Role.RECEPTIONIST, Role.ADMIN)


@router.post("/patients/me", response_model=PatientOut, status_code=201)
def create_my_profile(data: PatientIn, confirm: bool = False, user=Depends(require_roles(Role.PATIENT)),
                      db: Session = Depends(get_db)):
    """HAP-F-010: a registered patient fills in their profile and gets an MRN."""
    if service.patient_for_user(db, user.id):
        raise ApiError(409, "PROFILE_EXISTS", "You already have a patient profile.")
    return service.create_patient(db, data, user.id, user.id, confirm)


@router.get("/patients/me", response_model=PatientOut)
def my_profile(user=Depends(require_roles(Role.PATIENT)), db: Session = Depends(get_db)):
    patient = service.patient_for_user(db, user.id)
    if patient is None:
        raise ApiError(404, "NOT_FOUND", "Please complete your patient profile first.")
    return patient


@router.patch("/patients/me", response_model=PatientOut)
def update_my_profile(data: PatientUpdate, user=Depends(require_roles(Role.PATIENT)), db: Session = Depends(get_db)):
    """HAP-F-011: patients edit their contact details, but never MRN or date of birth."""
    patient = service.patient_for_user(db, user.id)
    if patient is None:
        raise ApiError(404, "NOT_FOUND", "Please complete your patient profile first.")
    changes = data.model_dump(exclude_unset=True)
    if "mrn" in changes or "date_of_birth" in changes:
        raise ApiError(403, "FORBIDDEN", "MRN and date of birth can only be changed by the Admin.")
    for key, value in changes.items():
        setattr(patient, key, value)
    if "date_of_birth" in changes:
        events.audit(db, staff, "ADMIN", "patient", patient.id, client_ip(request), "date of birth corrected")
    db.commit()
    return patient


@router.post("/patients", response_model=PatientOut, status_code=201)
def register_walk_in(data: PatientIn, confirm: bool = False, staff=Depends(require_roles(*STAFF)),
                     db: Session = Depends(get_db)):
    """HAP-F-011: the Receptionist registers walk-in patients (no login needed)."""
    return service.create_patient(db, data, None, staff.id, confirm)


@router.get("/patients", response_model=PatientList)
def search_patients(q: str | None = None, page: int = Query(1, ge=1), staff=Depends(require_roles(*STAFF)),
                    db: Session = Depends(get_db)):
    items, total = service.search(db, q, page)
    return PatientList(items=items, page=page, total=total)


@router.get("/patients/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, staff=Depends(require_roles(*STAFF)), db: Session = Depends(get_db)):
    return service.get_patient(db, patient_id)


@router.patch("/patients/{patient_id}", response_model=PatientOut)
def staff_update(patient_id: int, data: PatientUpdate, request: Request, staff=Depends(require_roles(*STAFF)),
                 db: Session = Depends(get_db)):
    patient = service.get_patient(db, patient_id)
    changes = data.model_dump(exclude_unset=True)
    if "mrn" in changes:
        raise ApiError(403, "FORBIDDEN", "The MRN can never be changed.")
    if "date_of_birth" in changes and staff.role != Role.ADMIN.value:
        raise ApiError(403, "FORBIDDEN", "Only the Admin can correct a date of birth.")
    for key, value in changes.items():
        setattr(patient, key, value)
    if "date_of_birth" in changes:
        events.audit(db, staff, "ADMIN", "patient", patient.id, client_ip(request), "date of birth corrected")
    db.commit()
    return patient
