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


# extract_text_from_pdf() alone loses financial tables whenever a caller
# truncates the flat text (see content_fetch_utils.py's MAX_PDF_CHARS) --
# truncating from the start always keeps the cover page / AGM notice /
# chairman's message and drops the balance sheet / income statement that
# live 40-150 pages into a real annual report. This locates the pages
# that actually look like financial statements first (fast pymupdf
# keyword scan across all pages), then runs pdfplumber's much slower
# table extraction ONLY on those specific pages -- running pdfplumber
# over every page of a 200+ page report would be needlessly slow.
FINANCIAL_STATEMENT_KEYWORDS = [
    "balance sheet", "statement of financial position",
    "profit and loss", "income statement", "statement of comprehensive income",
    "statement of cash flows", "cash flow statement",
    "statement of changes in equity",
]
MAX_FINANCIAL_TABLE_PAGES = 25


def extract_financial_tables(file_path: str) -> str:
    """
    Returns financial-statement tables as readable pipe-delimited text
    (one line per row, tables separated by blank lines), or "" if no
    financial-statement-looking pages were found. Table extraction stays
    on pdfplumber -- pymupdf's table support is weaker for the kind of
    financial statement tables this app needs.
    """
    doc = fitz.open(file_path)
    candidate_pages = [
        i for i, page in enumerate(doc)
        if any(kw in page.get_text().lower() for kw in FINANCIAL_STATEMENT_KEYWORDS)
    ]
    doc.close()

    if not candidate_pages:
        return ""
    candidate_pages = candidate_pages[:MAX_FINANCIAL_TABLE_PAGES]

    blocks = []
    with pdfplumber.open(file_path) as pdf:
        for i in candidate_pages:
            if i >= len(pdf.pages):
                continue
            for table in pdf.pages[i].extract_tables():
                rows = [" | ".join(cell or "" for cell in row) for row in table]
                if rows:
                    blocks.append("\n".join(rows))

    return "\n\n".join(blocks)


# NOTE: chunking now lives in app/sources/chunking.py (chunk_text_by_boundary),
# which respects sentence/paragraph boundaries and sizes chunks per source
# confidence tier. The old flat chunk_text() here has been removed -- don't
# recreate a character-slicing chunker, it cuts facts off mid-sentence.