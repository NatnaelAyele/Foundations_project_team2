from backend.routes.accounts import dashboard_router, router as accounts_router
from backend.routes.admin import router as admin_router

__all__ = ["accounts_router", "admin_router", "dashboard_router"]
