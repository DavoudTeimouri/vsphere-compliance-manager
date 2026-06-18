import { create } from 'zustand'

interface User {
  id: number
  username: string
  full_name: string | null
  email: string | null
  role: 'admin' | 'operator' | 'viewer'
}

interface AuthState {
  token: string | null
  user: User | null
  setAuth: (token: string, user: User) => void
  logout: () => void
  isAdmin: () => boolean
  isOperator: () => boolean
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem('vcm_token'),
  user: (() => {
    try {
      const u = localStorage.getItem('vcm_user')
      return u ? JSON.parse(u) : null
    } catch { return null }
  })(),
  setAuth: (token, user) => {
    localStorage.setItem('vcm_token', token)
    localStorage.setItem('vcm_user', JSON.stringify(user))
    set({ token, user })
  },
  logout: () => {
    localStorage.removeItem('vcm_token')
    localStorage.removeItem('vcm_user')
    set({ token: null, user: null })
  },
  isAdmin: () => get().user?.role === 'admin',
  isOperator: () => ['admin', 'operator'].includes(get().user?.role ?? ''),
}))
