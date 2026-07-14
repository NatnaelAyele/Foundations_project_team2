from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import Config
from backend.database.connection import Base, engine
from backend import models
from backend.routes.accounts import router as accounts_router


def create_app(create_database=True):
    @asynccontextmanager
    async def lifespan(app):
        if create_database:
            Base.metadata.create_all(bind=engine)
        yield

    api = FastAPI(title="FreshLink API", version="1.0.0", lifespan=lifespan)
    api.add_middleware(
        CORSMiddleware,
        allow_origins=Config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    api.include_router(accounts_router)

    @api.get("/health", tags=["Health"])
    def health_check():
        return {"status": "ok"}

    return api


app = create_app()
