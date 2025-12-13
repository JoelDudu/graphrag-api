# GraphRAG API v3.1

API assíncrona para processamento de documentos com extração de grafo de conhecimento usando LLMs.

## 🎉 Novidades v3.1

### 🔐 Autenticação JWT
- Todos os endpoints protegidos (exceto `/health`)
- Tokens com expiração configurável (padrão: 24h)
- Usuários padrão: `admin/admin123` e `user/user123`

### 📁 Suporte a Múltiplos Formatos
- **PDF** (.pdf)
- **Word** (.docx, .doc)
- **Excel** (.xlsx, .xls)
- **PowerPoint** (.pptx, .ppt)
- **Texto** (.txt, .csv)

**Veja detalhes completos em:** `CHANGELOG_v3.1.md`

## Arquitetura

- **API**: FastAPI (`graph_api_v3.py`)
- **Worker**: Celery (`celery_worker.py`)
- **LLMs**: Claude, OpenAI, Kimi (`llm_providers.py`)
- **Prompts**: Especializados por domínio (`extraction_prompts.py`)
- **Vector Store**: Neo4j (`neo4j_store.py`)

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

Edite `.env`:

```env
# Neo4j
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LLMs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
MOONSHOT_API_KEY=sk-...

# Redis
REDIS_URL=redis://localhost:6379

# JWT (IMPORTANTE: Altere em produção!)
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_EXPIRE_MINUTES=1440
```

## Iniciar

### Opção 1: Script de Setup (Windows)
```bash
setup_v3.1.bat
```

### Opção 2: Manual

**Terminal 1 - Worker Celery:**
```bash
python -m celery -A celery_worker worker --loglevel=info --pool=solo
```

**Terminal 2 - API:**
```bash
python graph_api_v3.py
# ou
uvicorn graph_api_v3:app --reload
```

### Testar
```bash
# Teste básico
python test_api.py

# Teste com upload
python test_api.py documento.docx claude generic
```

## Uso Rápido

### 1. Autenticar
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### 2. Upload (com token)
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@documento.docx"
```

### 3. Processar
```bash
curl -X POST "http://localhost:8000/process" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "DOC_ID",
    "model": "claude",
    "doc_type": "generic"
  }'
```

### 4. Consultar
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Faça um resumo",
    "document_id": "DOC_ID",
    "search_type": "hybrid"
  }'
```

## Cliente Python

```python
from client_example import GraphRAGClient

client = GraphRAGClient("http://localhost:8000")
client.login("admin", "admin123")

doc_id = client.upload_file("documento.xlsx")
client.process_document(doc_id, model="claude", doc_type="financial")
client.wait_for_completion(doc_id)

result = client.query("Quais são os dados financeiros?", doc_id)
print(result['answer'])
```

## Endpoints

| Endpoint | Método | Auth | Descrição |
|----------|--------|------|-----------|
| `/auth/login` | POST | ❌ | Obter token JWT |
| `/auth/me` | GET | ✅ | Info do usuário |
| `/health` | GET | ❌ | Status da API |
| `/upload` | POST | ✅ | Upload de arquivo |
| `/process` | POST | ✅ | Processar documento |
| `/status/{id}` | GET | ✅ | Status do processamento |
| `/query` | POST | ✅ | Consultar documentos |
| `/documents` | GET | ✅ | Listar documentos |
| `/documents/{id}` | DELETE | ✅ | Excluir documento |
| `/supported-formats` | GET | ✅ | Formatos suportados |
| `/doc-types` | GET | ✅ | Tipos de documentos |

## Tipos de Busca

- **semantic**: Busca por similaridade semântica (embeddings)
- **graph**: Navega entidades e relacionamentos
- **hybrid**: Combina semantic + graph

## Modelos Suportados

- **Claude**: Batch API (50% desconto)
- **OpenAI**: Batch API (50% desconto)
- **Kimi**: Processamento paralelo (máx 3 simultâneos)

## 📚 Documentação

- **Swagger UI**: http://localhost:8000/docs
- **API_AUTH_GUIDE.md**: Guia completo de autenticação
- **CHANGELOG_v3.1.md**: Novidades e mudanças
- **client_example.py**: Cliente Python completo

## 🔒 Segurança

⚠️ **ANTES DE PRODUÇÃO:**

1. Altere `JWT_SECRET_KEY` no `.env`
2. Altere senhas padrão em `auth.py`
3. Use HTTPS
4. Configure CORS adequadamente
5. Implemente rate limiting

## 📦 Arquivos Principais

```
├── graph_api_v3.py          # API principal
├── auth.py                  # Autenticação JWT (NOVO)
├── file_processor.py        # Processador de arquivos (NOVO)
├── celery_worker.py         # Worker assíncrono
├── llm_providers.py         # Provedores LLM
├── neo4j_store.py          # Store Neo4j
├── extraction_prompts.py    # Prompts de extração
├── test_api.py             # Script de teste (NOVO)
├── client_example.py       # Cliente Python (NOVO)
└── requirements.txt        # Dependências
```

## 🆘 Suporte

- **Guia de autenticação**: `API_AUTH_GUIDE.md`
- **Teste rápido**: `python test_api.py`
- **Health check**: http://localhost:8000/health
- **Documentação**: http://localhost:8000/docs

---

**Versão:** 3.1.0  
**Última atualização:** 13/12/2024
