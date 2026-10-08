"""Role checks (TD-002/AC-5). Authorization is enforced server-side on every admin route."""

from typing import Annotated

from fastapi import Depends

from app.core.errors import ProblemError
from app.core.security import Principal, current_principal


async def require_admin(principal: Annotated[Principal, Depends(current_principal)]) -> Principal:
    if principal.role != "admin":
        raise ProblemError(403, "Forbidden", "Admin role required.")
    return principal


Admin = Annotated[Principal, Depends(require_admin)]
