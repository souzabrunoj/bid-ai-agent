"""
Streamlit UI for Bid AI Agent.

User-friendly interface for automated bid document organization.
"""

import streamlit as st
import logging
from pathlib import Path
from typing import List, Optional
import sys
import tempfile
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings, ensure_directories
from agent import (
    EditalReader,
    DocumentClassifier,
    RequirementComparator,
    FolderGenerator,
    BidRequirement,
    ClassifiedDocument
)
from models import get_llm, LLMError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Page configuration
st.set_page_config(
    page_title="Bid AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def init_session_state():
    """Initialize session state variables."""
    if 'edital_uploaded' not in st.session_state:
        st.session_state.edital_uploaded = False
    if 'documents_uploaded' not in st.session_state:
        st.session_state.documents_uploaded = False
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'report' not in st.session_state:
        st.session_state.report = None
    if 'output_folder' not in st.session_state:
        st.session_state.output_folder = None
    if 'edital_analysis' not in st.session_state:
        st.session_state.edital_analysis = None
    if 'classified_docs' not in st.session_state:
        st.session_state.classified_docs = []


def check_llm_availability() -> bool:
    """Check if LLM model is available."""
    try:
        llm = get_llm()
        return llm.is_model_loaded()
    except LLMError:
        return False


def save_uploaded_file(uploaded_file, destination: Path) -> Path:
    """
    Save uploaded file to destination.
    
    Args:
        uploaded_file: Streamlit uploaded file
        destination: Destination path
        
    Returns:
        Path to saved file
    """
    file_path = destination / uploaded_file.name
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def display_header():
    """Display application header."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("🤖 Bid AI Agent")
        st.markdown("**Organizador Automático de Documentos para Licitações**")
        st.caption("Processamento 100% local • Privacidade garantida • IA especializada")
    
    with col2:
        st.metric("Versão", settings.app_version)


def display_system_status():
    """Display system status in sidebar."""
    with st.sidebar:
        st.header("⚙️ Status do Sistema")
        
        # LLM status
        llm_available = check_llm_availability()
        if llm_available:
            st.success("✅ IA Local: Ativa")
        else:
            st.warning("⚠️ IA Local: Indisponível")
            st.caption("Usando modo baseado em regras")
        
        # Directories
        st.info(f"📁 Entrada: `{settings.input_dir}`")
        st.info(f"📦 Saída: `{settings.output_dir}`")
        
        # Settings
        with st.expander("Configurações"):
            st.text(f"OCR: {'Ativado' if settings.ocr_enabled else 'Desativado'}")
            st.text(f"Max File Size: {settings.max_file_size_mb}MB")
            st.text(f"Debug: {'Ativo' if settings.debug_mode else 'Inativo'}")


def section_edital_upload():
    """Section: Upload bid notice (edital)."""
    st.header("1️⃣ Upload do Edital")
    st.markdown("Envie o arquivo PDF do edital de licitação")
    
    edital_file = st.file_uploader(
        "Selecione o edital (PDF)",
        type=['pdf'],
        key='edital_uploader',
        help="Arquivo PDF contendo as exigências da licitação"
    )
    
    if edital_file:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.success(f"✅ Edital carregado: **{edital_file.name}**")
        with col2:
            st.caption(f"Tamanho: {edital_file.size / 1024:.1f} KB")
        
        st.session_state.edital_uploaded = True
        st.session_state.edital_file = edital_file
    else:
        st.session_state.edital_uploaded = False
        st.info("📄 Aguardando upload do edital...")


def section_documents_upload():
    """Section: Upload company documents."""
    st.header("2️⃣ Documentos da Empresa")
    st.markdown("Envie todos os documentos que você possui")
    
    document_files = st.file_uploader(
        "Selecione os documentos (múltiplos PDFs)",
        type=['pdf'],
        accept_multiple_files=True,
        key='documents_uploader',
        help="Todos os documentos da empresa para análise"
    )
    
    if document_files:
        st.success(f"✅ {len(document_files)} documento(s) carregado(s)")
        
        with st.expander("Ver lista de documentos", expanded=False):
            for i, doc_file in enumerate(document_files, 1):
                st.text(f"{i}. {doc_file.name} ({doc_file.size / 1024:.1f} KB)")
        
        st.session_state.documents_uploaded = True
        st.session_state.document_files = document_files
    else:
        st.session_state.documents_uploaded = False
        st.info("📂 Aguardando upload dos documentos...")


def section_options():
    """Section: Processing options."""
    st.header("⚙️ Opções de Processamento")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        validate_dates = st.checkbox(
            "Validar datas de validade",
            value=True,
            help="Verificar se documentos estão vencidos"
        )
    
    with col2:
        include_expired = st.checkbox(
            "Incluir documentos vencidos",
            value=False,
            help="Copiar documentos vencidos para a pasta final"
        )
    
    with col3:
        detailed_checklist = st.checkbox(
            "Gerar checklist detalhado",
            value=True,
            help="Incluir observações detalhadas no checklist"
        )
    
    return {
        'validate_dates': validate_dates,
        'include_expired': include_expired,
        'detailed_checklist': detailed_checklist
    }


def process_bid():
    """Process bid documents."""
    st.header("▶️ Processamento")
    
    # Create temporary directory for processing
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Save edital
        status_text.text("📄 Salvando edital...")
        edital_path = save_uploaded_file(st.session_state.edital_file, temp_dir)
        progress_bar.progress(10)
        
        # Step 2: Analyze edital
        status_text.text("🔍 Analisando edital...")
        with st.spinner("Extraindo requisitos do edital..."):
            reader = EditalReader(use_llm=check_llm_availability())
            edital_analysis = reader.analyze_edital(edital_path)
            st.session_state.edital_analysis = edital_analysis
        progress_bar.progress(30)
        
        # Step 3: Save and classify documents
        status_text.text("📑 Classificando documentos...")
        doc_dir = temp_dir / "documentos"
        doc_dir.mkdir()
        
        document_paths = []
        for doc_file in st.session_state.document_files:
            doc_path = save_uploaded_file(doc_file, doc_dir)
            document_paths.append(doc_path)
        
        progress_bar.progress(40)
        
        with st.spinner("Classificando documentos..."):
            classifier = DocumentClassifier(use_llm=check_llm_availability())
            classified_docs = classifier.classify_documents_batch(document_paths)
            st.session_state.classified_docs = classified_docs
        progress_bar.progress(60)
        
        # Step 4: Compare requirements
        status_text.text("⚖️ Comparando requisitos...")
        with st.spinner("Comparando documentos com requisitos..."):
            requirements = [
                BidRequirement.from_dict(req)
                for req in edital_analysis['requirements']
            ]
            
            comparator = RequirementComparator()
            report = comparator.compare(requirements, classified_docs)
            st.session_state.report = report
        progress_bar.progress(80)
        
        # Step 5: Generate organized folder
        status_text.text("📦 Gerando pasta organizada...")
        with st.spinner("Criando estrutura de pastas..."):
            generator = FolderGenerator()
            output_folder = generator.generate_organized_folder(
                report,
                bid_name=edital_path.stem,
                include_expired=st.session_state.options['include_expired'],
                edital_info={
                    'file_name': edital_path.name,
                    'total_requirements': edital_analysis['total_requirements'],
                    'extraction_method': edital_analysis['extraction_method']
                }
            )
            st.session_state.output_folder = output_folder
        progress_bar.progress(100)
        
        status_text.text("✅ Processamento concluído!")
        st.session_state.processing_complete = True
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erro durante o processamento: {str(e)}")
        logger.exception("Processing error")
        return False
    
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory: {e}")


def display_results():
    """Display processing results."""
    st.header("📋 Resultados")
    
    if not st.session_state.processing_complete:
        st.info("Execute o processamento para ver os resultados")
        return
    
    report = st.session_state.report
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "✅ OK",
            report.statistics['requirements_ok'],
            delta=None,
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "⚠️ Avisos",
            report.statistics['requirements_warning'],
            delta=None
        )
    
    with col3:
        st.metric(
            "❌ Vencidos",
            report.statistics['requirements_expired'],
            delta=None,
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "❓ Faltantes",
            report.statistics['requirements_missing'],
            delta=None,
            delta_color="inverse"
        )
    
    # Compliance status
    st.divider()
    
    compliance_rate = report.get_compliance_rate()
    
    if report.is_compliant():
        st.success(f"✅ **DOCUMENTAÇÃO COMPLETA** ({compliance_rate:.1f}% conforme)")
    else:
        st.warning(f"⚠️ **DOCUMENTAÇÃO INCOMPLETA** ({compliance_rate:.1f}% conforme)")
    
    # Detailed results
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["📊 Resumo", "📝 Checklist", "📁 Arquivos"])
    
    with tab1:
        display_summary_tab(report)
    
    with tab2:
        display_checklist_tab(report)
    
    with tab3:
        display_files_tab()


def display_summary_tab(report):
    """Display summary tab."""
    st.subheader("Resumo Executivo")
    
    # Missing documents
    if report.statistics['requirements_missing'] > 0:
        with st.expander("❌ Documentos Faltantes", expanded=True):
            for match in report.matches:
                if match.status == 'missing':
                    st.error(f"• {match.requirement.name}")
                    if match.requirement.description:
                        st.caption(f"  {match.requirement.description}")
    
    # Expired documents
    if report.statistics['requirements_expired'] > 0:
        with st.expander("⏰ Documentos Vencidos", expanded=True):
            for match in report.matches:
                if match.status == 'expired' and match.matched_document:
                    st.warning(f"• {match.matched_document.file_name}")
                    for obs in match.get_observations():
                        st.caption(f"  {obs}")
    
    # Warnings
    if report.statistics['requirements_warning'] > 0:
        with st.expander("⚠️ Documentos com Aviso"):
            for match in report.matches:
                if match.status == 'warning' and match.matched_document:
                    st.info(f"• {match.matched_document.file_name}")
                    for obs in match.get_observations():
                        st.caption(f"  {obs}")
    
    # OK documents
    if report.statistics['requirements_ok'] > 0:
        with st.expander("✅ Documentos OK"):
            for match in report.matches:
                if match.status == 'ok' and match.matched_document:
                    st.success(f"• {match.matched_document.file_name}")


def display_checklist_tab(report):
    """Display checklist tab."""
    st.subheader("Checklist Detalhado")
    
    # Group by category
    by_category = {}
    for match in report.matches:
        category = match.requirement.category
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(match)
    
    category_names = {
        'habilitacao_juridica': '⚖️ Habilitação Jurídica',
        'regularidade_fiscal': '💰 Regularidade Fiscal',
        'qualificacao_tecnica': '🔧 Qualificação Técnica',
        'qualificacao_economica': '📊 Qualificação Econômico-Financeira',
        'proposta_comercial': '💼 Proposta Comercial',
        'outros': '📎 Outros'
    }
    
    for category, matches in by_category.items():
        with st.expander(category_names.get(category, category), expanded=False):
            for match in matches:
                status_icon = {
                    'ok': '✅',
                    'expired': '❌',
                    'missing': '❓',
                    'warning': '⚠️'
                }.get(match.status, '?')
                
                st.markdown(f"**{status_icon} {match.requirement.name}**")
                
                if match.matched_document:
                    st.caption(f"📄 Arquivo: {match.matched_document.file_name}")
                
                for obs in match.get_observations():
                    st.caption(f"→ {obs}")
                
                st.divider()


def display_files_tab():
    """Display files tab."""
    st.subheader("Pasta Gerada")
    
    output_folder = st.session_state.output_folder
    
    st.info(f"📁 **Pasta:** `{output_folder}`")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📂 Abrir Pasta no Explorador", use_container_width=True):
            import subprocess
            import platform
            
            system = platform.system()
            try:
                if system == "Darwin":  # macOS
                    subprocess.run(["open", str(output_folder)])
                elif system == "Windows":
                    subprocess.run(["explorer", str(output_folder)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(output_folder)])
                st.success("Pasta aberta!")
            except Exception as e:
                st.error(f"Erro ao abrir pasta: {e}")
    
    with col2:
        # Read checklist file
        checklist_path = output_folder / "CHECKLIST.txt"
        if checklist_path.exists():
            with open(checklist_path, 'r', encoding='utf-8') as f:
                checklist_content = f.read()
            
            st.download_button(
                label="⬇️ Baixar Checklist",
                data=checklist_content,
                file_name="CHECKLIST.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    st.divider()
    
    st.markdown("**Arquivos gerados:**")
    st.text("• CHECKLIST.txt - Lista detalhada de documentos")
    st.text("• RESUMO.txt - Resumo executivo")
    st.text("• relatorio.json - Relatório técnico completo")
    st.text("• LEIA-ME.txt - Instruções importantes")


def main():
    """Main application function."""
    # Initialize
    init_session_state()
    ensure_directories()
    
    # Display UI
    display_header()
    display_system_status()
    
    st.divider()
    
    # Upload sections
    section_edital_upload()
    st.divider()
    section_documents_upload()
    st.divider()
    
    # Options
    options = section_options()
    st.session_state.options = options
    st.divider()
    
    # Processing button
    can_process = (
        st.session_state.edital_uploaded and
        st.session_state.documents_uploaded
    )
    
    if can_process:
        if st.button("▶️ Processar Licitação", type="primary", use_container_width=True):
            with st.spinner("Processando..."):
                process_bid()
    else:
        st.button(
            "▶️ Processar Licitação",
            type="primary",
            disabled=True,
            use_container_width=True,
            help="Faça upload do edital e dos documentos primeiro"
        )
    
    st.divider()
    
    # Results
    if st.session_state.processing_complete:
        display_results()
    
    # Footer
    st.divider()
    st.caption(
        "⚠️ **IMPORTANTE:** Revise manualmente todos os documentos antes do envio oficial. "
        "Este sistema é uma ferramenta de apoio. A responsabilidade jurídica final é sua."
    )
    st.caption(f"Bid AI Agent v{settings.app_version} • Processamento 100% local • Dados seguros")


if __name__ == "__main__":
    main()
