"""Página de upload de documentos"""

import streamlit as st
from pathlib import Path
from utils.session_manager import init_session_state
from components.header import render_header
from services.document_service import get_document_service
from utils.formatters import format_date, format_file_size
import logging

logger = logging.getLogger(__name__)

# Configurar página
st.set_page_config(
    page_title="Upload - RAG",
    page_icon="📤",
    layout="wide"
)

# Inicializar session state
init_session_state()

# Renderizar header
render_header()

st.subheader("📤 Upload de Documentos")
st.caption("Envie documentos PDF para vetorização e indexação")

st.markdown("---")

# Seção de upload
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Enviar Documento")
    
    uploaded_file = st.file_uploader(
        "Selecione um arquivo",
        type=["pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "txt", "csv"],
        help="Aceita: PDF, Word, Excel, PowerPoint, TXT, CSV"
    )
    
    if uploaded_file is not None:
        # Validar arquivo (apenas verificar extensão)
        valid_extensions = [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".csv"]
        file_ext = Path(uploaded_file.name).suffix.lower()
        
        if file_ext not in valid_extensions:
            st.error(f"❌ Tipo de arquivo não suportado. Use: {', '.join(valid_extensions)}")
        else:
            st.success(f"✅ Arquivo selecionado: {uploaded_file.name}")
            st.caption(f"Tamanho: {format_file_size(uploaded_file.size)}")
            
            if st.button("Enviar Documento", use_container_width=True):
                try:
                    with st.spinner("Enviando documento..."):
                        service = get_document_service()
                        result = service.upload_document(uploaded_file)
                        
                        document_id = result.get("document_id")
                        
                        st.success("✅ Documento enviado com sucesso!")
                        st.info(f"ID do documento: `{document_id}`")
                        
                        # Armazenar em recent_documents
                        if "recent_documents" not in st.session_state:
                            st.session_state.recent_documents = []
                        
                        st.session_state.recent_documents.append({
                            "document_id": document_id,
                            "filename": uploaded_file.name,
                            "status": "Pending"
                        })
                        
                        # Oferecer opção de processar
                        st.markdown("---")
                        st.subheader("Próximos Passos")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("⚙️ Processar Agora", use_container_width=True):
                                st.session_state.selected_document = document_id
                                st.switch_page("pages/3_⚙️_Processamento.py")
                        
                        with col2:
                            if st.button("📋 Ir para Gestão", use_container_width=True):
                                st.switch_page("pages/4_📋_Gestão.py")
                
                except Exception as e:
                    st.error(f"❌ Erro ao enviar documento: {str(e)}")
                    logger.error(f"Upload error: {str(e)}")

with col2:
    st.markdown("### Documentos Recentes")
    
    if st.session_state.get("recent_documents"):
        for doc in st.session_state.recent_documents[-5:]:  # Últimos 5
            with st.container(border=True):
                st.caption(f"📄 {doc['filename']}")
                st.caption(f"Status: {doc['status']}")
                st.caption(f"ID: `{doc['document_id'][:8]}...`")
    else:
        st.info("Nenhum documento enviado ainda.")

st.markdown("---")

# Seção de informações
st.subheader("ℹ️ Informações")

with st.expander("Como funciona o upload?"):
    st.markdown("""
    1. **Selecione um PDF**: Clique em "Selecione um arquivo PDF" e escolha seu documento
    2. **Valide o arquivo**: O sistema verifica se é um PDF válido
    3. **Envie**: Clique em "Enviar Documento"
    4. **Processe**: Após o upload, você pode processar o documento imediatamente
    5. **Acompanhe**: Vá para "Gestão" para acompanhar o processamento
    """)

with st.expander("Tipos de documentos suportados"):
    st.markdown("""
    **Formatos aceitos:**
    - 📄 **PDF**: Documentos em formato PDF
    - 📝 **Word**: .docx, .doc
    - 📊 **Excel**: .xlsx, .xls
    - 🎯 **PowerPoint**: .pptx, .ppt
    - 📋 **Texto**: .txt, .csv
    
    **Limitações:**
    - Tamanho máximo: 200 MB
    - Idioma: Português, Inglês e outros idiomas suportados
    """)

st.caption("Desenvolvido com ❤️ para RAG")
