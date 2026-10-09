"""Role checks (TD-002/AC-5). Authorization is enforced server-side on every admin route."""

from typing import Annotated

from fastapi import Depends

from app.core.errors import ProblemError
from app.core.security import Principal, current_principal
from app.features.users import service


async def require_admin(principal: Annotated[Principal, Depends(current_principal)]) -> Principal:
    # Check the token's role AND the database: a demoted or deactivated admin's access token
    # stays valid for up to 15 minutes, but must lose admin powers immediately.
    if principal.role != "admin" or await service.current_role(principal) != "admin":
        raise ProblemError(403, "Forbidden", "Admin role required.")
    return principal


Admin = Annotated[Principal, Depends(require_admin)]


async def member(principal: Annotated[Principal, Depends(current_principal)]) -> Principal:
    """Any active member. Uses the role as it is NOW in the database, not as it was when the
    token was issued (moved here from tickets/router.py once a second feature needed it)."""
    role = await service.current_role(principal)
    if role is None:
        raise ProblemError(403, "Forbidden", "Account deactivated.")
    return Principal(principal.user_id, principal.tenant_id, role)


Member = Annotated[Principal, Depends(member)]
