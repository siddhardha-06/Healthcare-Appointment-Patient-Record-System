import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import crypto, events
from app.core.database import get_db
from app.core.errors import ApiError, conflict, forbidden, not_found
from app.core.roles import Role
from app.core.security import client_ip, require_roles
from app.services.appointments.models import Status
from app.services.appointments.service import change_status, get_appointment
from app.services.records.access import authorize_chart, current_doctor
from app.services.records.models import Consultation, ConsultationVersion
from app.services.records.schemas_clinical import ConsultationEdit, ConsultationIn, ConsultationOut

router = APIRouter(tags=["records"])


def _version_out(v: ConsultationVersion, include_notes: bool = True) -> dict:
    return {"version": v.version, "symptoms": crypto.decrypt(v.symptoms_enc), "diagnosis": crypto.decrypt(v.diagnosis_enc),
            "notes": crypto.decrypt(v.notes_enc) if include_notes else None, "vitals": json.loads(v.vitals_json),
            "author_id": v.author_id, "change_reason": v.change_reason, "created_at": v.created_at}


def _new_version(consultation: Consultation, number: int, data: ConsultationIn, author_id: int,
                 reason: str | None) -> ConsultationVersion:
    return ConsultationVersion(consultation_id=consultation.id, version=number,
                               symptoms_enc=crypto.encrypt(data.symptoms), diagnosis_enc=crypto.encrypt(data.diagnosis),
                               notes_enc=crypto.encrypt(data.notes),
                               vitals_json=json.dumps(data.vitals.model_dump(by_alias=True, exclude_none=True)),
                               author_id=author_id, change_reason=reason)


def _out(db: Session, c: Consultation, include_versions: bool, include_notes: bool = True, status=None) -> dict:
    versions = list(db.scalars(select(ConsultationVersion).where(ConsultationVersion.consultation_id == c.id)
                               .order_by(ConsultationVersion.version)))
    current = next(v for v in versions if v.version == c.current_version)
    return {"consultation_id": c.id, "appointment_id": c.appointment_id, "version": c.current_version,
            "appointment_status": status, "current": _version_out(current, include_notes),
            "previous_versions": [_version_out(v, include_notes) for v in versions if v.version != c.current_version]
            if include_versions else []}


@router.post("/appointments/{appointment_id}/consultation", response_model=ConsultationOut, status_code=201)
def record_consultation(appointment_id: int, data: ConsultationIn, request: Request,
                        user=Depends(require_roles(Role.DOCTOR)), db: Session = Depends(get_db)):
    """HAP-F-041: notes for a CHECKED_IN appointment; saving completes the appointment."""
    doctor = current_doctor(db, user)
    appt = get_appointment(db, appointment_id)
    if appt.doctor_id != doctor.id:
        raise forbidden("This appointment belongs to another doctor.")
    if db.scalar(select(Consultation).where(Consultation.appointment_id == appt.id)):
        raise conflict("INVALID_STATUS_TRANSITION", "A consultation already exists. Edit it instead (PUT /consultations/{id}).")
    if appt.status != Status.CHECKED_IN:
        raise conflict("APPOINTMENT_NOT_CHECKED_IN", "The patient must be checked in before notes can be recorded.")
    c = Consultation(appointment_id=appt.id, patient_id=appt.patient_id, doctor_id=doctor.id, current_version=1)
    db.add(c)
    db.flush()
    db.add(_new_version(c, 1, data, user.id, None))
    change_status(db, appt, Status.COMPLETED)
    events.audit(db, user, "WRITE", "consultation", c.id, client_ip(request), "version 1")
    db.commit()
    return _out(db, c, include_versions=False, status=appt.status)


@router.put("/consultations/{consultation_id}", response_model=ConsultationOut)
def edit_consultation(consultation_id: int, data: ConsultationEdit, request: Request,
                      user=Depends(require_roles(Role.DOCTOR)), db: Session = Depends(get_db)):
    """HAP-F-044: an edit never overwrites – it adds version n+1 with author and time."""
    c = db.get(Consultation, consultation_id)
    if c is None:
        raise not_found("Consultation")
    doctor = current_doctor(db, user)
    if c.doctor_id != doctor.id:
        raise forbidden("Only the doctor who wrote this consultation can edit it.")
    c.current_version += 1
    db.add(_new_version(c, c.current_version, data, user.id, data.change_reason))
    events.audit(db, user, "WRITE", "consultation", c.id, client_ip(request), f"version {c.current_version}")
    db.commit()
    return _out(db, c, include_versions=True)


@router.get("/consultations/{consultation_id}", response_model=ConsultationOut)
def get_consultation(consultation_id: int, request: Request, include: str | None = None,
                     user=Depends(require_roles(Role.DOCTOR, Role.PATIENT)), db: Session = Depends(get_db)):
    c = db.get(Consultation, consultation_id)
    if c is None:
        raise not_found("Consultation")
    authorize_chart(db, user, c.patient_id, request)
    events.audit(db, user, "READ", "consultation", c.id, client_ip(request))
    db.commit()
    # patients do not see the doctor's private notes field (HAP-F-043)
    return _out(db, c, include_versions=(include == "versions"), include_notes=user.role == Role.DOCTOR.value)


@router.delete("/consultations/{consultation_id}")
def delete_consultation(consultation_id: int, user=Depends(require_roles(Role.DOCTOR, Role.ADMIN))):
    raise ApiError(405, "METHOD_NOT_ALLOWED", "Medical records are never deleted.")
