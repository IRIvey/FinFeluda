from fastapi import APIRouter
from .investigations import router as investigations_router
from .upload import router as upload_router
from .analyze import router as analyze_router
from .chat import router as chat_router
from .compare import router as compare_router
from .comparison_chat import router as comparison_chat_router
from .report import router as report_router
from .dashboard import router as dashboard_router

api_router = APIRouter()
api_router.include_router(investigations_router, prefix="/investigations", tags=["Investigations"])
api_router.include_router(upload_router, prefix="/upload", tags=["Upload"])
api_router.include_router(analyze_router, prefix="/analyze", tags=["Analyze"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(compare_router, prefix="/compare", tags=["Compare"])
api_router.include_router(comparison_chat_router, prefix="/compare/chat", tags=["Compare Chat"])
api_router.include_router(report_router, prefix="/report", tags=["Report"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
