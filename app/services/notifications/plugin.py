from app.core import scheduler
from app.services.notifications import mailer, service  # noqa: F401  (service registers the event handlers)
from app.services.notifications.router import router  # noqa: F401


def setup(app):
    scheduler.register_job("reminders", 300, service.send_reminders)
    scheduler.register_job("email-retry", 300, mailer.retry_pending)
