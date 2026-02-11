"""
Loader for training examples to improve extraction accuracy.

Allows loading manual extractions to enhance the AI agent's understanding
of document requirements.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class TrainingExample:
    """Represents a training example with manual extraction."""
    
    def __init__(
        self,
        edital_name: str,
        requirements: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize training example.
        
        Args:
            edital_name: Name of the edital
            requirements: List of requirement dictionaries
            metadata: Optional metadata about the example
        """
        self.edital_name = edital_name
        self.requirements = requirements
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'edital_name': self.edital_name,
            'requirements': self.requirements,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrainingExample':
        """Create from dictionary."""
        return cls(
            edital_name=data.get('edital_name', ''),
            requirements=data.get('requirements', []),
            metadata=data.get('metadata', {})
        )


class ExamplesLoader:
    """
    Loads and manages training examples.
    
    Helps improve extraction accuracy by providing reference examples.
    """
    
    def __init__(self, examples_dir: Optional[Path] = None):
        """
        Initialize examples loader.
        
        Args:
            examples_dir: Directory containing example files
        """
        if examples_dir is None:
            examples_dir = Path(__file__).parent / "examples"
        
        self.examples_dir = Path(examples_dir)
        self.examples_dir.mkdir(parents=True, exist_ok=True)
        
        self.examples: List[TrainingExample] = []
        self._load_examples()
    
    def _load_examples(self) -> None:
        """Load all examples from directory."""
        json_files = list(self.examples_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    example = TrainingExample.from_dict(data)
                    self.examples.append(example)
                    logger.info(f"Loaded example: {example.edital_name}")
            except Exception as e:
                logger.error(f"Failed to load example {json_file}: {e}")
        
        logger.info(f"Loaded {len(self.examples)} training examples")
    
    def add_example(
        self,
        edital_name: str,
        requirements: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        save: bool = True
    ) -> TrainingExample:
        """
        Add a new training example.
        
        Args:
            edital_name: Name of the edital
            requirements: List of requirements
            metadata: Optional metadata
            save: Whether to save to file
            
        Returns:
            Created TrainingExample
        """
        example = TrainingExample(edital_name, requirements, metadata)
        self.examples.append(example)
        
        if save:
            self.save_example(example)
        
        return example
    
    def save_example(self, example: TrainingExample) -> Path:
        """
        Save example to JSON file.
        
        Args:
            example: Training example to save
            
        Returns:
            Path to saved file
        """
        # Create safe filename
        safe_name = "".join(
            c if c.isalnum() or c in (' ', '_', '-') else '_'
            for c in example.edital_name
        ).strip()
        
        filename = f"{safe_name}.json"
        filepath = self.examples_dir / filename
        
        # Avoid overwriting - add number if exists
        counter = 1
        while filepath.exists():
            filename = f"{safe_name}_{counter}.json"
            filepath = self.examples_dir / filename
            counter += 1
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(example.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved example to: {filepath}")
        return filepath
    
    def get_similar_examples(
        self,
        edital_text: str,
        limit: int = 3
    ) -> List[TrainingExample]:
        """
        Get similar examples based on edital text.
        
        Args:
            edital_text: Edital text to compare
            limit: Maximum number of examples to return
            
        Returns:
            List of similar examples
        """
        if not self.examples:
            return []
        
        # Simple keyword-based similarity for now
        # Could be improved with embeddings/semantic search
        
        edital_keywords = set(edital_text.lower().split())
        
        scored_examples = []
        for example in self.examples:
            # Get keywords from requirements
            req_text = " ".join(
                req.get('name', '') + " " + req.get('description', '')
                for req in example.requirements
            ).lower()
            req_keywords = set(req_text.split())
            
            # Calculate Jaccard similarity
            intersection = len(edital_keywords & req_keywords)
            union = len(edital_keywords | req_keywords)
            similarity = intersection / union if union > 0 else 0
            
            scored_examples.append((similarity, example))
        
        # Sort by similarity and return top N
        scored_examples.sort(reverse=True, key=lambda x: x[0])
        return [ex for _, ex in scored_examples[:limit]]
    
    def get_all_requirements(self) -> List[Dict[str, Any]]:
        """
        Get all requirements from all examples.
        
        Returns:
            List of all requirements
        """
        all_requirements = []
        for example in self.examples:
            all_requirements.extend(example.requirements)
        return all_requirements
    
    def create_few_shot_prompt(
        self,
        edital_text: str,
        num_examples: int = 2
    ) -> str:
        """
        Create few-shot learning prompt with examples.
        
        Args:
            edital_text: Current edital text
            num_examples: Number of examples to include
            
        Returns:
            Formatted prompt with examples
        """
        similar_examples = self.get_similar_examples(edital_text, num_examples)
        
        if not similar_examples:
            return ""
        
        prompt_parts = [
            "Aqui estão exemplos de extrações corretas de outros editais:",
            ""
        ]
        
        for i, example in enumerate(similar_examples, 1):
            prompt_parts.append(f"### Exemplo {i}: {example.edital_name}")
            prompt_parts.append("Documentos extraídos:")
            prompt_parts.append(json.dumps(
                example.requirements[:5],  # First 5 to keep prompt manageable
                ensure_ascii=False,
                indent=2
            ))
            prompt_parts.append("")
        
        prompt_parts.append("Agora extraia os documentos do edital abaixo de forma similar:")
        prompt_parts.append("")
        
        return "\n".join(prompt_parts)


# Global instance
_examples_loader: Optional[ExamplesLoader] = None


def get_examples_loader() -> ExamplesLoader:
    """
    Get global examples loader instance.
    
    Returns:
        ExamplesLoader instance
    """
    global _examples_loader
    
    if _examples_loader is None:
        _examples_loader = ExamplesLoader()
    
    return _examples_loader


def load_manual_extraction(filepath: Path) -> TrainingExample:
    """
    Load a manual extraction from JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        TrainingExample instance
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return TrainingExample.from_dict(data)
