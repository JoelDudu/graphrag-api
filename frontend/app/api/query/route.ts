import { type NextRequest, NextResponse } from "next/server"

const API_BASE = "https://app-ragapi.i85yk7.easypanel.host"

export async function POST(request: NextRequest) {
  const token = request.cookies.get("api_token")?.value

  if (!token) {
    return NextResponse.json({ error: "Não autenticado" }, { status: 401 })
  }

  try {
    const body = await request.json()

    const response = await fetch(`${API_BASE}/query`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API responded with status ${response.status}: ${errorText}`);
        }

        const data = await response.json();
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("[v0] Erro na busca:", error)
    return NextResponse.json({ error: "Erro na busca" }, { status: 500 })
  }
}
