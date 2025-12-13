import { type NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function POST(request: NextRequest) {
  const token = request.cookies.get("api_token")?.value

  if (!token) {
    return NextResponse.json({ error: "Não autenticado" }, { status: 401 })
  }

  try {
    const formData = await request.formData()

    const response = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("[v0] Erro ao fazer upload:", error)
    return NextResponse.json({ error: "Erro ao fazer upload" }, { status: 500 })
  }
}
