from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import events
from app.core.database import get_db
from app.core.roles import Role
from app.core.schemas import CamelModel
from app.core.security import require_roles
from app.services.audit.models import AuditLogEntry

router = APIRouter(tags=["audit"])


class AuditOut(CamelModel):
    id: int
    user_id: int | None
    role: str | None
    action: str
    record_type: str
    record_id: int | None
    ip: str | None
    detail: str
    timestamp: datetime


@events.subscribe("audit")
def _store(db, user, action, record_type, record_id=None, ip=None, detail="", **_):
    db.add(AuditLogEntry(user_id=getattr(user, "id", None), role=getattr(user, "role", None), action=action,
                         record_type=record_type, record_id=record_id, ip=ip, detail=(detail or "")[:200]))


@router.get("/admin/audit", response_model=list[AuditOut])
def list_audit(record_type: str | None = Query(default=None, alias="recordType"),
               record_id: int | None = Query(default=None, alias="recordId"), action: str | None = None,
               limit: int = Query(200, le=1000), admin=Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    q = select(AuditLogEntry)
    if record_type:
        q = q.where(AuditLogEntry.record_type == record_type)
    if record_id is not None:
        q = q.where(AuditLogEntry.record_id == record_id)
    if action:
        q = q.where(AuditLogEntry.action == action.upper())
    return list(db.scalars(q.order_by(AuditLogEntry.id.desc()).limit(limit)))
