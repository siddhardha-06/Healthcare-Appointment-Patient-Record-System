from app.core import scheduler
from app.services.appointments.router import router  # noqa: F401
from app.services.appointments.service import mark_no_shows


def setup(app):
    scheduler.register_job("no-shows", 300, mark_no_shows)
