import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import settings
from app.core.errors import ApiError
from app.core.roles import Role
from app.core.security import hash_password, verify_password
from app.services.auth.models import User


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def create_user(db: Session, email: str, password: str, role: Role | str, full_name: str,
                phone: str | None = None, must_change_password: bool = False) -> User:
    if get_by_email(db, email):
        raise ApiError(409, "EMAIL_TAKEN", "An account with this email already exists.")
    user = User(email=email.strip().lower(), password_hash=hash_password(password),
                role=Role(role).value, full_name=full_name, phone=phone,
                must_change_password=must_change_password)
    db.add(user)
    db.flush()
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    """Login with lockout after 5 consecutive failures for 15 minutes (HAP-SR-005)."""
    user = get_by_email(db, email)
    generic = ApiError(401, "UNAUTHENTICATED", "Email or password is incorrect.")
    if user is None:
        verify_password(password, "$2b$04$" + "x" * 53)  # same work for unknown emails
        raise generic
    now = clock.now()
    if user.locked_until and user.locked_until > now:
        raise ApiError(423, "ACCOUNT_LOCKED", "Too many failed attempts. Try again in 15 minutes.")
    if not verify_password(password, user.password_hash):
        user.failed_logins = (user.failed_logins or 0) + 1
        if user.failed_logins >= settings.lockout_attempts:
            user.locked_until = now + timedelta(minutes=settings.lockout_minutes)
            user.failed_logins = 0
        db.commit()
        raise generic
    if not user.is_active:
        raise ApiError(403, "FORBIDDEN", "This account has been deactivated.")
    user.failed_logins = 0
    user.locked_until = None
    db.commit()
    return user


def new_one_time_password() -> str:
    return "Hap" + secrets.token_hex(4) + "9"


def ensure_admin(db: Session) -> None:
    """Create the first Admin account from ADMIN_EMAIL / ADMIN_PASSWORD if no Admin exists."""
    if db.scalar(select(User).where(User.role == Role.ADMIN.value)) is None:
        try:
            create_user(db, settings.admin_email, settings.admin_password, Role.ADMIN, "Hospital Administrator")
            db.commit()
        except IntegrityError:  # another server worker created it at the same moment
            db.rollback()
