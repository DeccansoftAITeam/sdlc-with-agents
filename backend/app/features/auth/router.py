"""HTTP routes for TD-001 signup and verification. No business logic here (AGENTS.md)."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Response, status

from app.core.email import EmailSender, get_email_sender
from app.features.auth import service
from app.features.auth.passwords import BreachedPasswordChecker, get_breach_checker
from app.features.auth.schemas import Accepted, ResendIn, SignupIn, SignupOut, VerifyIn

router = APIRouter(tags=["auth"])

Sender = Annotated[EmailSender, Depends(get_email_sender)]
Checker = Annotated[BreachedPasswordChecker, Depends(get_breach_checker)]
RESEND_ACCEPTED = Accepted(status="If the account exists and is unverified, we sent a new link.")


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: SignupIn, checker: Checker, sender: Sender) -> SignupOut:
    return SignupOut(tenant_slug=await service.signup(body, checker, sender))


@router.post("/t/{slug}/auth/verify", status_code=status.HTTP_204_NO_CONTENT)
async def verify(slug: str, body: VerifyIn) -> Response:
    await service.verify_email(slug, body.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/t/{slug}/auth/verify/resend", status_code=status.HTTP_202_ACCEPTED)
async def resend(slug: str, body: ResendIn, sender: Sender, tasks: BackgroundTasks) -> Accepted:
    await service.resolve_tenant(slug)  # unknown tenant -> 404 before accepting
    tasks.add_task(service.resend_verification, slug, body.email, sender)
    return RESEND_ACCEPTED
