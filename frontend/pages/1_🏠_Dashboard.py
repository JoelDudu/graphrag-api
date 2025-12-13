"""Dashboard principal"""

import streamlit as st
from utils.session_manager import init_session_state, is_authenticated
from components.header import render_header, render_health_check
from components.cards import render_dashboard_grid

# Configurar página
st.set_page_config(
    page_title="Dashboard - RAG",
    page_icon="🏠",
    layout="wide"
)

# Inicializar session state
init_session_state()

# Renderizar header
render_header()

# Renderizar health check
st.subheader("Status do Sistema")
render_health_check()

st.markdown("---")

# Renderizar grid de cards
st.subheader("Módulos Disponíveis")
render_dashboard_grid()

st.markdown("---")
st.caption("Desenvolvido com ❤️ para RAG")
