"""
Unit tests for utility modules.
"""

import pytest
from datetime import date, timedelta
from pathlib import Path

from utils import (
    DateValidator,
    InputSanitizer,
    FileValidator,
    SecurityValidationError
)


class TestDateValidator:
    """Tests for DateValidator class."""
    
    def test_parse_brazilian_date_format(self):
        """Test parsing Brazilian date format DD/MM/YYYY."""
        validator = DateValidator()
        
        result = validator.parse_date("15/03/2025")
        assert result == date(2025, 3, 15)
        
        result = validator.parse_date("01/12/2024")
        assert result == date(2024, 12, 1)
    
    def test_parse_iso_date_format(self):
        """Test parsing ISO date format YYYY-MM-DD."""
        validator = DateValidator()
        
        result = validator.parse_date("2025-03-15")
        assert result == date(2025, 3, 15)
    
    def test_is_expired(self):
        """Test document expiration checking."""
        validator = DateValidator()
        
        yesterday = date.today() - timedelta(days=1)
        assert validator.is_expired(yesterday) is True
        
        tomorrow = date.today() + timedelta(days=1)
        assert validator.is_expired(tomorrow) is False
    
    def test_expires_soon(self):
        """Test expiration warning."""
        validator = DateValidator(grace_period_days=30)
        
        soon = date.today() + timedelta(days=15)
        assert validator.expires_soon(soon) is True
        
        far_future = date.today() + timedelta(days=90)
        assert validator.expires_soon(far_future) is False
    
    def test_extract_dates_from_text(self):
        """Test date extraction from text."""
        validator = DateValidator()
        
        text = "Este documento é válido até 15/03/2025 e deve ser renovado."
        dates = validator.extract_dates_from_text(text)
        
        assert len(dates) > 0
        assert any(d[0] == date(2025, 3, 15) for d in dates)


class TestInputSanitizer:
    """Tests for InputSanitizer class."""
    
    def test_sanitize_text(self):
        """Test text sanitization."""
        text = "Normal text with some content"
        result = InputSanitizer.sanitize_text(text)
        assert result == text
    
    def test_sanitize_text_removes_null_bytes(self):
        """Test null byte removal."""
        text = "Text with\x00null byte"
        result = InputSanitizer.sanitize_text(text)
        assert '\x00' not in result
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        dangerous = "../../../etc/passwd"
        result = InputSanitizer.sanitize_filename(dangerous)
        assert '..' not in result
        assert '/' not in result
    
    def test_sanitize_filename_removes_special_chars(self):
        """Test special character removal from filename."""
        filename = "My<File>Name:With*Special?Chars"
        result = InputSanitizer.sanitize_filename(filename)
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result
        assert '*' not in result
        assert '?' not in result


class TestFileValidator:
    """Tests for FileValidator class."""
    
    def test_validate_filename_valid(self):
        """Test valid filename."""
        validator = FileValidator()
        assert validator.validate_filename("document.pdf") is True
    
    def test_validate_filename_invalid_extension(self):
        """Test invalid file extension."""
        validator = FileValidator()
        
        with pytest.raises(SecurityValidationError):
            validator.validate_filename("document.exe")
    
    def test_validate_filename_path_traversal(self):
        """Test path traversal detection."""
        validator = FileValidator()
        
        with pytest.raises(SecurityValidationError):
            validator.validate_filename("../../../etc/passwd.pdf")
    
    def test_validate_filename_too_long(self):
        """Test filename length validation."""
        validator = FileValidator()
        
        long_name = "a" * 300 + ".pdf"
        with pytest.raises(SecurityValidationError):
            validator.validate_filename(long_name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
