from datetime import date
from typing import Literal

from pydantic import Field, field_validator

from app.core import clock
from app.core.schemas import CamelModel

Phone = Field(pattern=r"^\d{10}$")


class PatientIn(CamelModel):
    full_name: str = Field(min_length=2, max_length=120)
    date_of_birth: date
    gender: Literal["Male", "Female", "Other"]
    phone: str = Phone
    email: str | None = None
    address: str | None = Field(default=None, max_length=500)
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] | None = None
    allergies: str | None = Field(default=None, max_length=500)
    emergency_contact_name: str | None = Field(default=None, max_length=120)
    emergency_contact_phone: str | None = Field(default=None, pattern=r"^\d{10}$")

    @field_validator("date_of_birth")
    @classmethod
    def _not_future(cls, v: date) -> date:
        if v > clock.now().date():
            raise ValueError("cannot be in the future")
        return v


class PatientUpdate(CamelModel):
    """Fields a patient may change on their own profile (not MRN or date of birth)."""
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, pattern=r"^\d{10}$")
    email: str | None = None
    address: str | None = Field(default=None, max_length=500)
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] | None = None
    allergies: str | None = Field(default=None, max_length=500)
    emergency_contact_name: str | None = Field(default=None, max_length=120)
    emergency_contact_phone: str | None = Field(default=None, pattern=r"^\d{10}$")
    mrn: str | None = None
    date_of_birth: date | None = None


class PatientOut(CamelModel):
    id: int
    mrn: str
    full_name: str
    date_of_birth: date
    gender: str
    phone: str
    email: str | None = None
    address: str | None = None
    blood_group: str | None = None
    allergies: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class PatientList(CamelModel):
    items: list[PatientOut]
    page: int
    total: int
