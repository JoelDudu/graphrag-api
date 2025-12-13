"""Página de gestão de documentos"""

import streamlit as st
import pandas as pd
from utils.session_manager import init_session_state, is_authenticated
from components.header import render_header
from services.document_service import get_document_service
from utils.formatters import format_date, format_progress, format_status
import logging

logger = logging.getLogger(__name__)

# Configurar página
st.set_page_config(
    page_title="Gestão - RAG",
    page_icon="📋",
    layout="wide"
)

# Inicializar session state
init_session_state()

# Renderizar header
render_header()

st.subheader("📋 Gestão de Documentos")
st.caption("Visualize, filtre e gerencie todos os seus documentos")

st.markdown("---")

# Obter documentos
try:
    doc_service = get_document_service()
    documents = doc_service.list_documents()
except Exception as e:
    st.error(f"❌ Erro ao carregar documentos: {str(e)}")
    st.stop()

if not documents:
    st.info("📭 Nenhum documento encontrado. Faça upload de um documento para começar.")
    if st.button("📤 Ir para Upload"):
        st.switch_page("pages/2_📤_Upload.py")
    st.stop()

# Filtros
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    status_filter = st.multiselect(
        "Filtrar por Status",
        options=["Pending", "Processing", "Completed", "Error"],
        default=["Pending", "Processing", "Completed", "Error"],
        help="Selecione os status para exibir"
    )

with col2:
    search_query = st.text_input(
        "Buscar por nome",
        placeholder="Digite o nome do documento...",
        help="Busca por nome do arquivo"
    )

with col3:
    sort_by = st.selectbox(
        "Ordenar por",
        options=["Data (Recente)", "Data (Antigo)", "Nome (A-Z)", "Status"],
        help="Escolha como ordenar"
    )

st.markdown("---")

# Aplicar filtros
filtered_docs = documents.copy()

# Filtrar por status
filtered_docs = [d for d in filtered_docs if d.get("status") in status_filter]

# Filtrar por nome
if search_query:
    filtered_docs = [
        d for d in filtered_docs
        if search_query.lower() in d.get("filename", "").lower()
    ]

# Ordenar
if sort_by == "Data (Recente)":
    filtered_docs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
elif sort_by == "Data (Antigo)":
    filtered_docs.sort(key=lambda x: x.get("created_at", ""))
elif sort_by == "Nome (A-Z)":
    filtered_docs.sort(key=lambda x: x.get("filename", ""))
elif sort_by == "Status":
    status_order = {"Pending": 0, "Processing": 1, "Completed": 2, "Error": 3}
    filtered_docs.sort(key=lambda x: status_order.get(x.get("status"), 4))

# Exibir tabela
st.subheader(f"Documentos ({len(filtered_docs)})")

if filtered_docs:
    # Preparar dados para tabela
    table_data = []
    for doc in filtered_docs:
        table_data.append({
            "Nome": doc.get("filename", "N/A"),
            "Status": format_status(doc.get("status", "N/A")),
            "Progresso": format_progress(doc.get("progress", 0)),
            "Modelo": doc.get("model", "-"),
            "Data": format_date(doc.get("created_at", "N/A")),
            "ID": doc.get("document_id", "")
        })
    
    df = pd.DataFrame(table_data)
    
    # Exibir tabela
    st.dataframe(
        df[["Nome", "Status", "Progresso", "Modelo", "Data"]],
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Ações por documento
    st.subheader("Ações")
    
    selected_doc_name = st.selectbox(
        "Selecione um documento para ações",
        options=[d.get("filename") for d in filtered_docs],
        help="Escolha um documento"
    )
    
    selected_doc = next(
        (d for d in filtered_docs if d.get("filename") == selected_doc_name),
        None
    )
    
    if selected_doc:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Visualizar Detalhes", use_container_width=True):
                st.markdown("---")
                st.subheader("Detalhes do Documento")
                
                detail_cols = st.columns(2)
                
                with detail_cols[0]:
                    st.metric("Nome", selected_doc.get("filename", "N/A"))
                    st.metric("Status", format_status(selected_doc.get("status", "N/A")))
                    st.metric("Modelo", selected_doc.get("model", "-"))
                
                with detail_cols[1]:
                    st.metric("Progresso", format_progress(selected_doc.get("progress", 0)))
                    st.metric("Chunks", selected_doc.get("chunks", "-"))
                    st.metric("Entidades", selected_doc.get("entities", "-"))
                
                st.metric("Relacionamentos", selected_doc.get("relationships", "-"))
                st.metric("Data de Criação", format_date(selected_doc.get("created_at", "N/A")))
                st.metric("Última Atualização", format_date(selected_doc.get("updated_at", "N/A")))
                
                if selected_doc.get("error"):
                    st.error(f"Erro: {selected_doc.get('error')}")
        
        with col2:
            if selected_doc.get("status") == "Completed":
                if st.button("🔍 Buscar Neste Documento", use_container_width=True):
                    st.session_state.selected_document = selected_doc.get("document_id")
                    st.switch_page("pages/5_🔍_Busca_Semântica.py")
        
        with col3:
            if st.button("🗑️ Deletar", use_container_width=True, type="secondary"):
                # Confirmação
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Confirmar Deleção", use_container_width=True, type="primary"):
                        try:
                            with st.spinner("Deletando documento..."):
                                doc_service.delete_document(selected_doc.get("document_id"))
                                st.success("✅ Documento deletado com sucesso!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao deletar: {str(e)}")
                            logger.error(f"Delete error: {str(e)}")
                
                with col2:
                    if st.button("❌ Cancelar", use_container_width=True):
                        st.info("Deleção cancelada")

else:
    st.warning("⚠️ Nenhum documento encontrado com os filtros selecionados.")

st.markdown("---")
st.caption("Desenvolvido com ❤️ para RAG")
