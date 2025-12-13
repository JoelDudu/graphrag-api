"""Página de processamento de documentos (Vetorização)"""

import streamlit as st
from utils.session_manager import init_session_state, is_authenticated
from components.header import render_header
from services.document_service import get_document_service
from services.status_service import get_status_service
from utils.formatters import format_progress, format_status
from utils.constants import MODELS
import logging

logger = logging.getLogger(__name__)

# Configurar página
st.set_page_config(
    page_title="Processamento - RAG",
    page_icon="⚙️",
    layout="wide"
)

# Inicializar session state
init_session_state()

# Renderizar header
render_header()

st.subheader("⚙️ Vetorização de Documentos")
st.caption("Processe documentos para extrair entidades e relacionamentos")

st.markdown("---")

# Obter documentos e tipos
try:
    doc_service = get_document_service()
    documents = doc_service.list_documents()
    doc_types_response = doc_service.get_doc_types()
    doc_types = doc_types_response.get("available_types", [])
except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {str(e)}")
    st.stop()

# Filtrar documentos pendentes
pending_docs = [d for d in documents if d.get("status") == "Pending"]

if not pending_docs:
    st.warning("⚠️ Nenhum documento pendente para processar. Faça upload de um documento primeiro.")
    if st.button("📤 Ir para Upload"):
        st.switch_page("pages/2_📤_Upload.py")
    st.stop()

# Formulário de processamento
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Configurar Processamento")
    
    # Seletor de documento
    doc_options = {d["filename"]: d["document_id"] for d in pending_docs}
    selected_doc_name = st.selectbox(
        "Selecione um documento",
        options=list(doc_options.keys()),
        help="Escolha um documento para processar"
    )
    selected_doc_id = doc_options[selected_doc_name]
    
    # Seletor de modelo
    selected_model = st.selectbox(
        "Modelo de IA",
        options=MODELS,
        help="Escolha o modelo para processamento"
    )
    
    # Seletor de tipo de documento
    selected_doc_type = st.selectbox(
        "Tipo de Documento",
        options=doc_types,
        help="Escolha o tipo para otimizar a extração"
    )
    
    # Botão de processar
    if st.button("▶️ Processar", use_container_width=True, type="primary"):
        try:
            with st.spinner("Iniciando processamento..."):
                # Fazer POST /process
                from services.api_client import get_api_client
                client = get_api_client()
                response = client.post(
                    "/process",
                    data={
                        "document_id": selected_doc_id,
                        "model": selected_model,
                        "doc_type": selected_doc_type
                    }
                )
                
                st.success("✅ Processamento iniciado!")
                st.info(f"Modelo: {selected_model} | Tipo: {selected_doc_type}")
                
                # Iniciar polling
                st.markdown("---")
                st.subheader("⏳ Acompanhando Processamento")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_service = get_status_service()
                    final_status = status_service.poll_status(
                        selected_doc_id,
                        interval=5,
                        max_attempts=120
                    )
                    
                    # Atualizar barra de progresso
                    progress_bar.progress(1.0)
                    
                    if final_status.get("status") == "Completed":
                        st.success("✅ Processamento concluído!")
                        
                        # Exibir resumo
                        st.markdown("---")
                        st.subheader("📊 Resumo do Processamento")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            chunks = final_status.get("chunks", 0)
                            st.metric("Chunks", chunks)
                        
                        with col2:
                            entities = final_status.get("entities", 0)
                            st.metric("Entidades", entities)
                        
                        with col3:
                            relationships = final_status.get("relationships", 0)
                            st.metric("Relacionamentos", relationships)
                        
                        # Próximos passos
                        st.markdown("---")
                        st.subheader("Próximos Passos")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("🔍 Busca Semântica", use_container_width=True):
                                st.switch_page("pages/5_🔍_Busca_Semântica.py")
                        
                        with col2:
                            if st.button("🌐 Busca Grafo", use_container_width=True):
                                st.switch_page("pages/6_🌐_Busca_Grafo.py")
                        
                        with col3:
                            if st.button("💬 Chatbot", use_container_width=True):
                                st.switch_page("pages/8_💬_Chatbot.py")
                    
                    else:
                        st.error(f"❌ Erro no processamento: {final_status.get('error', 'Desconhecido')}")
                
                except Exception as e:
                    st.error(f"❌ Erro durante polling: {str(e)}")
                    logger.error(f"Polling error: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ Erro ao iniciar processamento: {str(e)}")
            logger.error(f"Processing error: {str(e)}")

with col2:
    st.markdown("### Informações")
    
    with st.container(border=True):
        st.markdown("**Documento Selecionado**")
        selected_doc = next((d for d in pending_docs if d["document_id"] == selected_doc_id), None)
        if selected_doc:
            st.caption(f"📄 {selected_doc['filename']}")
            st.caption(f"Status: {format_status(selected_doc['status'])}")
    
    with st.expander("ℹ️ Sobre os Modelos"):
        st.markdown("""
        - **Claude**: Modelo Anthropic, excelente para análise de texto
        - **OpenAI**: GPT-4, versátil e poderoso
        - **Kimi**: Modelo especializado em processamento paralelo
        """)
    
    with st.expander("ℹ️ Sobre os Tipos"):
        for doc_type in doc_types:
            st.caption(f"**{doc_type}**: {doc_types_response['descriptions'].get(doc_type, 'N/A')}")

st.markdown("---")
st.caption("Desenvolvido com ❤️ para RAG")
