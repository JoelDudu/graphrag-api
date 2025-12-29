import { NextRequest, NextResponse } from "next/server"

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "")

export async function GET(request: NextRequest, { params }: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await params
  const path = `/${slug.join("/")}`
  const token = request.cookies.get("api_token")?.value

  try {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    }

    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }

    const response = await fetch(`${API_BASE_URL}${path}${request.nextUrl.search}`, {
      method: "GET",
      headers,
    })

    const data = await response.json()

    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("Proxy error:", error)
    return NextResponse.json({ error: "Proxy error" }, { status: 500 })
  }
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await params
  const path = `/${slug.join("/")}`
  const token = request.cookies.get("api_token")?.value

  try {
    const headers: HeadersInit = {}

    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }

    let body: any = null
    let fetchOptions: RequestInit = {
      method: "POST",
      headers,
    }

    // Verificar se é FormData (upload)
    const contentType = request.headers.get("content-type")
    if (contentType?.includes("multipart/form-data")) {
      body = await request.formData()
      fetchOptions.body = body
    } else if (contentType?.includes("application/json")) {
      try {
        body = await request.json()
        headers["Content-Type"] = "application/json"
        fetchOptions.body = JSON.stringify(body)
      } catch {
        // Empty body - that's OK for some endpoints like /cancel
        headers["Content-Type"] = "application/json"
      }
    }

    const response = await fetch(`${API_BASE_URL}${path}`, fetchOptions)

    const data = await response.json()

    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("Proxy error:", error)
    return NextResponse.json({ error: "Proxy error" }, { status: 500 })
  }
}

export async function DELETE(request: NextRequest, { params }: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await params
  const path = `/${slug.join("/")}`
  const token = request.cookies.get("api_token")?.value

  try {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    }

    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "DELETE",
      headers,
    })

    const data = await response.json()

    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("Proxy error:", error)
    return NextResponse.json({ error: "Proxy error" }, { status: 500 })
  }
}
