"""Turns domain events into in-app notifications + emails (HAP-F-050). Messages never include
diagnoses, notes or medicine names (SAD 4.4)."""
from datetime import timedelta

from sqlalchemy import select

from app.core import events
from app.services.appointments.models import Appointment, Status
from app.services.doctors.models import Doctor
from app.services.notifications import mailer
from app.services.notifications.models import Notification, ReminderSent
from app.services.patients.models import Patient

REMINDER_LEAD = timedelta(hours=24)
REMINDER_TOLERANCE = timedelta(minutes=5)


def _when(appt: Appointment) -> str:
    return f"{appt.start:%a %d %b %Y, %H:%M}"


def notify(db, patient_id: int, kind: str, message: str, appointment_id: int | None = None, subject: str | None = None):
    patient = db.get(Patient, patient_id)
    db.add(Notification(patient_id=patient_id, kind=kind, message=message, appointment_id=appointment_id))
    email = patient.email if patient and patient.email else None
    if email is None and patient and patient.user_id:
        from app.services.auth.models import User
        user = db.get(User, patient.user_id)
        email = user.email if user else None
    mailer.queue(db, email, subject or "HAP Clinic: appointment update", f"Dear {patient.full_name},\n\n{message}\n\nHAP Clinic")


def _doctor(db, appt) -> str:
    d = db.get(Doctor, appt.doctor_id)
    return d.name if d else "your doctor"


@events.subscribe("appointment.booked")
def on_booked(db, appointment, **_):
    notify(db, appointment.patient_id, "BOOKED",
           f"Your appointment with {_doctor(db, appointment)} on {_when(appointment)} is confirmed.", appointment.id,
           "HAP Clinic: appointment confirmed")


@events.subscribe("appointment.rescheduled")
def on_rescheduled(db, appointment, **_):
    notify(db, appointment.patient_id, "RESCHEDULED",
           f"Your appointment with {_doctor(db, appointment)} has moved to {_when(appointment)}.", appointment.id,
           "HAP Clinic: appointment rescheduled")


@events.subscribe("appointment.cancelled")
def on_cancelled(db, appointment, **_):
    notify(db, appointment.patient_id, "CANCELLED",
           f"Your appointment with {_doctor(db, appointment)} on {_when(appointment)} was cancelled.", appointment.id,
           "HAP Clinic: appointment cancelled")


@events.subscribe("appointment.leave_affected")
def on_leave(db, appointment, **_):
    notify(db, appointment.patient_id, "DOCTOR_LEAVE",
           f"{_doctor(db, appointment)} is unavailable on {appointment.start:%d %b %Y}. Please reschedule your "
           f"appointment at {appointment.start:%H:%M}.", appointment.id, "HAP Clinic: please reschedule")


@events.subscribe("prescription.issued")
def on_prescription(db, prescription, **_):
    notify(db, prescription.patient_id, "PRESCRIPTION",
           "A new prescription is ready. Log in to view or download it.", prescription.appointment_id,
           "HAP Clinic: prescription ready")


def send_reminders(db, now) -> int:
    """Reminder 24 h (± 5 min) before each BOOKED appointment, sent once."""
    lo, hi = now + REMINDER_LEAD - REMINDER_TOLERANCE, now + REMINDER_LEAD + REMINDER_TOLERANCE
    due = list(db.scalars(select(Appointment).where(Appointment.status == Status.BOOKED,
                                                    Appointment.start >= lo, Appointment.start <= hi)))
    sent = 0
    for appt in due:
        if db.get(ReminderSent, appt.id):
            continue
        notify(db, appt.patient_id, "REMINDER",
               f"Reminder: you have an appointment with {_doctor(db, appt)} tomorrow, {_when(appt)}.", appt.id,
               "HAP Clinic: appointment reminder")
        db.add(ReminderSent(appointment_id=appt.id))
        sent += 1
    db.commit()
    return sent
