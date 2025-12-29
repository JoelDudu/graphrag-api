"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
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
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Loader2, Plus, Pencil, Trash2, Users2, UserPlus, X } from "lucide-react"
import { apiClient } from "@/lib/api-client"

interface Group {
    id: string
    name: string
    description?: string
}

interface User {
    id: string
    username: string
    email?: string
    is_admin: boolean
}

export default function GroupManagement() {
    const [groups, setGroups] = useState<Group[]>([])
    const [allUsers, setAllUsers] = useState<User[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState("")

    // Dialog states
    const [dialogOpen, setDialogOpen] = useState(false)
    const [editingGroup, setEditingGroup] = useState<Group | null>(null)
    const [formData, setFormData] = useState({ name: "", description: "" })
    const [isSaving, setIsSaving] = useState(false)

    // Members dialog
    const [membersDialogOpen, setMembersDialogOpen] = useState(false)
    const [selectedGroup, setSelectedGroup] = useState<Group | null>(null)
    const [members, setMembers] = useState<User[]>([])
    const [loadingMembers, setLoadingMembers] = useState(false)
    const [selectedUserId, setSelectedUserId] = useState("")

    useEffect(() => {
        loadGroups()
        loadUsers()
    }, [])

    const loadGroups = async () => {
        setIsLoading(true)
        setError("")
        try {
            const data = await apiClient.getGroups()
            setGroups(data.groups || [])
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao carregar grupos")
        } finally {
            setIsLoading(false)
        }
    }

    const loadUsers = async () => {
        try {
            const data = await apiClient.getUsers()
            setAllUsers(data.users || [])
        } catch (err) {
            console.error("Erro ao carregar usuários:", err)
        }
    }

    const loadMembers = async (groupId: string) => {
        setLoadingMembers(true)
        try {
            const data = await apiClient.getGroupMembers(groupId)
            setMembers(data.members || [])
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao carregar membros")
        } finally {
            setLoadingMembers(false)
        }
    }

    const handleOpenCreate = () => {
        setEditingGroup(null)
        setFormData({ name: "", description: "" })
        setDialogOpen(true)
    }

    const handleOpenEdit = (group: Group) => {
        setEditingGroup(group)
        setFormData({ name: group.name, description: group.description || "" })
        setDialogOpen(true)
    }

    const handleOpenMembers = async (group: Group) => {
        setSelectedGroup(group)
        setMembersDialogOpen(true)
        await loadMembers(group.id)
    }

    const handleSave = async () => {
        setIsSaving(true)
        try {
            if (editingGroup) {
                await apiClient.updateGroup(editingGroup.id, {
                    name: formData.name,
                    description: formData.description || undefined,
                })
            } else {
                if (!formData.name) {
                    throw new Error("Nome é obrigatório")
                }
                await apiClient.createGroup({
                    name: formData.name,
                    description: formData.description || undefined,
                })
            }
            setDialogOpen(false)
            loadGroups()
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao salvar")
        } finally {
            setIsSaving(false)
        }
    }

    const handleDelete = async (group: Group) => {
        try {
            await apiClient.deleteGroup(group.id)
            loadGroups()
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao excluir")
        }
    }

    const handleAddMember = async () => {
        if (!selectedGroup || !selectedUserId) return
        try {
            await apiClient.addGroupMember(selectedGroup.id, selectedUserId)
            setSelectedUserId("")
            loadMembers(selectedGroup.id)
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao adicionar membro")
        }
    }

    const handleRemoveMember = async (userId: string) => {
        if (!selectedGroup) return
        try {
            await apiClient.removeGroupMember(selectedGroup.id, userId)
            loadMembers(selectedGroup.id)
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao remover membro")
        }
    }

    // Filter users not in current group
    const availableUsers = allUsers.filter(
        (u) => !members.some((m) => m.id === u.id)
    )

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-8">
                <Loader2 className="w-6 h-6 animate-spin" />
            </div>
        )
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Users2 className="w-5 h-5" />
                    <h3 className="text-lg font-semibold">Grupos</h3>
                    <Badge variant="secondary">{groups.length}</Badge>
                </div>
                <Button onClick={handleOpenCreate} size="sm">
                    <Plus className="w-4 h-4 mr-2" />
                    Novo Grupo
                </Button>
            </div>

            {error && (
                <div className="p-3 bg-destructive/10 text-destructive rounded-lg text-sm">
                    {error}
                </div>
            )}

            <div className="grid gap-3">
                {groups.map((group) => (
                    <Card key={group.id}>
                        <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                                        <Users2 className="w-5 h-5 text-blue-600" />
                                    </div>
                                    <div>
                                        <span className="font-medium">{group.name}</span>
                                        {group.description && (
                                            <p className="text-sm text-muted-foreground">{group.description}</p>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button variant="outline" size="sm" onClick={() => handleOpenMembers(group)}>
                                        <UserPlus className="w-4 h-4 mr-2" />
                                        Membros
                                    </Button>
                                    <Button variant="ghost" size="icon" onClick={() => handleOpenEdit(group)}>
                                        <Pencil className="w-4 h-4" />
                                    </Button>
                                    <AlertDialog>
                                        <AlertDialogTrigger asChild>
                                            <Button variant="ghost" size="icon" className="text-destructive">
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </AlertDialogTrigger>
                                        <AlertDialogContent>
                                            <AlertDialogHeader>
                                                <AlertDialogTitle>Excluir grupo?</AlertDialogTitle>
                                                <AlertDialogDescription>
                                                    Tem certeza que deseja excluir o grupo "{group.name}"?
                                                    Os membros não serão excluídos, apenas removidos do grupo.
                                                </AlertDialogDescription>
                                            </AlertDialogHeader>
                                            <AlertDialogFooter>
                                                <AlertDialogCancel>Cancelar</AlertDialogCancel>
                                                <AlertDialogAction onClick={() => handleDelete(group)}>
                                                    Excluir
                                                </AlertDialogAction>
                                            </AlertDialogFooter>
                                        </AlertDialogContent>
                                    </AlertDialog>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}

                {groups.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                        Nenhum grupo criado
                    </div>
                )}
            </div>

            {/* Create/Edit Dialog */}
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>
                            {editingGroup ? "Editar Grupo" : "Novo Grupo"}
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Nome *</Label>
                            <Input
                                id="name"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                placeholder="Nome do grupo"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="description">Descrição</Label>
                            <Input
                                id="description"
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                placeholder="Descrição opcional"
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDialogOpen(false)}>
                            Cancelar
                        </Button>
                        <Button onClick={handleSave} disabled={isSaving}>
                            {isSaving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                            {editingGroup ? "Salvar" : "Criar"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Members Dialog */}
            <Dialog open={membersDialogOpen} onOpenChange={setMembersDialogOpen}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle>
                            Membros de "{selectedGroup?.name}"
                        </DialogTitle>
                    </DialogHeader>

                    {/* Add member */}
                    <div className="flex gap-2">
                        <Select value={selectedUserId} onValueChange={setSelectedUserId}>
                            <SelectTrigger className="flex-1">
                                <SelectValue placeholder="Selecionar usuário..." />
                            </SelectTrigger>
                            <SelectContent>
                                {availableUsers.map((user) => (
                                    <SelectItem key={user.id} value={user.id}>
                                        {user.username}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        <Button onClick={handleAddMember} disabled={!selectedUserId}>
                            <UserPlus className="w-4 h-4" />
                        </Button>
                    </div>

                    {/* Members list */}
                    <ScrollArea className="h-[200px]">
                        {loadingMembers ? (
                            <div className="flex justify-center py-4">
                                <Loader2 className="w-5 h-5 animate-spin" />
                            </div>
                        ) : members.length > 0 ? (
                            <div className="space-y-2">
                                {members.map((member) => (
                                    <div
                                        key={member.id}
                                        className="flex items-center justify-between p-2 rounded-lg bg-muted"
                                    >
                                        <span className="text-sm">{member.username}</span>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-6 w-6"
                                            onClick={() => handleRemoveMember(member.id)}
                                        >
                                            <X className="w-3 h-3" />
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-4 text-muted-foreground text-sm">
                                Nenhum membro neste grupo
                            </div>
                        )}
                    </ScrollArea>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setMembersDialogOpen(false)}>
                            Fechar
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    )
}
