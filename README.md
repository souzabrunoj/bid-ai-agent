# 🤖 Bid AI Agent

**Local AI Agent for Bid Document Organization**

An intelligent, privacy-focused system that automatically organizes and validates documents for public procurement bids (licitações).

## 🎯 Features

- **Local Processing**: All data processing happens locally - no cloud uploads
- **Automatic Document Classification**: AI-powered document type identification
- **Validity Checking**: Automatic detection of expired documents
- **Organized Output**: Generates structured folders with properly categorized documents
- **Compliance Checklist**: Creates a detailed checklist of required vs. available documents
- **User-Friendly Interface**: Clean Streamlit-based UI

## 🏗️ Project Structure

```
bid-ai-agent/
├── ui/                          # Streamlit user interface
├── agent/                       # AI agent modules
│   ├── edital_reader.py        # Bid notice parser
│   ├── document_classifier.py  # Document classifier
│   ├── comparator.py           # Requirements comparator
│   └── folder_generator.py     # Output generator
├── models/                      # Local LLM management
├── utils/                       # Utility functions
│   ├── pdf_extractor.py        # PDF text extraction
│   ├── date_validator.py       # Date validation
│   └── security.py             # Security functions
├── input/                       # Input documents
│   ├── edital.pdf              # Bid notice
│   └── documentos_empresa/     # Company documents
├── output/                      # Generated results
├── tests/                       # Automated tests
└── config/                      # Configuration
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Tesseract OCR (for scanned PDFs)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/souzabrunoj/bid-ai-agent.git
cd bid-ai-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Download a local LLM model (e.g., Llama 3):
```bash
# Place your .gguf model file in the models/ directory
```

### Usage

```bash
streamlit run ui/app.py
```

Then:
1. Upload the bid notice (edital) PDF
2. Upload your company documents
3. Click "Process Bid"
4. Review the generated checklist and organized folders

## 📋 Document Categories

The system automatically classifies documents into:

- **Legal Qualification** (Habilitação Jurídica)
- **Tax Compliance** (Regularidade Fiscal)
- **Technical Qualification** (Qualificação Técnica)
- **Economic-Financial Qualification** (Qualificação Econômico-Financeira)

## 🔒 Security & Privacy

- **100% Local Processing**: No data leaves your machine
- **No Cloud Dependencies**: All AI models run locally
- **Secure File Handling**: Input validation and sanitization
- **Audit Trail**: Comprehensive logging for verification

## ⚖️ Legal Disclaimer

This tool is an **organizational assistant only**. The final responsibility for bid document accuracy and legal compliance remains with the user. Always perform manual verification before submission.

## 🧪 Testing

```bash
pytest tests/ -v --cov
```

## 📝 Development Status

- [ ] Phase 1: Environment Setup ✅
- [ ] Phase 2: PDF Extraction
- [ ] Phase 3: Bid Notice Reader
- [ ] Phase 4: Document Classifier
- [ ] Phase 5: Comparator
- [ ] Phase 6: Output Generator
- [ ] Phase 7: Streamlit UI
- [ ] Phase 8: Integration & Testing
- [ ] Phase 9: Security Audit
- [ ] Phase 10: Documentation

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

Built with security and privacy as top priorities, following OWASP guidelines and secure development practices.

---

**Made with ❤️ for transparent and efficient public procurement processes**
