from backend.routes.accounts import dashboard_router, router as accounts_router
from backend.routes.admin import router as admin_router
from backend.routes.hub import router as hub_router
from backend.routes.transporter import router as transporter_router

__all__ = [
    "accounts_router",
    "admin_router",
    "dashboard_router",
    "hub_router",
    "transporter_router",
]
