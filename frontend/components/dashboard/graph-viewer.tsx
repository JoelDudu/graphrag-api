"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Loader2, ZoomIn, ZoomOut, Maximize2 } from "lucide-react"
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

// Cores por tipo de entidade
const TYPE_COLORS: Record<string, string> = {
  Person: "#4CAF50",
  Organization: "#2196F3",
  Location: "#FF9800",
  Concept: "#9C27B0",
  Product: "#E91E63",
  Event: "#00BCD4",
  Technology: "#607D8B",
  Skill: "#795548",
  default: "#6366f1"
}

function getColorForType(type: string): string {
  return TYPE_COLORS[type] || TYPE_COLORS.default
}

export default function GraphViewer({ documentId, filename, isOpen, onClose }: GraphViewerProps) {
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const containerRef = useRef<HTMLDivElement>(null)
  const networkRef = useRef<any>(null)

  useEffect(() => {
    if (isOpen) {
      loadGraphData()
    }
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy()
        networkRef.current = null
      }
    }
  }, [isOpen, documentId])

  const loadGraphData = async () => {
    setIsLoading(true)
    setError("")
    try {
      const result = await apiClient.getGraph(documentId)
      setGraphData({
        entities: result.entities || [],
        relationships: result.relationships || [],
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao carregar grafo"
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  // Inicializa vis-network quando os dados carregarem
  useEffect(() => {
    if (!graphData || !containerRef.current || isLoading) return

    const initNetwork = async () => {
      try {
        const { Network } = await import("vis-network/standalone")
        const { DataSet } = await import("vis-data/standalone")

        // Deduplicar entidades pelo ID
        const uniqueEntities = graphData.entities.reduce((acc, entity) => {
          if (!acc.find(e => e.id === entity.id)) {
            acc.push(entity)
          }
          return acc
        }, [] as typeof graphData.entities)

        // Criar nó do documento como ponto central
        const documentNode = {
          id: "__document__",
          label: filename.length > 25 ? filename.substring(0, 25) + "..." : filename,
          title: `📄 Documento: ${filename}`,
          color: {
            background: "#FFD700",
            border: "#DAA520",
            highlight: {
              background: "#FFE55C",
              border: "#fff"
            }
          },
          font: { color: "#333", size: 14, bold: true },
          shape: "star",
          size: 40,
        }

        // Criar nós das entidades
        const entityNodes = uniqueEntities.map((entity, index) => ({
          id: entity.id,
          label: entity.id.length > 20 ? entity.id.substring(0, 20) + "..." : entity.id,
          title: `${entity.type}\n${entity.description || ""}`,
          color: {
            background: getColorForType(entity.type),
            border: getColorForType(entity.type),
            highlight: {
              background: getColorForType(entity.type),
              border: "#fff"
            }
          },
          font: { color: "#fff", size: 12 },
          shape: "dot",
          size: 20,
        }))

        // Combinar documento + entidades
        const nodes = new DataSet([documentNode, ...entityNodes])

        // Encontrar entidades mais conectadas para ligar ao documento
        const entityConnectionCount = new Map<string, number>()
        graphData.relationships.forEach(rel => {
          entityConnectionCount.set(rel.source, (entityConnectionCount.get(rel.source) || 0) + 1)
          entityConnectionCount.set(rel.target, (entityConnectionCount.get(rel.target) || 0) + 1)
        })

        // Ordenar por número de conexões e pegar os top 15
        const topEntities = [...entityConnectionCount.entries()]
          .sort((a, b) => b[1] - a[1])
          .slice(0, 15)
          .map(([id]) => id)

        // Se não houver entidades conectadas, pegar as primeiras 10
        const entitiesToConnect = topEntities.length > 0
          ? topEntities
          : uniqueEntities.slice(0, 10).map(e => e.id)

        // Criar arestas do documento para entidades principais
        const documentEdges = entitiesToConnect.map((entityId, idx) => ({
          id: `doc_${idx}`,
          from: "__document__",
          to: entityId,
          color: { color: "#DAA520", highlight: "#FFD700" },
          width: 2,
          dashes: true,
          smooth: { enabled: true, type: "curvedCW", roundness: 0.1 }
        }))

        // Criar arestas entre entidades
        const entityEdges = graphData.relationships.map((rel, index) => ({
          id: index + 1000,
          from: rel.source,
          to: rel.target,
          label: rel.type,
          arrows: "to",
          color: { color: "#888", highlight: "#6366f1" },
          font: { size: 10, color: "#666", strokeWidth: 0 },
          smooth: { enabled: true, type: "curvedCW", roundness: 0.2 }
        }))

        const edges = new DataSet([...documentEdges, ...entityEdges])

        // Opções do grafo
        const options = {
          nodes: {
            borderWidth: 2,
            shadow: true,
          },
          edges: {
            width: 1,
            shadow: true,
          },
          physics: {
            enabled: true,
            solver: "forceAtlas2Based",
            forceAtlas2Based: {
              gravitationalConstant: -50,
              centralGravity: 0.01,
              springLength: 100,
              springConstant: 0.08,
            },
            stabilization: {
              iterations: 100,
              fit: true
            }
          },
          interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true,
          }
        }

        // Criar rede
        if (networkRef.current) {
          networkRef.current.destroy()
        }

        if (!containerRef.current) return
        networkRef.current = new Network(containerRef.current, { nodes, edges }, options)

        // Ajustar ao container após estabilização
        networkRef.current.once("stabilizationIterationsDone", () => {
          networkRef.current.fit()
        })

      } catch (err) {
        console.error("Erro ao inicializar vis-network:", err)
        setError("Erro ao renderizar grafo")
      }
    }

    initNetwork()
  }, [graphData, isLoading])

  const handleZoomIn = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale()
      networkRef.current.moveTo({ scale: scale * 1.3 })
    }
  }

  const handleZoomOut = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale()
      networkRef.current.moveTo({ scale: scale / 1.3 })
    }
  }

  const handleFit = () => {
    if (networkRef.current) {
      networkRef.current.fit()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent
        className="flex flex-col p-4"
        style={{ maxWidth: '98vw', width: '98vw', height: '95vh' }}
      >
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center justify-between">
            <span>Grafo de Conhecimento - {filename}</span>
            {graphData && (
              <span className="text-sm font-normal text-muted-foreground">
                {new Set(graphData.entities.map(e => e.id)).size} entidades • {graphData.relationships.length} relacionamentos
              </span>
            )}
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 relative min-h-0">
          {isLoading ? (
            <div className="absolute inset-0 flex items-center justify-center bg-muted/50 rounded-lg">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
              <span className="ml-2">Carregando grafo...</span>
            </div>
          ) : error ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">{error}</div>
            </div>
          ) : graphData && graphData.entities.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
              Nenhuma entidade encontrada neste documento
            </div>
          ) : (
            <>
              {/* Canvas do grafo */}
              <div
                ref={containerRef}
                className="absolute inset-0 rounded-lg border border-border bg-background"
              />

              {/* Controles de zoom */}
              <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
                <Button variant="outline" size="icon" onClick={handleZoomIn} title="Zoom In">
                  <ZoomIn className="w-4 h-4" />
                </Button>
                <Button variant="outline" size="icon" onClick={handleZoomOut} title="Zoom Out">
                  <ZoomOut className="w-4 h-4" />
                </Button>
                <Button variant="outline" size="icon" onClick={handleFit} title="Ajustar">
                  <Maximize2 className="w-4 h-4" />
                </Button>
              </div>

              {/* Legenda dinâmica baseada nos tipos reais do documento */}
              {graphData && (
                <div className="absolute bottom-4 left-4 bg-background/90 backdrop-blur rounded-lg p-3 border border-border z-10 max-w-xs">
                  <div className="text-xs font-medium mb-2">Legenda</div>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 max-h-48 overflow-y-auto">
                    {/* Documento */}
                    <div className="flex items-center gap-2 text-xs col-span-2 pb-1 mb-1 border-b">
                      <div className="w-4 h-4 flex-shrink-0" style={{ color: "#FFD700" }}>★</div>
                      <span className="font-medium">Documento (início)</span>
                    </div>
                    {/* Tipos de entidade */}
                    {[...new Set(graphData.entities.map(e => e.type))].slice(0, 12).map((type) => (
                      <div key={type} className="flex items-center gap-2 text-xs">
                        <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: getColorForType(type) }} />
                        <span className="truncate">{type}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="flex justify-end gap-2 flex-shrink-0 pt-2">
          <Button variant="outline" onClick={onClose}>
            Fechar
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
