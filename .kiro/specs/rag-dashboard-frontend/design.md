# Design Document - RAG Dashboard Frontend

## Overview

O RAG Dashboard Frontend é uma aplicação web construída com **Streamlit**, que consome a API GraphRAG v3. Streamlit permite desenvolvimento rápido de dashboards interativos em Python puro, sem necessidade de HTML/CSS/JavaScript. A arquitetura segue padrões de Streamlit com separação clara entre páginas, componentes reutilizáveis e serviços de API.

**Stack Tecnológico:**
- **Framework**: Streamlit (dashboard web em Python)
- **HTTP Client**: Requests com session management
- **Autenticação**: JWT com session state
- **State Management**: Streamlit Session State
- **Componentes**: Streamlit built-in + Streamlit Components customizados
- **Real-time Updates**: Polling com st.rerun()
- **Chat**: Streamlit chat interface nativa
- **Styling**: Streamlit theming + CSS customizado

## Architecture

```
frontend/
├── app.py                   # Entry point principal
├── pages/                   # Páginas Streamlit (multi-page)
│   ├── 1_🏠_Dashboard.py
│   ├── 2_📤_Upload.py
│   ├── 3_⚙️_Processamento.py
│   ├── 4_📋_Gestão.py
│   ├── 5_🔍_Busca_Semântica.py
│   ├── 6_🌐_Busca_Grafo.py
│   ├── 7_🔀_Busca_Híbrida.py
│   └── 8_💬_Chatbot.py
├── components/              # Componentes reutilizáveis
│   ├── header.py           # Header com navegação
│   ├── sidebar.py          # Sidebar com links
│   ├── cards.py            # Card components
│   ├── forms.py            # Formulários
│   ├── modals.py           # Modais
│   └── chat.py             # Chat interface
├── services/                # Lógica de API e negócio
│   ├── api_client.py       # Cliente HTTP com autenticação
│   ├── auth_service.py     # Autenticação
│   ├── document_service.py # Operações de documentos
│   ├── query_service.py    # Operações de busca
│   └── status_service.py   # Polling de status
├── utils/                   # Funções utilitárias
│   ├── formatters.py       # Formatação de dados
│   ├── validators.py       # Validação de entrada
│   ├── constants.py        # Constantes
│   └── session_manager.py  # Gerenciamento de session state
├── config/                  # Configuração
│   ├── settings.py         # Variáveis de ambiente
│   └── theme.py            # Tema Streamlit
├── requirements.txt
├── .streamlit/
│   └── config.toml         # Configuração Streamlit
└── .env
```

## Components and Interfaces

### 1. Autenticação (app.py)

**Login Flow**
- Página de login com email e senha
- Validação de entrada
- Chamada para `auth_service.login()`
- Armazenamento de JWT em `st.session_state`
- Redirecionamento para dashboard após sucesso

**Session State**
```python
st.session_state.token = None  # JWT token
st.session_state.user = None   # User info
st.session_state.is_authenticated = False
```

### 2. Dashboard Principal (pages/1_🏠_Dashboard.py)

**Dashboard Page**
- Grid de 6 cards com emojis (Vetorização, Busca Inteligente, IA Especialista, Gestão Completa, Upload, Busca Semântica)
- Cada card com título, descrição e botão "Acessar Módulo"
- Health check da API ao carregar
- Navegação para páginas via `st.page_link()`

### 3. Upload de Documentos (pages/2_📤_Upload.py)

**Upload Page**
- `st.file_uploader()` para upload de PDF
- Validação de tipo de arquivo
- Exibição de progresso com `st.progress()`
- Listagem de documentos recém-enviados
- Botão para iniciar processamento

### 4. Processamento (pages/3_⚙️_Processamento.py)

**Processing Page**
- `st.selectbox()` para documento (documentos pendentes)
- `st.selectbox()` para modelo (claude, openai, kimi)
- `st.selectbox()` para tipo de documento (carregado de GET /doc-types)
- Botão "Processar"
- `st.progress()` com status em tempo real
- Resumo de resultados com `st.metric()` (chunks, entidades, relacionamentos)

**Polling Logic**
```python
def poll_status(document_id: str, interval: int = 5):
    while True:
        status = status_service.get_status(document_id)
        if status['status'] in ['Completed', 'Error']:
            break
        time.sleep(interval)
        st.rerun()
```

### 5. Gestão de Documentos (pages/4_📋_Gestão.py)

**Management Page**
- `st.dataframe()` com colunas: Nome, Status, Progresso, Modelo, Data
- `st.selectbox()` para filtrar por status
- `st.text_input()` para busca por nome
- Botões de ação: Visualizar detalhes, Deletar
- `st.confirmation_dialog()` para confirmação de deleção
- Atualização em tempo real com polling

### 6. Busca Semântica (pages/5_🔍_Busca_Semântica.py)

**Semantic Search Page**
- `st.text_area()` para query
- `st.selectbox()` para documento (opcional)
- Botão "Buscar"
- Exibição de resposta com `st.info()` ou `st.success()`
- `st.expander()` para cada fonte com trecho de texto
- `st.spinner()` para indicador de carregamento

### 7. Busca por Grafo (pages/6_🌐_Busca_Grafo.py)

**Graph Search Page**
- `st.text_area()` para query
- Botão "Buscar"
- Exibição de resposta
- `st.columns()` para layout de entidades
- `st.expander()` para cada entidade (tipo, descrição)
- `st.write()` para relacionamentos

### 8. Busca Híbrida (pages/7_🔀_Busca_Híbrida.py)

**Hybrid Search Page**
- `st.text_area()` para query
- Botão "Buscar"
- `st.tabs()` para "Semântica" e "Grafo"
- Aba Semântica: `st.dataframe()` com trechos e scores
- Aba Grafo: entidades e relacionamentos
- `st.spinner()` para carregamento

### 9. Chatbot Especialista (pages/8_💬_Chatbot.py)

**Chatbot Page**
- `st.chat_message()` para histórico (user + assistant)
- `st.chat_input()` para input de mensagem
- Envio com Enter
- `st.spinner()` para indicador de digitação
- `st.expander()` para fontes em cada resposta
- Botão "Limpar Chat" com `st.session_state.clear()`

**Chat State**
```python
st.session_state.chat_messages = []  # Histórico
st.session_state.chat_context = {}   # Contexto da conversa
```

### 10. Componentes Comuns

**header.py**
```python
def render_header():
    st.set_page_config(page_title="RAG Dashboard", layout="wide")
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("🧠 RAG - Sistema de Documentos IA")
        st.caption("Retrieval-Augmented Generation")
    with col2:
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
```

**sidebar.py**
```python
def render_sidebar():
    with st.sidebar:
        st.title("Navegação")
        st.page_link("pages/1_🏠_Dashboard.py", label="Dashboard")
        st.page_link("pages/2_📤_Upload.py", label="Upload")
        # ... mais links
```

**cards.py**
```python
def render_card(title: str, description: str, icon: str, page: str):
    with st.container(border=True):
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            st.write(icon)
        with col2:
            st.subheader(title)
            st.caption(description)
            if st.button("Acessar Módulo", key=title):
                st.page_link(page, use_container_width=True)
```

**forms.py**
```python
def render_upload_form():
    uploaded_file = st.file_uploader("Selecione um PDF", type=["pdf"])
    if uploaded_file:
        # Validação e upload
        pass

def render_query_form():
    query = st.text_area("Digite sua pergunta")
    document_id = st.selectbox("Documento (opcional)", options=[...])
    if st.button("Buscar"):
        # Executar busca
        pass
```

**chat.py**
```python
def render_chat_interface():
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    if prompt := st.chat_input("Digite sua mensagem"):
        # Processar mensagem
        pass
```

## Data Models

### Document
```typescript
interface Document {
  document_id: string;
  filename: string;
  status: 'Pending' | 'Processing' | 'Completed' | 'Error';
  progress: number;
  model?: string;
  chunks?: number;
  entities?: number;
  relationships?: number;
  error?: string;
  created_at: string;
  updated_at: string;
}
```

### QueryResponse
```typescript
interface QueryResponse {
  answer: string;
  sources: Source[];
  model_used: string;
}

interface Source {
  text: string;
  score?: number;
  metadata: {
    search_type: 'semantic' | 'graph' | 'hybrid';
    position?: number;
    entity?: string;
    type?: string;
  };
}
```

### Message (Chat)
```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: Date;
}
```

## Error Handling

### API Error Interceptor
- Intercepta respostas com status 401 (token expirado) → redireciona para login
- Intercepta respostas com status 4xx → exibe mensagem de erro ao usuário
- Intercepta respostas com status 5xx → exibe mensagem genérica + log
- Retry automático para erros de rede (máx 3 tentativas)

### User Feedback
- Toast notifications para sucesso/erro
- Mensagens de erro inline em formulários
- Indicadores de carregamento em operações assíncronas
- Fallback UI quando dados não estão disponíveis

### Validação
- Validação de entrada em formulários (email, arquivo PDF, etc)
- Validação de resposta da API (schema validation com Zod)
- Tratamento de dados incompletos/nulos

## Testing Strategy

### Unit Tests
- Testes de funções de serviço (api_client, auth_service, etc) com pytest
- Testes de funções utilitárias (formatters, validators)
- Testes de lógica de negócio com mocks de API

### Integration Tests
- Testes de fluxos completos (upload → processamento → busca) com mocks
- Testes de autenticação (login → acesso protegido → logout)
- Testes de chamadas à API com responses library

### E2E Tests
- Testes com Streamlit testing framework ou Selenium
- Fluxo completo do usuário
- Testes de responsividade em diferentes tamanhos de tela

### Test Coverage
- Mínimo 70% de cobertura
- Foco em lógica crítica e fluxos de usuário

## Deployment

### Local Development
```bash
streamlit run app.py
```

### Production Deployment
- **Streamlit Cloud**: Deploy direto do GitHub (recomendado)
- **Docker**: Container com Streamlit + requirements.txt
- **Heroku/Railway**: Deploy com Procfile

### Environment Variables
```
API_URL=http://localhost:8000
API_TIMEOUT=30
LOG_LEVEL=INFO
```

### Performance
- Caching com `@st.cache_data` para dados estáticos
- Caching com `@st.cache_resource` para conexões
- Lazy loading de páginas (Streamlit multi-page automático)
- Otimização de requisições com session reuse

## Accessibility

- Streamlit já fornece acessibilidade básica
- Labels claros em todos os inputs
- Navegação por teclado (Tab, Enter)
- Contraste de cores adequado (tema light/dark)
- Mensagens de erro descritivas
- Indicadores de carregamento claros

## Design System (Streamlit Theme)

### Cores (config.toml)
```toml
[theme]
primaryColor = "#16a34a"      # Verde - ação principal
backgroundColor = "#ffffff"   # Branco
secondaryBackgroundColor = "#f9fafb"  # Cinza claro
textColor = "#1f2937"         # Cinza escuro
font = "sans serif"
```

### Componentes Streamlit
- `st.button()`: Botões primários
- `st.selectbox()`: Dropdowns
- `st.text_input()`: Inputs de texto
- `st.text_area()`: Áreas de texto
- `st.file_uploader()`: Upload de arquivos
- `st.dataframe()`: Tabelas
- `st.metric()`: Métricas
- `st.progress()`: Barras de progresso
- `st.spinner()`: Indicadores de carregamento
- `st.success()`, `st.error()`, `st.warning()`, `st.info()`: Mensagens

### Layout
- `st.columns()`: Layout em colunas
- `st.tabs()`: Abas
- `st.expander()`: Expandidores
- `st.container()`: Containers com border
- `st.sidebar`: Sidebar para navegação
