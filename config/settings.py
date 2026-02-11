"""
Configuration settings for Bid AI Agent.
Loads settings from environment variables with secure defaults.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    app_name: str = "Bid AI Agent"
    app_version: str = "1.0.0"
    debug_mode: bool = False
    log_level: str = "INFO"

    # Local LLM settings
    llm_model_path: str = str(PROJECT_ROOT / "models" / "llama-3-8b.gguf")
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    llm_context_size: int = 8192
    llm_enabled: bool = True  # Set to False in cloud deployment if model not available

    # Document processing
    max_file_size_mb: int = 50
    ocr_enabled: bool = True
    ocr_language: str = "por"

    # Output settings
    output_dir: str = str(PROJECT_ROOT / "output")
    create_zip_export: bool = True

    # Security settings
    file_validation_enabled: bool = True
    max_documents_per_batch: int = 50

    # Logging
    log_file_path: str = str(PROJECT_ROOT / "logs" / "app.log")
    log_rotation_max_size_mb: int = 10

    # Paths
    input_dir: str = str(PROJECT_ROOT / "input")
    company_docs_dir: str = str(PROJECT_ROOT / "input" / "documentos_empresa")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings: Application configuration
    """
    return settings


def ensure_directories() -> None:
    """
    Ensure all required directories exist.
    Creates directories if they don't exist.
    """
    directories = [
        settings.input_dir,
        settings.company_docs_dir,
        settings.output_dir,
        Path(settings.log_file_path).parent,
        PROJECT_ROOT / "models",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


# Ensure directories exist on import
ensure_directories()
