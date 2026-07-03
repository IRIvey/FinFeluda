"""
TEAMMATE SCOPE -- compares two completed investigations.
Stub only. Fill in once REASON-stage results are persisted.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def compare_investigations(id1: str, id2: str):
    return {"comparison": "not implemented yet"}
