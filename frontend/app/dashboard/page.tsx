"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import DocumentsTab from "@/components/dashboard/documents-tab"
import SearchTab from "@/components/dashboard/search-tab"
import ChatTab from "@/components/dashboard/chat-tab"
import SettingsTab from "@/components/dashboard/settings-tab"
import { Plus, LogOut, Loader2 } from "lucide-react"
import { useAuth } from "@/lib/auth-context"

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("documents")
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const { token, logout } = useAuth()

  useEffect(() => {
    // Check authentication
    const timer = setTimeout(() => {
      if (!token) {
        router.push("/login")
      } else {
        setIsLoading(false)
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [token, router])

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Carregando...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
            <p className="text-sm text-muted-foreground">Gerencie seus documentos e buscas inteligentes</p>
          </div>
          <div className="flex gap-3">
            <Button disabled>
              <Plus className="w-4 h-4 mr-2" />
              Novo Documento
            </Button>
            <Button variant="outline" onClick={handleLogout}>
              <LogOut className="w-4 h-4 mr-2" />
              Sair
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-4">
            <TabsTrigger value="documents">Documentos</TabsTrigger>
            <TabsTrigger value="search">Busca</TabsTrigger>
            <TabsTrigger value="chat">Chat</TabsTrigger>
            <TabsTrigger value="settings">Configurações</TabsTrigger>
          </TabsList>

          <TabsContent value="documents" className="mt-8">
            <DocumentsTab />
          </TabsContent>

          <TabsContent value="search" className="mt-8">
            <SearchTab />
          </TabsContent>

          <TabsContent value="chat" className="mt-8">
            <ChatTab />
          </TabsContent>

          <TabsContent value="settings" className="mt-8">
            <SettingsTab />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
