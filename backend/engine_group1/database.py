"""
Minimal DB session wiring so this package runs standalone.

If the DB person / API person already has a shared `database.py` with
`engine`, `SessionLocal`, and `get_db`, delete this file and import theirs
instead — don't run two separate connections to the same Postgres instance.
"""

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
