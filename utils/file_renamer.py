"""
Intelligent file renamer for better document identification.

Renames files to standardized names that help the AI model
identify document types more accurately.
"""

import logging
import re
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class FileRenamer:
    """
    Renames files to standardized, AI-friendly names.
    """
    
    # Mapping of patterns to standard names
    RENAME_PATTERNS = {
        # Federal
        r'cnd.*federal|certid[aã]o.*federal|receita.*federal': 'CND_Federal',
        r'tributos.*federais': 'CND_Federal',
        
        # Estadual
        r'cnd.*estadual|certid[aã]o.*estadual|fazenda.*estadual': 'CND_Estadual',
        
        # Municipal
        r'cnd.*municipal|certid[aã]o.*municipal|prefeitura': 'CND_Municipal',
        
        # Cível
        r'cnd.*civel|cnd.*c[íi]vel|certid[aã]o.*civel': 'CND_Civel',
        
        # FGTS
        r'fgts|crf|regularidade.*fgts': 'CRF_FGTS',
        
        # Trabalhista
        r'cndt|trabalhista|d[ée]bitos.*trabalhistas|cnd.*trab': 'CNDT_Trabalhista',
        
        # CNPJ
        r'cnpj|cadastro.*nacional': 'Comprovante_CNPJ',
        
        # Contrato Social
        r'contrato.*social|estatuto': 'Contrato_Social',
        
        # Balanço
        r'balan[cç]o|demonstra[cç][aã]o.*cont[aá]bil': 'Balanco_Patrimonial',
        
        # Falência/Concordata
        r'fal[êe]ncia|concordata|recupera[cç][aã]o.*judicial': 'Certidao_Falencia_Concordata',
        
        # Atestado
        r'atestado.*capacidade|atestado.*t[ée]cnica': 'Atestado_Capacidade_Tecnica',
        
        # CAT
        r'cat|acervo.*t[ée]cnico': 'CAT_Acervo_Tecnico',
        
        # Alvará
        r'alvar[aá]|licen[cç]a.*funcionamento|provis[óo]rio': 'Alvara_Funcionamento',
        
        # Dispensa Sanitária
        r'dispensa.*sanit[aá]ria|vigilancia.*sanit[aá]ria': 'Dispensa_Sanitaria',
    }
    
    @staticmethod
    def suggest_name(filename: str) -> Optional[str]:
        """
        Suggest a standardized name for a file.
        
        Args:
            filename: Original filename
            
        Returns:
            Suggested name or None if no match
        """
        filename_lower = filename.lower()
        filename_clean = filename_lower.replace('_', ' ').replace('-', ' ')
        
        for pattern, standard_name in FileRenamer.RENAME_PATTERNS.items():
            if re.search(pattern, filename_clean):
                return standard_name
        
        return None
    
    @staticmethod
    def rename_file(
        file_path: Path,
        new_name: Optional[str] = None,
        dry_run: bool = False
    ) -> Optional[Path]:
        """
        Rename file to standardized name.
        
        Args:
            file_path: Path to file
            new_name: New name (without extension), or None to auto-detect
            dry_run: If True, only suggest name without renaming
            
        Returns:
            New path if renamed, or None if no rename needed
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        # Auto-detect name if not provided
        if new_name is None:
            new_name = FileRenamer.suggest_name(file_path.stem)
        
        if new_name is None:
            logger.info(f"No standard name found for: {file_path.name}")
            return None
        
        # Keep original extension
        new_filename = f"{new_name}{file_path.suffix}"
        new_path = file_path.parent / new_filename
        
        # Check if already correctly named
        if file_path.name == new_filename:
            logger.info(f"File already correctly named: {file_path.name}")
            return file_path
        
        # Check if target exists
        if new_path.exists() and new_path != file_path:
            logger.warning(f"Target already exists: {new_path}")
            # Add number suffix
            counter = 1
            while new_path.exists():
                new_filename = f"{new_name}_{counter}{file_path.suffix}"
                new_path = file_path.parent / new_filename
                counter += 1
        
        if dry_run:
            logger.info(f"Would rename: {file_path.name} -> {new_path.name}")
            return new_path
        
        try:
            file_path.rename(new_path)
            logger.info(f"Renamed: {file_path.name} -> {new_path.name}")
            return new_path
        except Exception as e:
            logger.error(f"Failed to rename {file_path}: {e}")
            return None
    
    @staticmethod
    def batch_rename(
        directory: Path,
        dry_run: bool = False
    ) -> Dict[str, str]:
        """
        Rename all files in directory.
        
        Args:
            directory: Directory containing files
            dry_run: If True, only show what would be renamed
            
        Returns:
            Dictionary of old_name -> new_name
        """
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return {}
        
        renames = {}
        pdf_files = list(directory.glob("*.pdf"))
        
        logger.info(f"Processing {len(pdf_files)} files in {directory}")
        
        for pdf_file in pdf_files:
            new_path = FileRenamer.rename_file(pdf_file, dry_run=dry_run)
            if new_path and new_path != pdf_file:
                renames[pdf_file.name] = new_path.name
        
        if renames:
            logger.info(f"Renamed {len(renames)} files")
        else:
            logger.info("No files needed renaming")
        
        return renames


# Convenience function
def rename_document(file_path: Path, dry_run: bool = False) -> Optional[Path]:
    """
    Rename document to standard name (convenience function).
    
    Args:
        file_path: Path to file
        dry_run: Only suggest, don't rename
        
    Returns:
        New path or None
    """
    return FileRenamer.rename_file(file_path, dry_run=dry_run)
