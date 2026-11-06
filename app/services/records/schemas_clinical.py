"""Schemas for consultations and prescriptions (HAP-F-041, F-042, F-044)."""
import re as _re
from datetime import datetime

from pydantic import Field, field_validator

from app.core.schemas import CamelModel


class Vitals(CamelModel):
    bp: str | None = None
    pulse: int | None = Field(default=None, ge=20, le=300)
    temp_c: float | None = Field(default=None, ge=30, le=45, alias="tempC")
    weight_kg: float | None = Field(default=None, ge=0.5, le=400, alias="weightKg")

    @field_validator("bp")
    @classmethod
    def _bp(cls, v):
        if v is not None and not _re.fullmatch(r"\d{2,3}/\d{2,3}", v):
            raise ValueError("must look like 120/80")
        return v


class ConsultationIn(CamelModel):
    symptoms: str = Field(min_length=2, max_length=2000)
    vitals: Vitals = Vitals()
    diagnosis: str = Field(min_length=2, max_length=500)
    notes: str | None = Field(default=None, max_length=4000)


class ConsultationEdit(ConsultationIn):
    change_reason: str = Field(min_length=3, max_length=300)


class ConsultationVersionOut(CamelModel):
    version: int
    symptoms: str
    diagnosis: str
    notes: str | None = None
    vitals: dict
    author_id: int
    change_reason: str | None = None
    created_at: datetime


class ConsultationOut(CamelModel):
    consultation_id: int
    appointment_id: int
    version: int
    appointment_status: str | None = None
    current: ConsultationVersionOut
    previous_versions: list[ConsultationVersionOut] = []


class ItemIn(CamelModel):
    medicine: str = Field(min_length=2, max_length=120)
    dosage: str = Field(min_length=1, max_length=80)
    frequency: str = Field(min_length=1, max_length=80)
    duration_days: int = Field(ge=1, le=365)
    instructions: str | None = Field(default=None, max_length=300)


class PrescriptionIn(CamelModel):
    items: list[ItemIn] = Field(min_length=1, max_length=20)


class ItemOut(ItemIn):
    pass


class PrescriptionOut(CamelModel):
    prescription_id: int
    appointment_id: int
    date: datetime
    doctor: str
    patient_mrn: str
    patient_name: str
    items: list[ItemOut]
    version: int
    pdf_url: str
