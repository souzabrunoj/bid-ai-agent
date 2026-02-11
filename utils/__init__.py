"""
Utilities and helper functions.
"""

from .pdf_extractor import PDFExtractor, extract_pdf_text, PDFExtractionError
from .date_validator import DateValidator, parse_date, is_document_expired, DateValidationError
from .security import (
    FileValidator,
    InputSanitizer,
    DataProtection,
    validate_pdf_file,
    sanitize_user_input,
    SecurityValidationError
)

__all__ = [
    # PDF extraction
    'PDFExtractor',
    'extract_pdf_text',
    'PDFExtractionError',
    # Date validation
    'DateValidator',
    'parse_date',
    'is_document_expired',
    'DateValidationError',
    # Security
    'FileValidator',
    'InputSanitizer',
    'DataProtection',
    'validate_pdf_file',
    'sanitize_user_input',
    'SecurityValidationError',
]
