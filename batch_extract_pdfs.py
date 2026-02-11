#!/usr/bin/env python3
"""
Batch process multiple edital PDFs to create training examples.

Usage:
    python batch_extract_pdfs.py <directory_with_pdfs>
    python batch_extract_pdfs.py file1.pdf file2.pdf file3.pdf
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from extract_from_pdf import (
    extract_requirements_from_pdf,
    convert_to_training_format,
    save_training_example,
    print_summary
)


def process_directory(directory: Path, extracted_by: str = "Batch") -> list:
    """
    Process all PDFs in a directory.
    
    Args:
        directory: Directory containing PDFs
        extracted_by: Name for metadata
        
    Returns:
        List of processed files
    """
    pdf_files = list(directory.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  No PDF files found in {directory}")
        return []
    
    print(f"\n📂 Found {len(pdf_files)} PDF files in {directory}")
    print("-" * 60)
    
    results = []
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
        
        try:
            # Extract
            result = extract_requirements_from_pdf(pdf_path)
            
            # Convert to training format
            training_example = convert_to_training_format(result, pdf_path, extracted_by)
            
            # Save
            output_path = save_training_example(training_example)
            
            results.append({
                'input': pdf_path,
                'output': output_path,
                'requirements': len(training_example['requirements']),
                'success': True
            })
            
            print(f"   ✅ Saved: {output_path.name}")
            print(f"   📄 Requirements: {len(training_example['requirements'])}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'input': pdf_path,
                'output': None,
                'error': str(e),
                'success': False
            })
    
    return results


def print_batch_summary(results: list):
    """Print summary of batch processing."""
    print("\n" + "="*60)
    print("📊 BATCH PROCESSING SUMMARY")
    print("="*60)
    
    total = len(results)
    success = sum(1 for r in results if r['success'])
    failed = total - success
    
    print(f"\n📈 Statistics:")
    print(f"   Total files: {total}")
    print(f"   ✅ Successful: {success}")
    print(f"   ❌ Failed: {failed}")
    
    if success > 0:
        total_requirements = sum(r.get('requirements', 0) for r in results if r['success'])
        print(f"   📄 Total requirements: {total_requirements}")
        print(f"   📊 Average per edital: {total_requirements / success:.1f}")
    
    if failed > 0:
        print(f"\n❌ Failed files:")
        for r in results:
            if not r['success']:
                print(f"   • {r['input'].name}: {r.get('error', 'Unknown error')}")
    
    if success > 0:
        print(f"\n✅ Successfully created training examples:")
        for r in results:
            if r['success']:
                print(f"   • {r['output'].name} ({r['requirements']} requirements)")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python batch_extract_pdfs.py <directory>")
        print("  python batch_extract_pdfs.py file1.pdf file2.pdf ...")
        print("\nExamples:")
        print("  python batch_extract_pdfs.py editais/")
        print("  python batch_extract_pdfs.py edital1.pdf edital2.pdf")
        sys.exit(1)
    
    print("="*60)
    print("🎓 BATCH TRAINING EXAMPLE EXTRACTOR")
    print("="*60)
    
    extracted_by = input("\nYour name (for metadata) [Batch]: ").strip() or "Batch"
    
    all_results = []
    
    # Check if first argument is a directory
    first_arg = Path(sys.argv[1])
    
    if first_arg.is_dir():
        # Process directory
        results = process_directory(first_arg, extracted_by)
        all_results.extend(results)
    else:
        # Process individual files
        pdf_files = [Path(arg) for arg in sys.argv[1:]]
        
        # Validate all are PDFs
        for pdf_path in pdf_files:
            if not pdf_path.exists():
                print(f"⚠️  File not found: {pdf_path}")
                continue
            
            if pdf_path.suffix.lower() != '.pdf':
                print(f"⚠️  Not a PDF: {pdf_path}")
                continue
            
            try:
                print(f"\n📄 Processing: {pdf_path.name}")
                result = extract_requirements_from_pdf(pdf_path)
                training_example = convert_to_training_format(result, pdf_path, extracted_by)
                output_path = save_training_example(training_example)
                
                all_results.append({
                    'input': pdf_path,
                    'output': output_path,
                    'requirements': len(training_example['requirements']),
                    'success': True
                })
                
                print(f"   ✅ Saved: {output_path.name}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                all_results.append({
                    'input': pdf_path,
                    'output': None,
                    'error': str(e),
                    'success': False
                })
    
    # Print summary
    print_batch_summary(all_results)
    
    print(f"\n💡 Next steps:")
    print(f"   1. Review generated JSON files in training/examples/")
    print(f"   2. Edit if needed (fix descriptions, categories, etc.)")
    print(f"   3. Test the improvements: streamlit run ui/app.py")


if __name__ == "__main__":
    main()
