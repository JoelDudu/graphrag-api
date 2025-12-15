"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import DocumentsTab from "@/components/dashboard/documents-tab"
import SearchTab from "@/components/dashboard/search-tab"
import ChatTab from "@/components/dashboard/chat-tab"
import SettingsTab from "@/components/dashboard/settings-tab"
import {
  FileText,
  Search,
  MessageSquare,
  Settings,
  LogOut,
  Loader2,
  Plus,
  ChevronLeft,
  ChevronRight
} from "lucide-react"
import { useAuth } from "@/lib/auth-context"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

const menuItems = [
  { id: "documents", label: "Documentos", icon: FileText },
  { id: "search", label: "Busca", icon: Search },
  { id: "chat", label: "Chat", icon: MessageSquare },
  { id: "settings", label: "Configurações", icon: Settings },
]

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("documents")
  const [isLoading, setIsLoading] = useState(true)
  const [username, setUsername] = useState<string>("")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()
  const { token, logout } = useAuth()

  useEffect(() => {
    // Check authentication
    const timer = setTimeout(() => {
      if (!token) {
        router.push("/login")
      } else {
        setIsLoading(false)
        // Get username from localStorage
        const storedUsername = localStorage.getItem("username") || "Usuário"
        setUsername(storedUsername)
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [token, router])

  const handleLogout = () => {
    logout()
    localStorage.removeItem("username")
    router.push("/login")
  }

  const handleNewDocument = () => {
    setActiveTab("documents")
    // Trigger file input click after a short delay to ensure tab is active
    setTimeout(() => {
      fileInputRef.current?.click()
    }, 100)
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
    <TooltipProvider delayDuration={0}>
      <div className="h-screen flex bg-background overflow-hidden">
        {/* Sidebar */}
        <aside
          className={cn(
            "h-full flex flex-col bg-card border-r border-border transition-all duration-200",
            sidebarCollapsed ? "w-16" : "w-56"
          )}
        >
          {/* Logo/Brand */}
          <div className={cn(
            "p-4 border-b border-border",
            sidebarCollapsed && "px-3"
          )}>
            {sidebarCollapsed ? (
              <div className="flex justify-center">
                <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                  <span className="text-primary-foreground font-bold text-sm">G</span>
                </div>
              </div>
            ) : (
              <div>
                <h1 className="text-lg font-bold text-foreground">GraphRAG</h1>
                <p className="text-xs text-muted-foreground">Dashboard</p>
              </div>
            )}
          </div>

          {/* New Document Button */}
          <div className={cn("p-3", sidebarCollapsed && "px-2")}>
            {sidebarCollapsed ? (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    onClick={handleNewDocument}
                    size="icon"
                    className="w-full h-10"
                  >
                    <Plus className="w-5 h-5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">
                  Novo Documento
                </TooltipContent>
              </Tooltip>
            ) : (
              <Button
                onClick={handleNewDocument}
                className="w-full justify-start"
                size="sm"
              >
                <Plus className="w-4 h-4 mr-2" />
                Novo Documento
              </Button>
            )}
          </div>

          {/* Menu Items */}
          <nav className="flex-1 p-2 space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = activeTab === item.id

              if (sidebarCollapsed) {
                return (
                  <Tooltip key={item.id}>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => setActiveTab(item.id)}
                        className={cn(
                          "w-full flex items-center justify-center h-10 rounded-lg transition-colors",
                          isActive
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                        )}
                      >
                        <Icon className="w-5 h-5" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      {item.label}
                    </TooltipContent>
                  </Tooltip>
                )
              }

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-sm",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              )
            })}
          </nav>

          {/* User Section */}
          <div className={cn(
            "border-t border-border p-3",
            sidebarCollapsed && "px-2"
          )}>
            {sidebarCollapsed ? (
              <div className="space-y-2">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex justify-center">
                      <Avatar className="h-8 w-8 cursor-pointer">
                        <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                          {username.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    {username}
                  </TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={handleLogout}
                      className="w-full h-8"
                    >
                      <LogOut className="w-4 h-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    Sair
                  </TooltipContent>
                </Tooltip>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center gap-2 px-2 py-1">
                  <Avatar className="h-7 w-7">
                    <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                      {username.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{username}</p>
                    <p className="text-xs text-muted-foreground">Conectado</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLogout}
                  className="w-full justify-start text-muted-foreground hover:text-foreground"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Sair
                </Button>
              </div>
            )}
          </div>

          {/* Collapse Toggle */}
          <div className="border-t border-border p-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="w-full justify-center"
            >
              {sidebarCollapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <>
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  <span className="text-xs">Recolher</span>
                </>
              )}
            </Button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden">
          {activeTab === "documents" && (
            <DocumentsTab fileInputRef={fileInputRef} />
          )}
          {activeTab === "search" && (
            <div className="h-full overflow-auto p-6">
              <SearchTab />
            </div>
          )}
          {activeTab === "chat" && (
            <div className="h-full overflow-auto p-6">
              <ChatTab />
            </div>
          )}
          {activeTab === "settings" && (
            <div className="h-full overflow-auto p-6">
              <SettingsTab />
            </div>
          )}
        </main>
      </div>
    </TooltipProvider>
  )
}
