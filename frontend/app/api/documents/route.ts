import { type NextRequest, NextResponse } from "next/server"

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "")

export async function GET(request: NextRequest) {
  const token = request.cookies.get("api_token")?.value

  if (!token) {
    return NextResponse.json({ error: "Não autenticado" }, { status: 401 })
  }

  try {
    const response = await fetch(`${API_BASE}/documents`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/json",
      },
    })

    // Check if response is JSON
    const contentType = response.headers.get("content-type")
    if (!contentType || !contentType.includes("application/json")) {
      const text = await response.text()
      console.error("[v0] Backend returned non-JSON response:", text)
      return NextResponse.json(
        { error: `Backend error: ${text.substring(0, 100)}` },
        { status: response.status || 500 }
      )
    }

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("[v0] Erro ao listar documentos:", error)
    return NextResponse.json({ error: "Erro ao listar documentos" }, { status: 500 })
  }
}
