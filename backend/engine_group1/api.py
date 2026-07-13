# I built this so my pipeline can be called over the network, not just imported directly.
# The API person can mount this straight into their FastAPI app with include_router.
# The demo dashboard also calls this to show real data instead of mock data.

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
    # as_of lets me override "today" for testing without waiting for real dates to line up.
    return run_group1(db, today=as_of)
