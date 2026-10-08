"""FastAPI entry point. Routers only wire HTTP to feature services: no business logic here."""

from fastapi import FastAPI

from app.core import errors, ratelimit, security, telemetry
from app.core.config import get_settings
from app.features.auth.router import router as auth_router
from app.features.health.router import router as health_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    errors.install(app)
    ratelimit.install(app)
    security.check_signing_key()
    telemetry.install(app, settings)
    app.include_router(health_router)
    app.include_router(auth_router)
    return app


app = create_app()
