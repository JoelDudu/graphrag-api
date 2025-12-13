"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FileText, Trash2, Share2, Download, CheckCircle, Clock, Loader2, AlertCircle, Network } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api-client"
import { Alert, AlertDescription } from "@/components/ui/alert"
import GraphViewer from "./graph-viewer"

interface Document {
  document_id: string
  filename: string
  status: string
  progress?: number
  created_at: string
  size?: string
  model?: string
}

export default function DocumentsTab() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({})
  const [processingDocs, setProcessingDocs] = useState<Set<string>>(new Set())
  const [graphViewerOpen, setGraphViewerOpen] = useState(false)
  const [selectedDocForGraph, setSelectedDocForGraph] = useState<Document | null>(null)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    setIsLoading(true)
    setError("")
    try {
      const docs = await apiClient.listDocuments()
      setDocuments(docs)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao carregar documentos"
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.currentTarget.files?.[0]
    if (!file) return

    setError("")
    const fileId = file.name
    setUploadProgress({ ...uploadProgress, [fileId]: 0 })

    try {
      const doc = await apiClient.uploadDocument(file)
      setUploadProgress({ ...uploadProgress, [fileId]: 100 })

      // Auto-process after upload
      setProcessingDocs((prev) => new Set([...prev, doc.document_id]))
      try {
        await apiClient.processDocument(doc.document_id)
      } catch {
        console.error("Processamento iniciado em background")
      }

      setTimeout(() => loadDocuments(), 1000)
      setTimeout(() => setUploadProgress({}), 2000)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao fazer upload"
      setError(message)
      setUploadProgress({})
    }
  }

  const handleDeleteDocument = async (documentId: string) => {
    if (!confirm("Tem certeza que deseja deletar este documento?")) return

    try {
      await apiClient.deleteDocument(documentId)
      setDocuments(documents.filter((d) => d.document_id !== documentId))
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao deletar documento"
      setError(message)
    }
  }

  const handleProcessDocument = async (documentId: string) => {
    try {
      setProcessingDocs((prev) => new Set([...prev, documentId]))
      await apiClient.processDocument(documentId, "claude", "generic")
      setTimeout(() => loadDocuments(), 1000)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao processar documento"
      setError(message)
    } finally {
      setProcessingDocs((prev) => {
        const newSet = new Set(prev)
        newSet.delete(documentId)
        return newSet
      })
    }
  }

  const getStatusBadge = (status: string, progress?: number) => {
    switch (status) {
      case "Pending":
        return (
          <Badge variant="outline" className="bg-yellow-50">
            <Clock className="w-3 h-3 mr-1" />
            Pendente
          </Badge>
        )
      case "Processing":
        return (
          <Badge variant="outline" className="bg-blue-50">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            Processando {progress ? `(${Math.round(progress)}%)` : ""}
          </Badge>
        )
      case "Completed":
        return (
          <Badge variant="outline" className="bg-green-50">
            <CheckCircle className="w-3 h-3 mr-1" />
            Processado
          </Badge>
        )
      case "Failed":
        return (
          <Badge variant="outline" className="bg-red-50">
            <AlertCircle className="w-3 h-3 mr-1" />
            Erro
          </Badge>
        )
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Upload Section */}
      <Card className="border-2 border-dashed border-border hover:border-primary/50 transition-colors">
        <CardContent className="pt-6">
          <div className="text-center">
            <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="font-semibold text-foreground mb-2">Envie um documento</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Arraste aqui ou clique para enviar (PDF, DOCX, TXT, XLSX, etc)
            </p>
            <label htmlFor="file-upload">
              <Button asChild>
                <span>Escolher Arquivo</span>
              </Button>
              <input
                id="file-upload"
                type="file"
                onChange={handleFileUpload}
                className="hidden"
                accept=".pdf,.docx,.txt,.xlsx,.xls,.doc"
              />
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Documents List */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle>Seus Documentos ({documents.length})</CardTitle>
              <CardDescription>Gerencie e compartilhe seus arquivos processados</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={loadDocuments} disabled={isLoading}>
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Atualizar"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {documents.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              Nenhum documento enviado ainda. Comece enviando um arquivo acima.
            </div>
          ) : (
            <div className="space-y-4">
              {documents.map((doc) => (
                <div
                  key={doc.document_id}
                  className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <FileText className="w-8 h-8 text-primary flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-foreground truncate">{doc.filename}</h4>
                      <div className="flex gap-3 text-sm text-muted-foreground mt-1">
                        <span>{doc.size || "—"}</span>
                        <span>{new Date(doc.created_at).toLocaleDateString("pt-BR")}</span>
                        {getStatusBadge(doc.status, doc.progress)}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {doc.status === "Pending" && (
                      <Button
                        size="sm"
                        variant="default"
                        onClick={() => handleProcessDocument(doc.document_id)}
                        disabled={processingDocs.has(doc.document_id)}
                      >
                        {processingDocs.has(doc.document_id) ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                            Processando...
                          </>
                        ) : (
                          "Processar"
                        )}
                      </Button>
                    )}
                    {doc.status === "Completed" && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          title="Visualizar grafo"
                          onClick={() => {
                            setSelectedDocForGraph(doc)
                            setGraphViewerOpen(true)
                          }}
                        >
                          <Network className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="outline">
                          <Share2 className="w-4 h-4" />
                        </Button>
                      </>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-destructive hover:text-destructive bg-transparent"
                      onClick={() => handleDeleteDocument(doc.document_id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {selectedDocForGraph && (
        <GraphViewer
          documentId={selectedDocForGraph.document_id}
          filename={selectedDocForGraph.filename}
          isOpen={graphViewerOpen}
          onClose={() => {
            setGraphViewerOpen(false)
            setSelectedDocForGraph(null)
          }}
        />
      )}
    </div>
  )
}
