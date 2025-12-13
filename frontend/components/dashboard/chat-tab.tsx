"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Loader2, AlertCircle } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"

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

export default function ChatTab() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Olá! Sou seu assistente de IA. Posso ajudá-lo a buscar e entender seus documentos. Qual é sua pergunta?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState("")
  const [documents, setDocuments] = useState<Document[]>([])
  const [error, setError] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadDocuments()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const loadDocuments = async () => {
    try {
      const docs = await apiClient.listDocuments()
      setDocuments(docs.filter((d) => d.status === "processed"))
      if (docs.length > 0) {
        setSelectedDoc(docs[0].document_id)
      }
    } catch (err) {
      console.error("Erro ao carregar documentos")
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const handleSendMessage = async () => {
    if (!input.trim() || !selectedDoc) return

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
      const searchResults = await apiClient.query(input, selectedDoc, "hybrid", "claude", 5)

      // Build context from search results
      const context = searchResults.results?.map((r) => `${r.title}: ${r.excerpt}`).join("\n\n")

      // Create assistant response based on search results
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: context
          ? `Com base nos documentos: ${context}\n\nPara respostas mais detalhadas, considere fazer uma busca específica.`
          : "Desculpe, não encontrei informações relevantes para sua pergunta. Tente refinar sua busca.",
        timestamp: new Date(),
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
    <div className="space-y-4 h-[600px] flex flex-col">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Document Selection */}
      {documents.length > 0 && (
        <Select value={selectedDoc} onValueChange={setSelectedDoc}>
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
      )}

      <Card className="flex-1 flex flex-col">
        <CardHeader>
          <CardTitle>Chat com seus Documentos</CardTitle>
          <CardDescription>Faça perguntas e obtenha respostas baseadas no conteúdo de seus documentos</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col overflow-hidden">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-4">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-xs px-4 py-2 rounded-lg ${
                    message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  <span className="text-xs opacity-70 mt-1 block">{message.timestamp.toLocaleTimeString()}</span>
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
              disabled={isLoading || !selectedDoc}
              className="flex-1"
            />
            <Button onClick={handleSendMessage} disabled={isLoading || !input.trim() || !selectedDoc}>
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
