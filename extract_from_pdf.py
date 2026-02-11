#!/usr/bin/env python3
"""
Extract training examples from edital PDF files.

This script helps create training examples by:
1. Extracting text from edital PDFs
2. Using the existing extraction logic to identify requirements
3. Generating a JSON file with the extraction
4. Allowing manual review and editing

Usage:
    python extract_from_pdf.py path/to/edital.pdf
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.pdf_extractor import extract_pdf_text
from agent.edital_reader import EditalReader, BidRequirement
from config.settings import settings


def extract_requirements_from_pdf(pdf_path: Path) -> Dict[str, Any]:
    """
    Extract requirements from PDF using the edital reader.
    
    Args:
        pdf_path: Path to the edital PDF
        
    Returns:
        Dictionary with extraction results
    """
    print(f"\n📄 Processing: {pdf_path.name}")
    print("-" * 60)
    
    # Initialize reader (will use rules if LLM not available)
    reader = EditalReader(use_llm=settings.llm_enabled)
    
    # Analyze edital
    result = reader.analyze_edital(pdf_path)
    
    print(f"\n✅ Extraction complete!")
    print(f"   Method: {result['extraction_method']}")
    print(f"   Requirements found: {result['total_requirements']}")
    print(f"   Categories: {len(result['requirements_by_category'])}")
    
    return result


def convert_to_training_format(
    result: Dict[str, Any],
    pdf_path: Path,
    extracted_by: str = "Automated"
) -> Dict[str, Any]:
    """
    Convert extraction result to training example format.
    
    Args:
        result: Extraction result from EditalReader
        pdf_path: Path to the PDF file
        extracted_by: Name of person reviewing
        
    Returns:
        Training example dictionary
    """
    # Convert BidRequirement objects to dictionaries
    requirements = []
    for req in result['requirements']:
        requirements.append({
            'name': req.name,
            'category': req.category,
            'description': req.description,
            'requirements': req.requirements,
            'is_mandatory': req.is_mandatory
        })
    
    # Create training example
    training_example = {
        'edital_name': pdf_path.stem,  # Use filename without extension
        'requirements': requirements,
        'metadata': {
            'extraction_date': datetime.now().strftime('%Y-%m-%d'),
            'extracted_by': extracted_by,
            'extraction_method': result['extraction_method'],
            'source_file': pdf_path.name,
            'notes': 'Automatically extracted. Review and edit as needed.'
        }
    }
    
    return training_example


def save_training_example(example: Dict[str, Any], output_path: Path = None) -> Path:
    """
    Save training example to JSON file.
    
    Args:
        example: Training example dictionary
        output_path: Optional specific output path
        
    Returns:
        Path to saved file
    """
    if output_path is None:
        # Generate filename
        examples_dir = Path(__file__).parent / "training" / "examples"
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        safe_name = "".join(
            c if c.isalnum() or c in (' ', '_', '-') else '_'
            for c in example['edital_name']
        ).strip().replace(' ', '_').lower()
        
        # Find available filename
        counter = 1
        filename = f"{safe_name}.json"
        output_path = examples_dir / filename
        
        while output_path.exists():
            filename = f"{safe_name}_{counter}.json"
            output_path = examples_dir / filename
            counter += 1
    
    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(example, f, ensure_ascii=False, indent=2)
    
    return output_path


def print_summary(example: Dict[str, Any]):
    """Print summary of extracted requirements."""
    print("\n" + "="*60)
    print("📊 EXTRACTION SUMMARY")
    print("="*60)
    
    print(f"\n📋 Edital: {example['edital_name']}")
    print(f"📅 Date: {example['metadata']['extraction_date']}")
    print(f"🔧 Method: {example['metadata']['extraction_method']}")
    print(f"📄 Requirements: {len(example['requirements'])}")
    
    # Group by category
    by_category = {}
    for req in example['requirements']:
        cat = req['category']
        by_category[cat] = by_category.get(cat, 0) + 1
    
    print(f"\n📂 By Category:")
    for cat, count in sorted(by_category.items()):
        print(f"   • {cat}: {count}")
    
    print(f"\n📝 Sample Requirements:")
    for i, req in enumerate(example['requirements'][:5], 1):
        mandatory = "✓" if req['is_mandatory'] else "○"
        print(f"   {i}. [{mandatory}] {req['name']}")
        print(f"      Category: {req['category']}")
        if i < 5 and i < len(example['requirements']):
            print()


def review_and_edit(example: Dict[str, Any]) -> Dict[str, Any]:
    """
    Allow user to review and edit the extraction.
    
    Args:
        example: Training example to review
        
    Returns:
        Updated example
    """
    print("\n" + "="*60)
    print("✏️  REVIEW AND EDIT")
    print("="*60)
    print("\nYou can now:")
    print("  1. Accept as-is")
    print("  2. Edit the edital name")
    print("  3. Add notes")
    print("  4. Skip saving")
    
    choice = input("\nWhat would you like to do? (1-4) [1]: ").strip() or "1"
    
    if choice == "1":
        return example
    
    elif choice == "2":
        new_name = input(f"\nCurrent name: {example['edital_name']}\nNew name: ").strip()
        if new_name:
            example['edital_name'] = new_name
    
    elif choice == "3":
        notes = input("\nAdd notes: ").strip()
        if notes:
            example['metadata']['notes'] = notes
    
    elif choice == "4":
        return None
    
    return example


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python extract_from_pdf.py <path_to_edital.pdf>")
        print("\nExample:")
        print("  python extract_from_pdf.py input/edital_001_2026.pdf")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    
    if not pdf_path.exists():
        print(f"❌ Error: File not found: {pdf_path}")
        sys.exit(1)
    
    if pdf_path.suffix.lower() != '.pdf':
        print(f"❌ Error: Not a PDF file: {pdf_path}")
        sys.exit(1)
    
    try:
        print("\n" + "="*60)
        print("🎓 TRAINING EXAMPLE EXTRACTOR")
        print("="*60)
        
        # Extract requirements
        result = extract_requirements_from_pdf(pdf_path)
        
        # Convert to training format
        extracted_by = input("\nYour name (for metadata) [Automated]: ").strip() or "Automated"
        training_example = convert_to_training_format(result, pdf_path, extracted_by)
        
        # Show summary
        print_summary(training_example)
        
        # Review and edit
        training_example = review_and_edit(training_example)
        
        if training_example is None:
            print("\n❌ Cancelled. Not saving.")
            return
        
        # Save
        output_path = save_training_example(training_example)
        
        print(f"\n✅ Training example saved!")
        print(f"   File: {output_path}")
        print(f"   Requirements: {len(training_example['requirements'])}")
        
        print(f"\n💡 Next steps:")
        print(f"   1. Review the JSON file: {output_path}")
        print(f"   2. Edit if needed (fix categories, descriptions, etc.)")
        print(f"   3. Run the app: streamlit run ui/app.py")
        print(f"   4. Test with the same edital to see improvement")
        
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
