"""Entry point da aplicação Streamlit"""

import streamlit as st
import logging
from utils.session_manager import init_session_state
from services.api_client import get_api_client

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar página
st.set_page_config(
    page_title="RAG Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session state
init_session_state()

# Marcar como autenticado (sem login real)
st.session_state.authenticated = True


def render_dashboard():
    """Renderiza dashboard principal"""
    # Header
    st.title("🧠 RAG - Sistema de Documentos IA")
    st.caption("Retrieval-Augmented Generation")
    
    st.markdown("---")
    
    # Health check
    try:
        with st.spinner("Verificando API..."):
            client = get_api_client()
            health = client.get("/health")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                api_status = "✅ OK" if health.get("api") == "ok" else "❌ Erro"
                st.metric("API", api_status)
            with col2:
                neo4j_status = health.get("neo4j", "unknown")
                st.metric("Neo4j", neo4j_status)
            with col3:
                redis_status = health.get("redis", "unknown")
                st.metric("Redis", redis_status)
    
    except Exception as e:
        st.error(f"❌ Erro ao verificar API: {str(e)}")
    
    st.markdown("---")
    
    # Dashboard cards
    st.subheader("Módulos Disponíveis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown("### ⚡ Vetorização")
            st.caption("Documentos convertidos em vetores para busca semântica")
            if st.button("Acessar Módulo", key="vectorization", use_container_width=True):
                st.switch_page("pages/3_⚙️_Processamento.py")
    
    with col2:
        with st.container(border=True):
            st.markdown("### 🔍 Busca Inteligente")
            st.caption("Encontre informações por similaridade. Não apenas palavras-chave")
            if st.button("Acessar Módulo", key="intelligent_search", use_container_width=True):
                st.switch_page("pages/7_🔀_Busca_Híbrida.py")
    
    with col3:
        with st.container(border=True):
            st.markdown("### 💬 IA Especialista")
            st.caption("Chatbot especializado em estética com base nos documentos")
            if st.button("Acessar Módulo", key="specialist_ai", use_container_width=True):
                st.switch_page("pages/8_💬_Chatbot.py")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown("### 📋 Gestão Completa")
            st.caption("Organize e gerencie todos os documentos em um só lugar")
            if st.button("Acessar Módulo", key="complete_management", use_container_width=True):
                st.switch_page("pages/4_📋_Gestão.py")
    
    with col2:
        with st.container(border=True):
            st.markdown("### 📤 Upload de Documentos")
            st.caption("Envie documentos PDF para vetorização e indexação")
            if st.button("Acessar Módulo", key="upload", use_container_width=True):
                st.switch_page("pages/2_📤_Upload.py")
    
    with col3:
        with st.container(border=True):
            st.markdown("### 🔍 Busca Semântica")
            st.caption("Pesquise documentos por similaridade semântica")
            if st.button("Acessar Módulo", key="semantic_search", use_container_width=True):
                st.switch_page("pages/5_🔍_Busca_Semântica.py")


def main():
    """Função principal"""
    render_dashboard()


if __name__ == "__main__":
    main()
