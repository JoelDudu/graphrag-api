"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { AlertCircle, Loader2, Copy, Check, Users, Users2 } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { useAuth } from "@/lib/auth-context"
import { Alert, AlertDescription } from "@/components/ui/alert"
import UserManagement from "@/components/admin/user-management"
import GroupManagement from "@/components/admin/group-management"

interface SharedUser {
  email: string
  role: "viewer" | "editor" | "admin"
  added_date: string
}

interface Document {
  document_id: string
  filename: string
  status: string
}

export default function SettingsTab() {
  const [email, setEmail] = useState("user@example.com")
  const [notifications, setNotifications] = useState(true)
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocForShare, setSelectedDocForShare] = useState("")
  const [shared, setShared] = useState<SharedUser[]>([])
  const [newEmail, setNewEmail] = useState("")
  const [newRole, setNewRole] = useState<"viewer" | "editor" | "admin">("viewer")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [successMessage, setSuccessMessage] = useState("")
  const [copiedEmail, setCopiedEmail] = useState("")
  const [isAdmin, setIsAdmin] = useState(false)
  const { logout } = useAuth()

  useEffect(() => {
    loadDocuments()
    checkAdmin()
  }, [])

  const checkAdmin = async () => {
    try {
      const me = await apiClient.getMe()
      // Check if it's redirecting (401 response)
      if (me && !me._redirecting) {
        setIsAdmin(me.is_admin || false)
      }
    } catch (err) {
      // Silently fail - user just won't see admin tabs
      // This is expected when API is not reachable
    }
  }

  useEffect(() => {
    if (selectedDocForShare) {
      loadSharedUsers()
    }
  }, [selectedDocForShare])

  const loadDocuments = async () => {
    try {
      const response = await apiClient.listDocuments()
      // Handle both array response and object with documents property
      const docs = Array.isArray(response) ? response : (response?.documents || [])
      setDocuments(docs)
      if (docs.length > 0) {
        setSelectedDocForShare(docs[0].document_id)
      }
    } catch (err) {
      console.error("Erro ao carregar documentos", err)
    }
  }

  const loadSharedUsers = async () => {
    try {
      const result = await apiClient.getDocumentPermissions(selectedDocForShare)
      // Converter para formato antigo para manter compatibilidade visual
      const shares = (result.shares || []).filter((s: any) => s.entity_type === 'user')
      setShared(shares.map((s: any) => ({
        email: s.entity_name,
        role: s.permission === 'manage' ? 'admin' : 'viewer',
        added_date: new Date().toISOString(),
        entity_id: s.entity_id
      })))
    } catch (err) {
      console.error("Erro ao carregar usuários compartilhados")
    }
  }

  const handleAddSharedUser = async () => {
    if (!newEmail.trim() || !selectedDocForShare) return

    setIsLoading(true)
    setError("")
    setSuccessMessage("")

    try {
      // Buscar user_id pelo username (simplificado - adiciona como username)
      const permission = newRole === 'admin' ? 'manage' : 'read'
      await apiClient.shareDocument(selectedDocForShare, 'user', newEmail, permission as 'read' | 'manage')
      await loadSharedUsers()
      setNewEmail("")
      setNewRole("viewer")
      setSuccessMessage(`${newEmail} adicionado com sucesso!`)
      setTimeout(() => setSuccessMessage(""), 3000)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao compartilhar"
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRemoveSharedUser = async (userEmail: string, entityId?: string) => {
    if (!selectedDocForShare) return

    setError("")
    setSuccessMessage("")

    try {
      await apiClient.unshareDocument(selectedDocForShare, 'user', entityId || userEmail)
      await loadSharedUsers()
      setSuccessMessage(`${userEmail} removido com sucesso!`)
      setTimeout(() => setSuccessMessage(""), 3000)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao remover usuário"
      setError(message)
    }
  }

  const handleUpdateRole = async (userEmail: string, newRole: "viewer" | "editor" | "admin", entityId?: string) => {
    if (!selectedDocForShare) return

    setError("")
    setSuccessMessage("")

    try {
      // Para atualizar, primeiro remove e depois adiciona com nova permissão
      const permission = newRole === 'admin' ? 'manage' : 'read'
      await apiClient.unshareDocument(selectedDocForShare, 'user', entityId || userEmail)
      await apiClient.shareDocument(selectedDocForShare, 'user', entityId || userEmail, permission as 'read' | 'manage')
      await loadSharedUsers()
      setSuccessMessage(`Permissão atualizada para ${newRole}!`)
      setTimeout(() => setSuccessMessage(""), 3000)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao atualizar permissão"
      setError(message)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedEmail(text)
    setTimeout(() => setCopiedEmail(""), 2000)
  }

  const getRoleDescription = (role: string) => {
    switch (role) {
      case "viewer":
        return "Apenas visualizar documentos"
      case "editor":
        return "Visualizar e fazer buscas"
      case "admin":
        return "Acesso total ao documento"
      default:
        return ""
    }
  }

  return (
    <Tabs defaultValue="account" className="w-full space-y-6">
      <TabsList className="flex-wrap h-auto">
        <TabsTrigger value="account">Conta</TabsTrigger>
        <TabsTrigger value="sharing">Compartilhamento</TabsTrigger>
        <TabsTrigger value="notifications">Notificações</TabsTrigger>
        {isAdmin && (
          <>
            <TabsTrigger value="users">
              <Users className="w-4 h-4 mr-1" /> Usuários
            </TabsTrigger>
            <TabsTrigger value="groups">
              <Users2 className="w-4 h-4 mr-1" /> Grupos
            </TabsTrigger>
          </>
        )}
      </TabsList>

      {/* Account Tab */}
      <TabsContent value="account">
        <Card>
          <CardHeader>
            <CardTitle>Configurações da Conta</CardTitle>
            <CardDescription>Gerencie suas informações pessoais</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} disabled />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Alterar Senha</Label>
              <Button variant="outline" disabled>
                Alterar Senha (em desenvolvimento)
              </Button>
            </div>
            <div className="pt-4 border-t border-border">
              <Button
                variant="destructive"
                onClick={() => {
                  logout()
                  window.location.href = "/login"
                }}
              >
                Sair da Conta
              </Button>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      {/* Sharing Tab */}
      <TabsContent value="sharing" className="space-y-6">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {successMessage && (
          <Alert className="border-green-200 bg-green-50">
            <AlertCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">{successMessage}</AlertDescription>
          </Alert>
        )}

        {documents.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>Selecione um Documento</CardTitle>
              <CardDescription>Escolha qual documento deseja compartilhar</CardDescription>
            </CardHeader>
            <CardContent>
              <Select value={selectedDocForShare} onValueChange={setSelectedDocForShare}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {documents.map((doc) => (
                    <SelectItem key={doc.document_id} value={doc.document_id}>
                      {doc.filename}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="py-8">
              <div className="text-center text-muted-foreground">
                <p className="text-lg font-medium mb-2">Nenhum documento encontrado</p>
                <p className="text-sm">Faça upload de documentos na aba "Documentos" para poder compartilhá-los aqui.</p>
              </div>
            </CardContent>
          </Card>
        )}

        {selectedDocForShare && (
          <Card>
            <CardHeader>
              <CardTitle>Controle de Acesso</CardTitle>
              <CardDescription>Gerencie quem tem acesso a este documento</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Add User */}
              <div className="space-y-4 p-4 border border-dashed border-border rounded-lg bg-muted/30">
                <h4 className="font-semibold text-foreground">Adicionar Novo Acesso</h4>
                <p className="text-sm text-muted-foreground">
                  Compartilhe este documento com membros da equipe ou outros usuários
                </p>
                <div className="flex gap-3 flex-col sm:flex-row">
                  <Input
                    placeholder="email@company.com"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    disabled={isLoading}
                    className="flex-1"
                  />
                  <Select value={newRole} onValueChange={(value: any) => setNewRole(value)} disabled={isLoading}>
                    <SelectTrigger className="w-full sm:w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="viewer">Visualizador</SelectItem>
                      <SelectItem value="editor">Editor</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button onClick={handleAddSharedUser} disabled={isLoading || !newEmail.trim()}>
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Adicionar"}
                  </Button>
                </div>
              </div>

              {/* Shared Users List */}
              <div className="space-y-3">
                <h4 className="font-semibold text-foreground">Usuários com Acesso ({shared.length})</h4>
                {shared.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground text-sm">
                    Nenhum usuário com acesso ainda. Compartilhe acima para começar.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {shared.map((user) => (
                      <div
                        key={user.email}
                        className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-foreground truncate">{user.email}</p>
                            <button
                              onClick={() => copyToClipboard(user.email)}
                              className="text-muted-foreground hover:text-foreground transition-colors"
                            >
                              {copiedEmail === user.email ? (
                                <Check className="w-4 h-4 text-green-600" />
                              ) : (
                                <Copy className="w-4 h-4" />
                              )}
                            </button>
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <Select
                              value={user.role}
                              onValueChange={(value: any) => handleUpdateRole(user.email, value)}
                            >
                              <SelectTrigger className="w-40 h-8 text-sm">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="viewer">Visualizador</SelectItem>
                                <SelectItem value="editor">Editor</SelectItem>
                                <SelectItem value="admin">Admin</SelectItem>
                              </SelectContent>
                            </Select>
                            <span className="text-xs text-muted-foreground ml-2">{getRoleDescription(user.role)}</span>
                          </div>
                          <p className="text-xs text-muted-foreground mt-2">
                            Adicionado em {new Date(user.added_date).toLocaleDateString("pt-BR")}
                          </p>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRemoveSharedUser(user.email)}
                          className="text-destructive hover:text-destructive ml-2 flex-shrink-0"
                        >
                          Remover
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Permissions Legend */}
              <div className="mt-6 p-4 bg-muted/50 rounded-lg space-y-2">
                <h5 className="text-sm font-semibold text-foreground">Níveis de Permissão</h5>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <p>
                    <strong className="text-foreground">Visualizador:</strong> Apenas visualizar e explorar documentos
                  </p>
                  <p>
                    <strong className="text-foreground">Editor:</strong> Visualizar, buscar e fazer perguntas ao chatbot
                  </p>
                  <p>
                    <strong className="text-foreground">Admin:</strong> Acesso total incluindo compartilhamento e
                    exclusão
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </TabsContent>

      {/* Notifications Tab */}
      <TabsContent value="notifications">
        <Card>
          <CardHeader>
            <CardTitle>Preferências de Notificação</CardTitle>
            <CardDescription>Escolha como ser notificado sobre atividades</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-base">Notificações por Email</Label>
                <p className="text-sm text-muted-foreground">Receba atualizações sobre seus documentos</p>
              </div>
              <Switch checked={notifications} onCheckedChange={setNotifications} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-base">Notificações de Compartilhamento</Label>
                <p className="text-sm text-muted-foreground">Quando alguém compartilhar um documento com você</p>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-base">Notificações de Processamento</Label>
                <p className="text-sm text-muted-foreground">Quando um documento terminar de processar</p>
              </div>
              <Switch defaultChecked />
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      {/* Users Tab (Admin only) */}
      {isAdmin && (
        <TabsContent value="users">
          <Card>
            <CardHeader>
              <CardTitle>Gerenciamento de Usuários</CardTitle>
              <CardDescription>Criar, editar e remover usuários do sistema</CardDescription>
            </CardHeader>
            <CardContent>
              <UserManagement />
            </CardContent>
          </Card>
        </TabsContent>
      )}

      {/* Groups Tab (Admin only) */}
      {isAdmin && (
        <TabsContent value="groups">
          <Card>
            <CardHeader>
              <CardTitle>Gerenciamento de Grupos</CardTitle>
              <CardDescription>Organizar usuários em grupos para facilitar compartilhamento</CardDescription>
            </CardHeader>
            <CardContent>
              <GroupManagement />
            </CardContent>
          </Card>
        </TabsContent>
      )}
    </Tabs>
  )
}
