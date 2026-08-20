import io
import logging

logger = logging.getLogger("pdf_service")

# Try importing pure-Python pypdf first for serverless compatibility, fallback to PyMuPDF
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import fitz as pymupdf
except ImportError:
    pymupdf = None


def extract_pdf_pages(file_bytes: bytes) -> list[dict]:
    """
    Extracts text page-by-page from PDF binary data.
    Uses pure-Python pypdf or PyMuPDF for serverless cloud compatibility.
    """
    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    if not file_bytes.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF file format. File does not start with valid PDF magic bytes.")

    pages_data = []
    total_extracted_length = 0

    # 1. Try pure-Python pypdf
    if pypdf:
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for idx, page in enumerate(reader.pages):
                text = (page.extract_text() or "").strip()
                if text:
                    pages_data.append({
                        "page_number": idx + 1,
                        "text": text
                    })
                    total_extracted_length += len(text)
            if total_extracted_length > 0:
                return pages_data
        except Exception as pypdf_err:
            logger.warning(f"pypdf extraction failed: {pypdf_err}")

    # 2. Try PyMuPDF fallback
    if pymupdf:
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            for page_index in range(doc.page_count):
                page = doc.load_page(page_index)
                text = page.get_text("text").strip()
                if text:
                    pages_data.append({
                        "page_number": page_index + 1,
                        "text": text
                    })
                    total_extracted_length += len(text)
            doc.close()
            if total_extracted_length > 0:
                return pages_data
        except Exception as pymupdf_err:
            logger.warning(f"pymupdf extraction failed: {pymupdf_err}")

    if total_extracted_length == 0:
        raise ValueError("PDF document contains no extractable text (it may contain scanned image pages or be password protected).")

    return pages_data
