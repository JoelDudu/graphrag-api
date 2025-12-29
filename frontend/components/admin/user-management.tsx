"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
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
import { Loader2, Plus, Pencil, Trash2, Users, Shield, ShieldCheck } from "lucide-react"
import { apiClient } from "@/lib/api-client"

interface User {
    id: string
    username: string
    email?: string
    is_admin: boolean
    is_active: boolean
}

export default function UserManagement() {
    const [users, setUsers] = useState<User[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState("")

    // Dialog states
    const [dialogOpen, setDialogOpen] = useState(false)
    const [editingUser, setEditingUser] = useState<User | null>(null)
    const [formData, setFormData] = useState({
        username: "",
        email: "",
        password: "",
        is_admin: false,
    })
    const [isSaving, setIsSaving] = useState(false)

    useEffect(() => {
        loadUsers()
    }, [])

    const loadUsers = async () => {
        setIsLoading(true)
        setError("")
        try {
            const data = await apiClient.getUsers()
            setUsers(data.users || [])
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao carregar usuários")
        } finally {
            setIsLoading(false)
        }
    }

    const handleOpenCreate = () => {
        setEditingUser(null)
        setFormData({ username: "", email: "", password: "", is_admin: false })
        setDialogOpen(true)
    }

    const handleOpenEdit = (user: User) => {
        setEditingUser(user)
        setFormData({
            username: user.username,
            email: user.email || "",
            password: "",
            is_admin: user.is_admin,
        })
        setDialogOpen(true)
    }

    const handleSave = async () => {
        setIsSaving(true)
        try {
            if (editingUser) {
                // Update
                await apiClient.updateUser(editingUser.id, {
                    email: formData.email || undefined,
                    password: formData.password || undefined,
                    is_admin: formData.is_admin,
                })
            } else {
                // Create
                if (!formData.username || !formData.password) {
                    throw new Error("Username e senha são obrigatórios")
                }
                await apiClient.createUser({
                    username: formData.username,
                    email: formData.email || undefined,
                    password: formData.password,
                    is_admin: formData.is_admin,
                })
            }
            setDialogOpen(false)
            loadUsers()
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao salvar")
        } finally {
            setIsSaving(false)
        }
    }

    const handleDelete = async (user: User) => {
        try {
            await apiClient.deleteUser(user.id)
            loadUsers()
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao excluir")
        }
    }

    const handleToggleActive = async (user: User) => {
        try {
            await apiClient.updateUser(user.id, { is_active: !user.is_active })
            loadUsers()
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro ao atualizar")
        }
    }

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
                    <Users className="w-5 h-5" />
                    <h3 className="text-lg font-semibold">Usuários</h3>
                    <Badge variant="secondary">{users.length}</Badge>
                </div>
                <Button onClick={handleOpenCreate} size="sm">
                    <Plus className="w-4 h-4 mr-2" />
                    Novo Usuário
                </Button>
            </div>

            {error && (
                <div className="p-3 bg-destructive/10 text-destructive rounded-lg text-sm">
                    {error}
                </div>
            )}

            <div className="grid gap-3">
                {users.map((user) => (
                    <Card key={user.id} className={!user.is_active ? "opacity-60" : ""}>
                        <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                                        {user.is_admin ? (
                                            <ShieldCheck className="w-5 h-5 text-primary" />
                                        ) : (
                                            <Shield className="w-5 h-5 text-muted-foreground" />
                                        )}
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <span className="font-medium">{user.username}</span>
                                            {user.is_admin && (
                                                <Badge variant="default" className="text-xs">Admin</Badge>
                                            )}
                                            {!user.is_active && (
                                                <Badge variant="secondary" className="text-xs">Inativo</Badge>
                                            )}
                                        </div>
                                        {user.email && (
                                            <span className="text-sm text-muted-foreground">{user.email}</span>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Switch
                                        checked={user.is_active}
                                        onCheckedChange={() => handleToggleActive(user)}
                                    />
                                    <Button variant="ghost" size="icon" onClick={() => handleOpenEdit(user)}>
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
                                                <AlertDialogTitle>Excluir usuário?</AlertDialogTitle>
                                                <AlertDialogDescription>
                                                    Tem certeza que deseja excluir o usuário "{user.username}"?
                                                    Esta ação não pode ser desfeita.
                                                </AlertDialogDescription>
                                            </AlertDialogHeader>
                                            <AlertDialogFooter>
                                                <AlertDialogCancel>Cancelar</AlertDialogCancel>
                                                <AlertDialogAction onClick={() => handleDelete(user)}>
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

                {users.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                        Nenhum usuário encontrado
                    </div>
                )}
            </div>

            {/* Create/Edit Dialog */}
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>
                            {editingUser ? "Editar Usuário" : "Novo Usuário"}
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        {!editingUser && (
                            <div className="space-y-2">
                                <Label htmlFor="username">Username *</Label>
                                <Input
                                    id="username"
                                    value={formData.username}
                                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                                    placeholder="nome.usuario"
                                />
                            </div>
                        )}
                        <div className="space-y-2">
                            <Label htmlFor="email">Email</Label>
                            <Input
                                id="email"
                                type="email"
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                placeholder="email@exemplo.com"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password">
                                {editingUser ? "Nova Senha (deixe vazio para manter)" : "Senha *"}
                            </Label>
                            <Input
                                id="password"
                                type="password"
                                value={formData.password}
                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                placeholder="••••••••"
                            />
                        </div>
                        <div className="flex items-center justify-between">
                            <Label htmlFor="is_admin">Administrador</Label>
                            <Switch
                                id="is_admin"
                                checked={formData.is_admin}
                                onCheckedChange={(checked) => setFormData({ ...formData, is_admin: checked })}
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDialogOpen(false)}>
                            Cancelar
                        </Button>
                        <Button onClick={handleSave} disabled={isSaving}>
                            {isSaving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                            {editingUser ? "Salvar" : "Criar"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    )
}
