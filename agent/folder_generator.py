"""
Organized folder generator for bid submission.

Creates structured directories and copies documents according
to compliance report results.
"""

import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

from agent.comparator import ComplianceReport, RequirementComparator
from config import settings

logger = logging.getLogger(__name__)


class FolderGeneratorError(Exception):
    """Raised when folder generation fails."""
    pass


class FolderGenerator:
    """
    Generates organized folder structure for bid submission.
    
    Creates categorized directories, copies documents, and generates
    checklist and summary reports.
    """
    
    # Category folder names (Brazilian Portuguese)
    CATEGORY_FOLDERS = {
        'habilitacao_juridica': '01_Habilitacao_Juridica',
        'regularidade_fiscal': '02_Regularidade_Fiscal',
        'qualificacao_tecnica': '03_Qualificacao_Tecnica',
        'qualificacao_economica': '04_Qualificacao_Economica',
        'proposta_comercial': '05_Proposta_Comercial',
        'outros': '06_Outros',
    }
    
    def __init__(self, output_base_dir: Optional[Path] = None):
        """
        Initialize folder generator.
        
        Args:
            output_base_dir: Base directory for output (default: from settings)
        """
        self.output_base_dir = Path(output_base_dir or settings.output_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
    
    def create_output_directory(self, bid_name: Optional[str] = None) -> Path:
        """
        Create timestamped output directory.
        
        Args:
            bid_name: Optional bid name for directory
            
        Returns:
            Path to created directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if bid_name:
            # Sanitize bid name
            bid_name_clean = "".join(
                c if c.isalnum() or c in (' ', '_', '-') else '_'
                for c in bid_name
            )
            dir_name = f"licitacao_{bid_name_clean}_{timestamp}"
        else:
            dir_name = f"licitacao_{timestamp}"
        
        output_dir = self.output_base_dir / dir_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created output directory: {output_dir}")
        return output_dir
    
    def create_category_folders(self, output_dir: Path) -> Dict[str, Path]:
        """
        Create category subdirectories.
        
        Args:
            output_dir: Main output directory
            
        Returns:
            Dictionary mapping categories to folder paths
        """
        category_paths = {}
        
        for category, folder_name in self.CATEGORY_FOLDERS.items():
            folder_path = output_dir / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)
            category_paths[category] = folder_path
            logger.debug(f"Created category folder: {folder_name}")
        
        return category_paths
    
    def copy_document(
        self,
        source_path: Path,
        destination_folder: Path,
        new_name: Optional[str] = None
    ) -> Path:
        """
        Copy document to destination folder.
        
        Args:
            source_path: Source document path
            destination_folder: Destination folder
            new_name: Optional new filename
            
        Returns:
            Path to copied document
            
        Raises:
            FolderGeneratorError: If copy fails
        """
        try:
            if new_name:
                dest_path = destination_folder / new_name
            else:
                dest_path = destination_folder / source_path.name
            
            # Handle duplicate names
            if dest_path.exists():
                stem = dest_path.stem
                suffix = dest_path.suffix
                counter = 1
                while dest_path.exists():
                    dest_path = destination_folder / f"{stem}_{counter}{suffix}"
                    counter += 1
            
            shutil.copy2(source_path, dest_path)
            logger.debug(f"Copied: {source_path.name} -> {dest_path.name}")
            
            return dest_path
            
        except Exception as e:
            raise FolderGeneratorError(f"Failed to copy document: {e}")
    
    def generate_checklist_file(
        self,
        output_dir: Path,
        report: ComplianceReport,
        comparator: RequirementComparator
    ) -> Path:
        """
        Generate checklist text file.
        
        Args:
            output_dir: Output directory
            report: Compliance report
            comparator: Comparator instance for text generation
            
        Returns:
            Path to checklist file
        """
        checklist_path = output_dir / "CHECKLIST.txt"
        
        try:
            checklist_text = comparator.generate_checklist_text(report)
            
            with open(checklist_path, 'w', encoding='utf-8') as f:
                f.write(checklist_text)
            
            logger.info(f"Generated checklist: {checklist_path}")
            return checklist_path
            
        except Exception as e:
            raise FolderGeneratorError(f"Failed to generate checklist: {e}")
    
    def generate_json_report(
        self,
        output_dir: Path,
        report: ComplianceReport,
        edital_info: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate JSON report with full details.
        
        Args:
            output_dir: Output directory
            report: Compliance report
            edital_info: Optional edital information
            
        Returns:
            Path to JSON report file
        """
        report_path = output_dir / "relatorio.json"
        
        try:
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'edital_info': edital_info or {},
                'compliance_report': report.to_dict()
            }
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Generated JSON report: {report_path}")
            return report_path
            
        except Exception as e:
            raise FolderGeneratorError(f"Failed to generate JSON report: {e}")
    
    def generate_summary_file(
        self,
        output_dir: Path,
        report: ComplianceReport
    ) -> Path:
        """
        Generate summary text file.
        
        Args:
            output_dir: Output directory
            report: Compliance report
            
        Returns:
            Path to summary file
        """
        summary_path = output_dir / "RESUMO.txt"
        
        try:
            lines = []
            lines.append("=" * 70)
            lines.append("RESUMO DA ANÁLISE DE LICITAÇÃO")
            lines.append("=" * 70)
            lines.append("")
            lines.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            lines.append("")
            lines.append(report.get_summary())
            lines.append("")
            lines.append("=" * 70)
            lines.append("AÇÕES NECESSÁRIAS")
            lines.append("=" * 70)
            lines.append("")
            
            if report.statistics['requirements_missing'] > 0:
                lines.append("❌ DOCUMENTOS FALTANTES:")
                for match in report.matches:
                    if match.status == 'missing':
                        lines.append(f"   - {match.requirement.name}")
                lines.append("")
            
            if report.statistics['requirements_expired'] > 0:
                lines.append("⏰ DOCUMENTOS VENCIDOS:")
                for match in report.matches:
                    if match.status == 'expired' and match.matched_document:
                        lines.append(f"   - {match.matched_document.file_name}")
                        if match.matched_document.expiration_date:
                            lines.append(
                                f"     Vencido em: {match.matched_document.expiration_date.isoformat()}"
                            )
                lines.append("")
            
            if report.statistics['requirements_warning'] > 0:
                lines.append("⚠️  DOCUMENTOS COM AVISO:")
                for match in report.matches:
                    if match.status == 'warning' and match.matched_document:
                        lines.append(f"   - {match.matched_document.file_name}")
                        for obs in match.get_observations():
                            lines.append(f"     {obs}")
                lines.append("")
            
            if report.is_compliant():
                lines.append("✅ SITUAÇÃO: DOCUMENTAÇÃO COMPLETA E VÁLIDA")
            else:
                lines.append("❌ SITUAÇÃO: DOCUMENTAÇÃO INCOMPLETA OU COM PENDÊNCIAS")
            
            lines.append("")
            lines.append("=" * 70)
            lines.append("IMPORTANTE")
            lines.append("=" * 70)
            lines.append("")
            lines.append("⚠️  Revise manualmente todos os documentos antes do envio.")
            lines.append("⚠️  Verifique o edital para requisitos específicos não detectados.")
            lines.append("⚠️  Este relatório é apenas uma ferramenta de apoio.")
            lines.append("")
            
            summary_text = "\n".join(lines)
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary_text)
            
            logger.info(f"Generated summary: {summary_path}")
            return summary_path
            
        except Exception as e:
            raise FolderGeneratorError(f"Failed to generate summary: {e}")
    
    def generate_organized_folder(
        self,
        report: ComplianceReport,
        bid_name: Optional[str] = None,
        include_expired: bool = False,
        edital_info: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate complete organized folder structure.
        
        Args:
            report: Compliance report with matches
            bid_name: Optional bid name
            include_expired: Whether to include expired documents
            edital_info: Optional edital information
            
        Returns:
            Path to generated folder
        """
        logger.info("Generating organized folder structure...")
        
        try:
            # Create main output directory
            output_dir = self.create_output_directory(bid_name)
            
            # Create category folders
            category_paths = self.create_category_folders(output_dir)
            
            # Copy matched documents
            copied_count = 0
            skipped_count = 0
            
            for match in report.matches:
                if match.matched_document:
                    doc = match.matched_document
                    
                    # Skip expired unless explicitly included
                    if doc.is_expired and not include_expired:
                        logger.warning(f"Skipping expired document: {doc.file_name}")
                        skipped_count += 1
                        continue
                    
                    # Get destination folder
                    dest_folder = category_paths.get(doc.category)
                    if not dest_folder:
                        logger.warning(f"Unknown category '{doc.category}', using 'outros'")
                        dest_folder = category_paths['outros']
                    
                    # Copy document
                    self.copy_document(doc.file_path, dest_folder)
                    copied_count += 1
            
            logger.info(f"Copied {copied_count} documents, skipped {skipped_count}")
            
            # Generate reports
            comparator = RequirementComparator()
            self.generate_checklist_file(output_dir, report, comparator)
            self.generate_summary_file(output_dir, report)
            self.generate_json_report(output_dir, report, edital_info)
            
            # Create README
            self._create_readme(output_dir, report)
            
            logger.info(f"Folder generation complete: {output_dir}")
            return output_dir
            
        except Exception as e:
            raise FolderGeneratorError(f"Failed to generate folder: {e}")
    
    def _create_readme(self, output_dir: Path, report: ComplianceReport) -> None:
        """Create README file with instructions."""
        readme_path = output_dir / "LEIA-ME.txt"
        
        content = f"""
╔══════════════════════════════════════════════════════════════════╗
║          PASTA ORGANIZADA PARA LICITAÇÃO                         ║
║              Gerada automaticamente                               ║
╚══════════════════════════════════════════════════════════════════╝

Data de geração: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}

═══════════════════════════════════════════════════════════════════

ESTRUTURA DA PASTA:

📁 Esta pasta contém seus documentos organizados por categoria:

  01_Habilitacao_Juridica/     - Documentos de habilitação jurídica
  02_Regularidade_Fiscal/       - Certidões e regularidades fiscais
  03_Qualificacao_Tecnica/      - Atestados e qualificações técnicas
  04_Qualificacao_Economica/    - Balanços e qualificações econômicas
  05_Proposta_Comercial/        - Proposta comercial (se aplicável)
  06_Outros/                    - Outros documentos

═══════════════════════════════════════════════════════════════════

ARQUIVOS DE CONTROLE:

📄 CHECKLIST.txt      - Lista completa de documentos exigidos
📄 RESUMO.txt         - Resumo executivo da análise
📄 relatorio.json     - Relatório técnico completo (JSON)
📄 LEIA-ME.txt        - Este arquivo

═══════════════════════════════════════════════════════════════════

STATUS DA DOCUMENTAÇÃO:

{report.get_summary()}

═══════════════════════════════════════════════════════════════════

⚠️  IMPORTANTE - LEIA COM ATENÇÃO:

1. Esta organização foi gerada automaticamente por IA
2. REVISE MANUALMENTE todos os documentos antes do envio
3. Verifique se os documentos correspondem às exigências do edital
4. Confira datas de validade e informações nos documentos
5. Consulte o arquivo CHECKLIST.txt para detalhes
6. A responsabilidade final pela conformidade é sua

═══════════════════════════════════════════════════════════════════

PRÓXIMOS PASSOS:

1. □ Revisar arquivo CHECKLIST.txt
2. □ Verificar RESUMO.txt para pendências
3. □ Conferir cada documento nas respectivas pastas
4. □ Providenciar documentos faltantes (se houver)
5. □ Renovar documentos vencidos (se houver)
6. □ Revisar proposta comercial
7. □ Preparar documentos para envio/upload

═══════════════════════════════════════════════════════════════════

Boa sorte com sua licitação! 🍀

═══════════════════════════════════════════════════════════════════
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Created README: {readme_path}")


# Convenience function
def generate_bid_folder(
    report: ComplianceReport,
    bid_name: Optional[str] = None,
    include_expired: bool = False,
    edital_info: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Generate organized bid folder (convenience function).
    
    Args:
        report: Compliance report
        bid_name: Optional bid name
        include_expired: Include expired documents
        edital_info: Edital information
        
    Returns:
        Path to generated folder
    """
    generator = FolderGenerator()
    return generator.generate_organized_folder(
        report,
        bid_name=bid_name,
        include_expired=include_expired,
        edital_info=edital_info
    )
