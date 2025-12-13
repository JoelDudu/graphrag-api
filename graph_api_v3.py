"""
GraphRAG API v3 - Arquitetura Assíncrona
Endpoints separados para upload, processamento, status e query.
Suporta autenticação JWT e múltiplos formatos de arquivo.
"""

import os
import uuid
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from neo4j import GraphDatabase

from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.openai import OpenAI as LlamaOpenAI

from llm_providers import LLMProvider
from neo4j_store import CustomNeo4jVectorStore
from celery_worker import process_document_task
from auth import (
    Token, User, authenticate_user, create_access_token, 
    get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from file_processor import FileProcessor

# Configuração de logging
logging.basicConfig(format="%(asctime)s - %(message)s", level="INFO")

# Configurar LlamaIndex defaults
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

app = FastAPI(
    title="GraphRAG API v3",
    description="API assíncrona para processamento de documentos com GraphRAG. Suporta PDF, Word, Excel, PowerPoint e mais.",
    version="3.0.0"
)

# Criar pasta de uploads
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================
# Pydantic Models
# ============================================

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str


class ProcessRequest(BaseModel):
    document_id: str
    model: str = "claude"  # 'claude', 'openai', 'kimi'
    doc_type: str = "generic"  # 'generic', 'legal', 'medical', 'technical', 'financial', 'aesthetics', 'health', 'it'


class ProcessResponse(BaseModel):
    document_id: str
    status: str
    model: str
    message: str


class StatusResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    progress: float
    model: Optional[str]
    chunks: Optional[int]
    entities: Optional[int]
    relationships: Optional[int]
    error: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class QueryRequest(BaseModel):
    query: str
    document_id: Optional[str] = None
    model: Optional[str] = None
    top_k: int = 5
    search_type: str = "semantic"  # 'semantic', 'graph', 'hybrid'


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    model_used: str


# ============================================
# Database Connection
# ============================================

def get_neo4j_driver():
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )


def get_neo4j_database():
    return os.getenv("NEO4J_DATABASE", "neo4j")


# ============================================
# Endpoints
# ============================================

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint de autenticação - retorna token JWT.
    
    Usuários padrão:
    - username: admin, password: admin123
    - username: user, password: user123
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@app.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Retorna informações do usuário autenticado"""
    return current_user


@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload de documento - Salva arquivo e cria nó Document com status='Pending'.
    Suporta: PDF, DOCX, DOC, XLSX, XLS, PPTX, PPT, TXT, CSV
    Retorna document_id para uso nos próximos endpoints.
    """
    # Validar tipo de arquivo
    file_extension = Path(file.filename).suffix.lower()
    if not FileProcessor.is_supported(file.filename):
        supported = ", ".join(FileProcessor.SUPPORTED_EXTENSIONS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo não suportado. Formatos aceitos: {supported}"
        )
    
    # Gerar ID único
    document_id = str(uuid.uuid4())
    
    # Salvar arquivo
    file_path = UPLOAD_DIR / f"{document_id}_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    file_size = len(content)
    file_type = file_extension.replace(".", "")
    
    # Criar nó Document no Neo4j
    driver = get_neo4j_driver()
    database = get_neo4j_database()
    try:
        with driver.session(database=database) as session:
            logging.info(f"Criando documento no banco: {database}, ID: {document_id}")
            session.run("""
                CREATE (d:Document {
                    id: $document_id,
                    fileName: $filename,
                    filePath: $file_path,
                    fileSize: $file_size,
                    fileType: $file_type,
                    status: 'Pending',
                    processingProgress: 0,
                    processingModel: null,
                    processingError: null,
                    fileSource: 'upload',
                    createdAt: datetime(),
                    updatedAt: datetime()
                })
            """, 
                document_id=document_id,
                filename=file.filename,
                file_path=str(file_path),
                file_size=file_size,
                file_type=file_type
            )
            logging.info(f"Documento criado com sucesso: {document_id}")
    finally:
        driver.close()
    
    return UploadResponse(
        document_id=document_id,
        filename=file.filename,
        status="Pending",
        message="Documento enviado. Use POST /process para iniciar processamento."
    )


@app.post("/process", response_model=ProcessResponse)
async def process_document(
    request: ProcessRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Inicia processamento do documento em background.
    Escolha o LLM: 'claude', 'openai' ou 'kimi'.
    """
    # Validar modelo
    if not LLMProvider.validate_model(request.model):
        raise HTTPException(
            status_code=400,
            detail=f"Modelo '{request.model}' não suportado. Use: {LLMProvider.SUPPORTED_MODELS}"
        )
    
    driver = get_neo4j_driver()
    database = get_neo4j_database()
    try:
        with driver.session(database=database) as session:
            # Verificar se documento existe
            logging.info(f"Buscando documento no banco: {database}, ID: {request.document_id}")
            result = session.run("""
                MATCH (d:Document {id: $document_id})
                RETURN d.status as status, d.filePath as filePath
            """, document_id=request.document_id)
            
            record = result.single()
            if not record:
                logging.error(f"Documento não encontrado: {request.document_id}")
                raise HTTPException(status_code=404, detail="Documento não encontrado")
            
            current_status = record["status"]
            file_path = record["filePath"]
            
            if current_status == "Processing":
                raise HTTPException(status_code=400, detail="Documento já está sendo processado")
            
            if current_status == "Completed":
                raise HTTPException(status_code=400, detail="Documento já foi processado")
            
            # Atualizar status para Processing
            session.run("""
                MATCH (d:Document {id: $document_id})
                SET d.status = 'Processing',
                    d.processingProgress = 0,
                    d.processingModel = $model,
                    d.processingError = null,
                    d.updatedAt = datetime()
            """, document_id=request.document_id, model=request.model)
    finally:
        driver.close()
    
    # Iniciar processamento em background via Celery
    from extraction_prompts import get_prompt
    extraction_prompt = get_prompt(request.doc_type)
    process_document_task.delay(request.document_id, file_path, request.model, extraction_prompt)
    
    return ProcessResponse(
        document_id=request.document_id,
        status="Processing",
        model=request.model,
        message="Processamento iniciado. Use GET /status/{document_id} para acompanhar."
    )


@app.get("/status/{document_id}", response_model=StatusResponse)
async def get_status(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retorna status atual do processamento do documento.
    """
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (d:Document {id: $document_id})
                RETURN d.fileName as filename,
                       d.status as status,
                       d.processingProgress as progress,
                       d.processingModel as model,
                       d.total_chunks as chunks,
                       d.entityNodeCount as entities,
                       d.entityEntityRelCount as relationships,
                       d.processingError as error,
                       toString(d.createdAt) as created_at,
                       toString(d.updatedAt) as updated_at
            """, document_id=document_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Documento não encontrado")
            
            return StatusResponse(
                document_id=document_id,
                filename=record["filename"],
                status=record["status"],
                progress=record["progress"] or 0,
                model=record["model"],
                chunks=record["chunks"],
                entities=record["entities"],
                relationships=record["relationships"],
                error=record["error"],
                created_at=record["created_at"],
                updated_at=record["updated_at"]
            )
    finally:
        driver.close()


@app.get("/documents")
async def list_documents(current_user: User = Depends(get_current_active_user)):
    """
    Lista todos os documentos e seus status.
    """
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (d:Document)
                RETURN d.id as id,
                       d.fileName as filename,
                       d.status as status,
                       d.processingProgress as progress,
                       d.processingModel as model,
                       toString(d.createdAt) as created_at
                ORDER BY d.createdAt DESC
            """)
            
            documents = []
            for record in result:
                documents.append({
                    "document_id": record["id"],
                    "filename": record["filename"],
                    "status": record["status"],
                    "progress": record["progress"] or 0,
                    "model": record["model"],
                    "created_at": record["created_at"]
                })
            
            return {"documents": documents, "total": len(documents)}
    finally:
        driver.close()


def query_graph(query: str, document_id: str, driver, database: str, top_k: int = 5) -> List[Dict]:
    """Busca por grafo - navega entidades e relacionamentos"""
    with driver.session(database=database) as session:
        # Extrair palavras-chave da query
        keywords = [word.lower() for word in query.split() if len(word) > 3]
        
        # Buscar entidades relacionadas
        cypher = """
            MATCH (d:Document {id: $document_id})-[:FIRST_CHUNK]->()-[:NEXT_CHUNK*0..]->
                  (c:Chunk)-[:HAS_ENTITY]->(e:__Entity__)
            WHERE any(keyword IN $keywords WHERE toLower(e.id) CONTAINS keyword 
                                              OR toLower(e.description) CONTAINS keyword)
            WITH e, c
            OPTIONAL MATCH (e)-[r]->(e2:__Entity__)
            RETURN e.id as entity_id, e.type as entity_type, e.description as entity_desc,
                   type(r) as rel_type, e2.id as related_entity,
                   c.text as chunk_text, c.position as chunk_position
            LIMIT $top_k
        """
        
        result = session.run(cypher, document_id=document_id, keywords=keywords, top_k=top_k)
        
        sources = []
        for record in result:
            source = {
                "entity": record["entity_id"],
                "type": record["entity_type"],
                "description": record["entity_desc"],
                "text": record["chunk_text"][:500] if record["chunk_text"] else "",
                "metadata": {
                    "position": record["chunk_position"],
                    "search_type": "graph"
                }
            }
            
            if record["rel_type"] and record["related_entity"]:
                source["relationship"] = f"{record['rel_type']} -> {record['related_entity']}"
            
            sources.append(source)
        
        return sources


def query_hybrid(query: str, document_id: str, driver, database: str, vector_store, top_k: int = 5) -> tuple:
    """Busca híbrida - combina semântica + grafo"""
    # Busca semântica
    from llama_index.core import VectorStoreIndex
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    query_engine = index.as_query_engine(similarity_top_k=top_k)
    semantic_response = query_engine.query(query)
    
    semantic_sources = []
    if hasattr(semantic_response, 'source_nodes'):
        for node in semantic_response.source_nodes:
            semantic_sources.append({
                "text": node.text[:500] + "..." if len(node.text) > 500 else node.text,
                "score": node.score if hasattr(node, 'score') else None,
                "metadata": {**node.metadata, "search_type": "semantic"}
            })
    
    # Busca por grafo
    graph_sources = query_graph(query, document_id, driver, database, top_k)
    
    # Combinar resultados
    all_sources = semantic_sources + graph_sources
    
    return str(semantic_response), all_sources


@app.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Faz pergunta aos documentos processados.
    
    Tipos de busca:
    - semantic: Busca por similaridade semântica (embeddings)
    - graph: Busca navegando entidades e relacionamentos
    - hybrid: Combina semantic + graph
    """
    driver = get_neo4j_driver()
    database = get_neo4j_database()
    
    try:
        # Verificar se há documentos processados
        with driver.session(database=database) as session:
            if request.document_id:
                result = session.run("""
                    MATCH (d:Document {id: $document_id})
                    WHERE d.status = 'Completed'
                    RETURN d.processingModel as model
                """, document_id=request.document_id)
            else:
                result = session.run("""
                    MATCH (d:Document)
                    WHERE d.status = 'Completed'
                    RETURN d.processingModel as model
                    LIMIT 1
                """)
            
            record = result.single()
            if not record:
                raise HTTPException(
                    status_code=400,
                    detail="Nenhum documento processado encontrado"
                )
            
            # Usar modelo do documento ou o especificado
            model_to_use = request.model or record["model"] or "claude"
        
        # Configurar LLM
        llm = LLMProvider.get_llm(model_to_use)
        if model_to_use == "claude":
            Settings.llm = Anthropic(model="claude-sonnet-4-20250514")
        else:
            Settings.llm = LlamaOpenAI(model="gpt-4o")
        
        # Executar busca baseado no tipo
        if request.search_type == "graph":
            # Busca por grafo
            sources = query_graph(request.query, request.document_id, driver, database, request.top_k)
            
            # Gerar resposta com LLM baseado nas entidades encontradas
            context = "\n".join([
                f"- {s['entity']} ({s['type']}): {s['description']}"
                for s in sources
            ])
            
            prompt = f"""Baseado nas seguintes entidades do grafo de conhecimento:

{context}

Responda a pergunta: {request.query}"""
            
            from langchain_core.messages import HumanMessage
            response = llm.invoke([HumanMessage(content=prompt)])
            answer = response.content if hasattr(response, 'content') else str(response)
            
        elif request.search_type == "hybrid":
            # Busca híbrida
            vector_store = CustomNeo4jVectorStore(
                username=os.getenv("NEO4J_USER"),
                password=os.getenv("NEO4J_PASSWORD"),
                url=os.getenv("NEO4J_URI"),
                embedding_dimension=1536,
                database=database
            )
            
            answer, sources = query_hybrid(
                request.query, 
                request.document_id, 
                driver, 
                database, 
                vector_store, 
                request.top_k
            )
            
        else:  # semantic (padrão)
            # Busca semântica
            vector_store = CustomNeo4jVectorStore(
                username=os.getenv("NEO4J_USER"),
                password=os.getenv("NEO4J_PASSWORD"),
                url=os.getenv("NEO4J_URI"),
                embedding_dimension=1536,
                database=database
            )
            
            index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
            query_engine = index.as_query_engine(similarity_top_k=request.top_k)
            response = query_engine.query(request.query)
            
            answer = str(response)
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    sources.append({
                        "text": node.text[:500] + "..." if len(node.text) > 500 else node.text,
                        "score": node.score if hasattr(node, 'score') else None,
                        "metadata": {**node.metadata, "search_type": "semantic"}
                    })
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            model_used=model_to_use
        )
        
    finally:
        driver.close()


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Exclui documento e todos os dados relacionados.
    """
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            # Verificar se existe
            result = session.run("""
                MATCH (d:Document {id: $document_id})
                RETURN d.filePath as filePath
            """, document_id=document_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Documento não encontrado")
            
            file_path = record["filePath"]
            
            # Deletar arquivo
            if file_path and Path(file_path).exists():
                Path(file_path).unlink()
            
            # Deletar do Neo4j (Document, Chunks, Entities relacionadas)
            session.run("""
                MATCH (d:Document {id: $document_id})
                OPTIONAL MATCH (d)-[:FIRST_CHUNK]->(c:Chunk)
                OPTIONAL MATCH (c)-[:HAS_ENTITY]->(e:__Entity__)
                DETACH DELETE d, c
            """, document_id=document_id)
            
            return {"message": "Documento excluído com sucesso", "document_id": document_id}
    finally:
        driver.close()


@app.get("/doc-types")
async def get_document_types(current_user: User = Depends(get_current_active_user)):
    """
    Retorna lista de tipos de documentos disponíveis para extração.
    Use o 'type' no endpoint /process para especificar qual usar.
    """
    from extraction_prompts import PROMPTS_BY_TYPE
    
    doc_types = {
        "available_types": list(PROMPTS_BY_TYPE.keys()),
        "descriptions": {
            "generic": "Extração genérica - máximo de entidades e relacionamentos",
            "legal": "Documentos jurídicos - contratos, processos, leis",
            "medical": "Documentos médicos - diagnósticos, tratamentos, procedimentos",
            "technical": "Documentos técnicos - software, arquitetura, frameworks",
            "financial": "Documentos financeiros - transações, investimentos, mercado",
            "aesthetics": "Documentos de estética - procedimentos, produtos, tratamentos",
            "health": "Documentos de saúde geral - wellness, nutrição, lifestyle",
            "it": "Documentos de TI - infraestrutura, DevOps, segurança"
        }
    }
    
    return doc_types


@app.get("/supported-formats")
async def get_supported_formats(current_user: User = Depends(get_current_active_user)):
    """
    Retorna lista de formatos de arquivo suportados.
    """
    return {
        "supported_formats": FileProcessor.get_supported_formats(),
        "total": len(FileProcessor.SUPPORTED_EXTENSIONS)
    }


@app.get("/debug/document/{document_id}")
async def debug_document(document_id: str):
    """Debug: Verifica se documento existe no Neo4j"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (d:Document {id: $document_id})
                RETURN d
            """, document_id=document_id)
            
            record = result.single()
            if record:
                doc = dict(record["d"])
                return {"found": True, "document": doc}
            else:
                # Tentar buscar todos os documentos
                all_docs = session.run("MATCH (d:Document) RETURN d.id as id, d.fileName as name LIMIT 10")
                docs_list = [{"id": r["id"], "name": r["name"]} for r in all_docs]
                return {"found": False, "all_documents": docs_list}
    finally:
        driver.close()


@app.get("/health")
async def health_check():
    """Verifica saúde da API e conexões (endpoint público)"""
    health = {"api": "ok", "neo4j": "unknown", "redis": "unknown"}
    
    # Testar Neo4j
    try:
        driver = get_neo4j_driver()
        with driver.session(database=get_neo4j_database()) as session:
            session.run("RETURN 1")
        health["neo4j"] = "ok"
        driver.close()
    except Exception as e:
        health["neo4j"] = f"error: {str(e)}"
    
    # Testar Redis
    try:
        import redis
        from urllib.parse import quote
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Se a URL tem caracteres especiais na senha, fazer URL encoding
        if "@" in redis_url and "://" in redis_url:
            # Extrair partes da URL
            protocol, rest = redis_url.split("://", 1)
            if "@" in rest:
                auth, host = rest.rsplit("@", 1)
                user, password = auth.split(":", 1)
                # Fazer URL encoding da senha
                password_encoded = quote(password, safe='')
                redis_url = f"{protocol}://{user}:{password_encoded}@{host}"
        
        r = redis.from_url(redis_url)
        r.ping()
        health["redis"] = "ok"
    except Exception as e:
        health["redis"] = f"error: {str(e)}"
    
    return health


# ============================================
# Startup
# ============================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando GraphRAG API v3 - Arquitetura Assíncrona")
    print("📚 Documentação: http://localhost:8000/docs")
    print("")
    print("⚠️  Lembre-se de iniciar o worker Celery:")
    print("    python -m celery -A celery_worker worker --loglevel=info --pool=solo")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8000)
