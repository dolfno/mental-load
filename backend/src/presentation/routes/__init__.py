from .tasks import router as tasks_router
from .members import router as members_router
from .history import router as history_router
from .auth import router as auth_router
from .admin import router as admin_router
from .notes import router as notes_router

__all__ = ["tasks_router", "members_router", "history_router", "auth_router", "admin_router", "notes_router"]
