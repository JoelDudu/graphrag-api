import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { username, password } = body

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    const clientId = process.env.CLIENT_ID
    const clientSecret = process.env.CLIENT_SECRET

    console.log("[v0] Proxy: Tentando login na API RAG para usuário:", username)
    console.log("[v0] Proxy: URL:", `${apiUrl}/auth/login`)

    const payload = new URLSearchParams()
    payload.append("grant_type", "password")
    payload.append("username", username)
    payload.append("password", password)
    payload.append("scope", "")
    if (clientId) payload.append("client_id", clientId)
    if (clientSecret) payload.append("client_secret", clientSecret)

    const response = await fetch(`${apiUrl}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Accept: "application/json",
      },
      body: payload.toString(),
    })

    console.log("[v0] Proxy: Response status:", response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error("[v0] Proxy: API error:", errorText)
      return NextResponse.json({ error: `Falha na autenticação: ${response.status}` }, { status: response.status })
    }

    const data = await response.json()
    console.log("[v0] Proxy: Login bem-sucedido")
    return NextResponse.json(data)
  } catch (error) {
    console.error("[v0] Proxy: Exception:", error)
    return NextResponse.json(
      { error: `Erro ao fazer login: ${error instanceof Error ? error.message : "Erro desconhecido"}` },
      { status: 500 },
    )
  }
}
