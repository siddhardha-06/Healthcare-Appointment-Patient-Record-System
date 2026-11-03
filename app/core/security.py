"""Passwords (bcrypt, HAP-SR-001), JWT tokens (HAP-SR-002) and server-side role checks (HAP-SR-004)."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import ApiError
from app.core.roles import Role

_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=settings.bcrypt_rounds)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def create_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "role": role, "iat": int(now.timestamp()),
               "exp": int((now + timedelta(minutes=settings.jwt_minutes)).timestamp())}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "TOKEN_EXPIRED", "Your session has expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise ApiError(401, "UNAUTHENTICATED", "Invalid login token.")


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer), db: Session = Depends(get_db)):
    from app.services.auth.models import User  # local import: core must not depend on services at import time

    if creds is None or not creds.credentials:
        raise ApiError(401, "UNAUTHENTICATED", "Please log in.")
    payload = decode_token(creds.credentials)
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise ApiError(401, "UNAUTHENTICATED", "Account not found or deactivated.")
    return user


def require_roles(*roles: Role):
    """Dependency factory: `user = Depends(require_roles(Role.ADMIN))`. The role always comes from the
    signed token's user record, never from the request body (STRIDE: elevation of privilege)."""
    allowed = {r.value if isinstance(r, Role) else r for r in roles}

    def checker(user=Depends(get_current_user)):
        if user.role not in allowed:
            raise ApiError(403, "FORBIDDEN", "Your role is not allowed to use this feature.")
        return user

    return checker
