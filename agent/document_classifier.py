"""
Document classifier for company documents.

Identifies document types and categories, extracts validity dates,
and prepares documents for compliance checking.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import date

from models import get_llm, PromptTemplates, LLMError
from utils import (
    extract_pdf_text,
    PDFExtractionError,
    validate_pdf_file,
    SecurityValidationError,
    DateValidator,
    DateValidationError
)

logger = logging.getLogger(__name__)


class DocumentClassifierError(Exception):
    """Raised when document classification fails."""
    pass


class ClassifiedDocument:
    """
    Represents a classified company document.
    """
    
    def __init__(
        self,
        file_path: Path,
        document_type: str,
        category: str,
        confidence: float = 0.0,
        expiration_date: Optional[date] = None,
        is_expired: bool = False,
        days_until_expiration: Optional[int] = None,
        text_content: Optional[str] = None
    ):
        """
        Initialize classified document.
        
        Args:
            file_path: Path to document file
            document_type: Type of document
            category: Document category
            confidence: Classification confidence (0.0 to 1.0)
            expiration_date: Document expiration date
            is_expired: Whether document is expired
            days_until_expiration: Days until expiration
            text_content: Extracted text content (optional)
        """
        self.file_path = file_path
        self.file_name = file_path.name
        self.document_type = document_type
        self.category = category
        self.confidence = confidence
        self.expiration_date = expiration_date
        self.validity_date = expiration_date  # Alias for compatibility
        self.is_expired = is_expired
        self.days_until_expiration = days_until_expiration
        self.text_content = text_content
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file_name': self.file_name,
            'file_path': str(self.file_path),
            'document_type': self.document_type,
            'category': self.category,
            'confidence': self.confidence,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'is_expired': self.is_expired,
            'days_until_expiration': self.days_until_expiration,
            'status': self.get_status()
        }
    
    def get_status(self) -> str:
        """Get document status."""
        if self.is_expired:
            return 'expired'
        elif self.expiration_date and self.days_until_expiration is not None:
            if self.days_until_expiration < 30:
                return 'expires_soon'
            return 'valid'
        elif self.expiration_date is None and not self.is_expired:
            # No expiration date found - could be non-expiring document or unknown
            return 'valid'  # Assume valid if no date and not marked as expired
        return 'unknown'
    
    def __repr__(self) -> str:
        return f"ClassifiedDocument(type='{self.document_type}', category='{self.category}', status='{self.get_status()}')"


class DocumentClassifier:
    """
    Classifies company documents for bid compliance.
    
    Identifies document types, extracts validity dates, and
    categorizes documents for requirement matching.
    """
    
    # Valid categories (same as EditalReader)
    VALID_CATEGORIES = {
        'habilitacao_juridica',
        'regularidade_fiscal',
        'qualificacao_tecnica',
        'qualificacao_economica',
        'proposta_comercial',
        'outros',
    }
    
    # Document type patterns for filename-based classification
    FILENAME_PATTERNS = {
        'habilitacao_juridica': [
            'contrato', 'cnpj', 'constituicao', 'estatuto', 'ata',
            'registro', 'social', 'assembleia', 'contrato_social'
        ],
        'regularidade_fiscal': [
            'certidao', 'cnd', 'regularidade', 'fiscal', 'fazenda',
            'fgts', 'inss', 'trabalhista', 'federal', 'estadual', 'municipal',
            'civel', 'tributos', 'debitos', 'crf', 'cndt'
        ],
        'qualificacao_tecnica': [
            'atestado', 'capacidade', 'tecnica', 'acervo', 'cat',
            'registro', 'profissional', 'experiencia', 'alvara', 'licenca'
        ],
        'qualificacao_economica': [
            'balanco', 'contabil', 'demonstracao', 'patrimonio',
            'falencia', 'liquidez', 'capital', 'concordata', 'recuperacao'
        ],
    }
    
    # Documents that DO NOT expire (no validity date)
    NO_EXPIRY_PATTERNS = [
        'contrato_social',      # Social contract - valid until amended
        'contrato social',
        'estatuto',             # Company statute
        'cnpj',                 # CNPJ registration
        'ata',                  # Meeting minutes
        'atestado',             # Technical attestation
        'capacidade_tecnica',   # Technical capacity certificate
        'capacidade tecnica',
        'acervo',               # Technical portfolio
        'registro',             # Professional registration (some types)
        'inscricao',            # Registration documents
    ]
    
    # Documents with ISSUANCE date (not expiry) - typically 90 days validity
    ISSUANCE_DATE_PATTERNS = [
        'falencia',             # Bankruptcy certificate
        'concordata',           # Concordat certificate
        'recuperacao',          # Judicial recovery certificate
        'certidao_falencia',
        'certidao falencia',
        'civel',                # Civil court certificate
        'cnd_civel',
        'certidao civel',
        'certidao_civel',
    ]
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize document classifier.
        
        Args:
            use_llm: Whether to use LLM for classification
        """
        self.use_llm = use_llm
        self.llm = None
        self.date_validator = DateValidator(grace_period_days=30)
        
        if use_llm:
            try:
                self.llm = get_llm()
                logger.info("LLM initialized for document classification")
            except LLMError as e:
                logger.warning(f"LLM initialization failed: {e}")
                self.use_llm = False
    
    def _is_non_expiring_document(self, filename: str) -> bool:
        """
        Check if document type does not have expiration date.
        
        Args:
            filename: Document filename
            
        Returns:
            True if document doesn't expire
        """
        filename_lower = filename.lower()
        
        for pattern in self.NO_EXPIRY_PATTERNS:
            if pattern in filename_lower:
                return True
        
        return False
    
    def _is_issuance_date_document(self, filename: str) -> bool:
        """
        Check if document has issuance date (not expiry) with 90-day validity.
        
        Args:
            filename: Document filename
            
        Returns:
            True if document uses issuance date
        """
        filename_lower = filename.lower()
        
        for pattern in self.ISSUANCE_DATE_PATTERNS:
            if pattern in filename_lower:
                return True
        
        return False
    
    def classify_by_filename(self, filename: str) -> tuple[str, float]:
        """
        Classify document based on filename.
        
        Args:
            filename: Document filename
            
        Returns:
            Tuple of (category, confidence)
        """
        filename_lower = filename.lower()
        
        # Check each category's patterns
        matches = []
        for category, patterns in self.FILENAME_PATTERNS.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    matches.append((category, 0.6))  # Medium confidence for filename match
                    break
        
        if matches:
            # Return first match (could be improved with scoring)
            return matches[0]
        
        return ('outros', 0.3)
    
    def classify_by_content_llm(
        self,
        text_content: str,
        filename: str
    ) -> tuple[str, str, float]:
        """
        Classify document using LLM analysis.
        
        Args:
            text_content: Document text content
            filename: Original filename
            
        Returns:
            Tuple of (document_type, category, confidence)
        """
        if not self.llm:
            raise DocumentClassifierError("LLM not available")
        
        try:
            # Truncate content for analysis (use first 2000 chars)
            content_sample = text_content[:2000]
            
            # Create prompt
            prompt = PromptTemplates.classify_document(content_sample, filename)
            
            # Generate classification
            result = self.llm.generate_json(
                prompt,
                max_tokens=500,
                temperature=0.1
            )
            
            document_type = result.get('document_type', 'Documento não identificado')
            category = result.get('category', 'outros')
            confidence = float(result.get('confidence', 0.5))
            
            # Validate category
            if category not in self.VALID_CATEGORIES:
                logger.warning(f"Invalid category '{category}', setting to 'outros'")
                category = 'outros'
                confidence *= 0.5  # Reduce confidence
            
            return (document_type, category, confidence)
            
        except (LLMError, KeyError, ValueError) as e:
            logger.error(f"LLM classification failed: {e}")
            raise DocumentClassifierError(f"Failed to classify with LLM: {e}")
    
    def classify_by_content_rules(
        self,
        text_content: str,
        filename: str
    ) -> tuple[str, str, float]:
        """
        Classify document using rule-based content analysis.
        
        Args:
            text_content: Document text content
            filename: Original filename
            
        Returns:
            Tuple of (document_type, category, confidence)
        """
        text_lower = text_content.lower()
        
        # Check for specific document indicators
        if 'contrato social' in text_lower or 'cnpj' in text_lower:
            return ('Contrato Social / CNPJ', 'habilitacao_juridica', 0.7)
        
        if 'certidão' in text_lower or 'certidao' in text_lower:
            if 'regularidade fiscal' in text_lower or 'fazenda' in text_lower:
                return ('Certidão de Regularidade Fiscal', 'regularidade_fiscal', 0.7)
            elif 'fgts' in text_lower:
                return ('Certidão de Regularidade do FGTS', 'regularidade_fiscal', 0.7)
            elif 'trabalhista' in text_lower:
                return ('Certidão Negativa Trabalhista', 'regularidade_fiscal', 0.7)
        
        if 'atestado' in text_lower and ('capacidade' in text_lower or 'técnica' in text_lower):
            return ('Atestado de Capacidade Técnica', 'qualificacao_tecnica', 0.7)
        
        if 'balanço' in text_lower or 'balanco' in text_lower or 'demonstração contábil' in text_lower:
            return ('Demonstração Contábil / Balanço', 'qualificacao_economica', 0.7)
        
        # Fallback to filename classification
        category, confidence = self.classify_by_filename(filename)
        return (filename, category, confidence * 0.8)
    
    def extract_validity_date(self, text_content: str) -> Dict[str, Any]:
        """
        Extract validity/expiration date from document.
        
        Args:
            text_content: Document text content
            
        Returns:
            Dictionary with date validation results
        """
        try:
            result = self.date_validator.validate_document_date(text_content)
            return result
        except Exception as e:
            logger.warning(f"Date extraction failed: {e}")
            return {
                'has_date': False,
                'expiration_date': None,
                'is_expired': False,
                'days_until_expiration': None,
                'status': 'unknown'
            }
    
    def extract_issuance_date(self, text_content: str, max_days: int = 90) -> Dict[str, Any]:
        """
        Extract ISSUANCE date from document (for certificates with 90-day validity).
        
        Args:
            text_content: Document text content
            max_days: Maximum days since issuance (default 90)
            
        Returns:
            Dictionary with issuance date validation results
        """
        from datetime import datetime, date
        import re
        
        try:
            # Look for issuance date patterns
            issuance_patterns = [
                r'(?:data\s+de\s+)?emiss[ãa]o[:\s]+(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
                r'(?:data\s+de\s+)?expedi[çc][ãa]o[:\s]+(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
                r'expedido\s+em[:\s]+(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
                r'emitido\s+em[:\s]+(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',
            ]
            
            issuance_date = None
            for pattern_str in issuance_patterns:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                match = pattern.search(text_content.lower())
                
                if match:
                    try:
                        day, month, year = match.groups()
                        issuance_date = date(int(year), int(month), int(day))
                        logger.info(f"Found issuance date: {issuance_date}")
                        break
                    except (ValueError, IndexError):
                        continue
            
            if not issuance_date:
                return {
                    'has_date': False,
                    'issuance_date': None,
                    'days_since_issuance': None,
                    'is_expired': False,
                    'status': 'unknown'
                }
            
            # Calculate days since issuance
            today = date.today()
            days_since = (today - issuance_date).days
            
            # Check if within 90-day limit
            is_expired = days_since > max_days
            
            status = 'expired' if is_expired else 'valid'
            if not is_expired and days_since > (max_days - 10):  # Within 10 days of limit
                status = 'expires_soon'
            
            logger.info(f"Issuance date validation: {issuance_date}, {days_since} days ago, status: {status}")
            
            return {
                'has_date': True,
                'issuance_date': issuance_date,
                'days_since_issuance': days_since,
                'is_expired': is_expired,
                'expiration_date': None,  # Not applicable
                'days_until_expiration': None,
                'status': status
            }
            
        except Exception as e:
            logger.warning(f"Issuance date extraction failed: {e}")
            return {
                'has_date': False,
                'issuance_date': None,
                'days_since_issuance': None,
                'is_expired': False,
                'status': 'unknown'
            }
    
    def classify_document(
        self,
        file_path: Path,
        extract_text: bool = True
    ) -> ClassifiedDocument:
        """
        Complete document classification pipeline.
        
        Args:
            file_path: Path to document PDF
            extract_text: Whether to extract and analyze text content
            
        Returns:
            ClassifiedDocument instance
        """
        logger.info(f"Classifying document: {file_path.name}")
        
        try:
            # Validate file
            validate_pdf_file(file_path)
            
            # Extract text if requested
            text_content = None
            if extract_text:
                try:
                    text_content = extract_pdf_text(file_path, enable_ocr=True)
                except PDFExtractionError as e:
                    logger.warning(f"Text extraction failed for {file_path.name}: {e}")
            
            # Classify document
            if text_content and self.use_llm and self.llm:
                try:
                    document_type, category, confidence = self.classify_by_content_llm(
                        text_content, file_path.name
                    )
                except DocumentClassifierError:
                    document_type, category, confidence = self.classify_by_content_rules(
                        text_content, file_path.name
                    )
            elif text_content:
                document_type, category, confidence = self.classify_by_content_rules(
                    text_content, file_path.name
                )
            else:
                # Filename only
                category, confidence = self.classify_by_filename(file_path.name)
                document_type = file_path.name
            
            # Extract validity date (only if document type can expire)
            date_info = None
            if text_content and not self._is_non_expiring_document(file_path.name):
                # Check if it's an issuance-date document (90-day validity)
                if self._is_issuance_date_document(file_path.name):
                    logger.info(f"Document {file_path.name} uses issuance date (90-day validity)")
                    date_info = self.extract_issuance_date(text_content, max_days=90)
                else:
                    date_info = self.extract_validity_date(text_content)
            elif self._is_non_expiring_document(file_path.name):
                logger.info(f"Document {file_path.name} is a non-expiring type, skipping date validation")
            
            # Create classified document
            # Handle both expiration_date and issuance_date
            if date_info:
                expiration_date = date_info.get('expiration_date') or date_info.get('issuance_date')
                is_expired = date_info.get('is_expired', False)
                days_until_expiration = date_info.get('days_until_expiration') or date_info.get('days_since_issuance')
            else:
                expiration_date = None
                is_expired = False
                days_until_expiration = None
            
            classified = ClassifiedDocument(
                file_path=file_path,
                document_type=document_type,
                category=category,
                confidence=confidence,
                expiration_date=expiration_date,
                is_expired=is_expired,
                days_until_expiration=days_until_expiration,
                text_content=text_content if extract_text else None
            )
            
            logger.info(
                f"Classified: {file_path.name} -> {category} "
                f"(confidence: {confidence:.2f}, status: {classified.get_status()})"
            )
            
            return classified
            
        except (PDFExtractionError, SecurityValidationError) as e:
            raise DocumentClassifierError(f"Failed to classify document: {e}")
    
    def classify_documents_batch(
        self,
        file_paths: List[Path]
    ) -> List[ClassifiedDocument]:
        """
        Classify multiple documents in batch.
        
        Args:
            file_paths: List of document file paths
            
        Returns:
            List of ClassifiedDocument instances
        """
        logger.info(f"Classifying {len(file_paths)} documents...")
        
        classified_docs = []
        errors = []
        
        for file_path in file_paths:
            try:
                classified = self.classify_document(file_path)
                classified_docs.append(classified)
            except DocumentClassifierError as e:
                logger.error(f"Failed to classify {file_path.name}: {e}")
                errors.append((file_path, str(e)))
        
        logger.info(
            f"Classification complete: {len(classified_docs)} successful, "
            f"{len(errors)} failed"
        )
        
        return classified_docs


# Convenience function
def classify_document_file(file_path: Path) -> ClassifiedDocument:
    """
    Classify document file (convenience function).
    
    Args:
        file_path: Path to document PDF
        
    Returns:
        ClassifiedDocument instance
    """
    classifier = DocumentClassifier()
    return classifier.classify_document(file_path)
