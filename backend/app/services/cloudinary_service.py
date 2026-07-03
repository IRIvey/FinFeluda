"""
Cloudinary storage for uploaded PDFs. Used by upload.py (your scope)
to persist the original file for sharing/download, separate from the
local temp copy used for immediate text extraction.
"""
import cloudinary
import cloudinary.uploader
from app.core.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)


def upload_pdf(file_bytes: bytes, filename: str) -> str:
    """Upload PDF to Cloudinary and return its secure URL."""
    result = cloudinary.uploader.upload(
        file_bytes,
        resource_type="raw",
        public_id=f"due_diligence/{filename}",
        format="pdf",
    )
    return result["secure_url"]
