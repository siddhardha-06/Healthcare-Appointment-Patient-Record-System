from datetime import datetime

from sqlalchemy import DateTime, Integer, String, event
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import now
from app.core.database import Base


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    action: Mapped[str] = mapped_column(String(10), index=True)  # READ / WRITE / DENIED / ADMIN
    record_type: Mapped[str] = mapped_column(String(40))
    record_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[str] = mapped_column(String(200), default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class AppendOnlyError(RuntimeError):
    pass


@event.listens_for(AuditLogEntry, "before_update")
def _no_update(*_):
    raise AppendOnlyError("Audit log entries cannot be changed.")


@event.listens_for(AuditLogEntry, "before_delete")
def _no_delete(*_):
    raise AppendOnlyError("Audit log entries cannot be deleted.")
