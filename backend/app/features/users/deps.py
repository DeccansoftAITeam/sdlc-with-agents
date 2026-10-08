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
