"""
Requirements comparator for bid compliance checking.

Compares required documents from bid notice against available
company documents and generates compliance reports.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from datetime import date

from agent.edital_reader import BidRequirement
from agent.document_classifier import ClassifiedDocument

logger = logging.getLogger(__name__)


class ComparatorError(Exception):
    """Raised when comparison fails."""
    pass


class RequirementMatch:
    """
    Represents a match between requirement and document.
    """
    
    def __init__(
        self,
        requirement: BidRequirement,
        matched_document: Optional[ClassifiedDocument] = None,
        match_confidence: float = 0.0,
        status: str = 'missing'
    ):
        """
        Initialize requirement match.
        
        Args:
            requirement: Bid requirement
            matched_document: Matched company document (if any)
            match_confidence: Confidence of the match
            status: Match status ('ok', 'expired', 'missing', 'warning')
        """
        self.requirement = requirement
        self.matched_document = matched_document
        self.match_confidence = match_confidence
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'requirement': self.requirement.to_dict(),
            'matched_document': self.matched_document.to_dict() if self.matched_document else None,
            'match_confidence': self.match_confidence,
            'status': self.status,
            'observations': self.get_observations()
        }
    
    def get_observations(self) -> List[str]:
        """Get observations about the match."""
        observations = []
        
        if self.status == 'missing':
            observations.append("Documento não encontrado")
        elif self.status == 'expired':
            if self.matched_document and self.matched_document.expiration_date:
                observations.append(
                    f"Documento vencido em {self.matched_document.expiration_date.isoformat()}"
                )
            else:
                observations.append("Documento vencido")
        elif self.status == 'warning':
            if self.matched_document and self.matched_document.days_until_expiration:
                observations.append(
                    f"Documento vence em {self.matched_document.days_until_expiration} dias"
                )
        elif self.status == 'ok':
            if self.matched_document and self.matched_document.expiration_date:
                observations.append(
                    f"Documento válido até {self.matched_document.expiration_date.isoformat()}"
                )
        
        if self.match_confidence < 0.7:
            observations.append(f"Baixa confiança na correspondência ({self.match_confidence:.2f})")
        
        return observations
    
    def __repr__(self) -> str:
        return f"RequirementMatch(requirement='{self.requirement.name}', status='{self.status}')"


class ComplianceReport:
    """
    Comprehensive compliance report for bid submission.
    """
    
    def __init__(self):
        """Initialize compliance report."""
        self.matches: List[RequirementMatch] = []
        self.unmatched_documents: List[ClassifiedDocument] = []
        self.statistics: Dict[str, int] = {
            'total_requirements': 0,
            'requirements_ok': 0,
            'requirements_expired': 0,
            'requirements_missing': 0,
            'requirements_warning': 0,
            'total_documents': 0,
            'documents_matched': 0,
            'documents_unmatched': 0
        }
    
    def add_match(self, match: RequirementMatch) -> None:
        """Add a requirement match to the report."""
        self.matches.append(match)
        self.statistics['total_requirements'] += 1
        
        if match.status == 'ok':
            self.statistics['requirements_ok'] += 1
        elif match.status == 'expired':
            self.statistics['requirements_expired'] += 1
        elif match.status == 'missing':
            self.statistics['requirements_missing'] += 1
        elif match.status == 'warning':
            self.statistics['requirements_warning'] += 1
        
        if match.matched_document:
            self.statistics['documents_matched'] += 1
    
    def set_unmatched_documents(self, documents: List[ClassifiedDocument]) -> None:
        """Set unmatched documents."""
        self.unmatched_documents = documents
        self.statistics['documents_unmatched'] = len(documents)
    
    def is_compliant(self) -> bool:
        """Check if all requirements are met."""
        return (
            self.statistics['requirements_missing'] == 0 and
            self.statistics['requirements_expired'] == 0
        )
    
    def get_compliance_rate(self) -> float:
        """Calculate compliance rate."""
        total = self.statistics['total_requirements']
        if total == 0:
            return 0.0
        ok = self.statistics['requirements_ok']
        return (ok / total) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'matches': [match.to_dict() for match in self.matches],
            'unmatched_documents': [doc.to_dict() for doc in self.unmatched_documents],
            'statistics': self.statistics,
            'is_compliant': self.is_compliant(),
            'compliance_rate': self.get_compliance_rate(),
            'summary': self.get_summary()
        }
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        return (
            f"Compliance Report:\n"
            f"  ✅ OK: {self.statistics['requirements_ok']}\n"
            f"  ⚠️  Warning: {self.statistics['requirements_warning']}\n"
            f"  ❌ Expired: {self.statistics['requirements_expired']}\n"
            f"  ❓ Missing: {self.statistics['requirements_missing']}\n"
            f"  📊 Compliance Rate: {self.get_compliance_rate():.1f}%"
        )


class RequirementComparator:
    """
    Compares bid requirements against available documents.
    
    Performs intelligent matching and generates compliance reports.
    """
    
    def __init__(self, similarity_threshold: float = 0.5):
        """
        Initialize comparator.
        
        Args:
            similarity_threshold: Minimum similarity for a match
        """
        self.similarity_threshold = similarity_threshold
    
    def calculate_similarity(
        self,
        requirement: BidRequirement,
        document: ClassifiedDocument
    ) -> float:
        """
        Calculate similarity between requirement and document.
        
        Args:
            requirement: Bid requirement
            document: Company document
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        score = 0.0
        
        # Category match (most important)
        if requirement.category == document.category:
            score += 0.5
        
        # Name similarity (check both document type and filename)
        req_name_lower = requirement.name.lower()
        doc_type_lower = document.document_type.lower()
        doc_filename_lower = document.file_name.lower()
        
        # Common abbreviations and synonyms
        synonyms = {
            'cnd': ['certidão negativa', 'certidao negativa', 'certidão', 'certidao'],
            'cndt': ['certidão negativa de débitos trabalhistas', 'certidao trabalhista'],
            'fgts': ['regularidade do fgts', 'regularidade fgts', 'crf'],
            'municipal': ['prefeitura', 'município', 'municipio'],
            'estadual': ['estado', 'fazenda estadual'],
            'federal': ['receita federal', 'união', 'uniao']
        }
        
        # Extract keywords from requirement
        req_keywords = set(req_name_lower.split())
        
        # Extract keywords from document type AND filename
        doc_type_keywords = set(doc_type_lower.split())
        doc_filename_keywords = set(doc_filename_lower.replace('_', ' ').replace('-', ' ').split())
        doc_keywords = doc_type_keywords | doc_filename_keywords
        
        # Check for synonym matches
        for abbrev, full_terms in synonyms.items():
            if abbrev in req_name_lower or any(term in req_name_lower for term in full_terms):
                if abbrev in doc_filename_lower or abbrev in doc_type_lower:
                    score += 0.3
                elif any(term in doc_filename_lower or term in doc_type_lower for term in full_terms):
                    score += 0.25
        
        # Calculate Jaccard similarity
        if req_keywords and doc_keywords:
            intersection = len(req_keywords & doc_keywords)
            union = len(req_keywords | doc_keywords)
            keyword_similarity = intersection / union if union > 0 else 0
            score += keyword_similarity * 0.3
        
        # Boost for exact phrase matches in either document type or filename
        if req_name_lower in doc_type_lower or doc_type_lower in req_name_lower:
            score += 0.2
        if req_name_lower in doc_filename_lower or any(word in doc_filename_lower for word in req_keywords if len(word) > 3):
            score += 0.15
        
        # Use document's classification confidence
        score *= document.confidence
        
        return min(score, 1.0)
    
    def find_best_match(
        self,
        requirement: BidRequirement,
        documents: List[ClassifiedDocument]
    ) -> Optional[tuple[ClassifiedDocument, float]]:
        """
        Find best matching document for requirement.
        
        Args:
            requirement: Bid requirement
            documents: Available documents
            
        Returns:
            Tuple of (best_document, similarity_score) or None
        """
        best_match = None
        best_score = 0.0
        
        for document in documents:
            similarity = self.calculate_similarity(requirement, document)
            
            if similarity > best_score and similarity >= self.similarity_threshold:
                best_match = document
                best_score = similarity
        
        if best_match:
            return (best_match, best_score)
        
        return None
    
    def determine_match_status(
        self,
        document: Optional[ClassifiedDocument],
        similarity: float
    ) -> str:
        """
        Determine status of a match.
        
        Args:
            document: Matched document (if any)
            similarity: Match similarity score
            
        Returns:
            Status string ('ok', 'expired', 'missing', 'warning')
        """
        if not document:
            return 'missing'
        
        if document.is_expired:
            return 'expired'
        
        if document.days_until_expiration and document.days_until_expiration < 30:
            return 'warning'
        
        if similarity < 0.7:
            return 'warning'
        
        return 'ok'
    
    def compare(
        self,
        requirements: List[BidRequirement],
        documents: List[ClassifiedDocument]
    ) -> ComplianceReport:
        """
        Compare requirements against documents.
        
        Args:
            requirements: List of bid requirements
            documents: List of classified company documents
            
        Returns:
            ComplianceReport instance
        """
        logger.info(
            f"Comparing {len(requirements)} requirements against "
            f"{len(documents)} documents"
        )
        
        report = ComplianceReport()
        report.statistics['total_documents'] = len(documents)
        
        # Track matched documents
        matched_document_ids = set()
        
        # Match each requirement
        for requirement in requirements:
            match_result = self.find_best_match(requirement, documents)
            
            if match_result:
                matched_doc, similarity = match_result
                status = self.determine_match_status(matched_doc, similarity)
                
                match = RequirementMatch(
                    requirement=requirement,
                    matched_document=matched_doc,
                    match_confidence=similarity,
                    status=status
                )
                
                matched_document_ids.add(id(matched_doc))
            else:
                # No match found
                match = RequirementMatch(
                    requirement=requirement,
                    matched_document=None,
                    match_confidence=0.0,
                    status='missing'
                )
            
            report.add_match(match)
        
        # Identify unmatched documents
        unmatched = [
            doc for doc in documents
            if id(doc) not in matched_document_ids
        ]
        report.set_unmatched_documents(unmatched)
        
        logger.info(f"Comparison complete:\n{report.get_summary()}")
        
        return report
    
    def generate_checklist_text(self, report: ComplianceReport) -> str:
        """
        Generate human-readable checklist text.
        
        Args:
            report: Compliance report
            
        Returns:
            Formatted checklist text
        """
        lines = []
        lines.append("=" * 70)
        lines.append("CHECKLIST DE DOCUMENTOS PARA LICITAÇÃO")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Data de verificação: {date.today().isoformat()}")
        lines.append("")
        lines.append(report.get_summary())
        lines.append("")
        lines.append("=" * 70)
        lines.append("DOCUMENTOS EXIGIDOS")
        lines.append("=" * 70)
        lines.append("")
        
        # Group by category
        by_category: Dict[str, List[RequirementMatch]] = {}
        for match in report.matches:
            category = match.requirement.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(match)
        
        # Category names
        category_names = {
            'habilitacao_juridica': 'HABILITAÇÃO JURÍDICA',
            'regularidade_fiscal': 'REGULARIDADE FISCAL',
            'qualificacao_tecnica': 'QUALIFICAÇÃO TÉCNICA',
            'qualificacao_economica': 'QUALIFICAÇÃO ECONÔMICO-FINANCEIRA',
            'proposta_comercial': 'PROPOSTA COMERCIAL',
            'outros': 'OUTROS'
        }
        
        for category, matches in by_category.items():
            lines.append(f"\n{category_names.get(category, category.upper())}")
            lines.append("-" * 70)
            
            for match in matches:
                status_icon = {
                    'ok': '✅',
                    'expired': '❌',
                    'missing': '❓',
                    'warning': '⚠️'
                }.get(match.status, '?')
                
                lines.append(f"\n{status_icon} {match.requirement.name}")
                
                if match.matched_document:
                    lines.append(f"   Arquivo: {match.matched_document.file_name}")
                
                for obs in match.get_observations():
                    lines.append(f"   → {obs}")
        
        # Unmatched documents
        if report.unmatched_documents:
            lines.append("\n")
            lines.append("=" * 70)
            lines.append("DOCUMENTOS NÃO ASSOCIADOS")
            lines.append("=" * 70)
            lines.append("")
            
            for doc in report.unmatched_documents:
                lines.append(f"- {doc.file_name}")
                lines.append(f"  Tipo: {doc.document_type}")
                lines.append(f"  Categoria: {doc.category}")
                lines.append("")
        
        lines.append("=" * 70)
        lines.append("OBSERVAÇÕES IMPORTANTES")
        lines.append("=" * 70)
        lines.append("")
        lines.append("⚠️  Este checklist foi gerado automaticamente.")
        lines.append("⚠️  REVISE MANUALMENTE todos os documentos antes do envio.")
        lines.append("⚠️  A responsabilidade final pela conformidade é do usuário.")
        lines.append("")
        
        return "\n".join(lines)


# Convenience function
def compare_requirements(
    requirements: List[BidRequirement],
    documents: List[ClassifiedDocument]
) -> ComplianceReport:
    """
    Compare requirements and documents (convenience function).
    
    Args:
        requirements: Bid requirements
        documents: Classified documents
        
    Returns:
        ComplianceReport
    """
    comparator = RequirementComparator()
    return comparator.compare(requirements, documents)
