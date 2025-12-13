"""Componente de header"""

import streamlit as st
from utils.session_manager import clear_session
from services.api_client import get_api_client
import logging

logger = logging.getLogger(__name__)


def render_header():
    """Renderiza header da aplicação"""
    col1, col2 = st.columns([1, 0.1])
    
    with col1:
        st.title("🧠 RAG - Sistema de Documentos IA")
        st.caption("Retrieval-Augmented Generation")
    
    st.markdown("---")


def render_health_check():
    """Renderiza verificação de saúde da API"""
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
                if "error" in str(neo4j_status).lower():
                    st.metric("Neo4j", "❌ Erro")
                else:
                    st.metric("Neo4j", "✅ OK")
            
            with col3:
                redis_status = health.get("redis", "unknown")
                if "error" in str(redis_status).lower():
                    st.metric("Redis", "❌ Erro")
                else:
                    st.metric("Redis", "✅ OK")
    
    except Exception as e:
        st.error(f"❌ Erro ao verificar API: {str(e)}")
        logger.error(f"Health check error: {str(e)}")
