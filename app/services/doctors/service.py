from datetime import date, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core import clock, events
from app.core.errors import ApiError, not_found
from app.services.doctors.models import Availability, Doctor, Leave, Slot, SlotStatus
from src.scheduling import generate_slots

WINDOW_DAYS = 30


def get_doctor(db: Session, doctor_id: int) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise not_found("Doctor")
    return doctor


def doctor_for_user(db: Session, user_id: int) -> Doctor | None:
    return db.scalar(select(Doctor).where(Doctor.user_id == user_id))


def check_no_overlap(ranges) -> None:
    by_day: dict[int, list] = {}
    for r in ranges:
        by_day.setdefault(r.weekday, []).append((r.start_time, r.end_time))
    for day, items in by_day.items():
        items.sort()
        for (s1, e1), (s2, e2) in zip(items, items[1:]):
            if s2 < e1:
                raise ApiError(422, "VALIDATION_ERROR", f"Availability ranges overlap on weekday {day}.")


def regenerate_slots(db: Session, doctor: Doctor, start_day: date | None = None, days: int = WINDOW_DAYS) -> int:
    """HAP-F-021: build FREE slots for the next `days` days from the weekly availability.
    Slots that are BOOKED are never touched; FREE slots outside the new availability are removed."""
    start_day = start_day or clock.now().date()
    end_day = start_day + timedelta(days=days)
    rules = list(db.scalars(select(Availability).where(Availability.doctor_id == doctor.id)))
    leave_days = set(db.scalars(select(Leave.day).where(Leave.doctor_id == doctor.id)))
    wanted: set[datetime] = set()
    new_slots = []
    for offset in range(days):
        day = start_day + timedelta(days=offset)
        for rule in (r for r in rules if r.weekday == day.weekday()):
            for s, e in generate_slots(datetime.combine(day, rule.start_time), datetime.combine(day, rule.end_time),
                                       doctor.slot_minutes):
                wanted.add(s)
                new_slots.append((s, e, SlotStatus.BLOCKED if day in leave_days else SlotStatus.FREE))
    existing = {s.start: s for s in db.scalars(select(Slot).where(
        Slot.doctor_id == doctor.id, Slot.start >= datetime.combine(start_day, datetime.min.time()),
        Slot.start < datetime.combine(end_day, datetime.min.time())))}
    for start, slot in existing.items():
        if start not in wanted and slot.status != SlotStatus.BOOKED:
            db.delete(slot)
    created = 0
    for s, e, status in new_slots:
        if s not in existing:
            db.add(Slot(doctor_id=doctor.id, start=s, end=e, status=status))
            created += 1
    db.commit()
    return created


def set_availability(db: Session, doctor: Doctor, ranges) -> None:
    check_no_overlap(ranges)
    db.execute(delete(Availability).where(Availability.doctor_id == doctor.id))
    for r in ranges:
        db.add(Availability(doctor_id=doctor.id, weekday=r.weekday, start_time=r.start_time, end_time=r.end_time))
    db.flush()
    regenerate_slots(db, doctor)


def mark_leave(db: Session, doctor: Doctor, day: date, start_time=None, end_time=None) -> int:
    """HAP-F-022: FREE slots in the period become BLOCKED; booked patients are notified (via event)."""
    if day < clock.now().date():
        raise ApiError(422, "VALIDATION_ERROR", "Leave cannot be in the past.")
    if start_time is None and end_time is None and db.scalar(
            select(Leave).where(Leave.doctor_id == doctor.id, Leave.day == day)) is None:
        db.add(Leave(doctor_id=doctor.id, day=day))
    lo = datetime.combine(day, start_time or datetime.min.time())
    hi = datetime.combine(day, end_time) if end_time else datetime.combine(day + timedelta(days=1), datetime.min.time())
    slots = list(db.scalars(select(Slot).where(Slot.doctor_id == doctor.id, Slot.start >= lo, Slot.start < hi)))
    blocked = 0
    for slot in slots:
        if slot.status == SlotStatus.FREE:
            slot.status = SlotStatus.BLOCKED
            blocked += 1
    events.publish("doctor.leave", db=db, doctor=doctor, start=lo, end=hi)
    db.commit()
    return blocked


def free_slots(db: Session, doctor_id: int, day: date):
    lo = max(datetime.combine(day, datetime.min.time()), clock.now())
    hi = datetime.combine(day + timedelta(days=1), datetime.min.time())
    return list(db.scalars(select(Slot).where(Slot.doctor_id == doctor_id, Slot.status == SlotStatus.FREE,
                                              Slot.start >= lo, Slot.start < hi).order_by(Slot.start)))


def regenerate_all(db: Session) -> int:
    """Nightly job: keep a rolling 30-day window of slots for every active doctor."""
    total = 0
    for doctor in db.scalars(select(Doctor).where(Doctor.is_active.is_(True))):
        total += regenerate_slots(db, doctor)
    return total
