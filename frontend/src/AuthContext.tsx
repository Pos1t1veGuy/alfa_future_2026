import { createContext, useContext, useState } from 'react'
import { demoUsers, type Role, type User } from './mock/demo'

type AuthContextValue = { user: User | null; login: (role: Role) => void; logout: () => void }
const AuthContext = createContext<AuthContextValue | null>(null)
const storageKey = 'alfa-demo-user'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const saved = localStorage.getItem(storageKey)
  const [user, setUser] = useState<User | null>(saved ? JSON.parse(saved) as User : null)
  const login = (role: Role) => { const next = demoUsers[role]; localStorage.setItem(storageKey, JSON.stringify(next)); setUser(next) }
  const logout = () => { localStorage.removeItem(storageKey); setUser(null) }
  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>
}
export const useAuth = () => { const value = useContext(AuthContext); if (!value) throw new Error('AuthProvider is missing'); return value }
