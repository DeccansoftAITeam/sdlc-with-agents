"""FastAPI entry point. Routers only wire HTTP to feature services: no business logic here."""

from fastapi import FastAPI

from app.core import errors, ratelimit, security, telemetry
from app.core.config import get_settings
from app.features.auth.router import router as auth_router
from app.features.flags.router import router as flags_router
from app.features.health.router import router as health_router
from app.features.notifications.router import router as notifications_router
from app.features.sla.router import router as sla_router
from app.features.tickets.router import router as tickets_router
from app.features.users.router import router as users_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    errors.install(app)
    ratelimit.install(app)
    security.check_signing_key()
    telemetry.install(app, settings)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(tickets_router)
    app.include_router(sla_router)
    app.include_router(notifications_router)
    app.include_router(flags_router)
    return app


app = create_app()
