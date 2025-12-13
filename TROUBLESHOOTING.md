# 🔧 Troubleshooting - GraphRAG API v3.1

## 🚨 Problemas Comuns e Soluções

### 1. Erro de Autenticação

#### Problema: "401 Unauthorized"

```json
{
  "detail": "Credenciais inválidas"
}
```

**Soluções:**

1. Verifique usuário e senha:
```python
# Usuários padrão
username: "admin", password: "admin123"
username: "user", password: "user123"
```

2. Verifique se o token está sendo enviado:
```python
headers = {"Authorization": f"Bearer {token}"}
```

3. Verifique se o token não expirou:
```python
# Token padrão expira em 24h
# Faça login novamente se necessário
```

4. Verifique JWT_SECRET_KEY no .env:
```env
JWT_SECRET_KEY=your-secret-key-change-this-in-production
```

---

### 2. Erro no Upload de Arquivo

#### Problema: "400 Bad Request - Tipo de arquivo não suportado"

```json
{
  "detail": "Tipo de arquivo não suportado. Formatos aceitos: .pdf, .docx, ..."
}
```

**Soluções:**

1. Verifique a extensão do arquivo:
```python
# Formatos suportados
.pdf, .docx, .doc, .xlsx, .xls, .pptx, .ppt, .txt, .csv
```

2. Verifique se o arquivo existe:
```python
from pathlib import Path
if not Path("arquivo.docx").exists():
    print("Arquivo não encontrado!")
```

3. Liste formatos suportados:
```bash
curl -X GET "http://localhost:8000/supported-formats" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3. Erro no Processamento

#### Problema: Status "Failed"

```json
{
  "status": "Failed",
  "error": "Erro ao processar documento"
}
```

**Soluções:**

1. Verifique os logs do Celery Worker:
```bash
# Procure por erros no terminal do worker
python -m celery -A celery_worker worker --loglevel=info --pool=solo
```

2. Verifique se o Redis está rodando:
```bash
# Teste conexão Redis
curl http://localhost:8000/health
```

3. Verifique se o Neo4j está acessível:
```bash
# Teste conexão Neo4j
curl http://localhost:8000/health
```

4. Verifique as chaves de API no .env:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

5. Tente com arquivo menor:
```python
# Arquivos muito grandes podem causar timeout
# Tente com um arquivo de teste menor primeiro
```

---

### 4. Erro de Conexão com Neo4j

#### Problema: "neo4j": "error: ..."

```json
{
  "neo4j": "error: Failed to establish connection"
}
```

**Soluções:**

1. Verifique se o Neo4j está rodando:
```bash
# Verifique o serviço Neo4j
# Windows: Verifique nos serviços
# Linux: sudo systemctl status neo4j
```

2. Verifique as credenciais no .env:
```env
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
```

3. Teste conexão direta:
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "neo4j://localhost:7687",
    auth=("neo4j", "password")
)

with driver.session() as session:
    result = session.run("RETURN 1")
    print(result.single())

driver.close()
```

4. Verifique firewall/portas:
```bash
# Porta 7687 deve estar acessível
netstat -an | findstr 7687
```

---

### 5. Erro de Conexão com Redis

#### Problema: "redis": "error: ..."

```json
{
  "redis": "error: Connection refused"
}
```

**Soluções:**

1. Verifique se o Redis está rodando:
```bash
# Windows: Verifique nos serviços
# Linux: sudo systemctl status redis
```

2. Verifique a URL no .env:
```env
REDIS_URL=redis://localhost:6379/0
# ou com autenticação
REDIS_URL=redis://user:password@host:6379/0
```

3. Teste conexão direta:
```python
import redis

r = redis.from_url("redis://localhost:6379/0")
r.ping()
print("Redis OK!")
```

4. Verifique se a porta está acessível:
```bash
netstat -an | findstr 6379
```

---

### 6. Worker Celery Não Processa

#### Problema: Documento fica em "Processing" indefinidamente

**Soluções:**

1. Verifique se o worker está rodando:
```bash
# Deve estar rodando em um terminal separado
python -m celery -A celery_worker worker --loglevel=info --pool=solo
```

2. Verifique logs do worker:
```bash
# Procure por erros ou exceções
# O worker deve mostrar "Task received" quando um job chega
```

3. Reinicie o worker:
```bash
# Ctrl+C para parar
# Depois inicie novamente
python -m celery -A celery_worker worker --loglevel=info --pool=solo
```

4. Limpe a fila do Redis:
```python
import redis
r = redis.from_url("redis://localhost:6379/0")
r.flushdb()
print("Fila limpa!")
```

5. Verifique se há tasks travadas:
```bash
# No terminal do worker, procure por:
# "Task ... succeeded" ou "Task ... failed"
```

---

### 7. Erro de Memória

#### Problema: "MemoryError" ou processo travado

**Soluções:**

1. Reduza o tamanho dos chunks:
```env
# No .env
TOKEN_CHUNK_SIZE=100  # Reduzir de 130
MAX_TOKEN_CHUNK_SIZE=5000  # Reduzir de 10000
```

2. Processe arquivos menores:
```python
# Divida arquivos grandes em partes menores
```

3. Aumente memória disponível:
```bash
# Feche outros programas
# Ou aumente RAM da máquina/container
```

4. Use modelo mais leve:
```python
# OpenAI pode ser mais leve que Claude
client.process_document(doc_id, model="openai", doc_type="generic")
```

---

### 8. Erro de Timeout

#### Problema: Processamento muito lento ou timeout

**Soluções:**

1. Aumente o timeout:
```python
# No cliente
client.wait_for_completion(doc_id, timeout=1200)  # 20 minutos
```

2. Use Batch API (mais rápido):
```python
# Claude e OpenAI usam Batch API automaticamente
client.process_document(doc_id, model="claude", doc_type="generic")
```

3. Verifique conexão com APIs:
```bash
# Teste latência
curl -w "@curl-format.txt" -o /dev/null -s https://api.openai.com
```

4. Processe em horários de menor carga:
```python
# APIs podem estar mais lentas em horários de pico
```

---

### 9. Erro ao Extrair Texto de Arquivo

#### Problema: Arquivo não é processado corretamente

**Soluções:**

1. Verifique se o arquivo não está corrompido:
```python
# Tente abrir o arquivo manualmente
# Word, Excel, PowerPoint, etc.
```

2. Converta para formato mais novo:
```python
# .doc → .docx
# .xls → .xlsx
# .ppt → .pptx
```

3. Verifique encoding (para TXT/CSV):
```python
# Salve como UTF-8
```

4. Teste extração manual:
```python
from file_processor import FileProcessor

text = FileProcessor.extract_text("arquivo.docx")
print(text[:500])  # Primeiros 500 caracteres
```

---

### 10. Erro de Permissão

#### Problema: "Permission denied" ao acessar arquivo

**Soluções:**

1. Verifique permissões do arquivo:
```bash
# Windows: Propriedades → Segurança
# Linux: ls -la arquivo.pdf
```

2. Feche o arquivo em outros programas:
```python
# Certifique-se de que o arquivo não está aberto
# no Word, Excel, etc.
```

3. Execute com permissões adequadas:
```bash
# Windows: Execute como Administrador se necessário
```

4. Verifique permissões da pasta uploads:
```bash
# A pasta ./uploads deve ter permissão de escrita
```

---

## 🔍 Diagnóstico Geral

### Script de Diagnóstico

```python
"""
Script de diagnóstico completo
"""

import requests
import redis
from neo4j import GraphDatabase
import os
from pathlib import Path

def diagnostico_completo():
    print("🔍 Diagnóstico GraphRAG API v3.1\n")
    
    # 1. Verificar .env
    print("1️⃣ Verificando .env...")
    env_vars = [
        'NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD',
        'OPENAI_API_KEY', 'ANTHROPIC_API_KEY',
        'REDIS_URL', 'JWT_SECRET_KEY'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'*' * 10}")
        else:
            print(f"   ❌ {var}: NÃO CONFIGURADO")
    
    # 2. Verificar API
    print("\n2️⃣ Verificando API...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        health = response.json()
        print(f"   API: {health['api']}")
        print(f"   Neo4j: {health['neo4j']}")
        print(f"   Redis: {health['redis']}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # 3. Verificar Neo4j
    print("\n3️⃣ Verificando Neo4j...")
    try:
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )
        with driver.session() as session:
            result = session.run("RETURN 1")
            result.single()
        print("   ✅ Conexão OK")
        driver.close()
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # 4. Verificar Redis
    print("\n4️⃣ Verificando Redis...")
    try:
        r = redis.from_url(os.getenv("REDIS_URL"))
        r.ping()
        print("   ✅ Conexão OK")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # 5. Verificar arquivos
    print("\n5️⃣ Verificando arquivos...")
    arquivos = [
        'graph_api_v3.py', 'auth.py', 'file_processor.py',
        'celery_worker.py', 'llm_providers.py', 'neo4j_store.py'
    ]
    
    for arquivo in arquivos:
        if Path(arquivo).exists():
            print(f"   ✅ {arquivo}")
        else:
            print(f"   ❌ {arquivo}: NÃO ENCONTRADO")
    
    # 6. Verificar pasta uploads
    print("\n6️⃣ Verificando pasta uploads...")
    if Path("uploads").exists():
        print(f"   ✅ Pasta existe")
        arquivos = list(Path("uploads").glob("*"))
        print(f"   📁 {len(arquivos)} arquivos")
    else:
        print(f"   ❌ Pasta não existe")
    
    print("\n✅ Diagnóstico concluído!")

if __name__ == "__main__":
    diagnostico_completo()
```

Salve como `diagnostico.py` e execute:
```bash
python diagnostico.py
```

---

## 📞 Suporte

### Checklist Antes de Reportar Problema
