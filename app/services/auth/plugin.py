from app.core.database import SessionLocal
from app.services.auth.router import router  # noqa: F401  (registered by create_app)


def setup(app):
    def _bootstrap_admin():
        from app.services.auth.service import ensure_admin
        with SessionLocal() as db:
            ensure_admin(db)

    app.state.startup_hooks.append(_bootstrap_admin)
