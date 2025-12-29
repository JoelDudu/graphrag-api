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

# Configurar LlamaIndex defaults - usar embedding local
from llm_providers import LLMProvider
Settings.embed_model = LLMProvider.get_embedding_model("claude")  # retorna local por padrão

app = FastAPI(
    title="GraphRAG API v3",
    description="API assíncrona para processamento de documentos com GraphRAG. Suporta PDF, Word, Excel, PowerPoint e mais.",
    version="3.0.0"
)

# Criar pasta de uploads
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

from fastapi.staticfiles import StaticFiles
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


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


# ============================================
# User Management Endpoints
# ============================================

from auth import (
    list_users, create_user, update_user, delete_user, get_user_by_id,
    UserCreate, UserUpdate, get_current_admin_user, ensure_admin_exists
)

@app.get("/users")
async def get_users(current_user: User = Depends(get_current_admin_user)):
    """Lista todos os usuários (admin only)"""
    users = list_users()
    return {"users": [u.model_dump() for u in users], "total": len(users)}


@app.post("/users")
async def create_new_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """Cria novo usuário (admin only)"""
    try:
        user = create_user(user_data)
        return {"message": f"Usuário '{user.username}' criado com sucesso", "user": user.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Retorna detalhes de um usuário (admin only)"""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user.model_dump(exclude={"password_hash"})


@app.put("/users/{user_id}")
async def update_user_details(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    """Atualiza usuário (admin only)"""
    user = update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"message": "Usuário atualizado com sucesso", "user": user.model_dump()}


@app.delete("/users/{user_id}")
async def delete_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Deleta usuário (admin only)"""
    # Não permitir auto-exclusão
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Não é possível excluir seu próprio usuário")
    
    success = delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"message": "Usuário excluído com sucesso"}


# ============================================
# Group Management Endpoints
# ============================================

from auth import (
    list_groups, create_group, update_group, delete_group, get_group,
    get_group_members, add_group_member, remove_group_member,
    GroupCreate, GroupUpdate, GroupMember
)

@app.get("/groups")
async def get_groups(current_user: User = Depends(get_current_active_user)):
    """Lista todos os grupos"""
    groups = list_groups()
    return {"groups": [g.model_dump() for g in groups], "total": len(groups)}


@app.post("/groups")
async def create_new_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_current_admin_user)
):
    """Cria novo grupo (admin only)"""
    try:
        group = create_group(group_data)
        return {"message": f"Grupo '{group.name}' criado com sucesso", "group": group.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/groups/{group_id}")
async def get_group_details(
    group_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Retorna detalhes de um grupo"""
    group = get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    return group.model_dump()


@app.put("/groups/{group_id}")
async def update_group_details(
    group_id: str,
    group_data: GroupUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    """Atualiza grupo (admin only)"""
    group = update_group(group_id, group_data)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    return {"message": "Grupo atualizado com sucesso", "group": group.model_dump()}


@app.delete("/groups/{group_id}")
async def delete_group_by_id(
    group_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Deleta grupo (admin only)"""
    success = delete_group(group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    return {"message": "Grupo excluído com sucesso"}


@app.get("/groups/{group_id}/members")
async def list_group_members(
    group_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Lista membros de um grupo"""
    group = get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    
    members = get_group_members(group_id)
    return {"members": [m.model_dump() for m in members], "total": len(members)}


@app.post("/groups/{group_id}/members")
async def add_member_to_group(
    group_id: str,
    member: GroupMember,
    current_user: User = Depends(get_current_admin_user)
):
    """Adiciona membro a um grupo (admin only)"""
    group = get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    
    success = add_group_member(group_id, member.user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Falha ao adicionar membro")
    return {"message": "Membro adicionado ao grupo"}


@app.delete("/groups/{group_id}/members/{user_id}")
async def remove_member_from_group(
    group_id: str,
    user_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Remove membro de um grupo (admin only)"""
    success = remove_group_member(group_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Membro não encontrado no grupo")
    return {"message": "Membro removido do grupo"}


# ============================================
# Document Sharing Endpoints
# ============================================

from auth import (
    share_document, unshare_document, get_document_shares, check_document_access,
    ShareRequest, ShareInfo
)

@app.get("/documents/{document_id}/permissions")
async def get_document_permissions(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Lista permissões de um documento (dono ou admin)"""
    # Verificar se tem permissão de gestão
    access = check_document_access(document_id, current_user.id, current_user.username)
    is_admin = current_user.is_admin
    
    if not is_admin and access.get('permission') not in ['owner', 'manage']:
        raise HTTPException(status_code=403, detail="Apenas o dono ou quem tem permissão de gestão pode ver permissões")
    
    shares = get_document_shares(document_id)
    return {"shares": [s.model_dump() for s in shares], "total": len(shares)}


@app.post("/documents/{document_id}/share")
async def share_document_endpoint(
    document_id: str,
    share_data: ShareRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Compartilha documento com usuário ou grupo (dono ou admin)"""
    # Verificar se tem permissão de gestão
    access = check_document_access(document_id, current_user.id, current_user.username)
    is_admin = current_user.is_admin
    
    if not is_admin and access.get('permission') not in ['owner', 'manage']:
        raise HTTPException(status_code=403, detail="Apenas o dono ou quem tem permissão de gestão pode compartilhar")
    
    if share_data.permission not in ['read', 'manage']:
        raise HTTPException(status_code=400, detail="Permissão deve ser 'read' ou 'manage'")
    
    success = share_document(
        document_id, 
        share_data.entity_type, 
        share_data.entity_id, 
        share_data.permission
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Falha ao compartilhar documento")
    
    return {"message": "Documento compartilhado com sucesso"}


@app.delete("/documents/{document_id}/share/{entity_type}/{entity_id}")
async def unshare_document_endpoint(
    document_id: str,
    entity_type: str,
    entity_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Remove compartilhamento de documento (dono ou admin)"""
    # Verificar se tem permissão de gestão
    access = check_document_access(document_id, current_user.id, current_user.username)
    is_admin = current_user.is_admin
    
    if not is_admin and access.get('permission') not in ['owner', 'manage']:
        raise HTTPException(status_code=403, detail="Apenas o dono ou quem tem permissão de gestão pode remover compartilhamento")
    
    success = unshare_document(document_id, entity_type, entity_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")
    
    return {"message": "Compartilhamento removido com sucesso"}

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
                    ownerId: $owner_id,
                    createdAt: datetime(),
                    updatedAt: datetime()
                })
            """, 
                document_id=document_id,
                filename=file.filename,
                file_path=str(file_path),
                file_size=file_size,
                file_type=file_type,
                owner_id=current_user.username
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
    # Se modelo é o default, usar DEFAULT_MODEL do .env
    model_to_use = request.model
    if model_to_use == "claude":  # default do Pydantic
        model_to_use = os.getenv("DEFAULT_MODEL", "claude")
    
    # Validar modelo
    if not LLMProvider.validate_model(model_to_use):
        raise HTTPException(
            status_code=400,
            detail=f"Modelo '{model_to_use}' não suportado. Use: {LLMProvider.SUPPORTED_MODELS}"
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
    process_document_task.delay(request.document_id, file_path, model_to_use, extraction_prompt)
    
    return ProcessResponse(
        document_id=request.document_id,
        status="Processing",
        model=model_to_use,
        message="Processamento iniciado. Use GET /status/{document_id} para acompanhar."
    )


@app.post("/cancel/{document_id}")
async def cancel_processing(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Cancela processamento travado e reseta documento para Pending.
    """
    driver = get_neo4j_driver()
    database = get_neo4j_database()
    
    try:
        with driver.session(database=database) as session:
            result = session.run("""
                MATCH (d:Document {id: $document_id})
                SET d.status = 'Pending', d.progress = 0, d.error = 'Cancelado pelo usuário'
                RETURN d.filename as filename
            """, document_id=document_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Documento não encontrado")
            
            return {
                "message": f"Processamento cancelado para '{record['filename']}'",
                "document_id": document_id,
                "status": "Pending"
            }
    finally:
        driver.close()

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


from auth import get_accessible_document_ids

@app.get("/documents")
async def list_documents(current_user: User = Depends(get_current_active_user)):
    """
    Lista documentos que o usuário tem acesso.
    - Documentos que é dono
    - Documentos compartilhados diretamente
    - Documentos compartilhados via grupo
    - Admin vê todos
    """
    driver = get_neo4j_driver()
    try:
        is_admin = current_user.is_admin
        
        with driver.session(database=get_neo4j_database()) as session:
            if is_admin:
                # Admin vê todos os documentos
                result = session.run("""
                    MATCH (d:Document)
                    RETURN d.id as id,
                           d.fileName as filename,
                           d.status as status,
                           d.processingProgress as progress,
                           d.processingModel as model,
                           d.total_chunks as chunks,
                           d.entityNodeCount as entities,
                           d.entityEntityRelCount as relationships,
                           d.processingError as error,
                           d.ownerId as owner_id,
                           toString(d.createdAt) as created_at
                    ORDER BY d.createdAt DESC
                """)
            else:
                # Usuário normal vê apenas documentos que tem acesso
                result = session.run("""
                    // Documentos que o usuário é dono
                    MATCH (d:Document)
                    WHERE d.ownerId = $username
                    RETURN d.id as id,
                           d.fileName as filename,
                           d.status as status,
                           d.processingProgress as progress,
                           d.processingModel as model,
                           d.total_chunks as chunks,
                           d.entityNodeCount as entities,
                           d.entityEntityRelCount as relationships,
                           d.processingError as error,
                           d.ownerId as owner_id,
                           toString(d.createdAt) as created_at,
                           'owner' as access_type
                    
                    UNION
                    
                    // Documentos compartilhados diretamente
                    MATCH (d:Document)-[r:SHARED_WITH]->(u:User {id: $user_id})
                    RETURN d.id as id,
                           d.fileName as filename,
                           d.status as status,
                           d.processingProgress as progress,
                           d.processingModel as model,
                           d.total_chunks as chunks,
                           d.entityNodeCount as entities,
                           d.entityEntityRelCount as relationships,
                           d.processingError as error,
                           d.ownerId as owner_id,
                           toString(d.createdAt) as created_at,
                           r.permission as access_type
                    
                    UNION
                    
                    // Documentos compartilhados via grupo
                    MATCH (u:User {id: $user_id})-[:MEMBER_OF]->(g:Group)<-[r:SHARED_WITH]-(d:Document)
                    RETURN DISTINCT d.id as id,
                           d.fileName as filename,
                           d.status as status,
                           d.processingProgress as progress,
                           d.processingModel as model,
                           d.total_chunks as chunks,
                           d.entityNodeCount as entities,
                           d.entityEntityRelCount as relationships,
                           d.processingError as error,
                           d.ownerId as owner_id,
                           toString(d.createdAt) as created_at,
                           r.permission as access_type
                """, username=current_user.username, user_id=current_user.id)
            
            documents = []
            seen_ids = set()  # Evitar duplicatas
            
            for record in result:
                doc_id = record["id"]
                if doc_id in seen_ids:
                    continue
                seen_ids.add(doc_id)
                
                owner_id = record["owner_id"]
                is_owner = owner_id == current_user.username
                access_type = record.get("access_type", "owner") if not is_admin else "admin"
                
                # Permissões baseadas no tipo de acesso
                can_download = is_admin or is_owner or access_type in ['owner', 'manage', 'read']
                can_delete = is_admin or is_owner or access_type == 'manage'
                can_share = is_admin or is_owner or access_type == 'manage'
                
                documents.append({
                    "document_id": doc_id,
                    "filename": record["filename"],
                    "status": record["status"],
                    "progress": record["progress"] or 0,
                    "model": record["model"],
                    "chunks": record["chunks"] or 0,
                    "entities": record["entities"] or 0,
                    "relationships": record["relationships"] or 0,
                    "error": record["error"],
                    "created_at": record["created_at"],
                    "owner_id": owner_id,
                    "access_type": access_type,
                    "can_download": can_download,
                    "can_delete": can_delete,
                    "can_share": can_share
                })
            
            # Ordenar por data de criação (mais recente primeiro)
            documents.sort(key=lambda x: x["created_at"] or "", reverse=True)
            
            return {"documents": documents, "total": len(documents)}
    finally:
        driver.close()


def query_graph(query: str, document_id: str, driver, database: str, top_k: int = 5) -> List[Dict]:
    """Busca por grafo - navega entidades e relacionamentos"""
    with driver.session(database=database) as session:
        # Extrair palavras-chave da query
        keywords = [word.lower() for word in query.split() if len(word) > 3]
        
        # Buscar entidades relacionadas (com ou sem filtro de documento)
        if document_id:
            cypher = """
                MATCH (d:Document {id: $document_id})<-[:PART_OF]-(c:Chunk)-[:HAS_ENTITY]->(e:__Entity__)
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
        else:
            # Busca em todos os documentos
            cypher = """
                MATCH (c:Chunk)-[:HAS_ENTITY]->(e:__Entity__)
                WHERE any(keyword IN $keywords WHERE toLower(e.id) CONTAINS keyword 
                                                  OR toLower(e.description) CONTAINS keyword)
                WITH e, c
                OPTIONAL MATCH (e)-[r]->(e2:__Entity__)
                RETURN e.id as entity_id, e.type as entity_type, e.description as entity_desc,
                       type(r) as rel_type, e2.id as related_entity,
                       c.text as chunk_text, c.position as chunk_position
                LIMIT $top_k
            """
            result = session.run(cypher, keywords=keywords, top_k=top_k)
        
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
            
            # Usar modelo do documento, ou especificado, ou padrão do .env
            default_model = os.getenv("DEFAULT_MODEL", "claude")
            model_to_use = request.model or record["model"] or default_model
        
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
            # Busca híbrida - usar mesma lógica de dimensão do processamento
            force_openai = os.getenv("FORCE_OPENAI_EMBEDDINGS", "").lower() == "true"
            embedding_dim = 1536 if force_openai else int(os.getenv("LOCAL_EMBEDDING_DIMENSION", "384"))
            vector_store = CustomNeo4jVectorStore(
                username=os.getenv("NEO4J_USER"),
                password=os.getenv("NEO4J_PASSWORD"),
                url=os.getenv("NEO4J_URI"),
                embedding_dimension=embedding_dim,
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
            # Busca semântica - usar mesma lógica de dimensão do processamento
            force_openai = os.getenv("FORCE_OPENAI_EMBEDDINGS", "").lower() == "true"
            embedding_dim = 1536 if force_openai else int(os.getenv("LOCAL_EMBEDDING_DIMENSION", "384"))
            vector_store = CustomNeo4jVectorStore(
                username=os.getenv("NEO4J_USER"),
                password=os.getenv("NEO4J_PASSWORD"),
                url=os.getenv("NEO4J_URI"),
                embedding_dimension=embedding_dim,
                database=database
            )
            
            index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
            query_engine = index.as_query_engine(similarity_top_k=request.top_k)
            response = query_engine.query(request.query)
            
            answer = str(response)
            sources = []
            print(f"🔍 Busca semântica: '{request.query}'")
            print(f"   Resposta: {answer[:200]}..." if len(answer) > 200 else f"   Resposta: {answer}")
            if hasattr(response, 'source_nodes'):
                print(f"   Fontes encontradas: {len(response.source_nodes)}")
                for node in response.source_nodes:
                    sources.append({
                        "text": node.text[:500] + "..." if len(node.text) > 500 else node.text,
                        "score": node.score if hasattr(node, 'score') else None,
                        "metadata": {**node.metadata, "search_type": "semantic"}
                    })
            else:
                print("   Nenhuma fonte encontrada (source_nodes não existe)")
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            model_used=model_to_use
        )
        
    finally:
        driver.close()


class ChatRequest(BaseModel):
    message: str
    document_id: str
    top_k: int = 5


class ChatResponse(BaseModel):
    response: str
    model_used: str
    sources: List[Dict[str, Any]] = []


@app.post("/chat", response_model=ChatResponse)
async def chat_with_document(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Chat IA com documento específico.
    Usa o mesmo modelo que processou o documento.
    Recupera contexto relevante e gera resposta.
    """
    driver = get_neo4j_driver()
    database = get_neo4j_database()
    
    try:
        with driver.session(database=database) as session:
            # Buscar modelo do documento
            doc_result = session.run("""
                MATCH (d:Document {id: $document_id})
                WHERE d.status = 'Completed'
                RETURN d.processingModel as model, d.filename as filename
            """, document_id=request.document_id)
            
            doc_record = doc_result.single()
            if not doc_record:
                raise HTTPException(
                    status_code=404,
                    detail="Documento não encontrado ou não processado"
                )
            
            default_model = os.getenv("DEFAULT_MODEL", "claude")
            model_to_use = doc_record["model"] or default_model
            filename = doc_record["filename"]
            
            # Buscar chunks relevantes do documento (busca por palavras-chave)
            keywords = [word.lower() for word in request.message.split() if len(word) > 2]
            
            chunks_result = session.run("""
                MATCH (d:Document {id: $document_id})<-[:PART_OF]-(c:Chunk)
                WHERE any(keyword IN $keywords WHERE toLower(c.text) CONTAINS keyword)
                RETURN c.text as text, c.position as position
                ORDER BY c.position
                LIMIT $top_k
            """, document_id=request.document_id, keywords=keywords, top_k=request.top_k)
            
            chunks = [record["text"] for record in chunks_result]
            
            # Se não encontrou por keywords, pegar primeiros chunks
            if not chunks:
                chunks_result = session.run("""
                    MATCH (d:Document {id: $document_id})<-[:PART_OF]-(c:Chunk)
                    RETURN c.text as text
                    ORDER BY c.position
                    LIMIT $top_k
                """, document_id=request.document_id, top_k=request.top_k)
                chunks = [record["text"] for record in chunks_result]
        
        if not chunks:
            return ChatResponse(
                response="Não encontrei conteúdo no documento para responder.",
                model_used=model_to_use,
                sources=[]
            )
        
        # Construir contexto
        context = "\n\n".join(chunks)
        
        # Gerar resposta com o LLM do documento
        llm = LLMProvider.get_llm(model_to_use)
        
        prompt = f"""Você é um assistente especializado em responder perguntas sobre o documento "{filename}".

Baseado no seguinte contexto do documento:

{context}

Responda à pergunta do usuário de forma clara e objetiva. Se a informação não estiver no contexto, diga que não encontrou essa informação específica no documento.

Pergunta: {request.message}

Resposta:"""

        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content=prompt)])
        answer = response.content if hasattr(response, 'content') else str(response)
        
        print(f"💬 Chat IA: '{request.message[:50]}...' -> {model_to_use}")
        print(f"   Contexto: {len(chunks)} chunks")
        print(f"   Resposta: {answer[:100]}...")
        
        return ChatResponse(
            response=answer,
            model_used=model_to_use,
            sources=[{"text": c[:200] + "..." if len(c) > 200 else c} for c in chunks[:3]]
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
    Apenas o dono do documento ou administradores podem excluir.
    """
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            # Verificar se existe e obter ownerId
            result = session.run("""
                MATCH (d:Document {id: $document_id})
                RETURN d.filePath as filePath, d.ownerId as ownerId
            """, document_id=document_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Documento não encontrado")
            
            # Verificar permissão: dono ou admin
            owner_id = record["ownerId"]
            is_owner = owner_id == current_user.username
            is_admin = getattr(current_user, 'is_admin', False) or current_user.username == "admin"
            
            if not is_owner and not is_admin:
                raise HTTPException(
                    status_code=403, 
                    detail="Acesso negado. Apenas o dono do documento ou administradores podem excluir."
                )
            
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


@app.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retorna os chunks de um documento.
    """
    driver = get_neo4j_driver()
    database = get_neo4j_database()
    
    try:
        with driver.session(database=database) as session:
            result = session.run("""
                MATCH (d:Document {id: $document_id})<-[:PART_OF]-(c:Chunk)
                RETURN c.id as id, c.text as text, c.position as position
                ORDER BY c.position
            """, document_id=document_id)
            
            chunks = []
            for record in result:
                chunks.append({
                    "id": record["id"],
                    "text": record["text"],
                    "position": record["position"]
                })
            
            return {"chunks": chunks, "total": len(chunks)}
    finally:
        driver.close()


@app.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Download do documento original.
    Apenas o dono do documento ou administradores podem baixar.
    """
    from fastapi.responses import FileResponse
    
    driver = get_neo4j_driver()
    database = get_neo4j_database()
    
    try:
        with driver.session(database=database) as session:
            result = session.run("""
                MATCH (d:Document {id: $document_id})
                RETURN d.filePath as filePath, d.fileName as fileName, d.ownerId as ownerId
            """, document_id=document_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Documento não encontrado")
            
            file_path = record["filePath"]
            file_name = record["fileName"]
            owner_id = record["ownerId"]
            
            # Verificar permissão: dono ou admin
            is_owner = owner_id == current_user.username
            is_admin = getattr(current_user, 'is_admin', False) or current_user.username == "admin"
            
            if not is_owner and not is_admin:
                raise HTTPException(
                    status_code=403, 
                    detail="Acesso negado. Apenas o dono do documento ou administradores podem baixar."
                )
            
            # Verificar se arquivo existe
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor")
            
            return FileResponse(
                path=file_path,
                filename=file_name,
                media_type="application/octet-stream"
            )
    finally:
        driver.close()

@app.get("/documents/{document_id}/graph")
async def get_document_graph(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retorna entidades e relacionamentos do documento diretamente do Neo4j.
    Não requer LLM - apenas leitura do grafo armazenado.
    """
    driver = get_neo4j_driver()
    database = get_neo4j_database()
    
    try:
        with driver.session(database=database) as session:
            # Verificar se documento existe
            doc_result = session.run("""
                MATCH (d:Document {id: $document_id})
                RETURN d.fileName as filename, d.status as status
            """, document_id=document_id)
            doc = doc_result.single()
            
            if not doc:
                raise HTTPException(status_code=404, detail="Documento não encontrado")
            
            if doc["status"] != "Completed":
                raise HTTPException(status_code=400, detail="Documento ainda não foi processado")
            
            # Buscar entidades conectadas ao documento via chunks
            entities_result = session.run("""
                MATCH (d:Document {id: $document_id})<-[:PART_OF]-(c:Chunk)-[:HAS_ENTITY]->(e:__Entity__)
                WITH DISTINCT e
                RETURN e.id as id, labels(e) as labels, e.description as description
                ORDER BY e.id
                LIMIT 500
            """, document_id=document_id)
            
            entities = []
            entity_ids = set()
            for record in entities_result:
                entity_id = record["id"]
                entity_ids.add(entity_id)
                # Pegar o primeiro label que não seja __Entity__
                labels = [l for l in record["labels"] if l != "__Entity__"]
                entity_type = labels[0] if labels else "Entity"
                entities.append({
                    "id": entity_id,
                    "type": entity_type,
                    "description": record["description"] or ""
                })
            
            # Buscar relacionamentos entre as entidades do documento
            relationships = []
            if entity_ids:
                rels_result = session.run("""
                    MATCH (d:Document {id: $document_id})<-[:PART_OF]-(c:Chunk)-[:HAS_ENTITY]->(source:__Entity__)
                    MATCH (source)-[r]->(target:__Entity__)
                    WHERE type(r) <> 'HAS_ENTITY' AND type(r) <> 'PART_OF'
                    WITH DISTINCT source, r, target
                    RETURN source.id as source, target.id as target, type(r) as type
                    LIMIT 500
                """, document_id=document_id)
                
                for record in rels_result:
                    relationships.append({
                        "source": record["source"],
                        "target": record["target"],
                        "type": record["type"]
                    })
            
            return {
                "document_id": document_id,
                "filename": doc["filename"],
                "entities": entities,
                "relationships": relationships,
                "total_entities": len(entities),
                "total_relationships": len(relationships)
            }
    finally:
        driver.close()


@app.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retorna todos os chunks do documento com seu conteúdo de texto.
    """
    driver = get_neo4j_driver()
    database = get_neo4j_database()
    
    try:
        with driver.session(database=database) as session:
            # Verificar se documento existe e pegar resumo
            doc_result = session.run("""
                MATCH (d:Document {id: $document_id})
                RETURN d.fileName as filename, d.status as status, d.summary as summary
            """, document_id=document_id)
            doc = doc_result.single()
            
            if not doc:
                raise HTTPException(status_code=404, detail="Documento não encontrado")
            
            # Buscar chunks do documento
            chunks_result = session.run("""
                MATCH (d:Document {id: $document_id})<-[:PART_OF]-(c:Chunk)
                RETURN c.id as id, c.text as text, c.chunkSeqId as seq_id
                ORDER BY c.chunkSeqId
            """, document_id=document_id)
            
            chunks = []
            full_text = []
            for record in chunks_result:
                chunk_text = record["text"] or ""
                chunks.append({
                    "id": record["id"],
                    "seq_id": record["seq_id"] or len(chunks),
                    "text": chunk_text,
                    "preview": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text
                })
                full_text.append(chunk_text)
            
            return {
                "document_id": document_id,
                "filename": doc["filename"],
                "summary": doc["summary"] or "",
                "chunks": chunks,
                "total_chunks": len(chunks),
                "full_text": "\n\n".join(full_text)
            }
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
                
                # Contar chunks
                chunks_result = session.run("""
                    MATCH (d:Document {id: $document_id})<-[:PART_OF]-(c:Chunk)
                    RETURN count(c) as chunk_count
                """, document_id=document_id)
                chunk_count = chunks_result.single()["chunk_count"]
                
                # Contar entidades conectadas via HAS_ENTITY
                entities_via_has = session.run("""
                    MATCH (d:Document {id: $document_id})<-[:PART_OF]-(c:Chunk)-[:HAS_ENTITY]->(e)
                    RETURN count(DISTINCT e) as entity_count, collect(DISTINCT labels(e))[0..5] as sample_labels
                """, document_id=document_id)
                entities_record = entities_via_has.single()
                entity_count = entities_record["entity_count"]
                sample_labels = entities_record["sample_labels"]
                
                # Contar todas as entidades __Entity__
                all_entities = session.run("""
                    MATCH (e:__Entity__)
                    RETURN count(e) as total_entities
                """)
                total_entities = all_entities.single()["total_entities"]
                
                # Verificar se há relacionamentos HAS_ENTITY
                has_entity_count = session.run("""
                    MATCH ()-[r:HAS_ENTITY]->()
                    RETURN count(r) as rel_count
                """)
                has_entity_rel_count = has_entity_count.single()["rel_count"]
                
                return {
                    "found": True, 
                    "document": doc,
                    "debug": {
                        "chunks_for_document": chunk_count,
                        "entities_connected_to_chunks": entity_count,
                        "sample_entity_labels": sample_labels,
                        "total_entities_in_db": total_entities,
                        "total_has_entity_relationships": has_entity_rel_count
                    }
                }
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
    
    # Garantir que existe usuário admin
    try:
        ensure_admin_exists()
    except Exception as e:
        print(f"⚠️  Erro ao verificar admin: {e}")
    
    print("")
    print("⚠️  Lembre-se de iniciar o worker Celery:")
    print("    python -m celery -A celery_worker worker --loglevel=info --pool=solo")
    print("")
    uvicorn.run(app, host="127.0.0.1", port=8000)