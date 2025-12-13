"""Componente de chat"""

import streamlit as st
from utils.session_manager import get_chat_messages, add_chat_message, clear_chat
from services.query_service import get_query_service
from utils.validators import validate_query
import logging

logger = logging.getLogger(__name__)


def render_chat_interface():
    """Renderiza interface de chat"""
    
    # Exibir histórico de mensagens
    messages = get_chat_messages()
    
    for message in messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Exibir fontes se disponível
            if message.get("sources"):
                with st.expander("📚 Fontes"):
                    for source in message["sources"]:
                        text = source.get("text", "N/A")
                        if len(text) > 200:
                            text = text[:200] + "..."
                        st.caption(text)
    
    # Input de mensagem
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Validar entrada
        if not validate_query(prompt):
            st.error("❌ Mensagem muito curta (mínimo 3 caracteres)")
            return
        
        # Adicionar mensagem do usuário
        add_chat_message("user", prompt)
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Processar resposta
        try:
            with st.spinner("Processando..."):
                query_service = get_query_service()
                result = query_service.query_semantic(query=prompt, top_k=3)
            
            # Adicionar resposta do assistente
            answer = result.get("answer", "Desculpe, não consegui processar sua pergunta.")
            sources = result.get("sources", [])
            
            add_chat_message("assistant", answer, sources)
            
            with st.chat_message("assistant"):
                st.write(answer)
                
                if sources:
                    with st.expander("📚 Fontes"):
                        for source in sources:
                            text = source.get("text", "N/A")
                            if len(text) > 200:
                                text = text[:200] + "..."
                            st.caption(text)
            
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Erro ao processar mensagem: {str(e)}")
            logger.error(f"Chat error: {str(e)}")


def render_chat_controls():
    """Renderiza controles do chat"""
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Limpar Chat", use_container_width=True):
            clear_chat()
            st.rerun()
    
    with col2:
        messages = get_chat_messages()
        st.caption(f"Mensagens: {len(messages)}")
