"""
Security utilities for file validation and data protection.

Implements OWASP-compliant security measures for handling
sensitive bid documents and preventing common vulnerabilities.
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import Optional, List, Set, Tuple
import mimetypes

from config import settings

logger = logging.getLogger(__name__)


class SecurityValidationError(Exception):
    """Raised when security validation fails."""
    pass


class FileValidator:
    """
    Secure file validation following OWASP guidelines.
    
    Prevents path traversal, validates file types, and ensures
    files are safe to process.
    """
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'application/pdf',
    }
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf'}
    
    # Dangerous file patterns to reject
    DANGEROUS_PATTERNS = [
        r'\.\./',  # Path traversal
        r'\.\.\\',  # Path traversal (Windows)
        r'^\.',  # Hidden files (Unix)
        r'[<>:"|?*]',  # Invalid Windows characters
        r'[\x00-\x1f]',  # Control characters
    ]
    
    # Maximum filename length
    MAX_FILENAME_LENGTH = 255
    
    def __init__(self, base_directory: Optional[Path] = None):
        """
        Initialize file validator.
        
        Args:
            base_directory: Base directory for path validation
        """
        self.base_directory = base_directory or Path(settings.input_dir)
        self.compiled_patterns = [re.compile(pattern) for pattern in self.DANGEROUS_PATTERNS]
    
    def validate_filename(self, filename: str) -> bool:
        """
        Validate filename for security issues.
        
        Args:
            filename: Filename to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            SecurityValidationError: If validation fails
        """
        if not filename:
            raise SecurityValidationError("Filename cannot be empty")
        
        # Check length
        if len(filename) > self.MAX_FILENAME_LENGTH:
            raise SecurityValidationError(
                f"Filename too long: {len(filename)} chars "
                f"(max: {self.MAX_FILENAME_LENGTH})"
            )
        
        # Check for dangerous patterns
        for pattern in self.compiled_patterns:
            if pattern.search(filename):
                raise SecurityValidationError(
                    f"Filename contains dangerous pattern: {filename}"
                )
        
        # Check extension
        file_path = Path(filename)
        if file_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            raise SecurityValidationError(
                f"Invalid file extension: {file_path.suffix}. "
                f"Allowed: {self.ALLOWED_EXTENSIONS}"
            )
        
        return True
    
    def validate_path(self, file_path: Path) -> bool:
        """
        Validate file path to prevent path traversal attacks.
        
        Args:
            file_path: File path to validate
            
        Returns:
            True if valid
            
        Raises:
            SecurityValidationError: If path is invalid or dangerous
        """
        try:
            # Resolve to absolute path
            resolved_path = file_path.resolve()
            
            # Allow temporary directories (for Streamlit uploads, etc.)
            import tempfile
            temp_dir = Path(tempfile.gettempdir()).resolve()
            
            # Check if path is within base directory OR temporary directory
            base_resolved = self.base_directory.resolve()
            
            is_in_base = str(resolved_path).startswith(str(base_resolved))
            is_in_temp = str(resolved_path).startswith(str(temp_dir))
            
            if not (is_in_base or is_in_temp):
                raise SecurityValidationError(
                    f"Path traversal attempt detected: {file_path}"
                )
            
            # Check if path exists and is a file
            if resolved_path.exists() and not resolved_path.is_file():
                raise SecurityValidationError(
                    f"Path is not a file: {file_path}"
                )
            
            return True
            
        except (ValueError, OSError) as e:
            raise SecurityValidationError(f"Invalid path: {e}")
    
    def validate_file_content(self, file_path: Path) -> bool:
        """
        Validate file content and MIME type.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if valid
            
        Raises:
            SecurityValidationError: If content validation fails
        """
        if not file_path.exists():
            raise SecurityValidationError(f"File does not exist: {file_path}")
        
        # Check file size
        file_size = file_path.stat().st_size
        max_size = settings.max_file_size_mb * 1024 * 1024
        
        if file_size > max_size:
            raise SecurityValidationError(
                f"File too large: {file_size / 1024 / 1024:.2f}MB "
                f"(max: {settings.max_file_size_mb}MB)"
            )
        
        if file_size == 0:
            raise SecurityValidationError("File is empty")
        
        # Validate PDF magic bytes
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                raise SecurityValidationError(
                    "File does not appear to be a valid PDF"
                )
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type not in self.ALLOWED_MIME_TYPES:
            raise SecurityValidationError(
                f"Invalid MIME type: {mime_type}. "
                f"Allowed: {self.ALLOWED_MIME_TYPES}"
            )
        
        return True
    
    def validate_file(self, file_path: Path) -> bool:
        """
        Complete file validation.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if all validations pass
            
        Raises:
            SecurityValidationError: If any validation fails
        """
        file_path = Path(file_path)
        
        # Validate filename
        self.validate_filename(file_path.name)
        
        # Validate path
        self.validate_path(file_path)
        
        # Validate content
        self.validate_file_content(file_path)
        
        logger.info(f"File validation passed: {file_path.name}")
        return True


class InputSanitizer:
    """
    Sanitizes user inputs to prevent injection attacks.
    
    Implements OWASP input validation guidelines.
    """
    
    # Maximum input lengths
    MAX_TEXT_LENGTH = 1_000_000  # 1MB of text
    MAX_SEARCH_LENGTH = 1000
    
    # Patterns to remove or escape
    DANGEROUS_CHARS = r'[<>\'\"\\]'
    
    @staticmethod
    def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize text input.
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
            
        Raises:
            SecurityValidationError: If input is invalid
        """
        if not isinstance(text, str):
            raise SecurityValidationError("Input must be a string")
        
        # Check length
        max_len = max_length or InputSanitizer.MAX_TEXT_LENGTH
        if len(text) > max_len:
            raise SecurityValidationError(
                f"Input too long: {len(text)} chars (max: {max_len})"
            )
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove other control characters except newline, tab, carriage return
        text = ''.join(char for char in text 
                      if char in '\n\r\t' or ord(char) >= 32)
        
        return text.strip()
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to safe characters only.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed"
        
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        
        # Collapse multiple spaces/underscores
        filename = re.sub(r'[\s_]+', '_', filename)
        
        # Ensure not empty
        if not filename or filename == '.':
            filename = "unnamed"
        
        # Limit length
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:195] + ('.' + ext if ext else '')
        
        return filename.strip('._')


class DataProtection:
    """
    Utilities for protecting sensitive data.
    
    Implements encryption and secure handling of documents.
    """
    
    @staticmethod
    def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
        """
        Calculate cryptographic hash of file.
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('sha256', 'sha512', etc.)
            
        Returns:
            Hex digest of file hash
        """
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    @staticmethod
    def verify_file_integrity(file_path: Path, expected_hash: str, 
                             algorithm: str = 'sha256') -> bool:
        """
        Verify file integrity using hash.
        
        Args:
            file_path: Path to file
            expected_hash: Expected hash value
            algorithm: Hash algorithm used
            
        Returns:
            True if hashes match, False otherwise
        """
        actual_hash = DataProtection.calculate_file_hash(file_path, algorithm)
        return actual_hash.lower() == expected_hash.lower()
    
    @staticmethod
    def redact_sensitive_data(text: str) -> str:
        """
        Redact sensitive data from text for logging.
        
        Args:
            text: Text potentially containing sensitive data
            
        Returns:
            Text with sensitive data redacted
        """
        if not text:
            return text
        
        # Redact CPF (Brazilian ID): XXX.XXX.XXX-XX
        text = re.sub(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', 'CPF:[REDACTED]', text)
        
        # Redact CNPJ (Brazilian company ID): XX.XXX.XXX/XXXX-XX
        text = re.sub(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', 'CNPJ:[REDACTED]', text)
        
        # Redact email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                     'EMAIL:[REDACTED]', text)
        
        # Redact phone numbers (Brazilian format)
        text = re.sub(r'\b\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b', 'PHONE:[REDACTED]', text)
        
        return text


# Convenience functions
def validate_pdf_file(file_path: Path) -> bool:
    """
    Validate PDF file (convenience function).
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        True if valid
        
    Raises:
        SecurityValidationError: If validation fails
    """
    validator = FileValidator()
    return validator.validate_file(file_path)


def sanitize_user_input(text: str) -> str:
    """
    Sanitize user input (convenience function).
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    return InputSanitizer.sanitize_text(text)
