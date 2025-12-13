# RAG Dashboard Frontend

Frontend em Streamlit para o sistema RAG de gerenciamento de documentos com IA.

## Setup

### Pré-requisitos
- Python 3.9+
- API GraphRAG v3 rodando em `http://localhost:8000`

### Instalação

```bash
cd frontend
pip install -r requirements.txt
```

### Configuração

Edite `.env`:
```env
API_URL=http://localhost:8000
API_TIMEOUT=30
LOG_LEVEL=INFO
```

### Executar

```bash
streamlit run app.py
```

A aplicação estará disponível em `http://localhost:8501`

## Estrutura

```
frontend/
├── app.py                   # Entry point
├── pages/                   # Páginas Streamlit
├── components/              # Componentes reutilizáveis
├── services/                # Serviços de API
├── utils/                   # Funções utilitárias
├── config/                  # Configuração
├── tests/                   # Testes
└── requirements.txt
```

## Testes

```bash
pytest
pytest --cov=.  # Com cobertura
```

## Documentação

- [DEVELOPMENT.md](DEVELOPMENT.md) - Guia de desenvolvimento
- [API_INTEGRATION.md](API_INTEGRATION.md) - Integração com API
