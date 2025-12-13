"use client"

import { type ReactNode, useState, useEffect } from "react"
import { AuthContext } from "@/lib/auth-context"
import { apiClient } from "@/lib/api-client"

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const storedToken = localStorage.getItem("api_token")
    if (storedToken) {
      setToken(storedToken)
      apiClient.setToken(storedToken)
    }
    setIsLoading(false)
  }, [])

  const login = async (username: string, password: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await apiClient.login(username, password)
      setToken(response.access_token)
      localStorage.setItem("api_token", response.access_token)
      document.cookie = `api_token=${response.access_token}; path=/; max-age=${7 * 24 * 60 * 60}`
      apiClient.setToken(response.access_token)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao fazer login"
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    setToken(null)
    localStorage.removeItem("api_token")
    document.cookie = "api_token=; path=/; max-age=0"
    apiClient.clearToken()
  }

  return <AuthContext.Provider value={{ token, isLoading, error, login, logout }}>{children}</AuthContext.Provider>
}
