from datetime import datetime

from app.core.schemas import CamelModel


class PatientSummary(CamelModel):
    id: int
    mrn: str
    name: str
    age: int
    gender: str
    blood_group: str | None = None
    allergies: list[str]


class VisitOut(CamelModel):
    appointment_id: int
    consultation_id: int
    date: datetime
    doctor: str
    diagnosis: str
    version: int


class PrescriptionRef(CamelModel):
    prescription_id: int
    date: datetime
    doctor: str
    items: int


class ChartOut(CamelModel):
    patient: PatientSummary
    visits: list[VisitOut]
    prescriptions: list[PrescriptionRef]

