from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock, events
from app.core.database import get_db
from app.core.errors import ApiError, forbidden, not_found
from app.core.roles import Role
from app.core.schemas import CamelModel
from app.core.security import client_ip, require_roles
from app.services.notifications import reports
from app.services.notifications.models import Notification
from app.services.patients.service import patient_for_user

router = APIRouter(tags=["notifications"])


class NotificationOut(CamelModel):
    id: int
    kind: str
    message: str
    appointment_id: int | None
    is_read: bool
    created_at: object


@router.get("/notifications/me", response_model=list[NotificationOut])
def my_notifications(user=Depends(require_roles(Role.PATIENT)), db: Session = Depends(get_db)):
    patient = patient_for_user(db, user.id)
    if patient is None:
        return []
    return list(db.scalars(select(Notification).where(Notification.patient_id == patient.id)
                           .order_by(Notification.id.desc()).limit(100)))


@router.patch("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: int, user=Depends(require_roles(Role.PATIENT)), db: Session = Depends(get_db)):
    n = db.get(Notification, notification_id)
    patient = patient_for_user(db, user.id)
    if n is None:
        raise not_found("Notification")
    if patient is None or n.patient_id != patient.id:
        raise forbidden("This notification belongs to another patient.")
    n.is_read = True
    db.commit()
    return n


@router.get("/admin/dashboard")
def dashboard(admin=Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    """HAP-F-051"""
    return reports.dashboard(db, clock.now())


@router.get("/admin/reports/appointments.csv")
def export_csv(request: Request, start: date = Query(alias="from"), end: date = Query(alias="to"),
               admin=Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    """HAP-F-052: date range of at most 366 days; no clinical notes; the export is audited."""
    if end < start or (end - start).days > 366:
        raise ApiError(422, "VALIDATION_ERROR", "The date range must be 0–366 days and 'to' must not be before 'from'.")
    text, count = reports.appointments_csv(db, start, end)
    events.audit(db, admin, "ADMIN", "export", None, client_ip(request), f"appointments {start}..{end} ({count} rows)")
    db.commit()
    return Response(text, media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="appointments_{start}_{end}.csv"'})
