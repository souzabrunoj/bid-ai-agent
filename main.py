"""
Bid AI Agent - Main Entry Point

Local AI agent for bid document organization and validation.
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings, ensure_directories


def main() -> None:
    """
    Main entry point for the Bid AI Agent.
    
    This function initializes the application and starts the Streamlit UI.
    """
    print(f"🤖 {settings.app_name} v{settings.app_version}")
    print("=" * 50)
    print("Local AI Agent for Bid Document Organization")
    print("=" * 50)
    
    # Ensure all required directories exist
    print("\n📁 Checking directories...")
    ensure_directories()
    print("✅ All directories ready")
    
    # Check if LLM model exists
    model_path = Path(settings.llm_model_path)
    if not model_path.exists():
        print(f"\n⚠️  Warning: LLM model not found at {model_path}")
        print("Please download a local LLM model (.gguf format) and place it in the models/ directory")
        print("Example: llama-3-8b.gguf, mistral-7b.gguf")
    else:
        print(f"\n✅ LLM model found: {model_path.name}")
    
    print("\n🚀 Starting application...")
    print("\nTo start the UI, run:")
    print("  streamlit run ui/app.py")
    print("\nOr run directly from Python:")
    print("  python -m streamlit run ui/app.py")


if __name__ == "__main__":
    main()
