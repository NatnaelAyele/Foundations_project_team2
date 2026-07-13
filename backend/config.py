import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-secret-key")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./freshlink.db")

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:5500"
    ).split(",")
