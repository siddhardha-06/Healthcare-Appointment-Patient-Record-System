from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SlotStatus:
    FREE = "FREE"
    BOOKED = "BOOKED"
    BLOCKED = "BLOCKED"


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    specialization: Mapped[str] = mapped_column(String(80), index=True)
    department: Mapped[str] = mapped_column(String(80))
    qualification: Mapped[str] = mapped_column(String(120))
    slot_minutes: Mapped[int] = mapped_column(Integer, default=15)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Availability(Base):
    __tablename__ = "availability"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    weekday: Mapped[int] = mapped_column(Integer)  # 0 = Monday … 6 = Sunday
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)


class Leave(Base):
    __tablename__ = "doctor_leave"
    __table_args__ = (UniqueConstraint("doctor_id", "day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    day: Mapped[date] = mapped_column(Date)


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (UniqueConstraint("doctor_id", "start"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    start: Mapped[datetime] = mapped_column(DateTime, index=True)
    end: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(10), default=SlotStatus.FREE)
