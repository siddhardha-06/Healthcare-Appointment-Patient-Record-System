from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import events
from app.core.database import get_db
from app.core.errors import ApiError
from app.core.roles import Role
from app.core.security import client_ip, get_current_user, require_roles
from app.services.auth.models import User
from app.services.doctors import service
from app.services.doctors.models import Availability, Doctor, Slot
from app.services.doctors.schemas import (AvailabilityIn, AvailabilityOut, DoctorIn, DoctorOut, DoctorUpdate,
                                          LeaveIn, SlotOut)

router = APIRouter(tags=["doctors"])


def _my_doctor(db: Session, user) -> Doctor:
    doctor = service.doctor_for_user(db, user.id)
    if doctor is None:
        raise ApiError(404, "NOT_FOUND", "No doctor profile is linked to your account yet. Ask the Admin.")
    return doctor


@router.post("/doctors", response_model=DoctorOut, status_code=201)
def create_doctor(data: DoctorIn, request: Request, admin=Depends(require_roles(Role.ADMIN)),
                  db: Session = Depends(get_db)):
    """HAP-F-020: the Admin adds a doctor profile linked to a Doctor account."""
    account = db.get(User, data.user_id)
    if account is None or account.role != Role.DOCTOR.value:
        raise ApiError(422, "VALIDATION_ERROR", "userId must be an existing Doctor account.")
    if service.doctor_for_user(db, data.user_id):
        raise ApiError(409, "PROFILE_EXISTS", "This account already has a doctor profile.")
    doctor = Doctor(**data.model_dump())
    db.add(doctor)
    db.flush()
    events.audit(db, admin, "ADMIN", "doctor", doctor.id, client_ip(request), "create doctor profile")
    db.commit()
    return doctor


@router.patch("/doctors/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id: int, data: DoctorUpdate, request: Request, admin=Depends(require_roles(Role.ADMIN)),
                  db: Session = Depends(get_db)):
    doctor = service.get_doctor(db, doctor_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(doctor, key, value)  # a new slot length only affects slots generated afterwards
    events.audit(db, admin, "ADMIN", "doctor", doctor.id, client_ip(request), "edit doctor profile")
    db.commit()
    return doctor


@router.get("/doctors", response_model=list[DoctorOut])
def search_doctors(specialization: str | None = None, name: str | None = None, user=Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """Used by HAP-F-030: search active doctors by specialization or name."""
    q = select(Doctor).where(Doctor.is_active.is_(True))
    if specialization:
        q = q.where(func.lower(Doctor.specialization) == specialization.strip().lower())
    if name:
        q = q.where(func.lower(Doctor.name).like(f"%{name.strip().lower()}%"))
    return list(db.scalars(q.order_by(Doctor.name)))


@router.get("/doctors/me", response_model=DoctorOut)
def my_doctor_profile(user=Depends(require_roles(Role.DOCTOR)), db: Session = Depends(get_db)):
    return _my_doctor(db, user)


@router.get("/doctors/me/availability", response_model=list[AvailabilityOut])
def my_availability(user=Depends(require_roles(Role.DOCTOR)), db: Session = Depends(get_db)):
    doctor = _my_doctor(db, user)
    return list(db.scalars(select(Availability).where(Availability.doctor_id == doctor.id)
                           .order_by(Availability.weekday, Availability.start_time)))


@router.put("/doctors/me/availability", response_model=list[AvailabilityOut])
def set_my_availability(ranges: list[AvailabilityIn], user=Depends(require_roles(Role.DOCTOR)),
                        db: Session = Depends(get_db)):
    """HAP-F-021: replace the weekly availability and regenerate slots for the next 30 days."""
    doctor = _my_doctor(db, user)
    service.set_availability(db, doctor, ranges)
    return ranges


@router.post("/doctors/me/leave")
def mark_my_leave(data: LeaveIn, user=Depends(require_roles(Role.DOCTOR)), db: Session = Depends(get_db)):
    """HAP-F-022"""
    doctor = _my_doctor(db, user)
    blocked = service.mark_leave(db, doctor, data.day, data.start_time, data.end_time)
    return {"day": data.day, "blockedSlots": blocked}


@router.get("/doctors/me/slots", response_model=list[SlotOut])
def my_slots(day: date, user=Depends(require_roles(Role.DOCTOR)), db: Session = Depends(get_db)):
    doctor = _my_doctor(db, user)
    lo = datetime.combine(day, datetime.min.time())
    return list(db.scalars(select(Slot).where(Slot.doctor_id == doctor.id, Slot.start >= lo,
                                              Slot.start < lo + timedelta(days=1)).order_by(Slot.start)))


@router.get("/doctors/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return service.get_doctor(db, doctor_id)


@router.post("/admin/doctors/regenerate-slots")
def regenerate(admin=Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    return {"createdSlots": service.regenerate_all(db)}
