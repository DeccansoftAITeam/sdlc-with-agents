import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


def _normalise(value: str) -> str:
    return value.strip().lower()


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(max_length=128)  # policy in auth.passwords.enforce_policy

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return _normalise(value)


class UserCreateIn(RegisterIn):
    role: Literal["staff", "admin"]  # customers register themselves (TD-002/AC-3)


class UserPatchIn(BaseModel):
    role: Literal["admin", "staff", "customer"] | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str
    is_active: bool
