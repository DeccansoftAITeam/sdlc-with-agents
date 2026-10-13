"""RFC 7807 Problem Details for every error response (AD: errors)."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_JSON = "application/problem+json"


class Problem(BaseModel):
    """RFC 7807 body of every error response; `errors` only on 422."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    errors: list[dict[str, Any]] | None = None


# Documents every error status in OpenAPI (and replaces FastAPI's default 422 schema, which
# never matched what `install` returns). Found by contract fuzzing in M6.
PROBLEM_RESPONSES: dict[int | str, dict[str, Any]] = {
    "default": {"model": Problem, "description": "Error (RFC 7807 Problem Details)"}
}


class ProblemError(Exception):
    """Raise from services; rendered as Problem Details. Never include PII in `detail`."""

    def __init__(self, status: int, title: str, detail: str | None = None, type_: str = "about:blank"):
        self.status, self.title, self.detail, self.type = status, title, detail, type_


def problem(
    status: int, title: str, detail: str | None = None, type_: str = "about:blank", **extra: Any
) -> JSONResponse:
    body: dict[str, Any] = {"type": type_, "title": title, "status": status}
    if detail:
        body["detail"] = detail
    body.update(extra)
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON)


def install(app: FastAPI) -> None:
    @app.exception_handler(ProblemError)
    async def _problem(_: Request, exc: ProblemError) -> JSONResponse:
        return problem(exc.status, exc.title, exc.detail, exc.type)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return problem(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
        return problem(422, "Validation failed", errors=errors)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, __: Exception) -> JSONResponse:
        # No stack traces to clients; the exception is still recorded by telemetry.
        return problem(500, "Internal Server Error")
