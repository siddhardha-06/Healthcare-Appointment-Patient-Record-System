from fastapi import APIRouter, Depends

from app.core import scheduler
from app.core.config import settings
from app.core.errors import not_found
from app.core.roles import Role
from app.core.security import require_roles

router = APIRouter(tags=["jobs"])


@router.get("/admin/jobs")
def list_jobs(admin=Depends(require_roles(Role.ADMIN))):
    return [{"name": j.name, "everySeconds": j.every_seconds} for j in scheduler.jobs()]


@router.post("/admin/jobs/{name}/run")
def run(name: str, admin=Depends(require_roles(Role.ADMIN))):
    if name not in {j.name for j in scheduler.jobs()}:
        raise not_found("Job")
    return {"job": name, "processed": scheduler.run_job(name)}


def setup(app):
    if settings.enable_scheduler:
        app.state.startup_hooks.append(scheduler.start)
