"""
Local LLM handler for secure, privacy-focused AI processing.

Manages local language model inference without external API calls.
All processing happens on-device to maintain document confidentiality.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import json

from langchain.llms.base import LLM
from langchain_community.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManagerForLLMRun
from pydantic import Field

from config import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when LLM operations fail."""
    pass


class LocalLLM:
    """
    Handler for local LLM inference.
    
    Provides a secure interface to local language models without
    external API calls, ensuring document privacy and data security.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        context_size: int = 8192,
        n_gpu_layers: int = 0,  # 0 = CPU only, increase for GPU
        verbose: bool = False
    ):
        """
        Initialize local LLM handler.
        
        Args:
            model_path: Path to .gguf model file
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens to generate
            context_size: Context window size
            n_gpu_layers: Number of layers to offload to GPU (0 = CPU only)
            verbose: Enable verbose logging
        """
        self.model_path = Path(model_path or settings.llm_model_path)
        self.temperature = temperature or settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self.context_size = context_size or settings.llm_context_size
        self.n_gpu_layers = n_gpu_layers
        self.verbose = verbose
        
        self.llm: Optional[LlamaCpp] = None
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """
        Initialize the LLM model.
        
        Raises:
            LLMError: If model initialization fails
        """
        if not self.model_path.exists():
            raise LLMError(
                f"Model file not found: {self.model_path}\n"
                f"Please download a .gguf model file and place it in the models/ directory.\n"
                f"Recommended models:\n"
                f"  - Llama 3 8B: https://huggingface.co/models?search=llama-3-8b-gguf\n"
                f"  - Mistral 7B: https://huggingface.co/models?search=mistral-7b-gguf"
            )
        
        try:
            logger.info(f"Loading LLM model from: {self.model_path}")
            
            self.llm = LlamaCpp(
                model_path=str(self.model_path),
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                n_ctx=self.context_size,
                n_gpu_layers=self.n_gpu_layers,
                verbose=self.verbose,
                # Security: disable external requests
                use_mlock=True,  # Lock model in RAM
                n_batch=512,  # Batch size for prompt processing
                f16_kv=True,  # Use half-precision for key/value cache
            )
            
            logger.info("LLM model loaded successfully")
            
        except Exception as e:
            raise LLMError(f"Failed to initialize LLM model: {e}")
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """
        Generate text from prompt using local LLM.
        
        Args:
            prompt: Input prompt
            max_tokens: Override default max tokens
            temperature: Override default temperature
            stop_sequences: List of sequences to stop generation
            
        Returns:
            Generated text
            
        Raises:
            LLMError: If generation fails
        """
        if not self.llm:
            raise LLMError("LLM model not initialized")
        
        if not prompt:
            raise LLMError("Prompt cannot be empty")
        
        # Validate prompt length
        if len(prompt) > self.context_size * 4:  # Rough token estimate
            logger.warning(f"Prompt is very long ({len(prompt)} chars), may be truncated")
        
        try:
            logger.debug(f"Generating response for prompt ({len(prompt)} chars)")
            
            # Override parameters if provided
            kwargs = {}
            if max_tokens:
                kwargs['max_tokens'] = max_tokens
            if temperature is not None:
                kwargs['temperature'] = temperature
            if stop_sequences:
                kwargs['stop'] = stop_sequences
            
            # Generate response
            response = self.llm(prompt, **kwargs)
            
            logger.debug(f"Generated response ({len(response)} chars)")
            return response.strip()
            
        except Exception as e:
            raise LLMError(f"Text generation failed: {e}")
    
    def generate_json(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON response from prompt.
        
        Args:
            prompt: Input prompt (should request JSON output)
            max_tokens: Override default max tokens
            temperature: Override default temperature
            
        Returns:
            Parsed JSON response as dictionary
            
        Raises:
            LLMError: If generation or parsing fails
        """
        # Add JSON formatting instruction
        json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON. Do not include any explanation or markdown formatting."
        
        response = self.generate(
            json_prompt,
            max_tokens=max_tokens,
            temperature=temperature or 0.1,  # Lower temp for structured output
            stop_sequences=None
        )
        
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            # Parse JSON
            parsed = json.loads(response.strip())
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response}")
            raise LLMError(f"Failed to parse JSON response: {e}")
    
    def analyze_document(
        self,
        document_text: str,
        analysis_type: str,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Analyze document text using LLM.
        
        Args:
            document_text: Text content of document
            analysis_type: Type of analysis to perform
            max_tokens: Override default max tokens
            
        Returns:
            Analysis result
        """
        prompt = f"""Analyze the following document for {analysis_type}.

Document:
{document_text}

Analysis:"""
        
        return self.generate(prompt, max_tokens=max_tokens)
    
    def extract_structured_data(
        self,
        text: str,
        fields: List[str],
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Extract structured data from text.
        
        Args:
            text: Text to extract data from
            fields: List of fields to extract
            context: Additional context for extraction
            
        Returns:
            Dictionary with extracted fields
        """
        fields_str = ", ".join(fields)
        
        prompt = f"""Extract the following information from the text: {fields_str}

{context}

Text:
{text}

Provide the extracted information in JSON format with keys: {fields_str}"""
        
        return self.generate_json(prompt)
    
    def is_model_loaded(self) -> bool:
        """
        Check if model is loaded and ready.
        
        Returns:
            True if model is loaded, False otherwise
        """
        return self.llm is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about loaded model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_path': str(self.model_path),
            'model_exists': self.model_path.exists(),
            'model_name': self.model_path.name if self.model_path.exists() else None,
            'model_size_mb': self.model_path.stat().st_size / (1024 * 1024) 
                            if self.model_path.exists() else None,
            'is_loaded': self.is_model_loaded(),
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'context_size': self.context_size,
        }


class PromptTemplates:
    """
    Collection of prompt templates for document analysis.
    
    Provides pre-configured prompts for common bid document tasks.
    """
    
    @staticmethod
    def extract_bid_requirements(edital_text: str) -> str:
        """
        Create prompt to extract requirements from bid notice.
        
        Args:
            edital_text: Bid notice text
            
        Returns:
            Formatted prompt
        """
        return f"""You are a legal document analyst specialized in Brazilian public procurement (licitações).

Analyze the following bid notice (edital) and extract ALL required documents.

For each document, identify:
1. Document name
2. Category (one of: habilitacao_juridica, regularidade_fiscal, qualificacao_tecnica, qualificacao_economica)
3. Brief description
4. Any specific requirements or conditions

Bid Notice:
{edital_text}

Respond ONLY with valid JSON in this exact format:
{{
  "documents": [
    {{
      "name": "Document name",
      "category": "category_name",
      "description": "Brief description",
      "requirements": "Any specific requirements"
    }}
  ]
}}"""
    
    @staticmethod
    def classify_document(document_text: str, filename: str) -> str:
        """
        Create prompt to classify a document.
        
        Args:
            document_text: Document text content
            filename: Original filename
            
        Returns:
            Formatted prompt
        """
        return f"""Classify the following Brazilian business/legal document.

Filename: {filename}

Document content:
{document_text[:2000]}...

Determine:
1. document_type: What type of document is this? (e.g., "Certidão de Regularidade Fiscal", "Contrato Social", "CNPJ", etc.)
2. category: Which category? (habilitacao_juridica, regularidade_fiscal, qualificacao_tecnica, qualificacao_economica, or "unknown")
3. confidence: Your confidence in this classification (0.0 to 1.0)

Respond ONLY with valid JSON:
{{
  "document_type": "type",
  "category": "category",
  "confidence": 0.0
}}"""
    
    @staticmethod
    def extract_validity_date(document_text: str) -> str:
        """
        Create prompt to extract validity/expiration date.
        
        Args:
            document_text: Document text content
            
        Returns:
            Formatted prompt
        """
        return f"""Extract the validity or expiration date from this Brazilian document.

Document:
{document_text}

Look for phrases like: "validade", "vencimento", "válido até", "vigência", etc.

Respond ONLY with valid JSON:
{{
  "has_date": true/false,
  "date": "YYYY-MM-DD" or null,
  "context": "the text surrounding the date"
}}"""


# Global LLM instance (lazy loaded)
_global_llm: Optional[LocalLLM] = None


def get_llm() -> LocalLLM:
    """
    Get global LLM instance (singleton pattern).
    
    Returns:
        Initialized LocalLLM instance
    """
    global _global_llm
    
    if _global_llm is None:
        _global_llm = LocalLLM()
    
    return _global_llm


def reset_llm() -> None:
    """Reset global LLM instance."""
    global _global_llm
    _global_llm = None
