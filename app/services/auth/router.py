from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import events
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import ApiError, not_found
from app.core.roles import Role
from app.core.security import client_ip, create_token, get_current_user, hash_password, require_roles, verify_password
from app.services.auth import service
from app.services.auth.models import User
from app.services.auth.schemas import (LoginIn, PasswordChangeIn, RegisterIn, StaffCreateIn, StaffCreateOut,
                                       TokenOut, UserOut, UserUpdateIn)

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    """HAP-F-001: only Patients can self-register."""
    if data.role and data.role.upper() != Role.PATIENT.value:
        raise ApiError(403, "FORBIDDEN", "Only patients can register themselves. Staff accounts are created by the Admin.")
    user = service.create_user(db, data.email, data.password, Role.PATIENT, data.full_name, data.phone)
    db.commit()
    return user


@router.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = service.authenticate(db, data.email, data.password)
    return TokenOut(access_token=create_token(user.id, user.role), role=user.role,
                    expires_in=settings.jwt_minutes * 60, must_change_password=user.must_change_password)


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/auth/change-password", status_code=204)
def change_password(data: PasswordChangeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.current_password, user.password_hash):
        raise ApiError(401, "UNAUTHENTICATED", "Current password is incorrect.")
    user.password_hash = hash_password(data.new_password)
    user.must_change_password = False
    db.commit()


@router.get("/admin/users", response_model=list[UserOut])
def list_users(role: Role | None = None, admin: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    q = select(User).order_by(User.id)
    if role:
        q = q.where(User.role == role.value)
    return list(db.scalars(q))


@router.post("/admin/users", response_model=StaffCreateOut, status_code=201)
def create_staff(data: StaffCreateIn, request: Request, admin: User = Depends(require_roles(Role.ADMIN)),
                 db: Session = Depends(get_db)):
    """HAP-F-003: Admin creates Doctor and Receptionist accounts."""
    otp = None if data.password else service.new_one_time_password()
    user = service.create_user(db, data.email, data.password or otp, data.role, data.full_name, data.phone,
                               must_change_password=otp is not None)
    events.audit(db, admin, "ADMIN", "user", user.id, client_ip(request), f"create {user.role}")
    db.commit()
    out = StaffCreateOut.model_validate(user)
    out.one_time_password = otp
    return out


@router.patch("/admin/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdateIn, request: Request,
                admin: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    """HAP-F-003: deactivate / reactivate non-Admin accounts."""
    user = db.get(User, user_id)
    if user is None:
        raise not_found("User")
    if user.role == Role.ADMIN.value:
        raise ApiError(403, "FORBIDDEN", "Admin accounts cannot be deactivated here.")
    user.is_active = data.is_active
    events.audit(db, admin, "ADMIN", "user", user.id, client_ip(request),
                 "activate" if data.is_active else "deactivate")
    db.commit()
    return user
