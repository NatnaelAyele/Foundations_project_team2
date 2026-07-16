

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .database import get_db
from .pipeline import run_group1_pipeline

router = APIRouter(prefix="/api/engine/group1", tags=["engine-group1"])


@router.get("/run")
def run_pipeline(as_of: date | None = None, db: Session = Depends(get_db)) -> list[dict[str, Any]]:

    return run_group1_pipeline(db, today=as_of)
