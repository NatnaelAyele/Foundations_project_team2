"""
FastAPI router for Group 1's pipeline.

This is not part of the required checklist, but it gives you two things
for free:
1. A live endpoint the API person can mount as-is in their FastAPI app
   (they just need to `include_router`), rather than reading your code
   and re-wiring it themselves.
2. Something the demo dashboard (dashboard.html) can call to show real
   pipeline output instead of only mock data.

Mount it in the main app with, e.g.:

    from fastapi import FastAPI
    from group1_engine.api import router as group1_router

    app = FastAPI()
    app.include_router(group1_router)
"""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .database import get_db
from .pipeline import run_group1
from .schemas import Group1Result

router = APIRouter(prefix="/api/engine/group1", tags=["engine-group1"])


@router.get("/run", response_model=Group1Result)
def run_pipeline(
    as_of: date | None = None, db: Session = Depends(get_db)
) -> Group1Result:
    """Run steps 2-6 (read, validate, eligibility, cluster, demand) against
    the live database and return the result.

    `as_of` lets you override "today" for demoing/testing the coordination
    window without waiting for real dates to line up.
    """
    return run_group1(db, today=as_of)
