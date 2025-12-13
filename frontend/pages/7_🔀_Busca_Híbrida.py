"""Página de busca híbrida"""

import streamlit as st
import pandas as pd
from utils.session_manager import init_session_state, is_authenticated
from components.header import render_header
from services.query_service import get_query_service
from services.document_service import get_document_service
from utils.validators import validate_query
import logging

logger = logging.getLogger(__name__)

# Configurar página
st.set_page_config(
    page_title="Busca Híbrida - RAG",
    page_icon="🔀",
    layout="wide"
)

# Inicializar session state
init_session_state()

# Renderizar header
render_header()

st.subheader("🔀 Busca Híbrida")
st.caption("Combine busca semântica e por grafo para resultados mais completos")

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
        placeholder="Ex: Quais são os principais conceitos e suas relações?",
        height=100,
        help="Digite uma pergunta para busca híbrida"
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
            with st.spinner("Realizando busca híbrida..."):
                query_service = get_query_service()
                result = query_service.query_hybrid(
                    query=query,
                    document_id=selected_doc_id,
                    top_k=top_k
                )
            
            # Abas para diferentes visualizações
            tab1, tab2, tab3 = st.tabs(["💡 Resposta", "🔍 Semântica", "🌐 Grafo"])
            
            with tab1:
                st.subheader("Resposta")
                
                answer = result.get("answer", "Nenhuma resposta encontrada")
                st.info(answer)
                
                # Exibir modelo usado
                model_used = result.get("model_used", "desconhecido")
                st.caption(f"Modelo utilizado: {model_used}")
            
            with tab2:
                st.subheader("Resultados Semânticos")
                
                sources = result.get("sources", [])
                semantic_sources = [s for s in sources if s.get("metadata", {}).get("search_type") == "semantic"]
                
                if semantic_sources:
                    st.caption(f"Encontrados {len(semantic_sources)} resultados semânticos")
                    
                    for i, source in enumerate(semantic_sources, 1):
                        with st.expander(f"Resultado {i}", expanded=(i == 1)):
                            # Exibir texto
                            text = source.get("text", "N/A")
                            st.markdown(f"**Trecho:**\n\n{text}")
                            
                            # Exibir score
                            if source.get("score"):
                                score = source.get("score")
                                st.progress(score, text=f"Similaridade: {score:.2%}")
                else:
                    st.info("Nenhum resultado semântico encontrado")
            
            with tab3:
                st.subheader("Resultados do Grafo")
                
                sources = result.get("sources", [])
                graph_sources = [s for s in sources if s.get("metadata", {}).get("search_type") == "graph"]
                
                if graph_sources:
                    st.caption(f"Encontradas {len(graph_sources)} entidades/relacionamentos")
                    
                    # Separar entidades e relacionamentos
                    entities = [s for s in graph_sources if "entity" in s]
                    relationships = [s for s in graph_sources if "relationship" in s]
                    
                    if entities:
                        st.markdown("**Entidades:**")
                        entity_data = []
                        for entity in entities:
                            entity_data.append({
                                "Entidade": entity.get("entity", "N/A"),
                                "Tipo": entity.get("type", "N/A"),
                                "Descrição": entity.get("description", "N/A")[:80]
                            })
                        
                        if entity_data:
                            df = pd.DataFrame(entity_data)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    if relationships:
                        st.markdown("**Relacionamentos:**")
                        for rel in relationships:
                            st.caption(f"🔗 {rel.get('relationship', 'N/A')}")
                else:
                    st.info("Nenhum resultado do grafo encontrado")
        
        except Exception as e:
            st.error(f"❌ Erro ao realizar busca: {str(e)}")
            logger.error(f"Hybrid search error: {str(e)}")

st.markdown("---")

# Seção de informações
with st.expander("ℹ️ Como funciona a busca híbrida?"):
    st.markdown("""
    A busca híbrida combina dois tipos de busca:
    
    1. **Semântica**: Encontra conteúdo similar usando embeddings
    2. **Grafo**: Navega entidades e relacionamentos
    
    **Vantagens:**
    - Resultados mais completos e contextualizados
    - Combina relevância semântica com estrutura de conhecimento
    - Ideal para análises profundas
    - Melhor compreensão do domínio
    """)

with st.expander("💡 Dicas de busca"):
    st.markdown("""
    - **Use perguntas complexas**: Combine múltiplos conceitos
    - **Explore ambas as abas**: Compare resultados semânticos e estruturais
    - **Refine iterativamente**: Faça múltiplas buscas para explorar diferentes ângulos
    - **Combine com outras buscas**: Use semântica ou grafo isoladamente se necessário
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
    if st.button("💬 Chatbot", use_container_width=True):
        st.switch_page("pages/8_💬_Chatbot.py")

st.caption("Desenvolvido com ❤️ para RAG")
