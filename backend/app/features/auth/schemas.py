from pydantic import BaseModel, EmailStr, Field, field_validator

SLUG_PATTERN = r"^[a-z0-9-]{3,40}$"


class SignupIn(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    slug: str = Field(pattern=SLUG_PATTERN)
    admin_name: str = Field(min_length=1, max_length=200)
    email: EmailStr  # an identifier only: TicketDesk never sends email
    password: str = Field(max_length=128)  # length policy enforced in passwords.enforce_policy

    @field_validator("email")
    @classmethod
    def _normalise_email(cls, value: str) -> str:
        return value.strip().lower()


class SignupOut(BaseModel):
    tenant_slug: str
