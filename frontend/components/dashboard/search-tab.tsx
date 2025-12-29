"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Search, Network, Zap, Loader2, AlertCircle } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface Source {
  text: string
  score?: number
  metadata?: Record<string, any>
  entity?: string
  type?: string
  description?: string
}

export default function SearchTab() {
  const [searchQuery, setSearchQuery] = useState("")
  const [searchType, setSearchType] = useState<"semantic" | "graph" | "hybrid">("semantic")
  const [answer, setAnswer] = useState("")
  const [sources, setSources] = useState<Source[]>([])
  const [modelUsed, setModelUsed] = useState("")
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState("")


  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    setIsSearching(true)
    setError("")
    setAnswer("")
    setSources([])

    try {
      const response = await apiClient.query(searchQuery, searchType)
      setAnswer(response.answer || "")
      setSources(response.sources || [])
      setModelUsed(response.model_used || "")
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao buscar"
      setError(message)
    } finally {
      setIsSearching(false)
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

      {/* Search Options */}
      <Card>
        <CardHeader>
          <CardTitle>Tipo de Busca</CardTitle>
          <CardDescription>Escolha como deseja buscar seus documentos</CardDescription>
        </CardHeader>
        <CardContent>
          <RadioGroup value={searchType} onValueChange={(value: any) => setSearchType(value)} className="space-y-4">
            <div className="flex items-center space-x-2 p-4 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
              <RadioGroupItem value="semantic" id="semantic" />
              <Label htmlFor="semantic" className="flex-1 cursor-pointer">
                <div className="font-medium text-foreground flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  Busca Semântica
                </div>
                <p className="text-sm text-muted-foreground">Entende o significado e contexto</p>
              </Label>
            </div>

            <div className="flex items-center space-x-2 p-4 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
              <RadioGroupItem value="graph" id="graph" />
              <Label htmlFor="graph" className="flex-1 cursor-pointer">
                <div className="font-medium text-foreground flex items-center gap-2">
                  <Network className="w-4 h-4" />
                  Busca em Grafo
                </div>
                <p className="text-sm text-muted-foreground">Analisa relações entre conceitos</p>
              </Label>
            </div>

            <div className="flex items-center space-x-2 p-4 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
              <RadioGroupItem value="hybrid" id="hybrid" />
              <Label htmlFor="hybrid" className="flex-1 cursor-pointer">
                <div className="font-medium text-foreground flex items-center gap-2">
                  <Search className="w-4 h-4" />
                  Busca Híbrida
                </div>
                <p className="text-sm text-muted-foreground">Combina semântica + grafo</p>
              </Label>
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      {/* Search Input */}
      <Card>
        <CardHeader>
          <CardTitle>Digite sua Busca</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="O que você quer buscar?"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && !isSearching && handleSearch()}
              disabled={isSearching}
              className="flex-1"
            />
            <Button onClick={handleSearch} disabled={isSearching || !searchQuery.trim()}>
              {isSearching ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Buscando...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  Buscar
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {(answer || sources.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle>Resultado da Busca</CardTitle>
            <CardDescription>
              Busca {searchType} • Modelo: {modelUsed}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Resposta */}
            {answer && (
              <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                <h4 className="font-medium text-foreground mb-2">Resposta</h4>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">{answer}</p>
              </div>
            )}

            {/* Fontes */}
            {sources.length > 0 && (
              <div>
                <h4 className="font-medium text-foreground mb-3">Fontes ({sources.length})</h4>
                <div className="space-y-3">
                  {sources.map((source, idx) => (
                    <div
                      key={idx}
                      className="p-3 border border-border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      {source.entity && (
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium text-primary">{source.entity}</span>
                          {source.type && (
                            <span className="text-xs px-2 py-0.5 bg-muted rounded">{source.type}</span>
                          )}
                        </div>
                      )}
                      <p className="text-sm text-muted-foreground">
                        {source.text || source.description || JSON.stringify(source)}
                      </p>
                      {source.score && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Relevância: {Math.round(source.score * 100)}%
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
