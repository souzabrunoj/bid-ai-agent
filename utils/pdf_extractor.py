"""
PDF text extraction utilities with OCR support.

Provides secure PDF text extraction with support for both
regular PDFs and scanned documents using OCR.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

import pypdf
from PIL import Image
import pytesseract

from config import settings

logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    """Raised when PDF extraction fails."""
    pass


class PDFExtractor:
    """
    Secure PDF text extractor with OCR support.
    
    Handles both regular text-based PDFs and scanned documents.
    Implements security validations to prevent malicious file processing.
    """
    
    # Maximum file size in bytes (from settings, with fallback)
    MAX_FILE_SIZE = settings.max_file_size_mb * 1024 * 1024
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf'}
    
    def __init__(self, enable_ocr: bool = True, ocr_language: str = "por"):
        """
        Initialize PDF extractor.
        
        Args:
            enable_ocr: Enable OCR for scanned PDFs
            ocr_language: Language for OCR (default: Portuguese)
        """
        self.enable_ocr = enable_ocr and settings.ocr_enabled
        self.ocr_language = ocr_language or settings.ocr_language
        
    def validate_pdf(self, file_path: Path) -> None:
        """
        Validate PDF file before processing.
        
        Args:
            file_path: Path to PDF file
            
        Raises:
            PDFExtractionError: If validation fails
        """
        if not settings.file_validation_enabled:
            return
            
        # Check if file exists
        if not file_path.exists():
            raise PDFExtractionError(f"File not found: {file_path}")
        
        # Check if it's a file (not directory)
        if not file_path.is_file():
            raise PDFExtractionError(f"Path is not a file: {file_path}")
        
        # Check file extension
        if file_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            raise PDFExtractionError(
                f"Invalid file extension: {file_path.suffix}. "
                f"Allowed: {self.ALLOWED_EXTENSIONS}"
            )
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise PDFExtractionError(
                f"File too large: {file_size / 1024 / 1024:.2f}MB. "
                f"Maximum: {settings.max_file_size_mb}MB"
            )
        
        # Check if file is actually a PDF (magic bytes)
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                raise PDFExtractionError(
                    "File does not appear to be a valid PDF"
                )
    
    def extract_text_from_pdf(self, file_path: Path) -> str:
        """
        Extract text from a regular PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            PDFExtractionError: If extraction fails
        """
        try:
            text_content = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                # Extract text from each page
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content.append(f"--- Page {page_num} ---\n{page_text}")
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num}: {e}")
                        continue
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            raise PDFExtractionError(f"Failed to extract PDF text: {e}")
    
    def extract_text_with_ocr(self, file_path: Path) -> str:
        """
        Extract text from scanned PDF using OCR.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            PDFExtractionError: If OCR extraction fails
        """
        if not self.enable_ocr:
            raise PDFExtractionError("OCR is disabled")
        
        try:
            from pdf2image import convert_from_path
            
            logger.info(f"Using OCR for: {file_path.name}")
            
            # Convert PDF pages to images with specific DPI
            try:
                images = convert_from_path(
                    file_path,
                    dpi=300,  # Higher DPI for better OCR
                    fmt='png',
                    thread_count=2
                )
                logger.info(f"Converted {len(images)} pages to images")
            except Exception as e:
                logger.error(f"pdf2image conversion failed: {e}")
                raise PDFExtractionError(f"Failed to convert PDF to images: {e}")
            
            text_content = []
            for page_num, image in enumerate(images, start=1):
                try:
                    # Perform OCR on the image with Portuguese language
                    page_text = pytesseract.image_to_string(
                        image,
                        lang=self.ocr_language,
                        config='--psm 6'  # Assume uniform block of text
                    )
                    logger.debug(f"Page {page_num} OCR: {len(page_text)} chars")
                    
                    if page_text.strip():
                        text_content.append(f"--- Page {page_num} ---\n{page_text}")
                    else:
                        logger.warning(f"Page {page_num} produced no text")
                        
                except Exception as e:
                    logger.warning(f"OCR failed for page {page_num}: {e}")
                    continue
            
            result = "\n\n".join(text_content)
            logger.info(f"OCR complete: {len(result)} total characters from {len(images)} pages")
            
            return result
            
        except ImportError as e:
            raise PDFExtractionError(
                f"OCR dependency missing: {e}\n"
                "Install with: pip install pdf2image\n"
                "Also requires poppler: brew install poppler (macOS)"
            )
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            raise PDFExtractionError(f"OCR extraction failed: {e}")
    
    def extract_text(self, file_path: Path, force_ocr: bool = False) -> Dict[str, Any]:
        """
        Extract text from PDF file with automatic OCR fallback.
        
        Args:
            file_path: Path to PDF file
            force_ocr: Force OCR even if regular extraction works
            
        Returns:
            Dictionary with extracted text and metadata:
            {
                'text': str,
                'method': str,  # 'regular' or 'ocr'
                'pages': int,
                'success': bool
            }
        """
        # Convert to Path object
        file_path = Path(file_path)
        
        # Validate file
        self.validate_pdf(file_path)
        
        logger.info(f"Extracting text from: {file_path.name}")
        
        result = {
            'text': '',
            'method': 'regular',
            'pages': 0,
            'success': False,
            'file_name': file_path.name
        }
        
        try:
            # Try regular extraction first
            if not force_ocr:
                text = self.extract_text_from_pdf(file_path)
                
                # Check if we got meaningful content
                if text.strip() and len(text.strip()) > 50:
                    result['text'] = text
                    result['method'] = 'regular'
                    result['success'] = True
                    result['pages'] = text.count('--- Page')
                    logger.info(f"Successfully extracted {len(text)} characters using regular method")
                    return result
                else:
                    logger.info("Regular extraction yielded minimal content, trying OCR...")
            
            # Fallback to OCR or if forced
            if self.enable_ocr:
                text = self.extract_text_with_ocr(file_path)
                result['text'] = text
                result['method'] = 'ocr'
                result['success'] = True
                result['pages'] = text.count('--- Page')
                logger.info(f"Successfully extracted {len(text)} characters using OCR")
            else:
                logger.warning("OCR is disabled but regular extraction failed")
                result['text'] = text  # Use whatever we got from regular extraction
                result['success'] = len(text.strip()) > 0
                
            return result
            
        except PDFExtractionError:
            raise
        except Exception as e:
            raise PDFExtractionError(f"Text extraction failed: {e}")
    
    def sanitize_text(self, text: str) -> str:
        """
        Sanitize extracted text for safe processing.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        
        # Remove excessive blank lines (keep max 2 consecutive)
        result = []
        blank_count = 0
        for line in cleaned_lines:
            if not line:
                blank_count += 1
                if blank_count <= 2:
                    result.append(line)
            else:
                blank_count = 0
                result.append(line)
        
        return '\n'.join(result)


# Convenience function for simple extraction
def extract_pdf_text(file_path: Path, enable_ocr: bool = True) -> str:
    """
    Extract text from PDF file (convenience function).
    
    Args:
        file_path: Path to PDF file
        enable_ocr: Enable OCR for scanned documents
        
    Returns:
        Extracted and sanitized text
        
    Raises:
        PDFExtractionError: If extraction fails
    """
    extractor = PDFExtractor(enable_ocr=enable_ocr)
    result = extractor.extract_text(file_path)
    
    if not result['success'] or not result['text'].strip():
        # Return empty string instead of raising error
        logger.warning(f"No text extracted from {file_path.name}")
        return ""
    
    return extractor.sanitize_text(result['text'])
