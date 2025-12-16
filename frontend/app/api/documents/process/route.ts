import { type NextRequest, NextResponse } from "next/server"

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "")

export async function POST(request: NextRequest) {
  const token = request.cookies.get("api_token")?.value

  if (!token) {
    return NextResponse.json({ error: "Não autenticado" }, { status: 401 })
  }

  try {
    const body = await request.json()

    const response = await fetch(`${API_BASE}/process`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("[v0] Erro ao processar documento:", error)
    return NextResponse.json({ error: "Erro ao processar documento" }, { status: 500 })
  }
}
