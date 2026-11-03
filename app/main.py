"""Application factory.

Each service lives in app/services/<name>/ and exposes a `plugin.py` with a `router` and/or a
`setup(app)` function. create_app() discovers them, so a new service never has to edit this file.

Run locally:  uvicorn app.main:create_app --factory --reload
"""
import importlib
import logging
import pkgutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core import database, errors
from app.core.config import settings

API_PREFIX = "/api/v1"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
log = logging.getLogger("hap")


def discover_plugins():
    import app.services as services_pkg

    plugins = []
    for info in sorted(pkgutil.iter_modules(services_pkg.__path__), key=lambda m: m.name):
        try:
            plugins.append(importlib.import_module(f"app.services.{info.name}.plugin"))
        except ModuleNotFoundError as exc:
            if exc.name != f"app.services.{info.name}.plugin":
                raise
    return plugins


def create_app(database_url: str | None = None) -> FastAPI:
    database.configure(database_url or settings.database_url)
    plugins = discover_plugins()
    startup_hooks = []

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        for hook in startup_hooks:
            hook()
        yield

    app = FastAPI(title="Healthcare Appointment & Patient Record System", version="1.0", lifespan=lifespan)
    app.state.startup_hooks = startup_hooks
    errors.install(app)

    @app.get(f"{API_PREFIX}/health", tags=["health"])
    def health():
        return {"status": "ok"}

    for plugin in plugins:
        if hasattr(plugin, "router"):
            app.include_router(plugin.router, prefix=API_PREFIX)
        if hasattr(plugin, "setup"):
            plugin.setup(app)

    database.init_db()

    if FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app
