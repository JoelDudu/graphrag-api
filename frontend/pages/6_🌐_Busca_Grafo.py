"""Página de busca por grafo"""

import streamlit as st
from utils.session_manager import init_session_state, is_authenticated
from components.header import render_header
from services.query_service import get_query_service
from services.document_service import get_document_service
from utils.validators import validate_query
import logging

logger = logging.getLogger(__name__)

# Configurar página
st.set_page_config(
    page_title="Busca Grafo - RAG",
    page_icon="🌐",
    layout="wide"
)

# Inicializar session state
init_session_state()

# Renderizar header
render_header()

st.subheader("🌐 Busca por Grafo")
st.caption("Navegue pelo grafo de conhecimento (entidades e relacionamentos)")

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
        placeholder="Ex: Quais são as entidades principais?",
        height=100,
        help="Digite uma pergunta para explorar o grafo"
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
        help="Quantas entidades retornar"
    )

st.markdown("---")

# Botão de busca
if st.button("🔍 Buscar", use_container_width=True, type="primary"):
    # Validar query
    if not query or not validate_query(query):
        st.error("❌ Digite uma pergunta válida (mínimo 3 caracteres)")
    else:
        try:
            with st.spinner("Buscando no grafo..."):
                query_service = get_query_service()
                result = query_service.query_graph(
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
            
            # Exibir fontes (entidades e relacionamentos)
            sources = result.get("sources", [])
            
            if sources:
                st.markdown("---")
                
                # Separar entidades e relacionamentos
                entities = [s for s in sources if "entity" in s]
                relationships = [s for s in sources if "relationship" in s]
                
                # Abas para entidades e relacionamentos
                tab1, tab2 = st.tabs(["🏷️ Entidades", "🔗 Relacionamentos"])
                
                with tab1:
                    if entities:
                        st.subheader(f"Entidades Encontradas ({len(entities)})")
                        
                        # Criar tabela de entidades
                        entity_data = []
                        for entity in entities:
                            entity_data.append({
                                "Entidade": entity.get("entity", "N/A"),
                                "Tipo": entity.get("type", "N/A"),
                                "Descrição": entity.get("description", "N/A")[:100]
                            })
                        
                        if entity_data:
                            import pandas as pd
                            df = pd.DataFrame(entity_data)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhuma entidade encontrada")
                
                with tab2:
                    if relationships:
                        st.subheader(f"Relacionamentos ({len(relationships)})")
                        
                        for i, rel in enumerate(relationships, 1):
                            with st.expander(f"Relacionamento {i}"):
                                st.markdown(f"**Tipo:** {rel.get('relationship', 'N/A')}")
                                st.markdown(f"**Texto:** {rel.get('text', 'N/A')}")
                    else:
                        st.info("Nenhum relacionamento encontrado")
            else:
                st.warning("⚠️ Nenhuma entidade encontrada para esta pergunta")
        
        except Exception as e:
            st.error(f"❌ Erro ao realizar busca: {str(e)}")
            logger.error(f"Graph search error: {str(e)}")

st.markdown("---")

# Seção de informações
with st.expander("ℹ️ Como funciona a busca por grafo?"):
    st.markdown("""
    A busca por grafo navega pelo grafo de conhecimento extraído dos documentos,
    encontrando entidades (pessoas, lugares, conceitos) e seus relacionamentos.
    
    **Vantagens:**
    - Explora conexões entre conceitos
    - Encontra padrões e relacionamentos
    - Visualiza a estrutura do conhecimento
    - Ideal para análise de redes
    """)

with st.expander("💡 Dicas de busca"):
    st.markdown("""
    - **Busque por conceitos**: Procure por nomes, lugares, tópicos
    - **Explore relacionamentos**: Veja como as entidades se conectam
    - **Combine buscas**: Use múltiplas buscas para explorar diferentes aspectos
    - **Refine resultados**: Ajuste a pergunta para focar em áreas específicas
    """)

st.markdown("---")

# Navegação
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Busca Semântica", use_container_width=True):
        st.switch_page("pages/5_🔍_Busca_Semântica.py")

with col2:
    if st.button("🔀 Busca Híbrida", use_container_width=True):
        st.switch_page("pages/7_🔀_Busca_Híbrida.py")

with col3:
    if st.button("💬 Chatbot", use_container_width=True):
        st.switch_page("pages/8_💬_Chatbot.py")

st.caption("Desenvolvido com ❤️ para RAG")
