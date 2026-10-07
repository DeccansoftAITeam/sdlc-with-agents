"""Feature folders: backend/app/features/<feature>/ (router, schemas, service, models).

`load_models()` imports every feature's `models` module so Alembic sees all tables.
"""

import importlib
import pkgutil


def load_models() -> None:
    for mod in pkgutil.iter_modules(__path__):
        try:
            importlib.import_module(f"{__name__}.{mod.name}.models")
        except ModuleNotFoundError as exc:
            if exc.name != f"{__name__}.{mod.name}.models":
                raise
