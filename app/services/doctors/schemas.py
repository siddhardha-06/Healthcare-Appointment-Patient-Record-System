from datetime import date, datetime, time
from typing import Literal

from pydantic import Field, model_validator

from app.core.schemas import CamelModel


class DoctorIn(CamelModel):
    user_id: int
    name: str = Field(min_length=2, max_length=120)
    specialization: str = Field(min_length=2, max_length=80)
    department: str = Field(min_length=2, max_length=80)
    qualification: str = Field(min_length=2, max_length=120)
    slot_minutes: Literal[10, 15, 20, 30] = 15


class DoctorUpdate(CamelModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    specialization: str | None = None
    department: str | None = None
    qualification: str | None = None
    slot_minutes: Literal[10, 15, 20, 30] | None = None
    is_active: bool | None = None


class DoctorOut(CamelModel):
    id: int
    user_id: int
    name: str
    specialization: str
    department: str
    qualification: str
    slot_minutes: int
    is_active: bool


class AvailabilityIn(CamelModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def _order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end time must be after start time")
        return self


class AvailabilityOut(AvailabilityIn):
    pass


class LeaveIn(CamelModel):
    day: date
    start_time: time | None = None  # partial leave; omit both for the whole day
    end_time: time | None = None


class SlotOut(CamelModel):
    id: int
    doctor_id: int
    start: datetime
    end: datetime
    status: str
