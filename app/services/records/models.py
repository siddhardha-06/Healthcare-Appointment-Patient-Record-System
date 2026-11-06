"""Clinical records are never deleted. Edits add a new ConsultationVersion (HAP-F-044).
Fields ending in _enc hold AES-256-GCM ciphertext (HAP-SR-006)."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import now
from app.core.database import Base


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), unique=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    versions: Mapped[list["ConsultationVersion"]] = relationship(order_by="ConsultationVersion.version")


class ConsultationVersion(Base):
    __tablename__ = "consultation_versions"
    __table_args__ = (UniqueConstraint("consultation_id", "version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    consultation_id: Mapped[int] = mapped_column(ForeignKey("consultations.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    symptoms_enc: Mapped[str] = mapped_column(Text)
    diagnosis_enc: Mapped[str] = mapped_column(Text)
    notes_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    vitals_json: Mapped[str] = mapped_column(Text, default="{}")
    author_id: Mapped[int] = mapped_column(Integer)
    change_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    items: Mapped[list["PrescriptionItem"]] = relationship(order_by="PrescriptionItem.id")


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id"), index=True)
    medicine_enc: Mapped[str] = mapped_column(Text)
    dosage: Mapped[str] = mapped_column(String(80))
    frequency: Mapped[str] = mapped_column(String(80))
    duration_days: Mapped[int] = mapped_column(Integer)
    instructions: Mapped[str | None] = mapped_column(String(300), nullable=True)
