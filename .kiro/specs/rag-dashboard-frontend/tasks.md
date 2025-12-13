# Implementation Plan - RAG Dashboard Frontend

## Overview
Plano de implementação para o RAG Dashboard Frontend em Streamlit, seguindo abordagem test-driven e incremental. Cada tarefa constrói sobre a anterior, começando pela infraestrutura base e evoluindo para funcionalidades completas.

---

## Phase 1: Setup e Infraestrutura Base

- [x] 1. Configurar estrutura de projeto e dependências


  - Criar diretório `frontend/` com estrutura de pastas (pages, components, services, utils, config)
  - Criar `requirements.txt` com dependências: streamlit, requests, python-dotenv, pytest
  - Criar `.env` com variáveis: API_URL, API_TIMEOUT, LOG_LEVEL
  - Criar `.streamlit/config.toml` com tema e configurações
  - Criar `README.md` com instruções de setup
  - _Requirements: 10.1, 10.2, 10.3_



- [ ] 2. Implementar cliente HTTP com autenticação
  - Criar `services/api_client.py` com classe `APIClient`
  - Implementar método `login(email, password)` que retorna token JWT
  - Implementar interceptador para incluir token em todas as requisições
  - Implementar retry automático (máx 3 tentativas) para erros de rede
  - Implementar tratamento de erro 401 (token expirado)


  - Criar testes unitários para `APIClient`
  - _Requirements: 10.1, 10.2_

- [ ] 3. Implementar gerenciamento de session state
  - Criar `utils/session_manager.py` com funções para inicializar session state
  - Implementar `init_session_state()` que cria: token, user, authenticated, chat_history, recent_documents


  - Implementar `is_authenticated()` que verifica se token existe
  - Implementar `clear_session()` para logout
  - Criar testes unitários
  - _Requirements: 10.1_

- [ ] 4. Implementar página de login
  - Criar `app.py` como entry point
  - Implementar verificação de autenticação no início
  - Se não autenticado, exibir formulário de login com email e senha
  - Validar entrada (email válido, senha não vazia)
  - Chamar `auth_service.login()` ao clicar "Entrar"
  - Armazenar token em `st.session_state.token`
  - Redirecionar para dashboard após sucesso
  - Exibir mensagem de erro se falhar


  - Criar testes de integração
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9_

---

## Phase 2: Dashboard e Navegação



- [ ] 5. Implementar componente de header
  - Criar `components/header.py` com função `render_header()`
  - Exibir logo, título "🧠 RAG - Sistema de Documentos IA" e descrição
  - Exibir botão "Logout" que limpa session e redireciona para login
  - Fazer health check GET /health ao carregar
  - Exibir status da API (verde se ok, vermelho se erro)


  - Criar testes unitários
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 6. Implementar componente de cards
  - Criar `components/cards.py` com função `render_card(title, description, icon, page)`
  - Cada card com border, ícone (emoji), título, descrição
  - Botão "Acessar Módulo" que navega para página
  - Usar `st.container(border=True)` para styling
  - Criar testes unitários
  - _Requirements: 1.1, 1.2_

- [x] 7. Implementar dashboard principal


  - Criar `pages/1_🏠_Dashboard.py`
  - Chamar `render_header()` do componente
  - Criar grid de 6 cards em 2 linhas x 3 colunas usando `st.columns()`
  - Cards: Vetorização, Busca Inteligente, IA Especialista, Gestão Completa, Upload, Busca Semântica
  - Cada card navega para página correspondente
  - Fazer GET /health ao carregar e exibir status
  - Criar testes de integração
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_



---

## Phase 3: Upload de Documentos

- [ ] 8. Implementar serviço de documentos
  - Criar `services/document_service.py`
  - Implementar `upload_document(file)` que faz POST /upload
  - Implementar `list_documents()` que faz GET /documents
  - Implementar `get_document_status(document_id)` que faz GET /status/{document_id}
  - Implementar `delete_document(document_id)` que faz DELETE /documents/{document_id}
  - Implementar `get_doc_types()` que faz GET /doc-types
  - Criar testes unitários com mocks
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_



- [ ] 9. Implementar página de upload
  - Criar `pages/2_📤_Upload.py`
  - Exibir `st.file_uploader()` para PDF
  - Validar tipo de arquivo (apenas PDF)
  - Ao selecionar arquivo, fazer POST /upload via `document_service`
  - Exibir document_id retornado
  - Exibir mensagem de sucesso


  - Armazenar em `st.session_state.recent_documents`
  - Oferecer botão "Processar Agora" que navega para página de processamento
  - Exibir lista de documentos recém-enviados
  - Criar testes de integração
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

---

## Phase 4: Processamento de Documentos

- [ ] 10. Implementar serviço de status com polling
  - Criar `services/status_service.py`
  - Implementar `poll_status(document_id, interval=5, max_attempts=120)` que faz polling em GET /status
  - Retornar status atualizado a cada intervalo
  - Parar quando status === 'Completed' ou 'Error'


  - Implementar timeout se max_attempts atingido
  - Criar testes unitários
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ] 11. Implementar página de processamento
  - Criar `pages/3_⚙️_Processamento.py`
  - Exibir `st.selectbox()` para selecionar documento (documentos com status 'Pending')
  - Exibir `st.selectbox()` para modelo (claude, openai, kimi)
  - Fazer GET /doc-types e exibir `st.selectbox()` para tipo de documento
  - Botão "Processar" que faz POST /process
  - Iniciar polling com `status_service.poll_status()`
  - Exibir `st.progress()` baseado no campo progress
  - Quando completo, exibir resumo com `st.metric()`: chunks, entidades, relacionamentos
  - Se erro, exibir mensagem de erro
  - Criar testes de integração
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_



---

## Phase 5: Gestão de Documentos

- [ ] 12. Implementar página de gestão
  - Criar `pages/4_📋_Gestão.py`


  - Fazer GET /documents ao carregar
  - Exibir `st.dataframe()` com colunas: Nome, Status, Progresso, Modelo, Data
  - Implementar filtro por status com `st.multiselect()`
  - Implementar busca por nome com `st.text_input()`
  - Adicionar coluna de ações com botões "Visualizar" e "Deletar"
  - Ao clicar "Deletar", exibir confirmação com `st.confirmation_dialog()`
  - Se confirmado, fazer DELETE /documents/{document_id}
  - Atualizar tabela após deleção
  - Exibir mensagem "Nenhum documento encontrado" se lista vazia
  - Criar testes de integração
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

---



## Phase 6: Busca Semântica

- [ ] 13. Implementar serviço de query
  - Criar `services/query_service.py`
  - Implementar `query_semantic(query, document_id=None, top_k=5)` que faz POST /query com search_type="semantic"
  - Implementar `query_graph(query, document_id=None, top_k=5)` que faz POST /query com search_type="graph"
  - Implementar `query_hybrid(query, document_id=None, top_k=5)` que faz POST /query com search_type="hybrid"
  - Retornar resposta e fontes
  - Criar testes unitários com mocks
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [ ] 14. Implementar página de busca semântica
  - Criar `pages/5_🔍_Busca_Semântica.py`
  - Exibir `st.text_area()` para query
  - Exibir `st.selectbox()` para documento (opcional)


  - Botão "Buscar" que chama `query_service.query_semantic()`
  - Exibir resposta com `st.info()` ou `st.success()`
  - Para cada fonte, exibir `st.expander()` com trecho de texto
  - Exibir `st.spinner()` durante busca
  - Se erro, exibir mensagem de erro
  - Criar testes de integração
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

---

## Phase 7: Busca por Grafo

- [ ] 15. Implementar página de busca por grafo
  - Criar `pages/6_🌐_Busca_Grafo.py`
  - Exibir `st.text_area()` para query


  - Botão "Buscar" que chama `query_service.query_graph()`
  - Exibir resposta com `st.info()`
  - Usar `st.tabs()` para "Entidades" e "Relacionamentos"
  - Aba Entidades: exibir `st.dataframe()` com colunas: Entidade, Tipo, Descrição
  - Aba Relacionamentos: exibir lista de relacionamentos
  - Exibir `st.spinner()` durante busca
  - Se erro, exibir mensagem de erro


  - Criar testes de integração
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

---

## Phase 8: Busca Híbrida

- [ ] 16. Implementar página de busca híbrida
  - Criar `pages/7_🔀_Busca_Híbrida.py`
  - Exibir `st.text_area()` para query
  - Botão "Buscar" que chama `query_service.query_hybrid()`
  - Usar `st.tabs()` para "Resposta", "Semântica" e "Grafo"
  - Aba Resposta: exibir resposta com `st.info()`


  - Aba Semântica: exibir `st.dataframe()` com trechos e scores
  - Aba Grafo: exibir entidades e relacionamentos
  - Exibir `st.spinner()` durante busca
  - Se erro, exibir mensagem de erro
  - Criar testes de integração
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

---



## Phase 9: Chatbot Especialista

- [ ] 17. Implementar componente de chat
  - Criar `components/chat.py` com função `render_chat_interface()`
  - Exibir histórico de mensagens com `st.chat_message()`
  - Implementar `st.chat_input()` para input de mensagem
  - Ao enviar, adicionar à `st.session_state.chat_messages`
  - Exibir fontes em `st.expander()` para cada resposta
  - Criar testes unitários


  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

- [ ] 18. Implementar página de chatbot
  - Criar `pages/8_💬_Chatbot.py`
  - Inicializar `st.session_state.chat_messages` se não existe
  - Chamar `render_chat_interface()` do componente
  - Ao enviar mensagem, chamar `query_service.query_semantic()` com a mensagem
  - Adicionar resposta ao histórico
  - Exibir `st.spinner()` durante processamento
  - Botão "Limpar Chat" que limpa `st.session_state.chat_messages`


  - Criar testes de integração
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

---

## Phase 10: Testes e Refinamento

- [ ] 19. Implementar testes unitários completos
  - Criar `tests/` com estrutura espelhando `services/`, `components/`, `utils/`
  - Testes para `api_client.py`: login, retry, error handling
  - Testes para `document_service.py`: upload, list, delete
  - Testes para `query_service.py`: semantic, graph, hybrid
  - Testes para `status_service.py`: polling logic
  - Testes para funções utilitárias: formatters, validators


  - Executar com `pytest` e gerar relatório de cobertura
  - Mínimo 70% de cobertura
  - _Requirements: 11.1, 11.2, 11.3_

- [ ] 20. Implementar testes de integração
  - Criar testes que simulam fluxos completos
  - Teste: upload → processamento → busca
  - Teste: login → acesso protegido → logout




  - Teste: busca semântica → exibição de resultados
  - Teste: busca híbrida → abas funcionando
  - Teste: chat → histórico mantido
  - Usar mocks para API
  - Executar com `pytest`
  - _Requirements: 11.1, 11.2, 11.3_

- [ ] 21. Implementar validação de responsividade
  - Testar layout em diferentes tamanhos de tela (desktop, tablet, mobile)
  - Verificar se componentes se adaptam corretamente
  - Testar navegação em mobile (sidebar colapsável)
  - Testar inputs em mobile (teclado virtual)
  - Documentar breakpoints e comportamentos
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

---

## Phase 11: Documentação e Deploy

- [ ] 22. Criar documentação de desenvolvimento
  - Criar `DEVELOPMENT.md` com:
    - Setup local (clone, pip install, .env)
    - Como rodar a aplicação (`streamlit run app.py`)
    - Como rodar testes (`pytest`)
    - Estrutura de pastas explicada
    - Convenções de código
    - Como adicionar nova página
    - Como adicionar novo serviço
  - Criar `API_INTEGRATION.md` com:
    - Endpoints consumidos
    - Fluxo de autenticação
    - Tratamento de erros
    - Exemplos de requisições
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 23. Preparar para deploy
  - Criar `Dockerfile` para containerização
  - Criar `.dockerignore`
  - Criar `docker-compose.yml` para rodar com API
  - Criar `Procfile` para Heroku (opcional)
  - Criar `.github/workflows/` para CI/CD (opcional)
  - Testar build local com Docker
  - Documentar variáveis de ambiente necessárias
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 24. Refinamento final e otimizações
  - Revisar código para melhorias
  - Adicionar caching com `@st.cache_data` para dados estáticos
  - Adicionar caching com `@st.cache_resource` para conexões
  - Otimizar requisições à API (evitar duplicatas)
  - Melhorar mensagens de erro e feedback do usuário
  - Testar performance em conexão lenta
  - Documentar limitações conhecidas
  - _Requirements: 1.1, 1.2, 1.3, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

---

## Notes

- Cada tarefa deve ser testada antes de passar para a próxima
- Usar mocks para API em testes para não depender do backend
- Manter session state limpo entre testes
- Documentar decisões de design durante implementação
- Fazer commits pequenos e frequentes
- Revisar código antes de mergear
