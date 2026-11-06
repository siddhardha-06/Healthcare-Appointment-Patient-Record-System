"""Admin dashboard (HAP-F-051) and CSV export (HAP-F-052)."""
import csv
import io
from datetime import date, datetime, timedelta

from sqlalchemy import func, select

from app.services.appointments.models import Appointment, Status
from app.services.doctors.models import Doctor, Slot, SlotStatus
from app.services.patients.models import Patient


def _day_bounds(day: date):
    lo = datetime.combine(day, datetime.min.time())
    return lo, lo + timedelta(days=1)


def dashboard(db, now: datetime) -> dict:
    today = now.date()
    lo, hi = _day_bounds(today)
    per_doctor = {}
    for doctor_id, status, n in db.execute(select(Appointment.doctor_id, Appointment.status, func.count())
                                           .where(Appointment.start >= lo, Appointment.start < hi)
                                           .group_by(Appointment.doctor_id, Appointment.status)):
        per_doctor.setdefault(doctor_id, {})[status] = n
    names = {d.id: d.name for d in db.scalars(select(Doctor))}
    today_rows = [{"doctorId": did, "doctor": names.get(did, "?"), "byStatus": counts, "total": sum(counts.values())}
                  for did, counts in sorted(per_doctor.items())]

    since = now - timedelta(days=30)
    finished = db.scalar(select(func.count()).select_from(Appointment).where(
        Appointment.start >= since, Appointment.start < now,
        Appointment.status.in_([Status.COMPLETED, Status.NO_SHOW, Status.CHECKED_IN])))
    no_shows = db.scalar(select(func.count()).select_from(Appointment).where(
        Appointment.start >= since, Appointment.start < now, Appointment.status == Status.NO_SHOW))
    no_show_rate = round(100.0 * no_shows / finished, 1) if finished else 0.0

    week_start = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
    week_end = week_start + timedelta(days=7)
    utilisation = []
    for doctor_id, name in sorted(names.items()):
        generated = db.scalar(select(func.count()).select_from(Slot).where(
            Slot.doctor_id == doctor_id, Slot.start >= week_start, Slot.start < week_end))
        used = db.scalar(select(func.count()).select_from(Slot).where(
            Slot.doctor_id == doctor_id, Slot.start >= week_start, Slot.start < week_end,
            Slot.status == SlotStatus.BOOKED))
        utilisation.append({"doctorId": doctor_id, "doctor": name, "generatedSlots": generated, "usedSlots": used,
                            "utilisationPercent": round(100.0 * used / generated, 1) if generated else 0.0})
    return {"date": today.isoformat(), "todayByDoctor": today_rows, "noShowRate30Days": no_show_rate,
            "utilisationThisWeek": utilisation}


def appointments_csv(db, start: date, end: date) -> tuple[str, int]:
    lo, _ = _day_bounds(start)
    _, hi = _day_bounds(end)
    rows = db.execute(select(Appointment, Doctor, Patient).join(Doctor, Doctor.id == Appointment.doctor_id)
                      .join(Patient, Patient.id == Appointment.patient_id)
                      .where(Appointment.start >= lo, Appointment.start < hi).order_by(Appointment.start)).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "time", "doctor", "department", "mrn", "status"])
    for appt, doctor, patient in rows:
        w.writerow([f"{appt.start:%Y-%m-%d}", f"{appt.start:%H:%M}", doctor.name, doctor.department, patient.mrn, appt.status])
    return buf.getvalue(), len(rows)
