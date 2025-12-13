"""Componentes de cards"""

import streamlit as st


def render_card(title: str, description: str, icon: str, page: str) -> bool:
    """
    Renderiza um card com título, descrição e botão
    
    Args:
        title: Título do card
        description: Descrição do card
        icon: Emoji ou ícone
        page: Caminho da página para navegar
    
    Returns:
        True se botão foi clicado
    """
    with st.container(border=True):
        col1, col2 = st.columns([0.1, 0.9])
        
        with col1:
            st.markdown(f"# {icon}")
        
        with col2:
            st.subheader(title)
            st.caption(description)
        
        if st.button("Acessar Módulo", key=title, use_container_width=True):
            st.switch_page(page)
            return True
    
    return False


def render_dashboard_grid():
    """Renderiza grid de cards do dashboard"""
    cards = [
        {
            "title": "Vetorização",
            "description": "Documentos convertidos em vetores para busca semântica",
            "icon": "⚡",
            "page": "pages/3_⚙️_Processamento.py"
        },
        {
            "title": "Busca Inteligente",
            "description": "Encontre informações por similaridade. Não apenas palavras-chave",
            "icon": "🔍",
            "page": "pages/7_🔀_Busca_Híbrida.py"
        },
        {
            "title": "IA Especialista",
            "description": "Chatbot especializado em estética com base nos documentos",
            "icon": "💬",
            "page": "pages/8_💬_Chatbot.py"
        },
        {
            "title": "Gestão Completa",
            "description": "Organize e gerencie todos os documentos em um só lugar",
            "icon": "📋",
            "page": "pages/4_📋_Gestão.py"
        },
        {
            "title": "Upload de Documentos",
            "description": "Envie documentos PDF para vetorização e indexação",
            "icon": "📤",
            "page": "pages/2_📤_Upload.py"
        },
        {
            "title": "Busca Semântica",
            "description": "Pesquise documentos por similaridade semântica",
            "icon": "🔍",
            "page": "pages/5_🔍_Busca_Semântica.py"
        }
    ]
    
    # Renderizar em grid 3x2
    for i in range(0, len(cards), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(cards):
                card = cards[i + j]
                with col:
                    render_card(
                        card["title"],
                        card["description"],
                        card["icon"],
                        card["page"]
                    )
