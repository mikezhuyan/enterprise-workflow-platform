import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'
import { useAuthStore } from '../stores/auth'

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 自动设置Content-Type
    if (config.data instanceof URLSearchParams) {
      config.headers['Content-Type'] = 'application/x-www-form-urlencoded'
    } else if (typeof config.data === 'object' && !(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json'
    }
    
    console.log('请求:', config.method?.toUpperCase(), config.url, config.data)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log('响应:', response.config.url, response.status, response.data)
    return response.data
  },
  (error: AxiosError) => {
    console.error('响应错误:', error.message, error.response?.status, error.response?.data)
    
    const { response, config } = error
    
    if (response) {
      const { status, data } = response as any
      
      // 排除登录接口，避免登录失败时触发跳转
      const isLoginRequest = config?.url?.includes('/auth/login')
      
      switch (status) {
        case 401:
          if (!isLoginRequest) {
            message.error('登录已过期，请重新登录')
            useAuthStore.getState().logout()
            window.location.href = '/login'
          }
          break
        case 403:
          message.error('没有权限执行此操作')
          break
        case 404:
          message.error('请求的资源不存在')
          break
        case 422:
          message.error(data?.detail || '请求参数错误')
          break
        case 500:
          message.error('服务器内部错误')
          break
        default:
          if (!isLoginRequest) {
            message.error(data?.detail || '请求失败')
          }
      }
    } else {
      message.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

export default request

// 封装GET请求
export const get = <T>(url: string, params?: object): Promise<T> => {
  return request.get(url, { params }) as Promise<T>
}

// 封装POST请求
export const post = <T>(url: string, data?: object): Promise<T> => {
  return request.post(url, data) as Promise<T>
}

// 封装PUT请求
export const put = <T>(url: string, data?: object): Promise<T> => {
  return request.put(url, data) as Promise<T>
}

// 封装DELETE请求
export const del = <T>(url: string): Promise<T> => {
  return request.delete(url) as Promise<T>
}
