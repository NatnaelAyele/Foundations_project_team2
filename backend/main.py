from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.config import Config
from backend.database.connection import Base, engine
from backend.engine.scheduler import CoordinationScheduler
from backend import models
from backend.routes.accounts import dashboard_router, router as accounts_router
from backend.routes.admin import router as admin_router
from backend.routes.hub import router as hub_router
from backend.routes.transporter import router as transporter_router


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app(create_database=True, start_scheduler=True):
    @asynccontextmanager
    async def lifespan(app):
        if create_database:
            Base.metadata.create_all(bind=engine)
        scheduler = None
        if start_scheduler and Config.ENGINE_SCHEDULER_ENABLED:
            scheduler = CoordinationScheduler()
            scheduler.start()
        try:
            yield
        finally:
            if scheduler:
                scheduler.shutdown()

    api = FastAPI(title="FreshLink API", version="1.0.0", lifespan=lifespan)
    api.add_middleware(
        CORSMiddleware,
        allow_origins=Config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    api.include_router(accounts_router)
    api.include_router(admin_router)
    api.include_router(hub_router)
    api.include_router(transporter_router)
    api.include_router(dashboard_router)

    @api.get("/", include_in_schema=False)
    def landing_page():
        return RedirectResponse("/landing_page/index.html")

    api.mount(
        "/landing_page",
        StaticFiles(directory=FRONTEND_DIR / "landing_page"),
        name="landing_page",
    )
    api.mount("/shared", StaticFiles(directory=FRONTEND_DIR / "sevices"))
    api.mount("/admin/css", StaticFiles(directory=FRONTEND_DIR / "admin" / "css"))
    api.mount("/admin/js", StaticFiles(directory=FRONTEND_DIR / "admin" / "js"))
    api.mount(
        "/admin/images", StaticFiles(directory=FRONTEND_DIR / "admin" / "images")
    )
    api.mount(
        "/storagehub_dashboard/css",
        StaticFiles(directory=FRONTEND_DIR / "storagehub_dashboard" / "css"),
    )
    api.mount(
        "/storagehub_dashboard/js",
        StaticFiles(directory=FRONTEND_DIR / "storagehub_dashboard" / "js"),
    )
    api.mount(
        "/storagehub_dashboard/images",
        StaticFiles(directory=FRONTEND_DIR / "storagehub_dashboard" / "images"),
    )
    api.mount(
        "/transporter_dashboard/css",
        StaticFiles(directory=FRONTEND_DIR / "transporter_dashboard" / "css"),
    )
    api.mount(
        "/transporter_dashboard/js",
        StaticFiles(directory=FRONTEND_DIR / "transporter_dashboard" / "js"),
    )
    api.mount(
        "/transporter_dashboard/images",
        StaticFiles(directory=FRONTEND_DIR / "transporter_dashboard" / "images"),
    )

    @api.get("/health", tags=["Health"])
    def health_check():
        return {"status": "ok"}

    return api


app = create_app()
