"use client"

import { useState } from "react"
import { Search, Upload, FileText, RefreshCw, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Document } from "./documents-tab"

interface DocumentsSidebarProps {
  documents: Document[]
  selectedDocument: Document | null
  onSelectDocument: (document: Document) => void
  onRefresh: () => void
  onUpload: (file: File) => Promise<void>
  isLoading: boolean
  fileInputRef: React.RefObject<HTMLInputElement>
}

const LLM_MODELS = [
  { value: "claude", label: "Claude" },
  { value: "openai", label: "OpenAI GPT-4" },
  { value: "kimi", label: "Moonshot/Kimi" },
  { value: "deepseek", label: "DeepSeek" },
]

export default function DocumentsSidebar({
  documents,
  selectedDocument,
  onSelectDocument,
  onRefresh,
  onUpload,
  isLoading,
  fileInputRef,
}: DocumentsSidebarProps) {
  const [searchQuery, setSearchQuery] = useState("")

  // Upload modal state
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  const filteredDocuments = (documents || []).filter((doc) =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.currentTarget.files?.[0]
    if (file) {
      setPendingFile(file)
      setUploadModalOpen(true)
      e.target.value = "" // Reset input
    }
  }

  const handleConfirmUpload = async () => {
    if (!pendingFile) return

    setIsUploading(true)
    try {
      await onUpload(pendingFile)
      setUploadModalOpen(false)
      setPendingFile(null)
    } finally {
      setIsUploading(false)
    }
  }

  const handleCancelUpload = () => {
    setUploadModalOpen(false)
    setPendingFile(null)
  }

  const getStatusInfo = (status: string) => {
    switch (status) {
      case "Pending":
        return { color: "bg-yellow-500", textColor: "text-yellow-600", label: "Pendente" }
      case "Processing":
        return { color: "bg-blue-500", textColor: "text-blue-600", label: "Processando", spin: true }
      case "Completed":
        return { color: "bg-green-500", textColor: "text-green-600", label: "Concluído" }
      case "Failed":
        return { color: "bg-red-500", textColor: "text-red-600", label: "Erro" }
      default:
        return { color: "bg-gray-400", textColor: "text-gray-600", label: status }
    }
  }

  return (
    <>
      <div className="h-full flex flex-col bg-card border-r border-border overflow-hidden">
        {/* Header - Compact */}
        <div className="p-3 border-b border-border space-y-2 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-sm text-foreground">Documentos</h2>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onRefresh} disabled={isLoading}>
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </Button>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2.5 top-2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Buscar documento..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 h-8 text-sm"
            />
          </div>

          {/* Upload Button */}
          <label htmlFor="sidebar-file-upload" className="block">
            <Button variant="default" size="sm" className="w-full" asChild>
              <span>
                <Upload className="w-4 h-4 mr-2" />
                Upload
              </span>
            </Button>
            <input
              id="sidebar-file-upload"
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              className="hidden"
              accept=".pdf,.docx,.txt,.xlsx,.xls,.doc,.pptx,.ppt,.csv"
            />
          </label>
        </div>

        {/* Documents List */}
        <ScrollArea className="flex-1 min-h-0">
          <div className="p-2">
            {filteredDocuments.length === 0 ? (
              <div className="text-center py-8 px-4">
                <FileText className="w-10 h-10 mx-auto text-muted-foreground/50 mb-2" />
                <p className="text-sm text-muted-foreground">
                  {searchQuery ? "Nenhum documento encontrado" : "Nenhum documento"}
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                {filteredDocuments.map((doc) => {
                  const statusInfo = getStatusInfo(doc.status)
                  const isSelected = selectedDocument?.document_id === doc.document_id

                  return (
                    <div
                      key={doc.document_id}
                      onClick={() => onSelectDocument(doc)}
                      className={`p-3 rounded-lg cursor-pointer transition-all ${isSelected
                        ? "bg-primary/10 border-2 border-primary/30"
                        : "hover:bg-muted border-2 border-transparent"
                        }`}
                    >
                      {/* Status indicator + Document name */}
                      <div className="flex items-start gap-2">
                        {/* Status dot */}
                        <div className="mt-1.5 flex-shrink-0">
                          {doc.status === "Processing" ? (
                            <Loader2 className="w-3 h-3 text-blue-500 animate-spin" />
                          ) : (
                            <div className={`w-2.5 h-2.5 rounded-full ${statusInfo.color}`} />
                          )}
                        </div>

                        {/* Document info - full width */}
                        <div className="flex-1 min-w-0">
                          {/* Filename - can wrap to multiple lines */}
                          <p
                            className="text-sm font-medium text-foreground leading-tight break-words"
                            style={{ wordBreak: 'break-word' }}
                          >
                            {doc.filename}
                          </p>

                          {/* Date and status */}
                          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                            <span>{new Date(doc.created_at).toLocaleDateString("pt-BR")}</span>
                            <span>•</span>
                            <span className={statusInfo.textColor}>
                              {statusInfo.label}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="p-3 border-t border-border flex-shrink-0">
          <p className="text-xs text-muted-foreground text-center">
            {documents.length} {documents.length === 1 ? "documento" : "documentos"}
          </p>
        </div>
      </div>

      {/* Upload Modal with Model Selection */}
      <Dialog open={uploadModalOpen} onOpenChange={setUploadModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Upload de Documento</DialogTitle>
            <DialogDescription>
              Envie seu documento e selecione o modelo para processamento.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* File info */}
            <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
              <FileText className="w-8 h-8 text-primary flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm break-words">{pendingFile?.name}</p>
                <p className="text-xs text-muted-foreground">
                  {pendingFile && (pendingFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>

            <p className="text-xs text-muted-foreground">
              O documento será salvo e você poderá processá-lo depois.
            </p>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleCancelUpload} disabled={isUploading}>
              Cancelar
            </Button>
            <Button onClick={handleConfirmUpload} disabled={isUploading}>
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Enviando...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Enviar
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
