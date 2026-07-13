# Minimal DB connection so my code can run and be tested on its own.
# If there's already a shared database.py in the repo, delete this and import theirs instead -
# don't want two separate connections hitting the same Postgres database.

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/tomato_logistics"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
