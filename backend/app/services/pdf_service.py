"""
PDF text/table extraction. pymupdf (fitz) is the fast path; falls
back to OCR (pytesseract + pdf2image) only when pymupdf extracts
suspiciously little text, which signals a scanned/image-based PDF --
matches the spec's "extract text using OCR if necessary" requirement
without paying the OCR cost on every normal text-based PDF.
"""
import os
import tempfile
import logging
import fitz  # pymupdf
import pdfplumber
from typing import List

logger = logging.getLogger(__name__)

TEMP_PDF_DIR = os.path.join(tempfile.gettempdir(), "due_diligence_uploads")
os.makedirs(TEMP_PDF_DIR, exist_ok=True)

# If pymupdf extracts less than this many chars per page on average,
# assume it's a scanned PDF and fall back to OCR.
OCR_FALLBACK_CHARS_PER_PAGE = 50


def save_temp_pdf(content: bytes, filename: str) -> str:
    path = os.path.join(TEMP_PDF_DIR, filename)
    with open(path, "wb") as f:
        f.write(content)
    return path


def extract_text_from_pdf(file_path: str) -> str:
    """Primary extraction path: pymupdf, fast and accurate for text-based PDFs."""
    doc = fitz.open(file_path)
    text_parts = [page.get_text() for page in doc]
    page_count = len(doc)
    doc.close()

    full_text = "\n".join(text_parts)
    avg_chars_per_page = len(full_text) / max(page_count, 1)

    if avg_chars_per_page < OCR_FALLBACK_CHARS_PER_PAGE:
        logger.info(
            "PDF %s looks scanned (%.0f chars/page) -- falling back to OCR",
            file_path, avg_chars_per_page,
        )
        ocr_text = _extract_text_via_ocr(file_path)
        if len(ocr_text.strip()) > len(full_text.strip()):
            return ocr_text

    return full_text


def _extract_text_via_ocr(file_path: str) -> str:
    """OCR fallback for scanned/image-based PDFs. Requires the
    tesseract-ocr and poppler-utils system packages to be installed
    in the deploy environment (Render/Hugging Face Spaces Dockerfile)."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        logger.warning("OCR libraries not available -- skipping OCR fallback")
        return ""

    try:
        images = convert_from_path(file_path)
        return "\n".join(pytesseract.image_to_string(img) for img in images)
    except Exception as exc:
        logger.warning("OCR extraction failed for %s: %s", file_path, exc)
        return ""


def extract_tables_from_pdf(file_path: str) -> List[list]:
    """Table extraction stays on pdfplumber -- pymupdf's table support
    is weaker for the kind of financial statement tables this app needs."""
    tables = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    return tables


# NOTE: chunking now lives in app/sources/chunking.py (chunk_text_by_boundary),
# which respects sentence/paragraph boundaries and sizes chunks per source
# confidence tier. The old flat chunk_text() here has been removed -- don't
# recreate a character-slicing chunker, it cuts facts off mid-sentence.