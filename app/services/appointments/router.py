from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.database import get_db
from app.core.errors import ApiError, forbidden
from app.core.roles import Role
from app.core.security import get_current_user, require_roles
from app.services.appointments import service
from app.services.appointments.models import Appointment, Status
from app.services.appointments.schemas import (AppointmentList, AppointmentOut, BookIn, FreeSlots, RescheduleIn,
                                               StatusIn)
from app.services.doctors import service as doctors
from app.services.patients import service as patients

router = APIRouter(tags=["appointments"])


def _own_patient(db: Session, user):
    patient = patients.patient_for_user(db, user.id)
    if patient is None:
        raise ApiError(404, "NOT_FOUND", "Please complete your patient profile first.")
    return patient


def _visible(db: Session, appt: Appointment, user) -> None:
    """Record-level check (HAP-SR-004): patients see their own, doctors their own appointments."""
    if user.role == Role.PATIENT.value and appt.patient_id != _own_patient(db, user).id:
        raise forbidden("This appointment belongs to another patient.")
    if user.role == Role.DOCTOR.value:
        doctor = doctors.doctor_for_user(db, user.id)
        if doctor is None or appt.doctor_id != doctor.id:
            raise forbidden("This appointment belongs to another doctor.")


@router.get("/slots", response_model=FreeSlots)
def list_free_slots(doctor_id: int = Query(alias="doctorId"), day: date = Query(alias="date"),
                    user=Depends(get_current_user), db: Session = Depends(get_db)):
    """HAP-F-030: FREE slots for one doctor and date, up to 30 days ahead."""
    today = clock.now().date()
    if day < today or day > today + timedelta(days=doctors.WINDOW_DAYS):
        raise ApiError(400, "VALIDATION_ERROR", "Date must be between today and 30 days ahead.")
    doctors.get_doctor(db, doctor_id)
    slots = doctors.free_slots(db, doctor_id, day)
    return FreeSlots(doctor_id=doctor_id, date=day,
                     slots=[{"slot_id": s.id, "start": s.start, "end": s.end} for s in slots])


@router.post("/appointments", response_model=AppointmentOut, status_code=201)
def book(data: BookIn, user=Depends(require_roles(Role.PATIENT, Role.RECEPTIONIST)), db: Session = Depends(get_db)):
    """HAP-F-031 / F-035: a Patient books for themselves; a Receptionist books for a patient."""
    if user.role == Role.PATIENT.value:
        patient = _own_patient(db, user)
        if data.patient_id is not None and data.patient_id != patient.id:
            raise forbidden("Patients can only book for themselves.")
    else:
        if data.patient_id is None:
            raise ApiError(422, "VALIDATION_ERROR", "patientId: required when a Receptionist books")
        patient = patients.get_patient(db, data.patient_id)
    appt = service.book(db, patient, data.slot_id, data.reason, user.id)
    return service.to_out(db, appt)


@router.get("/appointments", response_model=AppointmentList)
def list_appointments(day: date | None = Query(default=None, alias="date"),
                      doctor_id: int | None = Query(default=None, alias="doctorId"),
                      patient_id: int | None = Query(default=None, alias="patientId"),
                      status: str | None = None,
                      needs_reschedule: bool | None = Query(default=None, alias="needsReschedule"),
                      page: int = Query(1, ge=1), user=Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(Appointment)
    if user.role == Role.PATIENT.value:
        own = _own_patient(db, user).id
        if patient_id is not None and patient_id != own:
            raise forbidden("Patients can only see their own appointments.")
        patient_id = own
    elif user.role == Role.DOCTOR.value:
        doctor = doctors.doctor_for_user(db, user.id)
        if doctor is None or (doctor_id is not None and doctor_id != doctor.id):
            raise forbidden("Doctors can only see their own schedule.")
        doctor_id = doctor.id
    if day:
        lo = datetime.combine(day, datetime.min.time())
        q = q.where(Appointment.start >= lo, Appointment.start < lo + timedelta(days=1))
    if doctor_id is not None:
        q = q.where(Appointment.doctor_id == doctor_id)
    if patient_id is not None:
        q = q.where(Appointment.patient_id == patient_id)
    if status:
        q = q.where(Appointment.status == status.upper())
    if needs_reschedule is not None:
        q = q.where(Appointment.needs_reschedule.is_(needs_reschedule))
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.scalars(q.order_by(Appointment.start).offset((page - 1) * service.PAGE_SIZE).limit(service.PAGE_SIZE))
    return AppointmentList(items=[service.to_out(db, a) for a in rows], page=page, total=total)


@router.get("/appointments/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    appt = service.get_appointment(db, appointment_id)
    _visible(db, appt, user)
    return service.to_out(db, appt)


@router.patch("/appointments/{appointment_id}/reschedule", response_model=AppointmentOut)
def reschedule(appointment_id: int, data: RescheduleIn, user=Depends(require_roles(Role.PATIENT, Role.RECEPTIONIST)),
               db: Session = Depends(get_db)):
    """HAP-F-033"""
    appt = service.get_appointment(db, appointment_id)
    _visible(db, appt, user)
    return service.to_out(db, service.reschedule(db, appt, data.new_slot_id, user))


@router.patch("/appointments/{appointment_id}/status", response_model=AppointmentOut)
def set_status(appointment_id: int, data: StatusIn,
               user=Depends(require_roles(Role.RECEPTIONIST, Role.DOCTOR, Role.ADMIN)), db: Session = Depends(get_db)):
    """HAP-F-034: Receptionist checks in; Doctor completes; Receptionist/Admin can mark NO_SHOW."""
    appt = service.get_appointment(db, appointment_id)
    _visible(db, appt, user)
    allowed = {Role.RECEPTIONIST.value: {Status.CHECKED_IN, Status.NO_SHOW},
               Role.DOCTOR.value: {Status.COMPLETED},
               Role.ADMIN.value: {Status.NO_SHOW}}[user.role]
    if data.status not in allowed:
        raise forbidden(f"Your role cannot set status {data.status}.")
    service.change_status(db, appt, data.status)
    db.commit()
    return service.to_out(db, appt)


@router.delete("/appointments/{appointment_id}", response_model=AppointmentOut)
def cancel(appointment_id: int, user=Depends(require_roles(Role.PATIENT, Role.RECEPTIONIST)),
           db: Session = Depends(get_db)):
    """HAP-F-033: the record is kept with status CANCELLED and the slot becomes FREE."""
    appt = service.get_appointment(db, appointment_id)
    _visible(db, appt, user)
    return service.to_out(db, service.cancel(db, appt, user))
