import { post, get } from './request'

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: {
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
}

export const login = (params: LoginParams): Promise<LoginResponse> => {
  const formData = new URLSearchParams()
  formData.append('username', params.username)
  formData.append('password', params.password)
  
  return post('/auth/login', formData) as Promise<LoginResponse>
}

export const getCurrentUser = (): Promise<LoginResponse['user']> => {
  return get('/auth/me') as Promise<LoginResponse['user']>
}

export const logout = (): Promise<void> => {
  return post('/auth/logout') as Promise<void>
}
