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

interface SearchResult {
  id: string
  title: string
  excerpt: string
  source: string
  relevance: number
}

interface Document {
  document_id: string
  filename: string
  status: string
}

export default function SearchTab() {
  const [searchQuery, setSearchQuery] = useState("")
  const [searchType, setSearchType] = useState<"semantic" | "graph" | "hybrid">("semantic")
  const [selectedDoc, setSelectedDoc] = useState("")
  const [documents, setDocuments] = useState<Document[]>([])
  const [results, setResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    loadDocuments()
  }, [])

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

  const handleSearch = async () => {
    if (!searchQuery.trim() || !selectedDoc) return

    setIsSearching(true)
    setError("")
    setResults([])

    try {
      const response = await apiClient.query(searchQuery, selectedDoc, searchType)
      setResults(response.results || [])
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

      {/* Document Selection */}
      {documents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Selecione um Documento</CardTitle>
          </CardHeader>
          <CardContent>
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
          </CardContent>
        </Card>
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
            <Button onClick={handleSearch} disabled={isSearching || !selectedDoc}>
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
      {results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Resultados ({results.length})</CardTitle>
            <CardDescription>Resultados da busca {searchType}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {results.map((result) => (
                <div
                  key={result.id}
                  className="p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium text-foreground">{result.title}</h4>
                    <div className="text-right">
                      <p className="text-sm font-medium text-primary">
                        {Math.round(result.relevance * 100)}% relevância
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">{result.excerpt}</p>
                  <p className="text-xs text-muted-foreground">Fonte: {result.source}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
