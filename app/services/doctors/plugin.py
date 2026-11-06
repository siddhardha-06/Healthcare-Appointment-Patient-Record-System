from app.core import scheduler
from app.services.doctors.router import router  # noqa: F401
from app.services.doctors.service import regenerate_all


def setup(app):
    scheduler.register_job("slot-generation", 24 * 3600, lambda db, now: regenerate_all(db))
