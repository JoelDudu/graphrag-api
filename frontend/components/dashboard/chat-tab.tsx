"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Loader2, AlertCircle, Database } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  sources?: Array<{ text: string; score?: number }>
}

export default function ChatTab() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Olá! Sou seu assistente de IA. Posso buscar informações em todos os seus documentos. Qual é sua pergunta?",
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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const handleSendMessage = async () => {
    if (!input.trim()) return

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
      // Buscar em todo o banco usando busca híbrida
      const response = await apiClient.query(input, "hybrid")

      // Criar resposta do assistente
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer || "Não encontrei informações relevantes para sua pergunta.",
        timestamp: new Date(),
        sources: response.sources || [],
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao processar mensagem"
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-4 h-[700px] flex flex-col">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Info Banner */}
      <div className="flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-lg text-sm">
        <Database className="w-4 h-4 text-primary" />
        <span>Buscando em <strong>todos os documentos</strong> do banco de dados</span>
      </div>

      <Card className="flex-1 flex flex-col">
        <CardHeader>
          <CardTitle>Chat com Base de Conhecimento</CardTitle>
          <CardDescription>Faça perguntas e obtenha respostas baseadas em todos os seus documentos</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col overflow-hidden">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-4">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[80%] px-4 py-3 rounded-lg ${message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
                    }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>

                  {/* Mostrar fontes se houver */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-border/50">
                      <p className="text-xs font-medium mb-1 opacity-70">Fontes ({message.sources.length}):</p>
                      <div className="space-y-1">
                        {message.sources.slice(0, 3).map((source, idx) => (
                          <p key={idx} className="text-xs opacity-60 truncate">
                            • {source.text?.substring(0, 100)}...
                          </p>
                        ))}
                      </div>
                    </div>
                  )}

                  <span className="text-xs opacity-50 mt-2 block">{message.timestamp.toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-muted px-4 py-2 rounded-lg">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                    <div
                      className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    />
                    <div
                      className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="flex gap-2 border-t border-border pt-4">
            <Input
              placeholder="Digite sua pergunta..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && !isLoading && handleSendMessage()}
              disabled={isLoading}
              className="flex-1"
            />
            <Button onClick={handleSendMessage} disabled={isLoading || !input.trim()}>
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
