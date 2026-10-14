"""
High-performance PDF text and page extraction service using PyMuPDF (pymupdf).
Preserves exact page-level provenance (page_number) and validates input integrity.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import pymupdf


@dataclass
class PDFPageData:
    page_number: int  # 1-indexed
    text_content: str
    char_count: int


@dataclass
class PDFExtractionResult:
    success: bool
    page_count: int
    pages: List[PDFPageData] = field(default_factory=list)
    total_characters: int = 0
    is_scanned: bool = False
    error_message: Optional[str] = None


def validate_pdf_file(filename: str, file_bytes: bytes, max_size_mb: int = 15) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded file format, magic bytes, and size boundaries.
    Does not trust filename or browser MIME type alone.
    """
    if not filename.lower().endswith(".pdf"):
        return False, "Only PDF (.pdf) documents are supported"

    file_size = len(file_bytes)
    if file_size == 0:
        return False, "Uploaded file is empty"

    max_bytes = max_size_mb * 1024 * 1024
    if file_size > max_bytes:
        return False, f"File size ({file_size / (1024 * 1024):.1f} MB) exceeds maximum limit of {max_size_mb} MB"

    # Validate PDF magic header bytes
    if not file_bytes.startswith(b"%PDF"):
        return False, "File is not a valid PDF document (invalid file header)"

    return True, None


def extract_pdf_pages(file_bytes: bytes) -> PDFExtractionResult:
    """
    Extract text page by page from PDF bytes using PyMuPDF.
    Preserves exact page numbering and detects image-only / scanned documents.
    """
    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        return PDFExtractionResult(
            success=False,
            page_count=0,
            error_message=f"Failed to parse PDF structure: {str(exc)}",
        )

    page_count = len(doc)
    if page_count == 0:
        return PDFExtractionResult(
            success=False,
            page_count=0,
            error_message="PDF contains zero pages",
        )

    pages: List[PDFPageData] = []
    total_chars = 0

    for idx in range(page_count):
        page = doc[idx]
        page_number = idx + 1  # 1-indexed page numbering
        # Extract plain text with normalized spacing
        text = page.get_text("text").strip()
        char_count = len(text)
        total_chars += char_count

        pages.append(
            PDFPageData(
                page_number=page_number,
                text_content=text,
                char_count=char_count,
            )
        )

    doc.close()

    # Detect scanned or image-only documents without embedded text
    if total_chars < 20 and page_count > 0:
        return PDFExtractionResult(
            success=False,
            page_count=page_count,
            pages=pages,
            total_characters=total_chars,
            is_scanned=True,
            error_message=(
                "Document appears to be a scanned image or lacks an embedded text layer. "
                "ProofLens requires text-based PDFs for grounded evidence analysis."
            ),
        )

    return PDFExtractionResult(
        success=True,
        page_count=page_count,
        pages=pages,
        total_characters=total_chars,
        is_scanned=False,
    )
