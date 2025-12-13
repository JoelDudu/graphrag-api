"""Página de chatbot especialista"""

import streamlit as st
from utils.session_manager import init_session_state, is_authenticated
from components.header import render_header
from components.chat import render_chat_interface, render_chat_controls

# Configurar página
st.set_page_config(
    page_title="Chatbot - RAG",
    page_icon="💬",
    layout="wide"
)

# Inicializar session state
init_session_state()

# Renderizar header
render_header()

st.subheader("💬 Chatbot Especialista")
st.caption("Converse com um assistente especializado em seus documentos")

st.markdown("---")

# Renderizar interface de chat
render_chat_interface()

st.markdown("---")

# Renderizar controles
render_chat_controls()

st.markdown("---")

# Seção de informações
with st.expander("ℹ️ Como usar o chatbot?"):
    st.markdown("""
    1. **Digite sua pergunta**: Use linguagem natural
    2. **Pressione Enter**: Envie a mensagem
    3. **Receba resposta**: O assistente responde com base nos documentos
    4. **Explore fontes**: Clique em "Fontes" para ver os trechos usados
    5. **Continue conversando**: Faça perguntas de acompanhamento
    
    **Dicas:**
    - O chatbot mantém contexto da conversa
    - Você pode fazer perguntas de acompanhamento
    - As respostas são baseadas nos documentos processados
    - Use "Limpar Chat" para começar uma nova conversa
    """)

with st.expander("💡 Exemplos de perguntas"):
    st.markdown("""
    - "Quais são os principais tópicos?"
    - "Explique o conceito de X"
    - "Como X se relaciona com Y?"
    - "Quais são os benefícios de X?"
    - "Resuma o documento em 3 pontos"
    """)

st.markdown("---")

# Navegação
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Busca Semântica", use_container_width=True):
        st.switch_page("pages/5_🔍_Busca_Semântica.py")

with col2:
    if st.button("🌐 Busca Grafo", use_container_width=True):
        st.switch_page("pages/6_🌐_Busca_Grafo.py")

with col3:
    if st.button("🔀 Busca Híbrida", use_container_width=True):
        st.switch_page("pages/7_🔀_Busca_Híbrida.py")

st.caption("Desenvolvido com ❤️ para RAG")
