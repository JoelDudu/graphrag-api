"use client"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { MessageSquare, Network, Search, Upload, LogIn, ArrowRight, Zap, Shield, Users } from "lucide-react"

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-muted/20">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Network className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-foreground">GraphRAG</span>
          </div>
          <div className="flex gap-3">
            <Link href="/login">
              <Button variant="outline" size="sm">
                <LogIn className="w-4 h-4 mr-2" />
                Login
              </Button>
            </Link>
            <Link href="/signup">
              <Button size="sm">Começar Grátis</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32">
        <div className="max-w-3xl">
          <h1 className="text-5xl md:text-6xl font-bold text-foreground mb-6 leading-tight text-balance">
            Busca inteligente em seus documentos com IA
          </h1>
          <p className="text-xl text-muted-foreground mb-8 leading-relaxed text-balance">
            Processe documentos de forma inteligente com busca semântica, análise de grafos e um chatbot interativo.
            Compartilhe com sua equipe com controle de acesso granular.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Link href="/dashboard">
              <Button size="lg" className="w-full sm:w-auto">
                Ir para Dashboard <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="w-full sm:w-auto bg-transparent">
              Ver Documentação
            </Button>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid md:grid-cols-3 gap-6 mt-20">
          <Card className="border-border/50 hover:border-border transition-colors">
            <CardHeader>
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <Upload className="w-6 h-6 text-primary" />
              </div>
              <CardTitle>Upload Fácil</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Envie documentos em múltiplos formatos e processe automaticamente com IA
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="border-border/50 hover:border-border transition-colors">
            <CardHeader>
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <Search className="w-6 h-6 text-primary" />
              </div>
              <CardTitle>Busca Inteligente</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Semântica, grafo e híbrida - escolha como buscar seus dados</CardDescription>
            </CardContent>
          </Card>

          <Card className="border-border/50 hover:border-border transition-colors">
            <CardHeader>
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <MessageSquare className="w-6 h-6 text-primary" />
              </div>
              <CardTitle>Chatbot IA</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Interaja naturalmente com seus documentos via conversas</CardDescription>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="border-t border-border bg-muted/50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-12 text-balance">
            Por que escolher GraphRAG?
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="flex gap-4">
              <Zap className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-foreground mb-2">Processamento Rápido</h3>
                <p className="text-muted-foreground">Índices otimizados para buscas em millisegundos</p>
              </div>
            </div>
            <div className="flex gap-4">
              <Shield className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-foreground mb-2">Segurança</h3>
                <p className="text-muted-foreground">Controle de acesso granular e dados criptografados</p>
              </div>
            </div>
            <div className="flex gap-4">
              <Users className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-foreground mb-2">Colaboração</h3>
                <p className="text-muted-foreground">Compartilhe documentos com sua equipe facilmente</p>
              </div>
            </div>
            <div className="flex gap-4">
              <Network className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-foreground mb-2">Análise de Grafos</h3>
                <p className="text-muted-foreground">Visualize conexões e relações entre conceitos</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6 text-balance">Pronto para começar?</h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Crie sua conta em segundos e comece a processar seus documentos com IA
          </p>
          <Link href="/signup">
            <Button size="lg">Criar Conta Grátis</Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-muted/30 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-muted-foreground text-sm">
          <p>&copy; 2025 GraphRAG. Todos os direitos reservados.</p>
        </div>
      </footer>
    </div>
  )
}
