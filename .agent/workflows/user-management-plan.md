---
description: Plano de implementação de gerenciamento de usuários e compartilhamento de documentos
---

# Sistema de Gerenciamento de Usuários e Permissões

## Modelo de Dados (Neo4j)

### Nós:
```cypher
(:User {
  id: string,
  username: string,
  email: string,
  password_hash: string,
  is_admin: boolean,
  is_active: boolean,
  created_at: datetime
})

(:Group {
  id: string,
  name: string,
  description: string,
  created_at: datetime
})
```

### Relacionamentos:
```cypher
(:User)-[:MEMBER_OF]->(:Group)
(:Document)-[:SHARED_WITH {permission: 'read'|'manage'}]->(:User)
(:Document)-[:SHARED_WITH {permission: 'read'|'manage'}]->(:Group)
```

## Endpoints API

### Usuários
- `GET /users` - Listar usuários (admin)
- `POST /users` - Criar usuário (admin)
- `PUT /users/{id}` - Editar usuário (admin)
- `DELETE /users/{id}` - Deletar usuário (admin)
- `GET /users/me` - Dados do usuário logado

### Grupos
- `GET /groups` - Listar grupos
- `POST /groups` - Criar grupo (admin)
- `PUT /groups/{id}` - Editar grupo (admin)
- `DELETE /groups/{id}` - Deletar grupo (admin)
- `POST /groups/{id}/members` - Adicionar membros
- `DELETE /groups/{id}/members/{user_id}` - Remover membro

### Compartilhamento de Documentos
- `GET /documents/{id}/permissions` - Listar permissões
- `POST /documents/{id}/share` - Compartilhar (com user ou group)
- `DELETE /documents/{id}/share/{entity_type}/{entity_id}` - Remover

## Frontend

### Novas Telas (em Configurações ou menu admin):
1. **Gestão de Usuários** - CRUD de usuários
2. **Gestão de Grupos** - CRUD de grupos + membros

### No Document Viewer:
- Botão "Compartilhar" → Modal com:
  - Buscar usuários/grupos
  - Selecionar permissão (Leitura/Gestão)
  - Lista de quem tem acesso
  - Remover acesso

## Fases de Implementação

### Fase 1: Backend - Usuários
- [ ] Migrar auth de fake_users para Neo4j
- [ ] CRUD de usuários
- [ ] Hash de senha com bcrypt

### Fase 2: Backend - Grupos
- [ ] CRUD de grupos
- [ ] Gerenciar membros

### Fase 3: Backend - Permissões de Documentos
- [ ] Endpoints de compartilhamento
- [ ] Ajustar list_documents para respeitar permissões
- [ ] Ajustar outros endpoints

### Fase 4: Frontend - Admin
- [ ] Tela de Gestão de Usuários
- [ ] Tela de Gestão de Grupos

### Fase 5: Frontend - Compartilhamento
- [ ] Botão e Modal de compartilhar
- [ ] Lista de permissões do documento
