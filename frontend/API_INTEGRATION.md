# Integração com API GraphRAG

## Visão Geral

O frontend consome a API GraphRAG v3 através do cliente HTTP `APIClient` com autenticação JWT e retry automático.

## Endpoints Consumidos

### Autenticação
```
POST /login
Body: { "email": "user@example.com", "password": "password" }
Response: { "token": "jwt_token", "user": {...} }
```

### Documentos
```
POST /upload
Files: { "file": <pdf_file> }
Response: { "document_id": "uuid", "filename": "...", "status": "Pending" }

GET /documents
Response: { "documents": [...], "total": 5 }

GET /status/{document_id}
Response: { "document_id": "...", "status": "Completed", "progress": 1.0, ... }

DELETE /documents/{document_id}
Response: { "message": "Deleted" }

GET /doc-types
Response: { "available_types": [...], "descriptions": {...} }
```

### Processamento
```
POST /process
Body: { "document_id": "...", "model": "claude", "doc_type": "generic" }
Response: { "document_id": "...", "status": "Processing" }
```

### Busca
```
POST /query
Body: {
  "query": "pergunta",
  "document_id": "...",
  "search_type": "semantic|graph|hybrid",
  "top_k": 5
}
Response: {
  "answer": "resposta",
  "sources": [...],
  "model_used": "claude"
}
```

### Health Check
```
GET /health
Response: { "api": "ok", "neo4j": "ok", "redis": "ok" }
```

## Fluxo de Autenticação

1. **Login**: Usuário faz login com email/senha
2. **Token**: API retorna JWT token
3. **Armazenamento**: Token armazenado em `st.session_state.token`
4. **Inclusão**: Token incluído em todas as requisições no header `Authorization: Bearer <token>`
5. **Renovação**: Se token expirar (401), usuário é redirecionado para login

## Tratamento de Erros

### Erros de Rede
- Retry automático (máx 3 tentativas)
- Timeout: 30 segundos
- Mensagem: "Erro ao conectar com a API"

### Erros HTTP
- 401: Token expirado → Logout automático
- 4xx: Erro do cliente → Mensagem específica
- 5xx: Erro do servidor → Retry automático

### Validação
- Validação de entrada antes de enviar
- Validação de resposta após receber
- Tratamento de dados nulos/incompletos

## Exemplo de Uso

### Upload de Documento
```python
from services.document_service import get_document_service

service = get_document_service()
result = service.upload_document(file)
document_id = result["document_id"]
```

### Busca Semântica
```python
from services.query_service import get_query_service

service = get_query_service()
result = service.query_semantic(
    query="Qual é a pergunta?",
    document_id="123",
    top_k=5
)
answer = result["answer"]
sources = result["sources"]
```

### Polling de Status
```python
from services.status_service import get_status_service

service = get_status_service()
status = service.poll_status(
    document_id="123",
    interval=5,
    max_attempts=120
)
```

## Modelos Suportados

- **claude**: Anthropic Claude (recomendado)
- **openai**: OpenAI GPT-4
- **kimi**: Kimi (processamento paralelo)

## Tipos de Documentos

- **generic**: Extração genérica
- **legal**: Documentos jurídicos
- **medical**: Documentos médicos
- **technical**: Documentos técnicos
- **financial**: Documentos financeiros
- **aesthetics**: Documentos de estética
- **health**: Documentos de saúde
- **it**: Documentos de TI

## Tipos de Busca

- **semantic**: Busca por similaridade semântica
- **graph**: Busca navegando grafo de conhecimento
- **hybrid**: Combinação de semântica + grafo

## Configuração

### Variáveis de Ambiente
```env
API_URL=http://localhost:8000
API_TIMEOUT=30
LOG_LEVEL=INFO
```

### Cliente HTTP
```python
from services.api_client import get_api_client

client = get_api_client()
response = client.get("/endpoint")
response = client.post("/endpoint", data={...})
response = client.delete("/endpoint")
```

## Testes

### Mock de API
```python
import responses

@responses.activate
def test_upload():
    responses.add(
        responses.POST,
        "http://localhost:8000/upload",
        json={"document_id": "123"},
        status=200
    )
    # Teste aqui
```

## Troubleshooting

### Erro 401 (Não Autenticado)
- Fazer login novamente
- Verificar se token está sendo enviado
- Verificar se token expirou

### Erro 404 (Não Encontrado)
- Verificar se document_id existe
- Verificar se endpoint está correto
- Verificar se API está rodando

### Timeout
- Aumentar `API_TIMEOUT` em `.env`
- Verificar conexão de rede
- Verificar se API está respondendo

### Erro de Conexão
- Verificar se API está rodando
- Verificar `API_URL` em `.env`
- Verificar firewall/proxy

## Performance

### Caching
- Documentos listados são cacheados
- Status é atualizado via polling
- Resultados de busca não são cacheados

### Otimizações
- Usar `top_k` apropriado (padrão 5)
- Limitar número de documentos em listagem
- Usar polling com intervalo adequado

## Segurança

- Token armazenado em session state (não em localStorage)
- Requisições incluem token no header
- Validação de entrada antes de enviar
- Tratamento de erros sem expor detalhes internos
