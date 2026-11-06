"""Who may see which chart (HAP-F-040, HAP-SR-004), with every access audited (HAP-SR-007)."""
from fastapi import Request

from app.core import events
from app.core.errors import ApiError, forbidden
from app.core.roles import Role
from app.core.security import client_ip
from app.services.appointments.service import has_care_relationship
from app.services.doctors.service import doctor_for_user
from app.services.patients.service import get_patient, patient_for_user


def authorize_chart(db, user, patient_id: int, request: Request):
    """Return the Patient if `user` may read this chart; otherwise log DENIED and raise 403."""
    patient = get_patient(db, patient_id)
    allowed = False
    if user.role == Role.PATIENT.value:
        own = patient_for_user(db, user.id)
        allowed = own is not None and own.id == patient.id
        error = forbidden("You can only view your own records.")
    elif user.role == Role.DOCTOR.value:
        doctor = doctor_for_user(db, user.id)
        allowed = doctor is not None and has_care_relationship(db, doctor.id, patient.id)
        error = ApiError(403, "NO_CARE_RELATIONSHIP", "You can only open charts of your own patients.")
    else:
        error = forbidden("Your role cannot open medical records.")
    if not allowed:
        events.audit(db, user, "DENIED", "chart", patient.id, client_ip(request))
        db.commit()
        raise error
    return patient


def current_doctor(db, user):
    doctor = doctor_for_user(db, user.id)
    if doctor is None:
        raise ApiError(404, "NOT_FOUND", "No doctor profile is linked to your account.")
    return doctor
