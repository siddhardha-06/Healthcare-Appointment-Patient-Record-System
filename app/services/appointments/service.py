"""Booking rules (HAP-F-031 … F-035). The conflict check and the insert run in ONE transaction:
lock the slot row -> check FREE -> check patient overlap -> insert -> mark slot BOOKED -> commit.
The partial unique index on active appointments per slot is the final guard (SAD 3.6)."""
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import clock, events
from app.core.errors import ApiError, conflict, not_found
from app.core.roles import Role
from app.services.appointments.models import Appointment, Status
from app.services.doctors.models import Doctor, Slot, SlotStatus
from app.services.patients.models import Patient

CHANGE_WINDOW = timedelta(hours=2)
NO_SHOW_AFTER = timedelta(minutes=30)
PAGE_SIZE = 50

TRANSITIONS = {
    Status.BOOKED: {Status.CHECKED_IN, Status.CANCELLED, Status.NO_SHOW},
    Status.CHECKED_IN: {Status.COMPLETED},
}


def get_appointment(db: Session, appointment_id: int) -> Appointment:
    appt = db.get(Appointment, appointment_id)
    if appt is None:
        raise not_found("Appointment")
    return appt


def _lock_slot(db: Session, slot_id: int) -> Slot:
    slot = db.scalar(select(Slot).where(Slot.id == slot_id).with_for_update())
    if slot is None:
        raise not_found("Slot")
    return slot


def _check_patient_overlap(db: Session, patient_id: int, slot: Slot, ignore_id: int | None = None) -> None:
    q = select(Appointment).where(Appointment.patient_id == patient_id, Appointment.status.in_(Status.ACTIVE),
                                  Appointment.start < slot.end, Appointment.end > slot.start)
    if ignore_id:
        q = q.where(Appointment.id != ignore_id)
    if db.scalar(q.limit(1)) is not None:
        raise conflict("PATIENT_OVERLAP", "You already have an appointment at this time.")


def _check_bookable(slot: Slot) -> None:
    if slot.status != SlotStatus.FREE:
        raise conflict("SLOT_TAKEN", "This slot was just booked. Please choose another time.")
    if slot.start <= clock.now():
        raise ApiError(422, "VALIDATION_ERROR", "This slot is in the past.")


def book(db: Session, patient: Patient, slot_id: int, reason: str, created_by: int) -> Appointment:
    try:
        slot = _lock_slot(db, slot_id)
        _check_bookable(slot)
        _check_patient_overlap(db, patient.id, slot)
        appt = Appointment(slot_id=slot.id, patient_id=patient.id, doctor_id=slot.doctor_id, start=slot.start,
                           end=slot.end, reason=reason, status=Status.BOOKED, created_by=created_by)
        db.add(appt)
        slot.status = SlotStatus.BOOKED
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        raise conflict("SLOT_TAKEN", "This slot was just booked. Please choose another time.")
    except ApiError:
        db.rollback()
        raise
    events.publish("appointment.booked", db=db, appointment=appt)
    db.commit()
    return appt


def _check_change_window(appt: Appointment, user) -> None:
    if user.role == Role.PATIENT.value and appt.start - clock.now() < CHANGE_WINDOW:
        raise conflict("CHANGE_WINDOW_CLOSED",
                       "Appointments can only be changed or cancelled up to 2 hours before the start time.")


def reschedule(db: Session, appt: Appointment, new_slot_id: int, user) -> Appointment:
    if appt.status != Status.BOOKED:
        raise conflict("INVALID_STATUS_TRANSITION", "Only BOOKED appointments can be rescheduled.")
    _check_change_window(appt, user)
    try:
        new_slot = _lock_slot(db, new_slot_id)
        _check_bookable(new_slot)
        _check_patient_overlap(db, appt.patient_id, new_slot, ignore_id=appt.id)
        old_slot = db.get(Slot, appt.slot_id)
        old_slot.status = SlotStatus.FREE
        appt.slot_id, appt.doctor_id = new_slot.id, new_slot.doctor_id
        appt.start, appt.end = new_slot.start, new_slot.end
        appt.needs_reschedule = False
        new_slot.status = SlotStatus.BOOKED
        db.commit()
    except IntegrityError:
        db.rollback()
        raise conflict("SLOT_TAKEN", "This slot was just booked. Please choose another time.")
    except ApiError:
        db.rollback()
        raise
    events.publish("appointment.rescheduled", db=db, appointment=appt)
    db.commit()
    return appt


def change_status(db: Session, appt: Appointment, new_status: str) -> Appointment:
    if new_status not in TRANSITIONS.get(appt.status, set()):
        raise conflict("INVALID_STATUS_TRANSITION", f"Cannot change an appointment from {appt.status} to {new_status}.")
    appt.status = new_status
    if new_status in (Status.CANCELLED,):
        slot = db.get(Slot, appt.slot_id)
        if slot and slot.status == SlotStatus.BOOKED:
            slot.status = SlotStatus.FREE  # freed immediately (HAP-F-033)
    db.flush()
    return appt


def cancel(db: Session, appt: Appointment, user) -> Appointment:
    if appt.status != Status.BOOKED:
        raise conflict("INVALID_STATUS_TRANSITION", f"A {appt.status} appointment cannot be cancelled.")
    _check_change_window(appt, user)
    change_status(db, appt, Status.CANCELLED)
    events.publish("appointment.cancelled", db=db, appointment=appt)
    db.commit()
    return appt


def mark_no_shows(db: Session, now=None) -> int:
    """HAP-F-034: BOOKED appointments never checked in are NO_SHOW 30 minutes after the slot ends."""
    now = now or clock.now()
    late = list(db.scalars(select(Appointment).where(Appointment.status == Status.BOOKED, Appointment.start < now)))
    count = 0
    for appt in late:
        if appt.end + NO_SHOW_AFTER <= now:
            appt.status = Status.NO_SHOW
            count += 1
    db.commit()
    return count


def has_care_relationship(db: Session, doctor_id: int, patient_id: int) -> bool:
    """The patient has or had a (non-cancelled) appointment with this doctor (HAP-F-040, HAP-SR-004)."""
    return db.scalar(select(func.count()).select_from(Appointment).where(
        Appointment.doctor_id == doctor_id, Appointment.patient_id == patient_id,
        Appointment.status != Status.CANCELLED)) > 0


def to_out(db: Session, appt: Appointment) -> dict:
    patient = db.get(Patient, appt.patient_id)
    doctor = db.get(Doctor, appt.doctor_id)
    return {"id": appt.id, "slot_id": appt.slot_id, "patient_id": appt.patient_id,
            "patient_mrn": patient.mrn if patient else None, "patient_name": patient.full_name if patient else None,
            "doctor_id": appt.doctor_id, "doctor_name": doctor.name if doctor else None, "start": appt.start,
            "end": appt.end, "reason": appt.reason, "status": appt.status,
            "needs_reschedule": appt.needs_reschedule, "created_by": appt.created_by}


@events.subscribe("doctor.leave")
def _flag_appointments_on_leave(db, doctor, start, end, **_):
    """HAP-F-022: appointments in the leave period are flagged for rescheduling and the patient is told."""
    affected = list(db.scalars(select(Appointment).where(Appointment.doctor_id == doctor.id,
                                                         Appointment.status == Status.BOOKED,
                                                         Appointment.start >= start, Appointment.start < end)))
    for appt in affected:
        appt.needs_reschedule = True
        events.publish("appointment.leave_affected", db=db, appointment=appt)
