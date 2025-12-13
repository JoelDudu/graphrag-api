# Guia de Desenvolvimento

## Setup Local

### Pré-requisitos
- Python 3.9+
- pip ou conda
- API GraphRAG v3 rodando em `http://localhost:8000`

### Instalação

```bash
# Clonar repositório
git clone <repo>
cd frontend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Configuração

Edite `.env`:
```env
API_URL=http://localhost:8000
API_TIMEOUT=30
LOG_LEVEL=INFO
```

### Executar Aplicação

```bash
streamlit run app.py
```

A aplicação estará disponível em `http://localhost:8501`

## Estrutura de Pastas

```
frontend/
├── app.py                   # Entry point
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
│   ├── header.py
│   ├── cards.py
│   └── chat.py
├── services/                # Serviços de API
│   ├── api_client.py
│   ├── auth_service.py
│   ├── document_service.py
│   ├── query_service.py
│   └── status_service.py
├── utils/                   # Funções utilitárias
│   ├── session_manager.py
│   ├── validators.py
│   ├── formatters.py
│   └── constants.py
├── config/                  # Configuração
│   ├── settings.py
│   └── theme.py
├── tests/                   # Testes
│   ├── test_api_client.py
│   ├── test_document_service.py
│   ├── test_query_service.py
│   ├── test_status_service.py
│   ├── test_validators.py
│   ├── test_formatters.py
│   ├── test_session_manager.py
│   ├── test_integration.py
│   └── __init__.py
├── requirements.txt
├── README.md
├── DEVELOPMENT.md
├── API_INTEGRATION.md
└── RESPONSIVENESS.md
```

## Convenções de Código

### Python
- PEP 8 compliant
- Type hints onde possível
- Docstrings em todas as funções
- Logging em operações importantes

### Streamlit
- Use `st.session_state` para estado global
- Use `@st.cache_data` para dados estáticos
- Use `@st.cache_resource` para conexões
- Sempre verificar autenticação no início da página

### Nomes
- Funções: `snake_case`
- Classes: `PascalCase`
- Constantes: `UPPER_CASE`
- Arquivos: `snake_case.py`

## Como Adicionar Nova Página

1. Criar arquivo em `pages/N_emoji_Nome.py`
2. Importar componentes necessários
3. Adicionar verificação de autenticação
4. Renderizar header
5. Implementar lógica
6. Adicionar navegação para outras páginas

Exemplo:
```python
import streamlit as st
from utils.session_manager import init_session_state, is_authenticated
from components.header import render_header

st.set_page_config(page_title="Nova Página", page_icon="🆕", layout="wide")
init_session_state()

if not is_authenticated():
    st.error("❌ Autenticação necessária")
    st.stop()

render_header()
st.subheader("🆕 Nova Página")

# Implementar lógica aqui
```

## Como Adicionar Novo Serviço

1. Criar arquivo em `services/novo_service.py`
2. Criar classe com métodos estáticos
3. Usar `get_api_client()` para requisições
4. Adicionar logging
5. Criar testes em `tests/test_novo_service.py`

Exemplo:
```python
from services.api_client import get_api_client
import logging

logger = logging.getLogger(__name__)

class NovoService:
    @staticmethod
    def fazer_algo(param):
        try:
            client = get_api_client()
            response = client.get("/endpoint")
            logger.info("Sucesso")
            return response
        except Exception as e:
            logger.error(f"Erro: {str(e)}")
            raise
```

## Testes

### Rodar Testes
```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=. --cov-report=html

# Teste específico
pytest tests/test_api_client.py

# Modo verbose
pytest -v
```

### Escrever Testes
- Use `@responses.activate` para mockar API
- Teste casos de sucesso e erro
- Mínimo 70% de cobertura
- Nomes descritivos: `test_funcao_cenario`

## Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Informação")
logger.warning("Aviso")
logger.error("Erro")
```

## Debugging

### Streamlit
```python
# Exibir variáveis
st.write(variavel)

# Exibir JSON
st.json(dados)

# Exibir código
st.code(codigo)

# Exibir erro
st.error("Mensagem de erro")
```

### Python
```python
# Breakpoint
import pdb; pdb.set_trace()

# Print debug
print(f"Debug: {variavel}")
```

## Performance

### Caching
```python
# Dados estáticos
@st.cache_data
def carregar_dados():
    return dados

# Conexões
@st.cache_resource
def get_conexao():
    return conexao
```

### Otimizações
- Evitar requisições desnecessárias
- Usar session state para armazenar dados
- Lazy load de componentes pesados
- Limpar cache quando necessário

## Deployment

### Docker
```bash
docker build -t rag-frontend .
docker run -p 8501:8501 rag-frontend
```

### Streamlit Cloud
1. Push para GitHub
2. Conectar repositório em Streamlit Cloud
3. Configurar secrets
4. Deploy automático

## Troubleshooting

### Erro de Autenticação
- Verificar se API está rodando
- Verificar credenciais
- Limpar cache do navegador

### Erro de Conexão
- Verificar `API_URL` em `.env`
- Verificar se API está acessível
- Verificar firewall

### Erro de Sessão
- Limpar `st.session_state`
- Fazer logout e login novamente
- Limpar cookies

## Recursos

- [Streamlit Docs](https://docs.streamlit.io)
- [Python Docs](https://docs.python.org/3)
- [Requests Docs](https://requests.readthedocs.io)
- [Pytest Docs](https://docs.pytest.org)
