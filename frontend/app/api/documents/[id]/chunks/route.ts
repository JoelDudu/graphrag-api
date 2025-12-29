import { NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function GET(
    request: Request,
    { params }: { params: Promise<{ id: string }> }
) {
    const { id: documentId } = await params

    try {
        const token = request.headers.get("authorization")?.split(" ")[1] || ""

        const response = await fetch(`${API_BASE}/documents/${documentId}/chunks`, {
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json",
            },
        })

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: "Erro ao buscar chunks" }))
            return NextResponse.json(
                { error: errorData.detail || "Erro ao buscar chunks" },
                { status: response.status }
            )
        }

        const data = await response.json()
        return NextResponse.json(data)
    } catch (error) {
        console.error("[API] Erro ao buscar chunks:", error)
        return NextResponse.json(
            { error: "Erro interno ao buscar chunks" },
            { status: 500 }
        )
    }
}
