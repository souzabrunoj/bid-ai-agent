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
import zipfile
import base64

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
from utils.file_renamer import FileRenamer
from utils import DateValidator, extract_pdf_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Company documents folder (persistent)
DOCUMENTOS_DIR = PROJECT_ROOT / "documentos"
DOCUMENTOS_DIR.mkdir(parents=True, exist_ok=True)

# Page configuration
st.set_page_config(
    page_title="Bid AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        'edital_uploaded': False,
        'documents_ready': False,
        'processing_complete': False,
        'report': None,
        'output_folder': None,
        'edital_analysis': None,
        'classified_docs': [],
        'options': {
            'validate_dates': True,
            'include_expired': False,
            'detailed_checklist': True
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def check_llm_availability() -> bool:
    """Check if LLM model is available and enabled."""
    # First check if LLM is enabled in settings
    if not settings.llm_enabled:
        return False
    
    # Then check if model is actually available
    try:
        llm = get_llm()
        return llm.is_model_loaded()
    except LLMError:
        return False


def get_local_documents() -> List[Path]:
    """Get all PDF documents from the documentos/ folder."""
    if not DOCUMENTOS_DIR.exists():
        return []
    return sorted(DOCUMENTOS_DIR.rglob("*.pdf"))


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_document_validity(doc_path: str) -> dict:
    """Get document validity date with caching."""
    try:
        # Try without OCR first (faster)
        text = extract_pdf_text(Path(doc_path), enable_ocr=False)
        date_validator = DateValidator()
        result = date_validator.validate_document_date(text, Path(doc_path).name)
        
        # If no date found, try with OCR
        if not result['has_date']:
            text = extract_pdf_text(Path(doc_path), enable_ocr=True)
            result = date_validator.validate_document_date(text, Path(doc_path).name)
        
        return result
    except Exception:
        return {'has_date': False, 'expiration_date': None}


def save_uploaded_file(uploaded_file, destination: Path) -> Path:
    """Save uploaded file to destination."""
    file_path = destination / uploaded_file.name
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def save_to_documentos(uploaded_file) -> Path:
    """Save uploaded file to documentos/ folder with smart renaming."""
    file_path = DOCUMENTOS_DIR / uploaded_file.name
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())

    # Try to rename to a standard name
    suggested = FileRenamer.suggest_name(file_path.stem)
    if suggested:
        new_path = DOCUMENTOS_DIR / f"{suggested}{file_path.suffix}"
        if not new_path.exists() or new_path == file_path:
            file_path.rename(new_path)
            return new_path

    return file_path


# ──────────────────────────────────────────────────────
# UI SECTIONS
# ──────────────────────────────────────────────────────

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

        llm_available = check_llm_availability()
        if llm_available:
            st.success("✅ IA Local: Ativa")
        else:
            st.warning("⚠️ IA Local: Indisponível")
            st.caption("Usando modo baseado em regras")

        local_docs = get_local_documents()
        st.info(f"📁 Documentos da empresa: **{len(local_docs)}** PDFs")
        st.info(f"📦 Saída: `{settings.output_dir}`")

        with st.expander("Configurações"):
            st.text(f"OCR: {'Ativado' if settings.ocr_enabled else 'Desativado'}")
            st.text(f"Max File Size: {settings.max_file_size_mb}MB")
            st.text(f"Debug: {'Ativo' if settings.debug_mode else 'Inativo'}")


def section_edital_upload():
    """Section 1: Upload bid notice (edital)."""
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


def section_documents():
    """Section 2: Company documents (local folder + upload)."""
    st.header("2️⃣ Documentos da Empresa")

    local_docs = get_local_documents()

    # Show local documents
    if local_docs:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"📁 **{len(local_docs)} documentos** encontrados na pasta `documentos/`")
        with col2:
            if st.button("🔄 Atualizar datas", help="Recarregar datas de validade", use_container_width=True):
                get_document_validity.clear()
                st.rerun()
        
        # Add custom CSS for button alignment and visibility
        st.markdown("""
            <style>
            .stButton button {
                height: 42px;
                padding: 0;
                margin-top: 4px;
                font-size: 20px;
                background-color: #0e1117;
                border: 1px solid #4a5568;
            }
            .stButton button:hover {
                background-color: #1e293b;
                border-color: #60a5fa;
                transform: scale(1.05);
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown("")  # Small space
        
        for doc in local_docs:
                # Get validity date (cached)
                date_info = get_document_validity(str(doc))
                
                # Determine status
                if date_info['has_date'] and date_info['expiration_date']:
                    exp_date = date_info['expiration_date'].strftime('%d/%m/%Y')
                    if date_info['is_expired']:
                        status_emoji = "⏰"
                        status_text = f"Vencido: {exp_date}"
                        status_color = "#ff4b4b"
                    elif date_info.get('expires_soon', False):
                        status_emoji = "⚠️"
                        status_text = f"Vence: {exp_date}"
                        status_color = "#ffa500"
                    else:
                        status_emoji = "✅"
                        status_text = f"Válido até: {exp_date}"
                        status_color = "#00cc66"
                else:
                    status_emoji = "⚠️"
                    status_text = "Verificar manualmente"
                    status_color = "#ffa500"
                
                # Single row layout
                cols = st.columns([4, 3, 1])
                
                with cols[0]:
                    st.markdown(f"<p style='margin: 12px 0;'>📄 <b>{doc.name}</b></p>", 
                               unsafe_allow_html=True)
                
                with cols[1]:
                    st.markdown(
                        f"<div style='background-color: {status_color}20; "
                        f"border-left: 4px solid {status_color}; "
                        f"padding: 8px 12px; "
                        f"margin: 4px 0; "
                        f"border-radius: 4px;'>"
                        f"{status_emoji} {status_text}"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                
                with cols[2]:
                    st.button("👁️", key=f"view_{doc.name}", help="Visualizar PDF", 
                             use_container_width=True,
                             on_click=lambda d=doc: st.session_state.update({'viewing_doc': d}))
        
        st.session_state.documents_ready = True
    else:
        st.warning("📁 Pasta `documentos/` vazia. Adicione PDFs ou faça upload abaixo.")
        st.session_state.documents_ready = False
    
    # PDF Viewer Modal
    if st.session_state.get('viewing_doc'):
        doc_to_view = st.session_state.viewing_doc
        
        @st.dialog(f"📄 {doc_to_view.name}", width="large")
        def show_pdf_viewer():
            try:
                with open(doc_to_view, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
                
                st.divider()
                
                # Download button
                with open(doc_to_view, "rb") as f:
                    st.download_button(
                        label="⬇️ Baixar PDF",
                        data=f.read(),
                        file_name=doc_to_view.name,
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                if st.button("✖️ Fechar", type="primary", use_container_width=True):
                    st.session_state.viewing_doc = None
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Erro ao visualizar PDF: {e}")
                st.info("💡 Baixe o arquivo:")
                with open(doc_to_view, "rb") as f:
                    st.download_button(
                        label="⬇️ Baixar PDF",
                        data=f.read(),
                        file_name=doc_to_view.name,
                        mime="application/pdf"
                    )
        
        show_pdf_viewer()

    # Upload new / replacement documents
    st.markdown("---")
    st.markdown("**Atualizar documentos** (substituir vencidos ou adicionar novos)")

    new_files = st.file_uploader(
        "Enviar novos documentos para a pasta da empresa (PDF ou ZIP)",
        type=['pdf', 'zip'],
        accept_multiple_files=True,
        key='new_docs_uploader',
        help="Os arquivos serão salvos na pasta documentos/ e renomeados automaticamente"
    )

    if new_files:
        saved = []
        for f in new_files:
            if f.name.lower().endswith('.zip'):
                # Extract ZIP into documentos/
                tmp = Path(tempfile.mkdtemp())
                zip_path = save_uploaded_file(f, tmp)
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        zf.extractall(tmp / "extracted")
                    for pdf in (tmp / "extracted").rglob("*.pdf"):
                        dest = DOCUMENTOS_DIR / pdf.name
                        shutil.copy2(pdf, dest)
                        suggested = FileRenamer.suggest_name(dest.stem)
                        if suggested:
                            new_dest = DOCUMENTOS_DIR / f"{suggested}{dest.suffix}"
                            if not new_dest.exists():
                                dest.rename(new_dest)
                                dest = new_dest
                        saved.append(dest.name)
                except zipfile.BadZipFile:
                    st.error(f"❌ ZIP inválido: {f.name}")
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)
            else:
                path = save_to_documentos(f)
                saved.append(path.name)

        if saved:
            st.success(f"✅ {len(saved)} documento(s) salvos na pasta `documentos/`:")
            for name in saved:
                st.caption(f"  📄 {name}")
            st.session_state.documents_ready = True
            st.rerun()


def section_options():
    """Section 3: Processing options."""
    st.header("⚙️ Opções de Processamento")

    col1, col2, col3 = st.columns(3)
    with col1:
        validate_dates = st.checkbox("Validar datas de validade", value=True)
    with col2:
        include_expired = st.checkbox("Incluir documentos vencidos", value=False)
    with col3:
        detailed_checklist = st.checkbox("Gerar checklist detalhado", value=True)

    st.session_state.options = {
        'validate_dates': validate_dates,
        'include_expired': include_expired,
        'detailed_checklist': detailed_checklist
    }


# ──────────────────────────────────────────────────────
# PROCESSING
# ──────────────────────────────────────────────────────

def process_bid():
    """Process bid documents."""
    temp_dir = Path(tempfile.mkdtemp())

    try:
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Step 1: Save edital to temp
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

        # Step 3: Collect documents from documentos/ folder
        status_text.text("📑 Classificando documentos...")
        document_paths = get_local_documents()

        if not document_paths:
            st.error("❌ Nenhum documento PDF encontrado na pasta documentos/")
            return False

        st.toast(f"📄 {len(document_paths)} documentos para processar", icon="✅")
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
        shutil.rmtree(temp_dir, ignore_errors=True)


# ──────────────────────────────────────────────────────
# RESULTS
# ──────────────────────────────────────────────────────

def display_results():
    """Display processing results."""
    st.header("📋 Resultados")

    if not st.session_state.processing_complete:
        st.info("Execute o processamento para ver os resultados")
        return

    report = st.session_state.report

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("✅ OK", report.statistics['requirements_ok'])
    with col2:
        st.metric("⚠️ Avisos", report.statistics['requirements_warning'])
    with col3:
        st.metric("❌ Vencidos", report.statistics['requirements_expired'])
    with col4:
        st.metric("❓ Faltantes", report.statistics['requirements_missing'])

    st.divider()

    compliance_rate = report.get_compliance_rate()
    if report.is_compliant():
        st.success(f"✅ **DOCUMENTAÇÃO COMPLETA** ({compliance_rate:.1f}% conforme)")
    else:
        st.warning(f"⚠️ **DOCUMENTAÇÃO INCOMPLETA** ({compliance_rate:.1f}% conforme)")

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

    if report.statistics['requirements_missing'] > 0:
        with st.expander("❌ Documentos Faltantes", expanded=True):
            for match in report.matches:
                if match.status == 'missing':
                    st.error(f"**• {match.requirement.name}**")
                    if match.requirement.description:
                        st.caption(f"   📋 {match.requirement.description}")
                    if match.requirement.requirements:
                        st.caption(f"   ⚠️ Exigência do edital: {match.requirement.requirements}")
                    st.caption(f"   📁 Categoria: {match.requirement.category.replace('_', ' ').title()}")
                    st.markdown("")

    if report.statistics['requirements_expired'] > 0:
        with st.expander("⏰ Documentos Vencidos", expanded=True):
            for match in report.matches:
                if match.status == 'expired' and match.matched_document:
                    st.warning(f"• {match.matched_document.file_name}")
                    for obs in match.get_observations():
                        st.caption(f"  {obs}")
                    st.caption("  💡 Faça upload do documento atualizado na seção 2")

    if report.statistics['requirements_warning'] > 0:
        with st.expander("⚠️ Documentos com Aviso"):
            for match in report.matches:
                if match.status == 'warning' and match.matched_document:
                    st.info(f"• {match.matched_document.file_name}")
                    for obs in match.get_observations():
                        st.caption(f"  {obs}")

    if report.statistics['requirements_ok'] > 0:
        with st.expander("✅ Documentos OK"):
            for match in report.matches:
                if match.status == 'ok' and match.matched_document:
                    st.success(f"• {match.matched_document.file_name}")


def display_checklist_tab(report):
    """Display checklist tab."""
    st.subheader("Checklist Detalhado")

    by_category = {}
    for match in report.matches:
        cat = match.requirement.category
        by_category.setdefault(cat, []).append(match)

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
                icon = {'ok': '✅', 'expired': '❌', 'missing': '❓', 'warning': '⚠️'}.get(match.status, '?')
                st.markdown(f"**{icon} {match.requirement.name}**")
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
                if system == "Darwin":
                    subprocess.run(["open", str(output_folder)])
                elif system == "Windows":
                    subprocess.run(["explorer", str(output_folder)])
                else:
                    subprocess.run(["xdg-open", str(output_folder)])
                st.success("Pasta aberta!")
            except Exception as e:
                st.error(f"Erro ao abrir pasta: {e}")

    with col2:
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


# ──────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────

def main():
    """Main application function."""
    init_session_state()
    ensure_directories()

    display_header()
    display_system_status()

    st.divider()
    section_edital_upload()
    st.divider()
    section_documents()
    st.divider()
    section_options()
    st.divider()

    # Process button
    can_process = st.session_state.edital_uploaded and st.session_state.documents_ready

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
            help="Faça upload do edital e adicione documentos na pasta documentos/"
        )

    st.divider()

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
