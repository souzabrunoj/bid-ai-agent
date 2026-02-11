"""
Bid notice (edital) reader and requirements extractor.

Analyzes bid notice documents to identify all required documents
and their categories for procurement participation.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

from models import get_llm, PromptTemplates, LLMError
from utils import extract_pdf_text, PDFExtractionError, validate_pdf_file, SecurityValidationError

logger = logging.getLogger(__name__)


class EditalReaderError(Exception):
    """Raised when edital reading fails."""
    pass


class BidRequirement:
    """
    Represents a single document requirement from bid notice.
    """
    
    def __init__(
        self,
        name: str,
        category: str,
        description: str = "",
        requirements: str = "",
        is_mandatory: bool = True
    ):
        """
        Initialize bid requirement.
        
        Args:
            name: Document name
            category: Document category
            description: Brief description
            requirements: Specific requirements
            is_mandatory: Whether document is mandatory
        """
        self.name = name
        self.category = category
        self.description = description
        self.requirements = requirements
        self.is_mandatory = is_mandatory
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'requirements': self.requirements,
            'is_mandatory': self.is_mandatory
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BidRequirement':
        """Create from dictionary."""
        return cls(
            name=data.get('name', ''),
            category=data.get('category', 'unknown'),
            description=data.get('description', ''),
            requirements=data.get('requirements', ''),
            is_mandatory=data.get('is_mandatory', True)
        )
    
    def __repr__(self) -> str:
        return f"BidRequirement(name='{self.name}', category='{self.category}')"


class EditalReader:
    """
    Reads and analyzes bid notice documents (editais).
    
    Extracts required documents and classifies them by category
    for procurement compliance checking.
    """
    
    # Valid document categories
    VALID_CATEGORIES = {
        'habilitacao_juridica',      # Legal qualification
        'regularidade_fiscal',       # Tax compliance
        'qualificacao_tecnica',      # Technical qualification
        'qualificacao_economica',    # Economic-financial qualification
        'proposta_comercial',        # Commercial proposal
        'outros',                    # Others
    }
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize edital reader.
        
        Args:
            use_llm: Whether to use LLM for analysis
        """
        self.use_llm = use_llm
        self.llm = None
        
        if use_llm:
            try:
                self.llm = get_llm()
                logger.info("LLM initialized for edital reading")
            except LLMError as e:
                logger.warning(f"LLM initialization failed: {e}")
                logger.warning("Falling back to rule-based extraction")
                self.use_llm = False
    
    def read_edital_file(self, file_path: Path) -> str:
        """
        Read edital PDF file and extract text.
        
        Args:
            file_path: Path to edital PDF
            
        Returns:
            Extracted text content
            
        Raises:
            EditalReaderError: If reading fails
        """
        try:
            # Validate file
            logger.info(f"Validating edital file: {file_path.name}")
            validate_pdf_file(file_path)
            
            # Extract text
            logger.info(f"Extracting text from edital: {file_path.name}")
            text = extract_pdf_text(file_path, enable_ocr=True)
            
            if not text or len(text.strip()) < 100:
                raise EditalReaderError(
                    "Edital appears to be empty or text extraction failed"
                )
            
            logger.info(f"Successfully extracted {len(text)} characters from edital")
            return text
            
        except (PDFExtractionError, SecurityValidationError) as e:
            raise EditalReaderError(f"Failed to read edital file: {e}")
    
    def extract_requirements_with_llm(self, edital_text: str) -> List[BidRequirement]:
        """
        Extract requirements using LLM analysis.
        
        Args:
            edital_text: Edital text content
            
        Returns:
            List of bid requirements
            
        Raises:
            EditalReaderError: If extraction fails
        """
        if not self.llm:
            raise EditalReaderError("LLM not available")
        
        try:
            logger.info("Analyzing edital with LLM...")
            
            # Create prompt
            prompt = PromptTemplates.extract_bid_requirements(edital_text)
            
            # Generate analysis
            result = self.llm.generate_json(
                prompt,
                max_tokens=4096,
                temperature=0.1
            )
            
            # Parse requirements
            requirements = []
            documents = result.get('documents', [])
            
            logger.info(f"LLM identified {len(documents)} required documents")
            
            for doc_data in documents:
                req = BidRequirement.from_dict(doc_data)
                
                # Validate category
                if req.category not in self.VALID_CATEGORIES:
                    logger.warning(
                        f"Invalid category '{req.category}' for document '{req.name}', "
                        f"setting to 'outros'"
                    )
                    req.category = 'outros'
                
                requirements.append(req)
            
            return requirements
            
        except (LLMError, KeyError, json.JSONDecodeError) as e:
            logger.error(f"LLM extraction failed: {e}")
            raise EditalReaderError(f"Failed to extract requirements with LLM: {e}")
    
    def extract_requirements_rule_based(self, edital_text: str) -> List[BidRequirement]:
        """
        Extract requirements using rule-based pattern matching.
        
        Fallback method when LLM is not available.
        
        Args:
            edital_text: Edital text content
            
        Returns:
            List of bid requirements
        """
        logger.info("Using rule-based extraction (LLM not available)")
        
        requirements = []
        
        # Common document patterns in Brazilian editais
        document_patterns = {
            'habilitacao_juridica': [
                'contrato social', 'ata de assembleia', 'registro comercial',
                'inscrição comercial', 'cnpj', 'documento de constituição'
            ],
            'regularidade_fiscal': [
                'certidão negativa', 'certidão de regularidade fiscal',
                'certidão de regularidade da fazenda', 'regularidade fgts',
                'certidão trabalhista', 'cnd', 'certidão federal',
                'certidão estadual', 'certidão municipal'
            ],
            'qualificacao_tecnica': [
                'atestado de capacidade técnica', 'certidão de acervo técnico',
                'registro profissional', 'comprovação de aptidão',
                'experiência anterior', 'certidão cat'
            ],
            'qualificacao_economica': [
                'balanço patrimonial', 'demonstração contábil',
                'certidão de falência', 'patrimônio líquido',
                'capital social', 'índice de liquidez'
            ]
        }
        
        text_lower = edital_text.lower()
        
        # Search for each pattern
        for category, patterns in document_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    # Create requirement
                    req = BidRequirement(
                        name=pattern.title(),
                        category=category,
                        description=f"Documento identificado: {pattern}",
                        requirements="Verificar exigências específicas no edital"
                    )
                    requirements.append(req)
        
        logger.info(f"Rule-based extraction found {len(requirements)} documents")
        
        if not requirements:
            logger.warning("No documents identified by rule-based extraction")
        
        return requirements
    
    def extract_requirements(self, edital_text: str) -> List[BidRequirement]:
        """
        Extract all requirements from edital text.
        
        Uses LLM if available, otherwise falls back to rule-based extraction.
        
        Args:
            edital_text: Edital text content
            
        Returns:
            List of bid requirements
        """
        if self.use_llm and self.llm:
            try:
                return self.extract_requirements_with_llm(edital_text)
            except EditalReaderError as e:
                logger.warning(f"LLM extraction failed, falling back to rules: {e}")
        
        # Fallback to rule-based
        return self.extract_requirements_rule_based(edital_text)
    
    def analyze_edital(self, file_path: Path) -> Dict[str, Any]:
        """
        Complete edital analysis pipeline.
        
        Args:
            file_path: Path to edital PDF
            
        Returns:
            Dictionary with analysis results:
            {
                'file_name': str,
                'requirements': List[BidRequirement],
                'requirements_by_category': Dict[str, List[BidRequirement]],
                'total_requirements': int,
                'extraction_method': str
            }
        """
        logger.info(f"Starting edital analysis: {file_path.name}")
        
        # Read edital
        edital_text = self.read_edital_file(file_path)
        
        # Extract requirements
        requirements = self.extract_requirements(edital_text)
        
        # Group by category
        requirements_by_category = {}
        for req in requirements:
            if req.category not in requirements_by_category:
                requirements_by_category[req.category] = []
            requirements_by_category[req.category].append(req)
        
        # Prepare result
        result = {
            'file_name': file_path.name,
            'requirements': [req.to_dict() for req in requirements],
            'requirements_by_category': {
                cat: [req.to_dict() for req in reqs]
                for cat, reqs in requirements_by_category.items()
            },
            'total_requirements': len(requirements),
            'extraction_method': 'llm' if (self.use_llm and self.llm) else 'rule_based',
            'categories_found': list(requirements_by_category.keys())
        }
        
        logger.info(f"Edital analysis complete: {len(requirements)} requirements found")
        logger.info(f"Categories: {', '.join(result['categories_found'])}")
        
        return result
    
    def save_analysis(self, analysis: Dict[str, Any], output_path: Path) -> None:
        """
        Save analysis results to JSON file.
        
        Args:
            analysis: Analysis results dictionary
            output_path: Path to save JSON file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            logger.info(f"Analysis saved to: {output_path}")
        except Exception as e:
            raise EditalReaderError(f"Failed to save analysis: {e}")


# Convenience function
def analyze_edital_file(file_path: Path) -> Dict[str, Any]:
    """
    Analyze edital file (convenience function).
    
    Args:
        file_path: Path to edital PDF
        
    Returns:
        Analysis results dictionary
    """
    reader = EditalReader()
    return reader.analyze_edital(file_path)
