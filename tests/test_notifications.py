"""TC-NOT-01 (HAP-F-050), HAP-F-051 dashboard, HAP-F-052 CSV export and the job runner."""
from datetime import datetime, timedelta

from app.core import clock
from app.services.notifications.models import EmailOutbox, Notification
from app.services.notifications.service import send_reminders
from tests.helpers_booking import NEXT_MONDAY, book, booked_visit, free_slots


def test_tc_not_01_confirmation_email_and_in_app_within_a_minute(client, make_user, db):
    v = booked_visit(client, make_user)
    mails = db.query(EmailOutbox).all()
    assert len(mails) == 1 and mails[0].to_address == v["patient_user"].email
    assert "confirmed" in mails[0].subject and mails[0].status in ("LOGGED", "SENT")
    assert (mails[0].sent_at - mails[0].created_at) <= timedelta(seconds=60)
    note = client.get("/api/v1/notifications/me", headers=v["patient_h"]).json()
    assert note[0]["kind"] == "BOOKED" and "Dr K Menon" in note[0]["message"]
    assert "Penicillin" not in mails[0].body  # no clinical data in emails


def test_tc_not_01_reminder_sent_once_24h_before(client, make_user, db):
    v = booked_visit(client, make_user)
    start = datetime.fromisoformat(v["appointment"]["start"])
    assert send_reminders(db, start - timedelta(hours=24, minutes=6)) == 0
    assert send_reminders(db, start - timedelta(hours=24, minutes=4)) == 1
    assert send_reminders(db, start - timedelta(hours=23, minutes=57)) == 0  # not twice
    kinds = [n.kind for n in db.query(Notification).order_by(Notification.id)]
    assert kinds == ["BOOKED", "REMINDER"]
    assert db.query(EmailOutbox).filter(EmailOutbox.subject.like("%reminder%")).count() == 1


def test_cancel_reschedule_leave_and_prescription_notifications(client, make_user, db):
    v = booked_visit(client, make_user)
    pat_h, aid = v["patient_h"], v["appointment"]["id"]
    new = free_slots(client, pat_h, v["doctor"]["id"])[2]
    client.patch(f"/api/v1/appointments/{aid}/reschedule", headers=pat_h, json={"newSlotId": new["slotId"]})
    client.post("/api/v1/doctors/me/leave", headers=v["doctor_h"], json={"day": NEXT_MONDAY})
    client.delete(f"/api/v1/appointments/{aid}", headers=pat_h)
    kinds = [n["kind"] for n in client.get("/api/v1/notifications/me", headers=pat_h).json()]
    assert kinds == ["CANCELLED", "DOCTOR_LEAVE", "RESCHEDULED", "BOOKED"]
    nid = client.get("/api/v1/notifications/me", headers=pat_h).json()[0]["id"]
    assert client.patch(f"/api/v1/notifications/{nid}/read", headers=pat_h).json()["isRead"] is True
    _, other_h = make_user("PATIENT")
    assert client.get("/api/v1/notifications/me", headers=other_h).json() == []
    assert client.patch(f"/api/v1/notifications/{nid}/read", headers=other_h).status_code == 403
    assert client.patch("/api/v1/notifications/9999/read", headers=pat_h).status_code == 404


def test_failed_smtp_is_retried_then_marked_failed(monkeypatch, client, make_user, db):
    from app.core.config import settings
    from app.services.notifications import mailer
    monkeypatch.setattr(settings, "smtp_host", "127.0.0.1")
    monkeypatch.setattr(settings, "smtp_port", 9)  # nothing listens here
    v = booked_visit(client, make_user)
    mail = db.query(EmailOutbox).one()
    assert mail.status == "PENDING" and mail.attempts == 1
    mailer.retry_pending(db)
    mailer.retry_pending(db)
    db.refresh(mail)
    assert mail.status == "FAILED" and mail.attempts == 3
    assert client.get("/api/v1/notifications/me", headers=v["patient_h"]).json()  # in-app still works


def test_f051_dashboard_figures(client, make_user, db):
    v = booked_visit(client, make_user)
    _, rec_h = make_user("RECEPTIONIST")
    today_slots = free_slots(client, rec_h, v["doctor"]["id"], "2026-11-02")
    book(client, rec_h, today_slots[0]["slotId"], patientId=v["patient"]["id"])
    clock.set_now(datetime(2026, 11, 2, 9, 0))
    d = client.get("/api/v1/admin/dashboard", headers=v["admin"]).json()
    assert d["todayByDoctor"][0]["byStatus"] == {"BOOKED": 1}
    util = d["utilisationThisWeek"][0]
    assert util["generatedSlots"] == 72 and util["usedSlots"] == 1 and util["utilisationPercent"] == round(100 / 72, 1)
    from app.services.appointments.service import mark_no_shows
    clock.set_now(datetime(2026, 11, 2, 11, 0))
    mark_no_shows(db)
    assert client.get("/api/v1/admin/dashboard", headers=v["admin"]).json()["noShowRate30Days"] == 100.0
    assert client.get("/api/v1/admin/dashboard", headers=v["patient_h"]).status_code == 403


def test_f052_csv_export(client, make_user, db):
    from app.services.audit.models import AuditLogEntry
    v = booked_visit(client, make_user)
    r = client.get("/api/v1/admin/reports/appointments.csv?from=2026-11-01&to=2026-11-30", headers=v["admin"])
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    lines = r.text.strip().splitlines()
    assert lines[0] == "date,time,doctor,department,mrn,status" and len(lines) == 2
    assert v["patient"]["mrn"] in lines[1] and "Fever" not in r.text
    assert db.query(AuditLogEntry).filter(AuditLogEntry.record_type == "export").count() == 1
    assert client.get("/api/v1/admin/reports/appointments.csv?from=2026-01-01&to=2027-06-01", headers=v["admin"]).status_code == 422
    assert client.get("/api/v1/admin/reports/appointments.csv?from=2026-11-30&to=2026-11-01", headers=v["admin"]).status_code == 422


def test_admin_job_runner(client, make_user):
    _, admin = make_user("ADMIN")
    names = {j["name"] for j in client.get("/api/v1/admin/jobs", headers=admin).json()}
    assert {"reminders", "email-retry"} <= names
    assert client.post("/api/v1/admin/jobs/reminders/run", headers=admin).json()["processed"] == 0
    assert client.post("/api/v1/admin/jobs/nope/run", headers=admin).status_code == 404


def test_scheduler_loop_runs_jobs():
    import time
    from app.core import scheduler
    calls = []
    scheduler.register_job("test-tick", 0, lambda db, now: calls.append(now) or 1)
    try:
        scheduler.start(tick=0.05)
        time.sleep(0.3)
    finally:
        scheduler.stop()
        scheduler._jobs.pop("test-tick")
    assert calls
