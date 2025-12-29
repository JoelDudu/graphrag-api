const API_BASE_URL = "/api"

let authToken: string | null = null
let isRedirecting = false  // Flag para evitar loop de redirects

// Handler para respostas 401 - limpa token e redireciona para login
function handleUnauthorized() {
  // Se já está redirecionando, não faz nada
  if (isRedirecting) {
    return
  }

  isRedirecting = true
  authToken = null

  // Limpar localStorage/sessionStorage e cookie (usando as mesmas chaves do auth-provider)
  if (typeof window !== "undefined") {
    localStorage.removeItem("api_token")
    localStorage.removeItem("username")
    sessionStorage.removeItem("api_token")
    // Limpar cookie também
    document.cookie = "api_token=; path=/; max-age=0"
    // Redirecionar para login
    window.location.href = "/login"
  }
}

// Função auxiliar para verificar resposta e tratar 401
async function checkResponse(response: Response, errorMessage: string) {
  if (response.status === 401) {
    handleUnauthorized()
    // Não lança erro se já está redirecionando
    if (isRedirecting) {
      return { _redirecting: true }  // Retorna objeto placeholder
    }
    throw new Error("Sessão expirada. Por favor, faça login novamente.")
  }
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || errorMessage)
  }
  return response.json()
}

export const apiClient = {
  setToken(token: string | null) {
    authToken = token
  },

  clearToken() {
    authToken = null
  },

  async getHeaders(contentType: string | null = "application/json") {
    const headers: HeadersInit = {}
    if (contentType) {
      headers["Content-Type"] = contentType
    }
    if (authToken) {
      headers["Authorization"] = `Bearer ${authToken}`
    }
    return headers
  },

  async login(username: string, password: string) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    })

    if (!response.ok) {
      throw new Error("Falha na autenticação")
    }
    return response.json()
  },

  async getMe() {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: await this.getHeaders(),
    })
    return checkResponse(response, "Falha ao obter dados do usuário")
  },

  async listDocuments() {
    const response = await fetch(`${API_BASE_URL}/documents`, {
      headers: await this.getHeaders(),
    })
    return checkResponse(response, "Falha ao listar documentos")
  },

  async uploadDocument(file: File) {
    const formData = new FormData()
    formData.append("file", file)

    // Para upload de arquivo, não definimos Content-Type manualmente (o browser define com boundary)
    const headers = await this.getHeaders(null)

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      headers,
      body: formData,
    })

    return checkResponse(response, "Falha ao fazer upload do documento")
  },

  async deleteDocument(documentId: string) {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
      method: "DELETE",
      headers: await this.getHeaders(),
    })

    return checkResponse(response, "Falha ao deletar documento")
  },

  async processDocument(documentId: string, model: string, type: string = "generic") {
    const response = await fetch(`${API_BASE_URL}/documents/process`, {
      method: "POST",
      headers: await this.getHeaders(),
      body: JSON.stringify({ document_id: documentId, model, doc_type: type }),
    })

    return checkResponse(response, "Falha ao iniciar processamento")
  },

  async query(query: string, search_type: string = "semantic", document_id?: string) {
    const body: Record<string, any> = { query, search_type }
    if (document_id) {
      body.document_id = document_id
    }

    const response = await fetch(`${API_BASE_URL}/query`, {
      method: "POST",
      headers: await this.getHeaders(),
      body: JSON.stringify(body),
    })

    return checkResponse(response, "Falha ao realizar busca")
  },

  async getGraph(documentId: string) {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/graph`, {
      headers: await this.getHeaders(),
    })
    return checkResponse(response, "Falha ao buscar grafo")
  },

  async getDocumentChunks(documentId: string) {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/chunks`, {
      headers: await this.getHeaders(),
    })
    return checkResponse(response, "Falha ao buscar chunks do documento")
  },

  async getDocumentStatus(documentId: string) {
    const response = await fetch(`${API_BASE_URL}/documents/status/${documentId}`, {
      headers: await this.getHeaders(),
    })
    return checkResponse(response, "Falha ao obter status do documento")
  },

  async chat(message: string, documentId: string) {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: await this.getHeaders(),
      body: JSON.stringify({ message, document_id: documentId }),
    })

    return checkResponse(response, "Falha ao processar chat")
  },

  async cancelProcessing(documentId: string) {
    const response = await fetch(`${API_BASE_URL}/cancel/${documentId}`, {
      method: "POST",
      headers: await this.getHeaders(),
    })

    return checkResponse(response, "Falha ao cancelar processamento")
  },

  async downloadDocument(documentId: string) {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/download`, {
      headers: await this.getHeaders(),
    })

    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || "Falha ao baixar documento")
    }

    return response.blob()
  },

  // ============================================
  // User Management
  // ============================================

  async getUsers() {
    const response = await fetch(`${API_BASE_URL}/users`, {
      headers: await this.getHeaders(),
    })
    return checkResponse(response, "Falha ao buscar usuários")
  },

  async createUser(userData: { username: string; email?: string; password: string; is_admin?: boolean }) {
    const response = await fetch(`${API_BASE_URL}/users`, {
      method: "POST",
      headers: await this.getHeaders(),
      body: JSON.stringify(userData),
    })
    return checkResponse(response, "Falha ao criar usuário")
  },

  async updateUser(userId: string, userData: { email?: string; password?: string; is_admin?: boolean; is_active?: boolean }) {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
      method: "PUT",
      headers: await this.getHeaders(),
      body: JSON.stringify(userData),
    })
    return checkResponse(response, "Falha ao atualizar usuário")
  },

  async deleteUser(userId: string) {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
      method: "DELETE",
      headers: await this.getHeaders(),
    })
    return checkResponse(response, "Falha ao excluir usuário")
  },

  // ============================================
  // Group Management
  // ============================================

  async getGroups() {
    const response = await fetch(`${API_BASE_URL}/groups`, {
      headers: await this.getHeaders(),
    })
    return checkResponse(response, "Falha ao buscar grupos")
  },

  async createGroup(groupData: { name: string; description?: string }) {
    const response = await fetch(`${API_BASE_URL}/groups`, {
      method: "POST",
      headers: await this.getHeaders(),
      body: JSON.stringify(groupData),
    })
    return checkResponse(response, "Falha ao criar grupo")
  },

  async updateGroup(groupId: string, groupData: { name?: string; description?: string }) {
    const response = await fetch(`${API_BASE_URL}/groups/${groupId}`, {
      method: "PUT",
      headers: await this.getHeaders(),
      body: JSON.stringify(groupData),
    })
    return checkResponse(response, "Falha ao atualizar grupo")
  },

  async deleteGroup(groupId: string) {
    const response = await fetch(`${API_BASE_URL}/groups/${groupId}`, {
      method: "DELETE",
      headers: await this.getHeaders(),
    })
    return checkResponse(response, "Falha ao excluir grupo")
  },

  async getGroupMembers(groupId: string) {
    const response = await fetch(`${API_BASE_URL}/groups/${groupId}/members`, {
      headers: await this.getHeaders(),
    })
    return checkResponse(response, "Falha ao buscar membros")
  },

  async addGroupMember(groupId: string, userId: string) {
    const response = await fetch(`${API_BASE_URL}/groups/${groupId}/members`, {
      method: "POST",
      headers: await this.getHeaders(),
      body: JSON.stringify({ user_id: userId }),
    })
    return checkResponse(response, "Falha ao adicionar membro")
  },

  async removeGroupMember(groupId: string, userId: string) {
    const response = await fetch(`${API_BASE_URL}/groups/${groupId}/members/${userId}`, {
      method: "DELETE",
      headers: await this.getHeaders(),
    })
    return checkResponse(response, "Falha ao remover membro")
  },

  // ============================================
  // Document Sharing
  // ============================================

  async getDocumentPermissions(documentId: string) {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/permissions`, {
      headers: await this.getHeaders(),
    })
    return checkResponse(response, "Falha ao buscar permissões")
  },

  async shareDocument(documentId: string, entityType: 'user' | 'group', entityId: string, permission: 'read' | 'manage') {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/share`, {
      method: "POST",
      headers: await this.getHeaders(),
      body: JSON.stringify({ entity_type: entityType, entity_id: entityId, permission }),
    })
    return checkResponse(response, "Falha ao compartilhar documento")
  },

  async unshareDocument(documentId: string, entityType: string, entityId: string) {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/share/${entityType}/${entityId}`, {
      method: "DELETE",
      headers: await this.getHeaders(),
    })
    return checkResponse(response, "Falha ao remover compartilhamento")
  }
}
