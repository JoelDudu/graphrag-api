"""Gerenciamento de session state do Streamlit"""

import streamlit as st


def init_session_state():
    """Inicializa session state com valores padrão"""
    if "token" not in st.session_state:
        st.session_state.token = None
    
    if "user" not in st.session_state:
        st.session_state.user = None
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    if "recent_documents" not in st.session_state:
        st.session_state.recent_documents = []
    
    if "selected_document" not in st.session_state:
        st.session_state.selected_document = None


def is_authenticated() -> bool:
    """Verifica se usuário está autenticado"""
    return st.session_state.get("token") is not None


def get_token() -> str | None:
    """Retorna token de autenticação"""
    return st.session_state.get("token")


def set_token(token: str):
    """Define token de autenticação"""
    st.session_state.token = token
    st.session_state.authenticated = True


def clear_session():
    """Limpa session state (logout)"""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.authenticated = False
    st.session_state.chat_messages = []
    st.session_state.recent_documents = []


def add_chat_message(role: str, content: str, sources: list = None):
    """Adiciona mensagem ao histórico de chat"""
    message = {
        "role": role,
        "content": content,
        "sources": sources or []
    }
    st.session_state.chat_messages.append(message)


def get_chat_messages() -> list:
    """Retorna histórico de chat"""
    return st.session_state.get("chat_messages", [])


def clear_chat():
    """Limpa histórico de chat"""
    st.session_state.chat_messages = []
