"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Loader2, X } from "lucide-react"
import { apiClient } from "@/lib/api-client"

interface GraphViewerProps {
  documentId: string
  filename: string
  isOpen: boolean
  onClose: () => void
}

interface Entity {
  id: string
  type: string
  description: string
}

interface Relationship {
  source: string
  target: string
  type: string
}

interface GraphData {
  entities: Entity[]
  relationships: Relationship[]
}

export default function GraphViewer({ documentId, filename, isOpen, onClose }: GraphViewerProps) {
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (isOpen) {
      loadGraphData()
    }
  }, [isOpen, documentId])

  const loadGraphData = async () => {
    setIsLoading(true)
    setError("")
    try {
      // Fazer uma query para obter as entidades e relacionamentos
      const result = await apiClient.query(
        "Retorne todas as entidades e relacionamentos do documento",
        documentId,
        "graph",
        "claude",
        100,
      )

      // Processar resultado para extrair entidades e relacionamentos
      const entities: Entity[] = []
      const relationships: Relationship[] = []

      if (result.sources) {
        result.sources.forEach((source: any) => {
          if (source.entity) {
            entities.push({
              id: source.entity,
              type: source.type || "Unknown",
              description: source.description || "",
            })

            if (source.relationship) {
              const [, target] = source.relationship.split(" -> ")
              if (target) {
                relationships.push({
                  source: source.entity,
                  target: target.trim(),
                  type: source.relationship.split(" ")[0],
                })
              }
            }
          }
        })
      }

      setGraphData({
        entities: Array.from(new Map(entities.map((e) => [e.id, e])).values()),
        relationships: relationships.filter((r, i, arr) => arr.findIndex((x) => x.source === r.source && x.target === r.target) === i),
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao carregar grafo"
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Grafo de Conhecimento - {filename}</DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <span className="ml-2">Carregando grafo...</span>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">{error}</div>
        ) : graphData ? (
          <div className="space-y-6">
            {/* Entidades */}
            <div>
              <h3 className="font-semibold text-lg mb-3">Entidades ({graphData.entities.length})</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {graphData.entities.map((entity) => (
                  <div key={entity.id} className="border border-border rounded-lg p-3 bg-muted/50">
                    <div className="font-medium text-foreground">{entity.id}</div>
                    <div className="text-xs text-muted-foreground mt-1">Tipo: {entity.type}</div>
                    {entity.description && <div className="text-sm text-foreground mt-2">{entity.description}</div>}
                  </div>
                ))}
              </div>
            </div>

            {/* Relacionamentos */}
            {graphData.relationships.length > 0 && (
              <div>
                <h3 className="font-semibold text-lg mb-3">Relacionamentos ({graphData.relationships.length})</h3>
                <div className="space-y-2">
                  {graphData.relationships.map((rel, idx) => (
                    <div key={idx} className="border border-border rounded-lg p-3 bg-muted/50 flex items-center gap-2">
                      <span className="font-medium text-foreground truncate">{rel.source}</span>
                      <span className="text-muted-foreground">→</span>
                      <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">{rel.type}</span>
                      <span className="text-muted-foreground">→</span>
                      <span className="font-medium text-foreground truncate">{rel.target}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {graphData.entities.length === 0 && graphData.relationships.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">Nenhuma entidade ou relacionamento encontrado</div>
            )}
          </div>
        ) : null}

        <div className="flex justify-end gap-2 mt-6">
          <Button variant="outline" onClick={onClose}>
            Fechar
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
