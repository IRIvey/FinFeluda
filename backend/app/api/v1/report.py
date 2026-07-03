"""
TEAMMATE SCOPE -- final due diligence report + PDF export.
Stub only.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/{investigation_id}")
def get_report(investigation_id: str):
    return {"report": "not implemented yet"}


@router.get("/{investigation_id}/download")
def download_report(investigation_id: str):
    return {"message": "not implemented yet"}
