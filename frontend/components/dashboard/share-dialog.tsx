"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Loader2, Share2, Users, Users2, Trash2, Shield, Eye } from "lucide-react"
import { apiClient } from "@/lib/api-client"

interface ShareInfo {
    entity_type: string
    entity_id: string
    entity_name: string
    permission: string
}

interface User {
    id: string
    username: string
    email?: string
    is_admin: boolean
}

interface Group {
    id: string
    name: string
    description?: string
}

interface ShareDialogProps {
    documentId: string
    documentName: string
    open: boolean
    onOpenChange: (open: boolean) => void
}

export default function ShareDialog({ documentId, documentName, open, onOpenChange }: ShareDialogProps) {
    const [shares, setShares] = useState<ShareInfo[]>([])
    const [users, setUsers] = useState<User[]>([])
    const [groups, setGroups] = useState<Group[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState("")
    const [success, setSuccess] = useState("")

    // Add share form
    const [selectedType, setSelectedType] = useState<"user" | "group">("user")
    const [selectedEntityId, setSelectedEntityId] = useState("")
    const [selectedPermission, setSelectedPermission] = useState<"read" | "manage">("read")
    const [isAdding, setIsAdding] = useState(false)

    useEffect(() => {
        if (open) {
            loadData()
        }
    }, [open, documentId])

    const loadData = async () => {
        setIsLoading(true)
        setError("")
        try {
            const [sharesData, usersData, groupsData] = await Promise.all([
                apiClient.getDocumentPermissions(documentId),
                apiClient.getUsers().catch(() => ({ users: [] })),
                apiClient.getGroups().catch(() => ({ groups: [] })),
            ])
            setShares(sharesData.shares || [])
            setUsers(usersData.users || [])
            setGroups(groupsData.groups || [])
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao carregar dados")
        } finally {
            setIsLoading(false)
        }
    }

    const handleAddShare = async () => {
        if (!selectedEntityId) return

        setIsAdding(true)
        setError("")
        setSuccess("")

        try {
            await apiClient.shareDocument(documentId, selectedType, selectedEntityId, selectedPermission)
            await loadData()
            setSelectedEntityId("")
            setSuccess("Compartilhamento adicionado!")
            setTimeout(() => setSuccess(""), 2000)
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao compartilhar")
        } finally {
            setIsAdding(false)
        }
    }

    const handleRemoveShare = async (share: ShareInfo) => {
        try {
            await apiClient.unshareDocument(documentId, share.entity_type, share.entity_id)
            await loadData()
            setSuccess("Compartilhamento removido!")
            setTimeout(() => setSuccess(""), 2000)
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao remover")
        }
    }

    const handleUpdatePermission = async (share: ShareInfo, newPermission: "read" | "manage") => {
        try {
            // Remove e adiciona com nova permissão
            await apiClient.unshareDocument(documentId, share.entity_type, share.entity_id)
            await apiClient.shareDocument(documentId, share.entity_type as "user" | "group", share.entity_id, newPermission)
            await loadData()
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao atualizar")
        }
    }

    // Filtrar entidades que ainda não têm acesso
    const availableUsers = users.filter(u => !shares.some(s => s.entity_type === "user" && s.entity_id === u.id))
    const availableGroups = groups.filter(g => !shares.some(s => s.entity_type === "group" && s.entity_id === g.id))

    const userShares = shares.filter(s => s.entity_type === "user")
    const groupShares = shares.filter(s => s.entity_type === "group")

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-lg">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Share2 className="w-5 h-5" />
                        Compartilhar Documento
                    </DialogTitle>
                    <p className="text-sm text-muted-foreground truncate">
                        {documentName}
                    </p>
                </DialogHeader>

                {isLoading ? (
                    <div className="flex justify-center py-8">
                        <Loader2 className="w-6 h-6 animate-spin" />
                    </div>
                ) : (
                    <div className="space-y-4">
                        {/* Messages */}
                        {error && (
                            <div className="p-2 bg-destructive/10 text-destructive text-sm rounded">
                                {error}
                            </div>
                        )}
                        {success && (
                            <div className="p-2 bg-green-100 text-green-700 text-sm rounded">
                                {success}
                            </div>
                        )}

                        {/* Add share form */}
                        <div className="p-4 border rounded-lg bg-muted/30 space-y-3">
                            <h4 className="font-medium text-sm">Adicionar Acesso</h4>

                            <Tabs value={selectedType} onValueChange={(v) => {
                                setSelectedType(v as "user" | "group")
                                setSelectedEntityId("")
                            }}>
                                <TabsList className="grid w-full grid-cols-2">
                                    <TabsTrigger value="user">
                                        <Users className="w-4 h-4 mr-1" /> Usuário
                                    </TabsTrigger>
                                    <TabsTrigger value="group">
                                        <Users2 className="w-4 h-4 mr-1" /> Grupo
                                    </TabsTrigger>
                                </TabsList>
                            </Tabs>

                            <div className="flex gap-2">
                                <Select value={selectedEntityId} onValueChange={setSelectedEntityId}>
                                    <SelectTrigger className="flex-1">
                                        <SelectValue placeholder={selectedType === "user" ? "Selecionar usuário..." : "Selecionar grupo..."} />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {selectedType === "user" ? (
                                            availableUsers.length > 0 ? (
                                                availableUsers.map(user => (
                                                    <SelectItem key={user.id} value={user.id}>
                                                        {user.username}
                                                    </SelectItem>
                                                ))
                                            ) : (
                                                <div className="p-2 text-sm text-muted-foreground">Nenhum usuário disponível</div>
                                            )
                                        ) : (
                                            availableGroups.length > 0 ? (
                                                availableGroups.map(group => (
                                                    <SelectItem key={group.id} value={group.id}>
                                                        {group.name}
                                                    </SelectItem>
                                                ))
                                            ) : (
                                                <div className="p-2 text-sm text-muted-foreground">Nenhum grupo disponível</div>
                                            )
                                        )}
                                    </SelectContent>
                                </Select>

                                <Select value={selectedPermission} onValueChange={(v) => setSelectedPermission(v as "read" | "manage")}>
                                    <SelectTrigger className="w-32">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="read">
                                            <div className="flex items-center gap-1">
                                                <Eye className="w-3 h-3" /> Leitura
                                            </div>
                                        </SelectItem>
                                        <SelectItem value="manage">
                                            <div className="flex items-center gap-1">
                                                <Shield className="w-3 h-3" /> Gestão
                                            </div>
                                        </SelectItem>
                                    </SelectContent>
                                </Select>

                                <Button onClick={handleAddShare} disabled={!selectedEntityId || isAdding}>
                                    {isAdding ? <Loader2 className="w-4 h-4 animate-spin" /> : "Adicionar"}
                                </Button>
                            </div>
                        </div>

                        {/* Current shares */}
                        <div className="space-y-2">
                            <h4 className="font-medium text-sm">Acessos Atuais ({shares.length})</h4>

                            <ScrollArea className="h-[200px]">
                                {shares.length === 0 ? (
                                    <div className="text-center py-8 text-muted-foreground text-sm">
                                        Nenhum compartilhamento
                                    </div>
                                ) : (
                                    <div className="space-y-2 pr-3">
                                        {/* User shares */}
                                        {userShares.map(share => (
                                            <div key={`user-${share.entity_id}`} className="flex items-center justify-between p-2 bg-muted rounded-lg">
                                                <div className="flex items-center gap-2">
                                                    <Users className="w-4 h-4 text-muted-foreground" />
                                                    <span className="text-sm font-medium">{share.entity_name}</span>
                                                    <Badge variant={share.permission === "manage" ? "default" : "secondary"} className="text-xs">
                                                        {share.permission === "manage" ? "Gestão" : "Leitura"}
                                                    </Badge>
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <Select
                                                        value={share.permission}
                                                        onValueChange={(v) => handleUpdatePermission(share, v as "read" | "manage")}
                                                    >
                                                        <SelectTrigger className="h-7 w-24 text-xs">
                                                            <SelectValue />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            <SelectItem value="read">Leitura</SelectItem>
                                                            <SelectItem value="manage">Gestão</SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="h-7 w-7 text-destructive"
                                                        onClick={() => handleRemoveShare(share)}
                                                    >
                                                        <Trash2 className="w-3 h-3" />
                                                    </Button>
                                                </div>
                                            </div>
                                        ))}

                                        {/* Group shares */}
                                        {groupShares.map(share => (
                                            <div key={`group-${share.entity_id}`} className="flex items-center justify-between p-2 bg-blue-50 rounded-lg">
                                                <div className="flex items-center gap-2">
                                                    <Users2 className="w-4 h-4 text-blue-600" />
                                                    <span className="text-sm font-medium">{share.entity_name}</span>
                                                    <Badge variant={share.permission === "manage" ? "default" : "secondary"} className="text-xs">
                                                        {share.permission === "manage" ? "Gestão" : "Leitura"}
                                                    </Badge>
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <Select
                                                        value={share.permission}
                                                        onValueChange={(v) => handleUpdatePermission(share, v as "read" | "manage")}
                                                    >
                                                        <SelectTrigger className="h-7 w-24 text-xs">
                                                            <SelectValue />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            <SelectItem value="read">Leitura</SelectItem>
                                                            <SelectItem value="manage">Gestão</SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="h-7 w-7 text-destructive"
                                                        onClick={() => handleRemoveShare(share)}
                                                    >
                                                        <Trash2 className="w-3 h-3" />
                                                    </Button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </ScrollArea>
                        </div>

                        {/* Permission legend */}
                        <div className="p-3 bg-muted/50 rounded text-xs text-muted-foreground space-y-1">
                            <p><strong>Leitura:</strong> Visualizar, buscar e fazer perguntas</p>
                            <p><strong>Gestão:</strong> Leitura + download, excluir e compartilhar</p>
                        </div>
                    </div>
                )}

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        Fechar
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
