import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY", "change-this-development-secret-key-before-deployment"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ENGINE_SCHEDULER_ENABLED = os.getenv("ENGINE_SCHEDULER_ENABLED", "true").lower() == "true"
    ENGINE_RUN_INTERVAL_HOURS = int(os.getenv("ENGINE_RUN_INTERVAL_HOURS", "2"))
    ENGINE_RUN_ON_FORECAST_CREATED = os.getenv(
        "ENGINE_RUN_ON_FORECAST_CREATED", "false"
    ).lower() == "true"
    AUTH_COOKIE_NAME = "freshlink_access_token"
    COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./freshlink.db")

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:5500"
    ).split(",")
