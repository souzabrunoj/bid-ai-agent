"""
AI agent modules for bid document processing.
"""

from .edital_reader import (
    EditalReader,
    BidRequirement,
    analyze_edital_file,
    EditalReaderError
)
from .document_classifier import (
    DocumentClassifier,
    ClassifiedDocument,
    classify_document_file,
    DocumentClassifierError
)
from .comparator import (
    RequirementComparator,
    RequirementMatch,
    ComplianceReport,
    compare_requirements,
    ComparatorError
)

__all__ = [
    # Edital reader
    'EditalReader',
    'BidRequirement',
    'analyze_edital_file',
    'EditalReaderError',
    # Document classifier
    'DocumentClassifier',
    'ClassifiedDocument',
    'classify_document_file',
    'DocumentClassifierError',
    # Comparator
    'RequirementComparator',
    'RequirementMatch',
    'ComplianceReport',
    'compare_requirements',
    'ComparatorError',
]
