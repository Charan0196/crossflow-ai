import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username, password) => {
        set({ isLoading: true, error: null })
        
        // Demo login - accepts demo/demo123
        if (username === 'demo' && password === 'demo123') {
          const user = {
            id: 1,
            username: 'demo',
            email: 'demo@crossflow.ai',
            is_active: true
          }
          const token = 'demo-token-' + Date.now()
          
          localStorage.setItem('access_token', token)
          
          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
            error: null
          })
          
          return true
        }
        
        // Try backend API for other credentials
        try {
          const response = await fetch('http://localhost:8000/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ username, password })
          })
          
          if (response.ok) {
            const data = await response.json()
            localStorage.setItem('access_token', data.access_token)
            
            set({
              user: { username },
              token: data.access_token,
              isAuthenticated: true,
              isLoading: false,
              error: null
            })
            return true
          }
        } catch (e) {
          console.log('Backend not available, using demo mode')
        }
        
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
          error: 'Invalid credentials'
        })
        return false
      },

      logout: () => {
        localStorage.removeItem('access_token')
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null
        })
      },

      initializeAuth: () => {
        const token = localStorage.getItem('access_token')
        if (token) {
          set({
            user: { username: 'demo' },
            token,
            isAuthenticated: true,
            error: null
          })
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)