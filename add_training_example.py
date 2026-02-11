#!/usr/bin/env python3
"""
Interactive script to add training examples from manual extractions.

Usage:
    python add_training_example.py
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


# Valid categories
CATEGORIES = {
    '1': ('habilitacao_juridica', 'Legal qualification documents'),
    '2': ('regularidade_fiscal', 'Tax compliance documents'),
    '3': ('qualificacao_tecnica', 'Technical qualification'),
    '4': ('qualificacao_economica', 'Economic-financial qualification'),
    '5': ('proposta_comercial', 'Commercial proposal'),
    '6': ('outros', 'Other documents')
}


def print_header():
    """Print welcome header."""
    print("\n" + "="*60)
    print("🎓 TRAINING EXAMPLE CREATOR")
    print("="*60)
    print("\nAdd manual extraction examples to improve the AI agent.\n")


def get_input(prompt: str, default: str = "") -> str:
    """Get user input with optional default."""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def get_yes_no(prompt: str, default: bool = True) -> bool:
    """Get yes/no input."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    
    if not response:
        return default
    return response in ('y', 'yes', 's', 'sim')


def select_category() -> str:
    """Let user select a category."""
    print("\n📂 Select document category:")
    for key, (code, description) in CATEGORIES.items():
        print(f"  {key}. {description}")
    
    while True:
        choice = input("\nCategory (1-6): ").strip()
        if choice in CATEGORIES:
            return CATEGORIES[choice][0]
        print("❌ Invalid choice. Try again.")


def add_requirement() -> Dict[str, Any]:
    """Add a single requirement interactively."""
    print("\n" + "-"*60)
    print("📄 NEW REQUIREMENT")
    print("-"*60)
    
    name = get_input("Document name (e.g., 'Certidão Negativa de Débitos Federais')")
    category = select_category()
    
    print("\n💬 Description (press Enter twice when done):")
    description_lines = []
    while True:
        line = input()
        if not line and description_lines:
            break
        if line:
            description_lines.append(line)
    description = " ".join(description_lines)
    
    print("\n📋 Specific requirements (press Enter twice when done):")
    requirements_lines = []
    while True:
        line = input()
        if not line and requirements_lines:
            break
        if line:
            requirements_lines.append(line)
    requirements = " ".join(requirements_lines)
    
    is_mandatory = get_yes_no("\nIs this document mandatory?", default=True)
    
    return {
        "name": name,
        "category": category,
        "description": description,
        "requirements": requirements,
        "is_mandatory": is_mandatory
    }


def create_training_example():
    """Create a complete training example."""
    print_header()
    
    # Get edital info
    edital_name = get_input("📋 Edital name (e.g., 'Pregão 001/2026 - Ovos de Páscoa')")
    
    # Add requirements
    requirements = []
    while True:
        req = add_requirement()
        requirements.append(req)
        
        print(f"\n✅ Requirement added: {req['name']}")
        print(f"   Total: {len(requirements)} requirement(s)")
        
        if not get_yes_no("\nAdd another requirement?", default=True):
            break
    
    # Metadata
    print("\n" + "-"*60)
    print("📝 METADATA")
    print("-"*60)
    
    extracted_by = get_input("Your name", default="Manual")
    notes = get_input("Additional notes (optional)", default="")
    
    # Build example
    example = {
        "edital_name": edital_name,
        "requirements": requirements,
        "metadata": {
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "extracted_by": extracted_by,
            "notes": notes
        }
    }
    
    # Preview
    print("\n" + "="*60)
    print("📄 PREVIEW")
    print("="*60)
    print(json.dumps(example, ensure_ascii=False, indent=2))
    
    # Save
    if get_yes_no("\n💾 Save this example?", default=True):
        save_example(example, edital_name)
    else:
        print("\n❌ Example discarded.")


def save_example(example: Dict[str, Any], edital_name: str):
    """Save example to JSON file."""
    # Create safe filename
    safe_name = "".join(
        c if c.isalnum() or c in (' ', '_', '-') else '_'
        for c in edital_name
    ).strip().replace(' ', '_').lower()
    
    examples_dir = Path(__file__).parent / "training" / "examples"
    examples_dir.mkdir(parents=True, exist_ok=True)
    
    # Find available filename
    counter = 1
    filename = f"{safe_name}.json"
    filepath = examples_dir / filename
    
    while filepath.exists():
        filename = f"{safe_name}_{counter}.json"
        filepath = examples_dir / filename
        counter += 1
    
    # Save
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(example, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Example saved: {filepath}")
    print(f"\n🎉 Training example created successfully!")
    print(f"   File: {filepath.name}")
    print(f"   Requirements: {len(example['requirements'])}")


def main():
    """Main function."""
    try:
        create_training_example()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")


if __name__ == "__main__":
    main()
