"""
=============================================================
Converts raw PDF bytes into plain text using pdfplumber.
Provides robust error handling for corrupted or empty PDFs.
=============================================================
"""

import io
import logging
import pdfplumber

logger = logging.getLogger("flowledger.extractor")


class PDFExtractionError(Exception):
    """Raised when PDF text extraction fails."""
    pass


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text content from raw PDF bytes.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF file.

    Returns:
        Concatenated text from all pages of the PDF.

    Raises:
        PDFExtractionError: If the PDF cannot be read or contains no text.
    """
    try:
        logger.info("Starting PDF text extraction...")
        text_pages: list[str] = []

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"PDF loaded successfully — {total_pages} page(s) detected.")

            if total_pages == 0:
                raise PDFExtractionError(
                    "The uploaded PDF has no pages. Please upload a valid document."
                )

            for i, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text)
                    logger.info(f"  ✓ Page {i}/{total_pages} — extracted {len(page_text)} chars.")
                else:
                    logger.warning(f"  ⚠ Page {i}/{total_pages} — no extractable text (might be scanned image).")

        full_text = "\n\n".join(text_pages).strip()

        if not full_text:
            raise PDFExtractionError(
                "No text could be extracted from the PDF. "
                "The document may be scanned/image-based. "
                "Please upload a text-based (digital) PDF."
            )

        logger.info(f"Extraction complete — {len(full_text)} total characters extracted.")
        return full_text

    except PDFExtractionError:
        raise  # Re-raise our custom errors as-is

    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise PDFExtractionError(
            f"Failed to read the PDF file. It may be corrupted or password-protected. "
            f"Error: {str(e)}"
        )
