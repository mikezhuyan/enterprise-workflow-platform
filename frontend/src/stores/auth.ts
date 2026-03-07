import { create } from 'zustand'
import { message } from 'antd'
import { login as loginApi, getCurrentUser } from '../services/auth'

interface User {
  id: string
  username: string
  email: string
  full_name: string | null
  avatar: string | null
  is_superuser: boolean
  roles: Array<{
    id: string
    name: string
  }>
}

interface AuthState {
  token: string | null
  refreshToken: string | null
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  // Actions
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  initialize: () => void
}

export const useAuthStore = create<AuthState>(
  (set, get) => ({
    token: localStorage.getItem('token'),
    refreshToken: localStorage.getItem('refreshToken'),
    user: null,
    isAuthenticated: !!localStorage.getItem('token'),
    isLoading: false,
    error: null,

    login: async (username: string, password: string) => {
      console.log('[AuthStore] 开始登录:', username)
      try {
        set({ isLoading: true, error: null })
        
        const response = await loginApi({ username, password })
        console.log('[AuthStore] 登录成功:', response)
        
        // 保存到localStorage
        localStorage.setItem('token', response.access_token)
        localStorage.setItem('refreshToken', response.refresh_token)
        localStorage.setItem('user', JSON.stringify(response.user))
        
        set({
          token: response.access_token,
          refreshToken: response.refresh_token,
          user: response.user,
          isAuthenticated: true,
          error: null,
        })
        
        message.success('登录成功')
        return true
      } catch (error: any) {
        console.error('[AuthStore] 登录失败:', error)
        const errorMsg = error.response?.data?.detail || error.message || '登录失败'
        set({ error: errorMsg })
        message.error(errorMsg)
        return false
      } finally {
        set({ isLoading: false })
      }
    },

    logout: () => {
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      set({
        token: null,
        refreshToken: null,
        user: null,
        isAuthenticated: false,
        error: null,
      })
      message.success('已退出登录')
    },

    initialize: () => {
      const token = localStorage.getItem('token')
      if (token) {
        getCurrentUser()
          .then((user) => {
            set({ user, isAuthenticated: true })
          })
          .catch(() => {
            get().logout()
          })
      }
    },
  })
)
