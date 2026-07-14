import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY", "change-this-development-secret-key-before-deployment"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./freshlink.db")

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:5500"
    ).split(",")
