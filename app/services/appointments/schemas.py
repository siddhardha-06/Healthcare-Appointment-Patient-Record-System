from datetime import date, datetime
from typing import Literal

from pydantic import Field

from app.core.schemas import CamelModel


class BookIn(CamelModel):
    slot_id: int
    reason: str = Field(min_length=5, max_length=300)
    patient_id: int | None = None  # only when a Receptionist books for a patient


class RescheduleIn(CamelModel):
    new_slot_id: int


class StatusIn(CamelModel):
    status: Literal["CHECKED_IN", "COMPLETED", "NO_SHOW"]


class CancelIn(CamelModel):
    reason: str | None = None


class FreeSlot(CamelModel):
    slot_id: int
    start: datetime
    end: datetime


class FreeSlots(CamelModel):
    doctor_id: int
    date: date
    slots: list[FreeSlot]


class AppointmentOut(CamelModel):
    id: int
    slot_id: int
    patient_id: int
    patient_mrn: str | None = None
    patient_name: str | None = None
    doctor_id: int
    doctor_name: str | None = None
    start: datetime
    end: datetime
    reason: str
    status: str
    needs_reschedule: bool
    created_by: int


class AppointmentList(CamelModel):
    items: list[AppointmentOut]
    page: int
    total: int
