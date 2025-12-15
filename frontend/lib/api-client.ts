const API_BASE_URL = "/api"

let authToken: string | null = null

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

  async listDocuments() {
    const response = await fetch(`${API_BASE_URL}/documents`, {
      headers: await this.getHeaders(),
    })
    if (!response.ok) {
      throw new Error("Falha ao listar documentos")
    }
    return response.json()
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

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || "Falha ao fazer upload do documento")
    }
    return response.json()
  },

  async deleteDocument(documentId: string) {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
      method: "DELETE",
      headers: await this.getHeaders(),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.error("Erro ao deletar:", response.status, errorData)
      throw new Error(errorData.detail || `Falha ao deletar documento: ${response.status}`)
    }
    return response.json()
  },

  async processDocument(documentId: string, model: string, type: string = "generic") {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/process`, {
      method: "POST",
      headers: await this.getHeaders(),
      body: JSON.stringify({ model, type }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || "Falha ao iniciar processamento")
    }
    return response.json()
  },

  async query(query: string, model: string) {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: "POST",
      headers: await this.getHeaders(),
      body: JSON.stringify({ query, model }),
    })

    if (!response.ok) {
      throw new Error("Falha ao realizar busca")
    }
    return response.json()
  },

  async getGraph(documentId: string) {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/graph`, {
      headers: await this.getHeaders(),
    })
    if (!response.ok) {
      throw new Error("Falha ao buscar grafo")
    }
    return response.json()
  }
}
