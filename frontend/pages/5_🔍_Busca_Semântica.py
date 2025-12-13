"""Página de busca semântica"""

import streamlit as st
from utils.session_manager import init_session_state, is_authenticated
from components.header import render_header
from services.query_service import get_query_service
from services.document_service import get_document_service
from utils.validators import validate_query
from utils.formatters import truncate_text
import logging

logger = logging.getLogger(__name__)

# Configurar página
st.set_page_config(
    page_title="Busca Semântica - RAG",
    page_icon="🔍",
    layout="wide"
)

# Inicializar session state
init_session_state()

# Renderizar header
render_header()

st.subheader("🔍 Busca Semântica")
st.caption("Pesquise documentos por similaridade semântica")

st.markdown("---")

# Obter documentos processados
try:
    doc_service = get_document_service()
    documents = doc_service.list_documents()
    completed_docs = [d for d in documents if d.get("status") == "Completed"]
except Exception as e:
    st.error(f"❌ Erro ao carregar documentos: {str(e)}")
    st.stop()

if not completed_docs:
    st.warning("⚠️ Nenhum documento processado encontrado. Processe um documento primeiro.")
    if st.button("⚙️ Ir para Processamento"):
        st.switch_page("pages/3_⚙️_Processamento.py")
    st.stop()

# Formulário de busca
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Sua Pergunta")
    
    query = st.text_area(
        "Digite sua pergunta",
        placeholder="Ex: Quais são os principais benefícios?",
        height=100,
        help="Digite uma pergunta sobre os documentos"
    )

with col2:
    st.markdown("### Filtros")
    
    doc_options = {d["filename"]: d["document_id"] for d in completed_docs}
    selected_doc_name = st.selectbox(
        "Documento (opcional)",
        options=["Todos"] + list(doc_options.keys()),
        help="Deixe em branco para buscar em todos"
    )
    
    selected_doc_id = None if selected_doc_name == "Todos" else doc_options.get(selected_doc_name)
    
    top_k = st.slider(
        "Número de resultados",
        min_value=1,
        max_value=20,
        value=5,
        help="Quantos resultados retornar"
    )

st.markdown("---")

# Botão de busca
if st.button("🔍 Buscar", use_container_width=True, type="primary"):
    # Validar query
    if not query or not validate_query(query):
        st.error("❌ Digite uma pergunta válida (mínimo 3 caracteres)")
    else:
        try:
            with st.spinner("Buscando..."):
                query_service = get_query_service()
                result = query_service.query_semantic(
                    query=query,
                    document_id=selected_doc_id,
                    top_k=top_k
                )
            
            # Exibir resposta
            st.markdown("---")
            st.subheader("💡 Resposta")
            
            answer = result.get("answer", "Nenhuma resposta encontrada")
            st.info(answer)
            
            # Exibir modelo usado
            model_used = result.get("model_used", "desconhecido")
            st.caption(f"Modelo utilizado: {model_used}")
            
            # Exibir fontes
            sources = result.get("sources", [])
            
            if sources:
                st.markdown("---")
                st.subheader(f"📚 Fontes ({len(sources)})")
                
                for i, source in enumerate(sources, 1):
                    with st.expander(f"Fonte {i}", expanded=(i == 1)):
                        # Exibir texto
                        text = source.get("text", "N/A")
                        st.markdown(f"**Trecho:**\n\n{text}")
                        
                        # Exibir score se disponível
                        if source.get("score"):
                            score = source.get("score")
                            st.caption(f"Similaridade: {score:.2%}")
                        
                        # Exibir metadados
                        metadata = source.get("metadata", {})
                        if metadata:
                            st.caption(f"Tipo: {metadata.get('search_type', 'N/A')}")
            else:
                st.warning("⚠️ Nenhuma fonte encontrada para esta pergunta")
        
        except Exception as e:
            st.error(f"❌ Erro ao realizar busca: {str(e)}")
            logger.error(f"Search error: {str(e)}")

st.markdown("---")

# Seção de informações
with st.expander("ℹ️ Como funciona a busca semântica?"):
    st.markdown("""
    A busca semântica utiliza embeddings (representações vetoriais) dos documentos para encontrar
    conteúdo similar ao da sua pergunta, mesmo que as palavras não sejam exatamente iguais.
    
    **Vantagens:**
    - Encontra informações mesmo com palavras diferentes
    - Compreende o significado, não apenas palavras-chave
    - Resultados mais relevantes e contextualizados
    """)

with st.expander("💡 Dicas de busca"):
    st.markdown("""
    - **Seja específico**: Quanto mais detalhes, melhor o resultado
    - **Use linguagem natural**: Escreva como faria uma pergunta normal
    - **Combine conceitos**: Mencione múltiplos tópicos se relevante
    - **Refine se necessário**: Ajuste a pergunta se não encontrar o que procura
    """)

st.markdown("---")

# Navegação
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🌐 Busca por Grafo", use_container_width=True):
        st.switch_page("pages/6_🌐_Busca_Grafo.py")

with col2:
    if st.button("🔀 Busca Híbrida", use_container_width=True):
        st.switch_page("pages/7_🔀_Busca_Híbrida.py")

with col3:
    if st.button("💬 Chatbot", use_container_width=True):
        st.switch_page("pages/8_💬_Chatbot.py")

st.caption("Desenvolvido com ❤️ para RAG")
