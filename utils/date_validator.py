"""
Date validation utilities for document expiration checking.

Provides secure date parsing and validation for Brazilian
document formats commonly used in public procurement.
"""

import re
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


class DateValidationError(Exception):
    """Raised when date validation fails."""
    pass


class DateValidator:
    """
    Validates and parses dates from Brazilian documents.
    
    Supports multiple date formats and provides expiration checking.
    """
    
    # Common Brazilian date patterns
    DATE_PATTERNS = [
        # DD/MM/YYYY with various separators
        r'\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})\b',
        # DD/MM/YY
        r'\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2})\b',
        # YYYY-MM-DD (ISO format)
        r'\b(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})\b',
        # Special: VALIDADE followed by date (for headers/fields)
        r'VALIDADE[:\s]+(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
    ]
    
    # Relative validity patterns (e.g., "prazo de 3 meses", "validade de 90 dias")
    RELATIVE_VALIDITY_PATTERNS = [
        (r'prazo de (\d+)\s*(?:meses|mês)', 'months'),
        (r'v[aá]lid[ao] por (\d+)\s*(?:meses|mês)', 'months'),
        (r'prazo de (\d+)\s*dias?', 'days'),
        (r'v[aá]lid[ao] por (\d+)\s*dias?', 'days'),
        (r'validade de (\d+)\s*(?:meses|mês)', 'months'),
        (r'validade de (\d+)\s*dias?', 'days'),
    ]
    
    # Context keywords that often precede validity dates
    VALIDITY_KEYWORDS = [
        'validade',
        'válidade',
        'vencimento',
        'expira em',
        'válido até',
        'valido ate',
        'valido até',
        'data de validade',
        'prazo de validade',
        'vigência',
        'vigencia',
        'vigente até',
        'vigente ate',
        'emissão',
        'emissao',
        'expedição',
        'expedicao',
        'data de expedição',
        'data de emissão',
    ]
    
    def __init__(self, grace_period_days: int = 0):
        """
        Initialize date validator.
        
        Args:
            grace_period_days: Number of days before expiration to warn
        """
        self.grace_period_days = grace_period_days
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) 
                                 for pattern in self.DATE_PATTERNS]
        self.compiled_relative_patterns = [
            (re.compile(pattern, re.IGNORECASE), unit)
            for pattern, unit in self.RELATIVE_VALIDITY_PATTERNS
        ]
    
    def parse_date(self, date_string: str) -> Optional[date]:
        """
        Parse date string to date object.
        
        Args:
            date_string: Date string in various formats
            
        Returns:
            Parsed date object or None if parsing fails
        """
        if not date_string or not isinstance(date_string, str):
            return None
        
        # Try regex patterns first (more controlled)
        for pattern in self.compiled_patterns:
            match = pattern.search(date_string)
            if match:
                try:
                    groups = match.groups()
                    
                    # Handle DD/MM/YYYY or DD/MM/YY
                    if len(groups) == 3:
                        # Could be (DD, MM, YYYY) or (YYYY, MM, DD)
                        first, second, third = groups
                        first = int(first)
                        second = int(second)
                        third = int(third)
                        
                        # Detect format
                        if first > 31:  # YYYY-MM-DD
                            year, month, day = first, second, third
                        else:  # DD/MM/YYYY
                            day, month, year = first, second, third
                        
                        # Handle 2-digit years
                        if year < 100:
                            year = 2000 + year if year < 50 else 1900 + year
                        
                        # Validate ranges
                        if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                            return date(year, month, day)
                            
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse date from pattern: {e}")
                    continue
        
        # Fallback to dateutil parser (less strict)
        try:
            parsed = date_parser.parse(date_string, dayfirst=True, fuzzy=True)
            return parsed.date()
        except (ValueError, TypeError, AttributeError):
            logger.debug(f"Failed to parse date: {date_string}")
            return None
    
    def extract_structured_date(self, text: str) -> Optional[date]:
        """
        Extract date from structured fields (e.g., VALIDADE: DD/MM/YYYY).
        
        Common in document headers and metadata.
        
        Args:
            text: Text to search
            
        Returns:
            Extracted date or None
        """
        if not text:
            return None
        
        # Patterns for structured fields
        structured_patterns = [
            r'VALIDADE[:\s]+(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
            r'VENCIMENTO[:\s]+(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
            r'V[ÁA]LIDO AT[ÉE][:\s]+(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
            r'EXPIRA[ÇC][ÃA]O[:\s]+(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
            r'EMISS[ÃA]O[:\s]+(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
            r'EXPEDI[ÇC][ÃA]O[:\s]+(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
        ]
        
        for pattern_str in structured_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            match = pattern.search(text)
            
            if match:
                try:
                    day = int(match.group(1))
                    month = int(match.group(2))
                    year = int(match.group(3))
                    
                    if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                        found_date = date(year, month, day)
                        logger.info(f"Found structured date: {found_date} from pattern {pattern_str}")
                        return found_date
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse structured date: {e}")
                    continue
        
        return None
    
    def extract_dates_from_text(self, text: str, context_window: int = 150) -> List[Tuple[date, str]]:
        """
        Extract dates from text with surrounding context.
        
        Args:
            text: Text to search for dates
            context_window: Number of characters around date for context
            
        Returns:
            List of (date, context) tuples
        """
        dates_found = []
        
        if not text:
            return dates_found
        
        # Search for dates with patterns
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                date_str = match.group(0)
                parsed_date = self.parse_date(date_str)
                
                if parsed_date:
                    # Extract context around the date
                    start = max(0, match.start() - context_window)
                    end = min(len(text), match.end() + context_window)
                    context = text[start:end].strip()
                    
                    dates_found.append((parsed_date, context))
        
        return dates_found
    
    def calculate_relative_validity(self, text: str) -> Optional[date]:
        """
        Calculate validity date from relative terms (e.g., "prazo de 3 meses").
        
        Args:
            text: Text to search
            
        Returns:
            Calculated validity date or None
        """
        # Try to find relative validity pattern
        relative_match = None
        unit = None
        
        for pattern, pattern_unit in self.compiled_relative_patterns:
            match = pattern.search(text)
            if match:
                relative_match = match
                unit = pattern_unit
                break
        
        if not relative_match or not unit:
            return None
        
        # Extract the number
        try:
            amount = int(relative_match.group(1))
        except (ValueError, IndexError):
            return None
        
        # Find issue/emission date near the relative validity statement
        # Look in a window around the relative validity mention
        window_start = max(0, relative_match.start() - 300)
        window_end = min(len(text), relative_match.end() + 300)
        window_text = text[window_start:window_end]
        
        # Look for emission/issue date
        emission_keywords = ['emissão', 'emissao', 'expedição', 'expedicao', 'emitida em', 'expedida em']
        
        dates_in_window = self.extract_dates_from_text(window_text, context_window=100)
        
        if not dates_in_window:
            # No emission date found, can't calculate
            return None
        
        # Find the most likely emission date (closest to today, in the past)
        emission_date = None
        best_score = -1
        
        for found_date, context in dates_in_window:
            score = 0
            context_lower = context.lower()
            
            # Check for emission keywords
            for keyword in emission_keywords:
                if keyword in context_lower:
                    score += 10
            
            # Prefer recent dates in the past
            if found_date <= date.today():
                days_ago = (date.today() - found_date).days
                if days_ago <= 180:  # Within last 6 months
                    score += 5
                    score -= days_ago // 30  # Slight penalty for older dates
            else:
                score -= 100  # Strong penalty for future dates
            
            if score > best_score:
                best_score = score
                emission_date = found_date
        
        if not emission_date:
            return None
        
        # Calculate validity date
        if unit == 'months':
            validity_date = emission_date + relativedelta(months=amount)
        else:  # days
            validity_date = emission_date + timedelta(days=amount)
        
        logger.info(f"Calculated validity: emission={emission_date}, +{amount} {unit} = {validity_date}")
        return validity_date
    
    def find_validity_date(self, text: str) -> Optional[date]:
        """
        Find the most likely validity/expiration date in text.
        
        Looks for dates near validity keywords and returns the most recent
        future date or the last date found.
        
        Args:
            text: Text to search
            
        Returns:
            Most likely validity date or None
        """
        if not text:
            return None
        
        # First, try to extract from structured fields (fastest and most accurate)
        structured_date = self.extract_structured_date(text)
        if structured_date:
            logger.info(f"Using structured field date: {structured_date}")
            return structured_date
        
        # Second, try to calculate from relative validity (e.g., "prazo de 3 meses")
        relative_date = self.calculate_relative_validity(text)
        if relative_date:
            logger.info(f"Using calculated relative validity date: {relative_date}")
            return relative_date
        
        # Extract all dates with context
        dates_with_context = self.extract_dates_from_text(text)
        
        if not dates_with_context:
            return None
        
        # Score dates based on proximity to validity keywords
        scored_dates = []
        
        for found_date, context in dates_with_context:
            score = 0
            context_lower = context.lower()
            
            # Check if validity keywords are in context
            for keyword in self.VALIDITY_KEYWORDS:
                if keyword in context_lower:
                    score += 10
                    # Bonus if keyword is very close to date (within 50 chars)
                    keyword_pos = context_lower.find(keyword)
                    if keyword_pos != -1 and abs(keyword_pos - len(context)//2) < 50:
                        score += 5
            
            # Prefer future dates (likely validity dates)
            if found_date > date.today():
                score += 8
            elif found_date == date.today():
                score += 3
            
            # Prefer dates within reasonable range (not too far in past/future)
            days_diff = abs((found_date - date.today()).days)
            if days_diff < 365 * 2:  # Within 2 years
                score += 5
            elif days_diff < 365 * 5:  # Within 5 years
                score += 2
            
            # Penalize very old dates
            if found_date < date.today() and days_diff > 365:
                score -= 10
            
            scored_dates.append((score, found_date, context))
        
        # Sort by score (highest first)
        scored_dates.sort(reverse=True, key=lambda x: x[0])
        
        # Return the highest scored date
        if scored_dates:
            best_score, best_date, best_context = scored_dates[0]
            logger.debug(f"Found validity date: {best_date} (score: {best_score})")
            logger.debug(f"Context: {best_context[:100]}")
            return best_date
        
        return None
    
    def is_expired(self, expiration_date: Optional[date], 
                   reference_date: Optional[date] = None) -> bool:
        """
        Check if a document is expired.
        
        Args:
            expiration_date: Date when document expires
            reference_date: Date to check against (default: today)
            
        Returns:
            True if expired, False otherwise
        """
        if expiration_date is None:
            return False  # Cannot determine expiration without date
        
        if reference_date is None:
            reference_date = date.today()
        
        return expiration_date < reference_date
    
    def expires_soon(self, expiration_date: Optional[date], 
                     reference_date: Optional[date] = None) -> bool:
        """
        Check if document expires within grace period.
        
        Args:
            expiration_date: Date when document expires
            reference_date: Date to check against (default: today)
            
        Returns:
            True if expires soon, False otherwise
        """
        if expiration_date is None:
            return False
        
        if reference_date is None:
            reference_date = date.today()
        
        warning_date = reference_date + timedelta(days=self.grace_period_days)
        
        return reference_date <= expiration_date <= warning_date
    
    def get_days_until_expiration(self, expiration_date: Optional[date],
                                   reference_date: Optional[date] = None) -> Optional[int]:
        """
        Calculate days until expiration.
        
        Args:
            expiration_date: Date when document expires
            reference_date: Date to check against (default: today)
            
        Returns:
            Number of days (negative if expired) or None if date is None
        """
        if expiration_date is None:
            return None
        
        if reference_date is None:
            reference_date = date.today()
        
        delta = expiration_date - reference_date
        return delta.days
    
    def validate_document_date(self, text: str, document_name: str = "") -> dict:
        """
        Complete validation of document expiration date.
        
        Args:
            text: Document text content
            document_name: Name of document (for logging)
            
        Returns:
            Dictionary with validation results:
            {
                'has_date': bool,
                'expiration_date': date or None,
                'is_expired': bool,
                'expires_soon': bool,
                'days_until_expiration': int or None,
                'status': str  # 'valid', 'expires_soon', 'expired', 'unknown'
            }
        """
        result = {
            'has_date': False,
            'expiration_date': None,
            'is_expired': False,
            'expires_soon': False,
            'days_until_expiration': None,
            'status': 'unknown',
            'document_name': document_name
        }
        
        # Find validity date
        expiration_date = self.find_validity_date(text)
        
        if expiration_date:
            result['has_date'] = True
            result['expiration_date'] = expiration_date
            result['is_expired'] = self.is_expired(expiration_date)
            result['expires_soon'] = self.expires_soon(expiration_date)
            result['days_until_expiration'] = self.get_days_until_expiration(expiration_date)
            
            # Determine status
            if result['is_expired']:
                result['status'] = 'expired'
            elif result['expires_soon']:
                result['status'] = 'expires_soon'
            else:
                result['status'] = 'valid'
        
        logger.info(f"Document '{document_name}' validation: {result['status']}")
        
        return result


# Convenience functions
def parse_date(date_string: str) -> Optional[date]:
    """
    Parse date string (convenience function).
    
    Args:
        date_string: Date string to parse
        
    Returns:
        Parsed date or None
    """
    validator = DateValidator()
    return validator.parse_date(date_string)


def is_document_expired(text: str) -> bool:
    """
    Check if document is expired (convenience function).
    
    Args:
        text: Document text content
        
    Returns:
        True if expired, False otherwise
    """
    validator = DateValidator()
    result = validator.validate_document_date(text)
    return result['is_expired']
