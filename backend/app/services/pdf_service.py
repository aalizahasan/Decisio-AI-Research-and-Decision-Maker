import pymupdf
import logging

logger = logging.getLogger("pdf_service")


def extract_pdf_pages(file_bytes: bytes) -> list[dict]:
    """
    Extracts text page-by-page from PDF binary data using PyMuPDF.
    
    Returns:
        List of dictionaries containing 'page_number' (1-indexed) and 'text'.
    
    Raises:
        ValueError: If file is not a valid PDF or contains no extractable text.
    """
    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    # Validate PDF magic header bytes (%PDF-)
    if not file_bytes.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF file format. File does not start with valid PDF magic bytes.")

    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        logger.error(f"Failed to open PDF stream with PyMuPDF: {e}")
        raise ValueError(f"Could not parse PDF document: {str(e)}")

    if doc.page_count == 0:
        doc.close()
        raise ValueError("Uploaded PDF document contains 0 pages.")

    pages_data = []
    total_extracted_length = 0

    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        text = page.get_text("text").strip()
        page_number = page_index + 1

        if text:
            pages_data.append({
                "page_number": page_number,
                "text": text
            })
            total_extracted_length += len(text)

    doc.close()

    if total_extracted_length == 0:
        raise ValueError("PDF document contains no extractable text (it may contain scanned image pages or be password protected).")

    return pages_data
