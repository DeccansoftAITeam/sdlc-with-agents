from pydantic import BaseModel, EmailStr, Field, field_validator

SLUG_PATTERN = r"^[a-z0-9-]{3,40}$"


def _normalise_email(value: str) -> str:
    return value.strip().lower()


class SignupIn(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    slug: str = Field(pattern=SLUG_PATTERN)
    admin_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(max_length=128)  # length policy enforced in passwords.enforce_policy

    _norm = field_validator("email")(_normalise_email)


class SignupOut(BaseModel):
    tenant_slug: str


class VerifyIn(BaseModel):
    token: str = Field(min_length=20, max_length=100)


class ResendIn(BaseModel):
    email: EmailStr

    _norm = field_validator("email")(_normalise_email)


class Accepted(BaseModel):
    status: str
