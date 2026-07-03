"""
TEAMMATE SCOPE -- dashboard stats (REASON-stage output).
Stub only. Fill in once analysis results are persisted.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats():
    return {"total_investigations": 0, "completed": 0, "processing": 0}
