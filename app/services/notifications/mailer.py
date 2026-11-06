"""SMTP delivery with retries (3 attempts, 5 minutes apart via the job). Without SMTP_HOST the
message is only recorded in the outbox (status LOGGED) – useful for local runs and tests."""
import smtplib
from email.message import EmailMessage

from sqlalchemy import select

from app.core import clock
from app.core.config import settings
from app.services.notifications.models import EmailOutbox

MAX_ATTEMPTS = 3


def queue(db, to_address: str | None, subject: str, body: str) -> EmailOutbox | None:
    if not to_address:
        return None
    mail = EmailOutbox(to_address=to_address, subject=subject, body=body)
    db.add(mail)
    db.flush()
    deliver(mail)
    return mail


def deliver(mail: EmailOutbox) -> None:
    mail.attempts += 1
    if not settings.smtp_host:
        mail.status, mail.sent_at = "LOGGED", clock.now()
        return
    try:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = settings.mail_from, mail.to_address, mail.subject
        msg.set_content(mail.body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.send_message(msg)
        mail.status, mail.sent_at = "SENT", clock.now()
    except (OSError, smtplib.SMTPException):
        mail.status = "FAILED" if mail.attempts >= MAX_ATTEMPTS else "PENDING"


def retry_pending(db, now=None) -> int:
    pending = list(db.scalars(select(EmailOutbox).where(EmailOutbox.status == "PENDING")))
    for mail in pending:
        deliver(mail)
    db.commit()
    return len(pending)
