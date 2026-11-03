"""Single source of 'now' so time rules (2-hour window, reminders, no-shows) can be tested."""
from datetime import datetime

_fixed: datetime | None = None


def now() -> datetime:
    return _fixed or datetime.now().replace(microsecond=0)


def set_now(value: datetime | None) -> None:
    global _fixed
    _fixed = value
