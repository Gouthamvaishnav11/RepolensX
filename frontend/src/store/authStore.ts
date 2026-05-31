import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { userAPI } from '@/lib/api'

interface User {
  id: string
  username: string
  email: string | null
  name: string | null
  avatar_url: string | null
  plan: 'free' | 'pro' | 'team' | 'enterprise'
  repos_analyzed_this_month: number
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  setTokens: (access: string, refresh: string) => void
  fetchUser: () => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      setTokens: (access: string, refresh: string) => {
        localStorage.setItem('access_token', access)
        localStorage.setItem('refresh_token', refresh)
        set({ isAuthenticated: true })
      },

      fetchUser: async () => {
        set({ isLoading: true })
        try {
          const res = await userAPI.getMe()
          set({ user: res.data, isAuthenticated: true, isLoading: false })
        } catch {
          set({ user: null, isAuthenticated: false, isLoading: false })
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        }
      },

      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, isAuthenticated: false })
      },
    }),
    {
      name: 'repolens-auth',
      partialize: (state) => ({ isAuthenticated: state.isAuthenticated }),
    }
  )
)
