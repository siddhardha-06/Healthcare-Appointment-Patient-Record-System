"""Lightweight background scheduler (replaces APScheduler, see deviations log).
Services register jobs in their plugin.setup(); jobs run in one daemon thread when ENABLE_SCHEDULER=1,
and the Admin can run any job on demand (POST /api/v1/admin/jobs/{name}/run)."""
import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable

from app.core import clock
from app.core.database import SessionLocal

log = logging.getLogger("hap.jobs")


@dataclass
class Job:
    name: str
    every_seconds: int
    fn: Callable  # fn(db, now) -> int (items processed)
    last_run: float = 0.0


_jobs: dict[str, Job] = {}
_thread: threading.Thread | None = None
_stop = threading.Event()


def register_job(name: str, every_seconds: int, fn: Callable) -> None:
    _jobs[name] = Job(name, every_seconds, fn)


def jobs() -> list[Job]:
    return list(_jobs.values())


def run_job(name: str) -> int:
    job = _jobs[name]
    with SessionLocal() as db:
        result = job.fn(db, clock.now())
    job.last_run = time.time()
    return result or 0


def _loop(tick: float) -> None:
    while not _stop.is_set():
        for job in jobs():
            if time.time() - job.last_run >= job.every_seconds:
                try:
                    run_job(job.name)
                except Exception:  # keep the loop alive; the error is logged without patient data
                    log.exception("job %s failed", job.name)
        _stop.wait(tick)


def start(tick: float = 30.0) -> None:
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, args=(tick,), name="hap-scheduler", daemon=True)
    _thread.start()


def stop() -> None:
    _stop.set()
