import re

from pydantic import Field, field_validator

from app.core.roles import Role
from app.core.schemas import CamelModel

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _check_email(v: str) -> str:
    v = v.strip().lower()
    if not EMAIL_RE.match(v):
        raise ValueError("must be a valid email address")
    return v


def _check_password(v: str) -> str:
    if len(v) < 8 or not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
        raise ValueError("must be at least 8 characters with a letter and a digit")
    return v


class RegisterIn(CamelModel):
    email: str
    password: str
    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = Field(default=None, pattern=r"^\d{10}$")
    role: str | None = None  # only PATIENT may self-register

    _email = field_validator("email")(_check_email)
    _password = field_validator("password")(_check_password)


class LoginIn(CamelModel):
    email: str
    password: str


class TokenOut(CamelModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    expires_in: int
    must_change_password: bool = False


class UserOut(CamelModel):
    id: int
    email: str
    role: str
    full_name: str
    phone: str | None = None
    is_active: bool


class StaffCreateIn(CamelModel):
    email: str
    full_name: str = Field(min_length=2, max_length=120)
    role: Role
    phone: str | None = Field(default=None, pattern=r"^\d{10}$")
    password: str | None = None

    _email = field_validator("email")(_check_email)

    @field_validator("role")
    @classmethod
    def _staff_only(cls, v: Role) -> Role:
        if v not in (Role.DOCTOR, Role.RECEPTIONIST):
            raise ValueError("must be DOCTOR or RECEPTIONIST")
        return v


class StaffCreateOut(UserOut):
    one_time_password: str | None = None


class UserUpdateIn(CamelModel):
    is_active: bool


class PasswordChangeIn(CamelModel):
    current_password: str
    new_password: str

    _password = field_validator("new_password")(_check_password)
