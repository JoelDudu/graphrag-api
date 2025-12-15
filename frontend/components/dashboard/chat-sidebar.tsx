"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Loader2, AlertCircle, MessageSquare, Trash2 } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { ScrollArea } from "@/components/ui/scroll-area"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

interface Document {
  document_id: string
  filename: string
  status: string
}

interface ChatSidebarProps {
  selectedDocument: Document | null
}

export default function ChatSidebar({ selectedDocument }: ChatSidebarProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Olá! Selecione um documento processado e faça perguntas.",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (selectedDocument) {
      const statusMsg = selectedDocument.status === "Completed"
        ? "Como posso ajudar?"
        : "Processe o documento primeiro para fazer perguntas."

      const welcomeMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: `📄 "${selectedDocument.filename.substring(0, 30)}${selectedDocument.filename.length > 30 ? '...' : ''}" selecionado.\n\n${statusMsg}`,
        timestamp: new Date(),
      }
      setMessages([welcomeMessage])
      setError("")
    }
  }, [selectedDocument?.document_id])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const clearChat = () => {
    setMessages([{
      id: Date.now().toString(),
      role: "assistant",
      content: selectedDocument
        ? `Chat limpo. Faça uma nova pergunta sobre "${selectedDocument.filename}".`
        : "Chat limpo. Selecione um documento.",
      timestamp: new Date(),
    }])
    setError("")
  }

  const handleSendMessage = async () => {
    if (!input.trim() || !selectedDocument) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)
    setError("")

    try {
      const searchResults = await apiClient.query(input, selectedDocument.document_id, "hybrid", "claude", 5)

      // Build response from search results
      const context = searchResults.results?.map((r: any) => `${r.title}: ${r.excerpt}`).join("\n\n")

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: context
          ? `${context}`
          : "Não encontrei informações relevantes. Tente reformular.",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao processar"
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !isLoading) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const canChat = selectedDocument?.status === "Completed"

  return (
    <div className="h-full flex flex-col bg-card border-l border-border overflow-hidden">
      {/* Header - Compact */}
      <div className="p-2 border-b border-border flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 min-w-0">
            <MessageSquare className="w-4 h-4 text-primary flex-shrink-0" />
            <h2 className="font-semibold text-xs text-foreground">Chat IA</h2>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={clearChat}
            title="Limpar chat"
          >
            <Trash2 className="w-3 h-3" />
          </Button>
        </div>
        {selectedDocument ? (
          <p className="text-[10px] text-muted-foreground truncate mt-1" title={selectedDocument.filename}>
            {selectedDocument.filename}
          </p>
        ) : (
          <p className="text-[10px] text-muted-foreground mt-1">Selecione um documento</p>
        )}
      </div>

      {error && (
        <Alert variant="destructive" className="m-2 p-2">
          <AlertCircle className="h-3 w-3" />
          <AlertDescription className="text-xs ml-1">{error}</AlertDescription>
        </Alert>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1 min-h-0">
        <div className="p-2 space-y-2">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[90%] px-2 py-1.5 rounded-lg ${message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-foreground border border-border"
                  }`}
              >
                <p className="text-xs whitespace-pre-wrap break-words leading-relaxed">{message.content}</p>
                <span className="text-[10px] opacity-60 mt-0.5 block">
                  {message.timestamp.toLocaleTimeString("pt-BR", { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-muted px-2 py-1.5 rounded-lg border border-border">
                <div className="flex gap-1">
                  <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" />
                  <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                  <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input - Compact */}
      <div className="p-2 border-t border-border flex-shrink-0">
        <div className="flex gap-1">
          <Input
            placeholder={canChat ? "Pergunte..." : "Processe primeiro"}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading || !canChat}
            className="flex-1 text-xs h-7"
          />
          <Button
            onClick={handleSendMessage}
            disabled={isLoading || !input.trim() || !canChat}
            size="icon"
            className="h-7 w-7"
          >
            {isLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
          </Button>
        </div>
      </div>
    </div>
  )
}
