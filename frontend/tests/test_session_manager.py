"""Testes para session manager"""

import pytest
import streamlit as st
from utils.session_manager import (
    init_session_state,
    is_authenticated,
    get_token,
    set_token,
    clear_session,
    add_chat_message,
    get_chat_messages,
    clear_chat
)


def test_init_session_state():
    """Testa inicialização de session state"""
    init_session_state()
    
    assert st.session_state.token is None
    assert st.session_state.user is None
    assert st.session_state.authenticated is False
    assert st.session_state.chat_messages == []
    assert st.session_state.recent_documents == []


def test_is_authenticated_false():
    """Testa is_authenticated quando não autenticado"""
    st.session_state.token = None
    assert is_authenticated() is False


def test_is_authenticated_true():
    """Testa is_authenticated quando autenticado"""
    st.session_state.token = "test_token"
    assert is_authenticated() is True


def test_get_token():
    """Testa get_token"""
    st.session_state.token = "my_token"
    assert get_token() == "my_token"


def test_set_token():
    """Testa set_token"""
    set_token("new_token")
    assert st.session_state.token == "new_token"
    assert st.session_state.authenticated is True


def test_clear_session():
    """Testa clear_session"""
    st.session_state.token = "token"
    st.session_state.user = {"name": "Test"}
    st.session_state.chat_messages = [{"role": "user", "content": "Hi"}]
    
    clear_session()
    
    assert st.session_state.token is None
    assert st.session_state.user is None
    assert st.session_state.authenticated is False
    assert st.session_state.chat_messages == []


def test_add_chat_message():
    """Testa add_chat_message"""
    st.session_state.chat_messages = []
    
    add_chat_message("user", "Hello")
    assert len(st.session_state.chat_messages) == 1
    assert st.session_state.chat_messages[0]["role"] == "user"
    assert st.session_state.chat_messages[0]["content"] == "Hello"


def test_add_chat_message_with_sources():
    """Testa add_chat_message com sources"""
    st.session_state.chat_messages = []
    sources = [{"text": "Source 1"}]
    
    add_chat_message("assistant", "Response", sources)
    assert st.session_state.chat_messages[0]["sources"] == sources


def test_get_chat_messages():
    """Testa get_chat_messages"""
    st.session_state.chat_messages = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello"}
    ]
    
    messages = get_chat_messages()
    assert len(messages) == 2


def test_clear_chat():
    """Testa clear_chat"""
    st.session_state.chat_messages = [{"role": "user", "content": "Hi"}]
    
    clear_chat()
    assert st.session_state.chat_messages == []
