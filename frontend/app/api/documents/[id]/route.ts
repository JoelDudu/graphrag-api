import { type NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function DELETE(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const token = request.cookies.get("api_token")?.value

  if (!token) {
    return NextResponse.json({ error: "Não autenticado" }, { status: 401 })
  }

  try {
    const { id } = await params
    const response = await fetch(`${API_BASE}/documents/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    return NextResponse.json({}, { status: response.status })
  } catch (error) {
    console.error("[v0] Erro ao deletar documento:", error)
    return NextResponse.json({ error: "Erro ao deletar documento" }, { status: 500 })
  }
}
