"""
Módulo de autenticação JWT para a API GraphRAG
Usuários armazenados no Neo4j
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from neo4j import GraphDatabase

# Configurações JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 horas padrão

# Security scheme
security = HTTPBearer()


# ============================================
# Pydantic Models
# ============================================

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    id: Optional[str] = None
    username: str
    email: Optional[str] = None
    is_admin: bool = False
    is_active: bool = True


class UserInDB(User):
    password_hash: str


class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    is_admin: bool = False


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


# ============================================
# Neo4j Connection
# ============================================

def get_neo4j_driver():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(user, password))


def get_neo4j_database():
    return os.getenv("NEO4J_DATABASE", "neo4j")


# ============================================
# Password Utilities
# ============================================

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verifica se a senha está correta"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == password_hash


def get_password_hash(password: str) -> str:
    """Gera hash da senha"""
    return hashlib.sha256(password.encode()).hexdigest()


# ============================================
# User CRUD (Neo4j)
# ============================================

def get_user(username: str) -> Optional[UserInDB]:
    """Busca usuário no Neo4j"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (u:User {username: $username})
                RETURN u.id as id, u.username as username, u.email as email,
                       u.password_hash as password_hash, u.is_admin as is_admin,
                       u.is_active as is_active
            """, username=username)
            
            record = result.single()
            if not record:
                return None
            
            return UserInDB(
                id=record["id"],
                username=record["username"],
                email=record["email"],
                password_hash=record["password_hash"],
                is_admin=record["is_admin"] or False,
                is_active=record["is_active"] if record["is_active"] is not None else True
            )
    finally:
        driver.close()


def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """Busca usuário por ID no Neo4j"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})
                RETURN u.id as id, u.username as username, u.email as email,
                       u.password_hash as password_hash, u.is_admin as is_admin,
                       u.is_active as is_active
            """, user_id=user_id)
            
            record = result.single()
            if not record:
                return None
            
            return UserInDB(
                id=record["id"],
                username=record["username"],
                email=record["email"],
                password_hash=record["password_hash"],
                is_admin=record["is_admin"] or False,
                is_active=record["is_active"] if record["is_active"] is not None else True
            )
    finally:
        driver.close()


def list_users() -> List[User]:
    """Lista todos os usuários"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (u:User)
                RETURN u.id as id, u.username as username, u.email as email,
                       u.is_admin as is_admin, u.is_active as is_active
                ORDER BY u.username
            """)
            
            users = []
            for record in result:
                users.append(User(
                    id=record["id"],
                    username=record["username"],
                    email=record["email"],
                    is_admin=record["is_admin"] or False,
                    is_active=record["is_active"] if record["is_active"] is not None else True
                ))
            return users
    finally:
        driver.close()


def create_user(user_data: UserCreate) -> User:
    """Cria novo usuário no Neo4j"""
    import uuid
    
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            # Verificar se username já existe
            existing = session.run("""
                MATCH (u:User {username: $username})
                RETURN u
            """, username=user_data.username).single()
            
            if existing:
                raise ValueError(f"Usuário '{user_data.username}' já existe")
            
            user_id = str(uuid.uuid4())
            password_hash = get_password_hash(user_data.password)
            
            session.run("""
                CREATE (u:User {
                    id: $id,
                    username: $username,
                    email: $email,
                    password_hash: $password_hash,
                    is_admin: $is_admin,
                    is_active: true,
                    created_at: datetime()
                })
            """, 
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                password_hash=password_hash,
                is_admin=user_data.is_admin
            )
            
            return User(
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                is_admin=user_data.is_admin,
                is_active=True
            )
    finally:
        driver.close()


def update_user(user_id: str, user_data: UserUpdate) -> Optional[User]:
    """Atualiza usuário no Neo4j"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            # Construir SET dinamicamente
            set_clauses = []
            params = {"user_id": user_id}
            
            if user_data.email is not None:
                set_clauses.append("u.email = $email")
                params["email"] = user_data.email
            
            if user_data.password is not None:
                set_clauses.append("u.password_hash = $password_hash")
                params["password_hash"] = get_password_hash(user_data.password)
            
            if user_data.is_admin is not None:
                set_clauses.append("u.is_admin = $is_admin")
                params["is_admin"] = user_data.is_admin
            
            if user_data.is_active is not None:
                set_clauses.append("u.is_active = $is_active")
                params["is_active"] = user_data.is_active
            
            if not set_clauses:
                return get_user_by_id(user_id)
            
            set_clauses.append("u.updated_at = datetime()")
            
            query = f"""
                MATCH (u:User {{id: $user_id}})
                SET {', '.join(set_clauses)}
                RETURN u.id as id, u.username as username, u.email as email,
                       u.is_admin as is_admin, u.is_active as is_active
            """
            
            result = session.run(query, **params)
            record = result.single()
            
            if not record:
                return None
            
            return User(
                id=record["id"],
                username=record["username"],
                email=record["email"],
                is_admin=record["is_admin"] or False,
                is_active=record["is_active"] if record["is_active"] is not None else True
            )
    finally:
        driver.close()


def delete_user(user_id: str) -> bool:
    """Deleta usuário do Neo4j"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})
                DETACH DELETE u
                RETURN count(u) as deleted
            """, user_id=user_id)
            
            record = result.single()
            return record["deleted"] > 0
    finally:
        driver.close()


def ensure_admin_exists():
    """Garante que existe pelo menos um usuário admin"""
    admin = get_user("admin")
    if not admin:
        print("🔧 Criando usuário admin padrão...")
        create_user(UserCreate(
            username="admin",
            email="admin@localhost",
            password="admin123",
            is_admin=True
        ))
        print("   ✅ Usuário 'admin' criado com senha 'admin123'")


# ============================================
# Authentication
# ============================================

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Autentica usuário"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Valida token JWT e retorna usuário atual"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        is_active=user.is_active
    )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Retorna usuário ativo"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Retorna usuário admin"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user


# ============================================
# Group Models
# ============================================

class Group(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class GroupMember(BaseModel):
    user_id: str


# ============================================
# Group CRUD (Neo4j)
# ============================================

def list_groups() -> List[Group]:
    """Lista todos os grupos"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (g:Group)
                RETURN g.id as id, g.name as name, g.description as description
                ORDER BY g.name
            """)
            
            groups = []
            for record in result:
                groups.append(Group(
                    id=record["id"],
                    name=record["name"],
                    description=record["description"]
                ))
            return groups
    finally:
        driver.close()


def get_group(group_id: str) -> Optional[Group]:
    """Busca grupo por ID"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (g:Group {id: $group_id})
                RETURN g.id as id, g.name as name, g.description as description
            """, group_id=group_id)
            
            record = result.single()
            if not record:
                return None
            
            return Group(
                id=record["id"],
                name=record["name"],
                description=record["description"]
            )
    finally:
        driver.close()


def create_group(group_data: GroupCreate) -> Group:
    """Cria novo grupo"""
    import uuid
    
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            # Verificar se nome já existe
            existing = session.run("""
                MATCH (g:Group {name: $name})
                RETURN g
            """, name=group_data.name).single()
            
            if existing:
                raise ValueError(f"Grupo '{group_data.name}' já existe")
            
            group_id = str(uuid.uuid4())
            
            session.run("""
                CREATE (g:Group {
                    id: $id,
                    name: $name,
                    description: $description,
                    created_at: datetime()
                })
            """, 
                id=group_id,
                name=group_data.name,
                description=group_data.description
            )
            
            return Group(
                id=group_id,
                name=group_data.name,
                description=group_data.description
            )
    finally:
        driver.close()


def update_group(group_id: str, group_data: GroupUpdate) -> Optional[Group]:
    """Atualiza grupo"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            set_clauses = []
            params = {"group_id": group_id}
            
            if group_data.name is not None:
                set_clauses.append("g.name = $name")
                params["name"] = group_data.name
            
            if group_data.description is not None:
                set_clauses.append("g.description = $description")
                params["description"] = group_data.description
            
            if not set_clauses:
                return get_group(group_id)
            
            set_clauses.append("g.updated_at = datetime()")
            
            query = f"""
                MATCH (g:Group {{id: $group_id}})
                SET {', '.join(set_clauses)}
                RETURN g.id as id, g.name as name, g.description as description
            """
            
            result = session.run(query, **params)
            record = result.single()
            
            if not record:
                return None
            
            return Group(
                id=record["id"],
                name=record["name"],
                description=record["description"]
            )
    finally:
        driver.close()


def delete_group(group_id: str) -> bool:
    """Deleta grupo"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (g:Group {id: $group_id})
                DETACH DELETE g
                RETURN count(g) as deleted
            """, group_id=group_id)
            
            record = result.single()
            return record["deleted"] > 0
    finally:
        driver.close()


def get_group_members(group_id: str) -> List[User]:
    """Lista membros de um grupo"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (u:User)-[:MEMBER_OF]->(g:Group {id: $group_id})
                RETURN u.id as id, u.username as username, u.email as email,
                       u.is_admin as is_admin, u.is_active as is_active
                ORDER BY u.username
            """, group_id=group_id)
            
            users = []
            for record in result:
                users.append(User(
                    id=record["id"],
                    username=record["username"],
                    email=record["email"],
                    is_admin=record["is_admin"] or False,
                    is_active=record["is_active"] if record["is_active"] is not None else True
                ))
            return users
    finally:
        driver.close()


def add_group_member(group_id: str, user_id: str) -> bool:
    """Adiciona membro a um grupo"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (u:User {id: $user_id}), (g:Group {id: $group_id})
                MERGE (u)-[:MEMBER_OF]->(g)
                RETURN count(*) as created
            """, user_id=user_id, group_id=group_id)
            
            record = result.single()
            return record["created"] > 0
    finally:
        driver.close()


def remove_group_member(group_id: str, user_id: str) -> bool:
    """Remove membro de um grupo"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[r:MEMBER_OF]->(g:Group {id: $group_id})
                DELETE r
                RETURN count(r) as deleted
            """, user_id=user_id, group_id=group_id)
            
            record = result.single()
            return record["deleted"] > 0
    finally:
        driver.close()


def get_user_groups(user_id: str) -> List[Group]:
    """Lista grupos de um usuário"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:MEMBER_OF]->(g:Group)
                RETURN g.id as id, g.name as name, g.description as description
                ORDER BY g.name
            """, user_id=user_id)
            
            groups = []
            for record in result:
                groups.append(Group(
                    id=record["id"],
                    name=record["name"],
                    description=record["description"]
                ))
            return groups
    finally:
        driver.close()


# ============================================
# Document Sharing Models
# ============================================

class ShareRequest(BaseModel):
    entity_type: str  # 'user' ou 'group'
    entity_id: str
    permission: str = 'read'  # 'read' ou 'manage'


class ShareInfo(BaseModel):
    entity_type: str
    entity_id: str
    entity_name: str
    permission: str


# ============================================
# Document Sharing Functions
# ============================================

def share_document(document_id: str, entity_type: str, entity_id: str, permission: str = 'read') -> bool:
    """Compartilha documento com usuário ou grupo"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            if entity_type == 'user':
                result = session.run("""
                    MATCH (d:Document {id: $document_id}), (u:User {id: $entity_id})
                    MERGE (d)-[r:SHARED_WITH]->(u)
                    SET r.permission = $permission, r.created_at = datetime()
                    RETURN count(r) as created
                """, document_id=document_id, entity_id=entity_id, permission=permission)
            elif entity_type == 'group':
                result = session.run("""
                    MATCH (d:Document {id: $document_id}), (g:Group {id: $entity_id})
                    MERGE (d)-[r:SHARED_WITH]->(g)
                    SET r.permission = $permission, r.created_at = datetime()
                    RETURN count(r) as created
                """, document_id=document_id, entity_id=entity_id, permission=permission)
            else:
                return False
            
            record = result.single()
            return record["created"] > 0
    finally:
        driver.close()


def unshare_document(document_id: str, entity_type: str, entity_id: str) -> bool:
    """Remove compartilhamento de documento"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            if entity_type == 'user':
                result = session.run("""
                    MATCH (d:Document {id: $document_id})-[r:SHARED_WITH]->(u:User {id: $entity_id})
                    DELETE r
                    RETURN count(r) as deleted
                """, document_id=document_id, entity_id=entity_id)
            elif entity_type == 'group':
                result = session.run("""
                    MATCH (d:Document {id: $document_id})-[r:SHARED_WITH]->(g:Group {id: $entity_id})
                    DELETE r
                    RETURN count(r) as deleted
                """, document_id=document_id, entity_id=entity_id)
            else:
                return False
            
            record = result.single()
            return record["deleted"] > 0
    finally:
        driver.close()


def get_document_shares(document_id: str) -> List[ShareInfo]:
    """Lista todos os compartilhamentos de um documento"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            # Buscar compartilhamentos com usuários
            users_result = session.run("""
                MATCH (d:Document {id: $document_id})-[r:SHARED_WITH]->(u:User)
                RETURN 'user' as type, u.id as id, u.username as name, r.permission as permission
            """, document_id=document_id)
            
            # Buscar compartilhamentos com grupos
            groups_result = session.run("""
                MATCH (d:Document {id: $document_id})-[r:SHARED_WITH]->(g:Group)
                RETURN 'group' as type, g.id as id, g.name as name, r.permission as permission
            """, document_id=document_id)
            
            shares = []
            for record in users_result:
                shares.append(ShareInfo(
                    entity_type=record["type"],
                    entity_id=record["id"],
                    entity_name=record["name"],
                    permission=record["permission"] or "read"
                ))
            
            for record in groups_result:
                shares.append(ShareInfo(
                    entity_type=record["type"],
                    entity_id=record["id"],
                    entity_name=record["name"],
                    permission=record["permission"] or "read"
                ))
            
            return shares
    finally:
        driver.close()


def check_document_access(document_id: str, user_id: str, username: str) -> dict:
    """
    Verifica se usuário tem acesso ao documento.
    Retorna: {'has_access': bool, 'permission': str, 'reason': str}
    """
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            # Verificar se é dono ou admin
            owner_result = session.run("""
                MATCH (d:Document {id: $document_id})
                RETURN d.ownerId as owner_id
            """, document_id=document_id)
            
            owner_record = owner_result.single()
            if not owner_record:
                return {'has_access': False, 'permission': None, 'reason': 'document_not_found'}
            
            owner_id = owner_record["owner_id"]
            
            # Verificar se é dono
            if owner_id == username:
                return {'has_access': True, 'permission': 'owner', 'reason': 'owner'}
            
            # Verificar se tem compartilhamento direto
            direct_result = session.run("""
                MATCH (d:Document {id: $document_id})-[r:SHARED_WITH]->(u:User {id: $user_id})
                RETURN r.permission as permission
            """, document_id=document_id, user_id=user_id)
            
            direct_record = direct_result.single()
            if direct_record:
                return {
                    'has_access': True, 
                    'permission': direct_record["permission"] or 'read', 
                    'reason': 'direct_share'
                }
            
            # Verificar se tem acesso via grupo
            group_result = session.run("""
                MATCH (u:User {id: $user_id})-[:MEMBER_OF]->(g:Group)<-[r:SHARED_WITH]-(d:Document {id: $document_id})
                RETURN r.permission as permission, g.name as group_name
                LIMIT 1
            """, document_id=document_id, user_id=user_id)
            
            group_record = group_result.single()
            if group_record:
                return {
                    'has_access': True, 
                    'permission': group_record["permission"] or 'read', 
                    'reason': f'group:{group_record["group_name"]}'
                }
            
            return {'has_access': False, 'permission': None, 'reason': 'no_access'}
    finally:
        driver.close()


def get_accessible_document_ids(user_id: str, username: str) -> List[str]:
    """Retorna IDs de todos os documentos que o usuário pode acessar"""
    driver = get_neo4j_driver()
    try:
        with driver.session(database=get_neo4j_database()) as session:
            result = session.run("""
                // Documentos que o usuário é dono
                MATCH (d:Document)
                WHERE d.ownerId = $username
                RETURN DISTINCT d.id as id
                
                UNION
                
                // Documentos compartilhados diretamente
                MATCH (d:Document)-[:SHARED_WITH]->(u:User {id: $user_id})
                RETURN DISTINCT d.id as id
                
                UNION
                
                // Documentos compartilhados via grupo
                MATCH (u:User {id: $user_id})-[:MEMBER_OF]->(g:Group)<-[:SHARED_WITH]-(d:Document)
                RETURN DISTINCT d.id as id
            """, user_id=user_id, username=username)
            
            return [record["id"] for record in result]
    finally:
        driver.close()
