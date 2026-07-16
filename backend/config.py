import os
from urllib.parse import quote_plus
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
    # DATABASE_URL overrides the individual PostgreSQL settings below.
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_ENGINE = os.getenv("DATABASE_ENGINE", "postgresql")
    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "freshlink")
    DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")
    DATABASE_SSL_MODE = os.getenv("DATABASE_SSL_MODE", "prefer")

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:5500"
    ).split(",")

    @classmethod
    def get_database_url(cls):
        if cls.DATABASE_URL:
            if cls.DATABASE_URL.startswith(
                ("postgres://", "postgresql://", "postgresql+psycopg://")
            ):
                return cls.DATABASE_URL
            raise ValueError("DATABASE_URL must use a PostgreSQL URL.")

        if cls.DATABASE_ENGINE.lower() in {"postgres", "postgresql"}:
            username = quote_plus(cls.DATABASE_USER)
            password = quote_plus(cls.DATABASE_PASSWORD)
            return (
                f"postgresql+psycopg://{username}:{password}"
                f"@{cls.DATABASE_HOST}:{cls.DATABASE_PORT}/{cls.DATABASE_NAME}"
                f"?sslmode={cls.DATABASE_SSL_MODE}"
            )

        raise ValueError(
            "DATABASE_ENGINE must be 'postgres' or 'postgresql'."
        )
