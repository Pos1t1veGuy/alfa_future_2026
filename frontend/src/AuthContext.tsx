import { createContext, useContext, useEffect, useState } from 'react'
import { api } from './api/client'

export type Role = 'client' | 'bank_manager' | 'admin'
export type User = { id: string; name: string; company: string; role: Role; email: string; inn?: string; phone?: string }
type AuthContextValue = {
  user: User | null
  ready: boolean
  login: (email: string, password: string) => Promise<User>
  register: (payload: { fullName: string; email: string; password: string; company: string; inn: string; phone: string }) => Promise<User>
  logout: () => void
}
const AuthContext = createContext<AuthContextValue | null>(null)
const storageKey = 'alfa-user'
function saveTokens(access: string, refresh: string, user: User) {
  localStorage.setItem('alfa-access', access)
  localStorage.setItem('alfa-refresh', refresh)
  localStorage.setItem(storageKey, JSON.stringify(user))
}
function fromPayload(raw: any): User {
  return { id: String(raw.id), email: raw.email, name: raw.fullName || raw.name || raw.email, company: raw.company || '', role: raw.role || 'client', inn: raw.inn || '', phone: raw.phone || '' }
}
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    try { const value = localStorage.getItem(storageKey); return value ? fromPayload(JSON.parse(value)) : null } catch { return null }
  })
  const [ready, setReady] = useState(false)
  useEffect(() => {
    const token = localStorage.getItem('alfa-access')
    if (!token) { setReady(true); return }
    api.get('/me/').then(({ data }) => { const next = fromPayload(data); localStorage.setItem(storageKey, JSON.stringify(next)); setUser(next) })
      .catch(() => { localStorage.removeItem('alfa-access'); localStorage.removeItem('alfa-refresh'); localStorage.removeItem(storageKey); setUser(null) })
      .finally(() => setReady(true))
  }, [])
  const login = async (email: string, password: string) => {
    const { data } = await api.post('/auth/login/', { username: email, password })
    const next = fromPayload(data.user)
    saveTokens(data.accessToken || data.access, data.refreshToken || data.refresh, next)
    setUser(next)
    return next
  }
  const register = async (payload: { fullName: string; email: string; password: string; company: string; inn: string; phone: string }) => {
    const { data } = await api.post('/auth/register/', payload)
    const next = fromPayload(data.user)
    saveTokens(data.accessToken, data.refreshToken, next)
    setUser(next)
    return next
  }
  const logout = () => {
    const refresh = localStorage.getItem('alfa-refresh')
    if (refresh) void api.post('/auth/logout/', { refreshToken: refresh }).catch(() => undefined)
    localStorage.removeItem('alfa-access'); localStorage.removeItem('alfa-refresh'); localStorage.removeItem(storageKey); setUser(null)
  }
  return <AuthContext.Provider value={{ user, ready, login, register, logout }}>{children}</AuthContext.Provider>
}
export const useAuth = () => { const value = useContext(AuthContext); if (!value) throw new Error('AuthProvider is missing'); return value }
