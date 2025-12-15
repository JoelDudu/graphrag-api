"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FileText, Download, Loader2, AlertCircle, Network, RefreshCw, Play, Trash2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
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

interface Document {
  document_id: string
  filename: string
  status: string
  progress?: number
  created_at: string
  size?: string
  model?: string
}

interface DocumentViewerProps {
  document: Document | null
  onProcess?: (documentId: string, model: string) => void
  onViewGraph?: (document: Document) => void
  onDelete?: (documentId: string) => void
}

const LLM_MODELS = [
  { value: "claude", label: "Claude" },
  { value: "openai", label: "OpenAI GPT-4" },
  { value: "kimi", label: "Moonshot/Kimi" },
  { value: "deepseek", label: "DeepSeek" },
]

export default function DocumentViewer({ document, onProcess, onViewGraph, onDelete }: DocumentViewerProps) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [content, setContent] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [isDeleting, setIsDeleting] = useState(false)

  // Process modal state
  const [processModalOpen, setProcessModalOpen] = useState(false)
  const [selectedModel, setSelectedModel] = useState("claude")

  useEffect(() => {
    if (document?.document_id) {
      loadDocumentContent(document.document_id)
    } else {
      setContent("")
    }
  }, [document?.document_id])

  const loadDocumentContent = async (documentId: string) => {
    setIsLoading(true)
    setError("")
    try {
      // TODO: Implementar endpoint para buscar conteúdo do documento
      setContent("Visualização de conteúdo do documento será implementada em breve.")
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao carregar documento"
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleConfirmProcess = async () => {
    if (!document || !onProcess) return

    setIsProcessing(true)
    try {
      await onProcess(document.document_id, selectedModel)
      setProcessModalOpen(false)
    } finally {
      setIsProcessing(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Pending":
        return "bg-yellow-100 text-yellow-800"
      case "Processing":
        return "bg-blue-100 text-blue-800"
      case "Completed":
        return "bg-green-100 text-green-800"
      case "Failed":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      Pending: "Pendente",
      Processing: "Processando",
      Completed: "Concluído",
      Failed: "Erro",
    }
    return labels[status] || status
  }

  if (!document) {
    return (
      <div className="h-full flex items-center justify-center bg-muted/30">
        <div className="text-center max-w-md">
          <FileText className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">Nenhum documento selecionado</h3>
          <p className="text-sm text-muted-foreground">
            Selecione um documento na barra lateral para visualizar seu conteúdo
          </p>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="h-full flex flex-col bg-background">
        {/* Header */}
        <div className="border-b border-border p-4 bg-card space-y-3 flex-shrink-0">
          {/* Document Name - Full width, can wrap */}
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-primary/10 flex-shrink-0">
              <FileText className="w-5 h-5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <h2
                className="text-lg font-semibold text-foreground leading-tight"
                style={{ wordBreak: 'break-word' }}
              >
                {document.filename}
              </h2>
              <div className="flex flex-wrap items-center gap-2 mt-1">
                <Badge className={getStatusColor(document.status)}>
                  {getStatusLabel(document.status)}
                  {document.status === "Processing" && document.progress && ` ${Math.round(document.progress)}%`}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  {new Date(document.created_at).toLocaleDateString("pt-BR")}
                </span>
                {document.model && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-muted">
                    {document.model}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Process Button */}
            {(document.status === "Pending" || document.status === "Failed") && onProcess && (
              <Button
                variant="default"
                size="sm"
                onClick={() => setProcessModalOpen(true)}
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : document.status === "Failed" ? (
                  <RefreshCw className="w-4 h-4 mr-2" />
                ) : (
                  <Play className="w-4 h-4 mr-2" />
                )}
                {document.status === "Failed" ? "Reprocessar" : "Processar"}
              </Button>
            )}

            {/* View Graph Button */}
            {document.status === "Completed" && onViewGraph && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onViewGraph(document)}
              >
                <Network className="w-4 h-4 mr-2" />
                Ver Grafo
              </Button>
            )}

            {/* Download Button */}
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Download
            </Button>

            {/* Delete Button with AlertDialog */}
            {onDelete && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                    disabled={isDeleting}
                  >
                    {isDeleting ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4 mr-2" />
                    )}
                    Deletar
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Tem certeza absoluta?</AlertDialogTitle>
                    <AlertDialogDescription>
                      Esta ação não pode ser desfeita. Isso excluirá permanentemente o documento
                      <span className="font-medium text-foreground"> "{document.filename}" </span>
                      e todos os dados associados.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancelar</AlertDialogCancel>
                    <AlertDialogAction
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      onClick={async (e) => {
                        e.preventDefault() // Prevent auto-close to show loading
                        setIsDeleting(true)
                        try {
                          await onDelete(document.document_id)
                          // Dialog will close automatically when component unmounts/updates due to deletion
                        } catch (error) {
                          console.error("Error deleting:", error)
                          setIsDeleting(false)
                        }
                      }}
                    >
                      {isDeleting ? "Deletando..." : "Sim, deletar"}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        </div>

        {/* Content */}
        <ScrollArea className="flex-1">
          <div className="p-6">
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : document.status === "Completed" ? (
              <div className="prose prose-sm max-w-none">
                <Card>
                  <CardHeader>
                    <CardTitle>Conteúdo do Documento</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-sm text-muted-foreground whitespace-pre-wrap">
                      {content || "Carregando conteúdo..."}
                    </div>
                  </CardContent>
                </Card>

                {/* Document Statistics */}
                <Card className="mt-4">
                  <CardHeader>
                    <CardTitle>Estatísticas</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Tamanho</p>
                        <p className="font-medium">{document.size || "—"}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Data de Upload</p>
                        <p className="font-medium">
                          {new Date(document.created_at).toLocaleString("pt-BR")}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Status</p>
                        <p className="font-medium">{getStatusLabel(document.status)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Modelo</p>
                        <p className="font-medium">{document.model || "—"}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {document.status === "Pending" &&
                    "Este documento ainda não foi processado. Clique em 'Processar' para começar."}
                  {document.status === "Processing" &&
                    "Este documento está sendo processado. Aguarde a conclusão para visualizar o conteúdo."}
                  {document.status === "Failed" &&
                    "Houve um erro ao processar este documento. Tente reprocessá-lo."}
                </AlertDescription>
              </Alert>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Process Modal with Model Selection */}
      <Dialog open={processModalOpen} onOpenChange={setProcessModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Processar Documento</DialogTitle>
            <DialogDescription>
              Selecione o modelo LLM para processar este documento.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="model-select">Modelo LLM</Label>
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger id="model-select">
                  <SelectValue placeholder="Selecione o modelo" />
                </SelectTrigger>
                <SelectContent>
                  {LLM_MODELS.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                O modelo escolhido será usado para extrair o grafo de conhecimento.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setProcessModalOpen(false)} disabled={isProcessing}>
              Cancelar
            </Button>
            <Button onClick={handleConfirmProcess} disabled={isProcessing}>
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processando...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Iniciar Processamento
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
