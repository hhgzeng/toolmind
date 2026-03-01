import { request } from '../utils/request'

export interface LoginForm {
  username: string
  password: string
}

export interface RegisterForm {
  user_name: string
  user_email?: string
  user_password: string
}

export interface LoginResponseData {
  access_token: string
  user_id: string
}

export interface LoginResponse {
  status_message: string
  data?: LoginResponseData
  status_code: number
  success: boolean
  message?: string
  token?: string
  userInfo?: {
    id: string
    username: string
    nickname?: string
    avatar?: string
  }
}

// 登录接口
export const loginAPI = (data: LoginForm) => {
  return request<LoginResponse>({
    url: '/api/v1/user/login',
    method: 'POST',
    data: {
      user_name: data.username,
      user_password: data.password
    }
  })
}

// 注册接口
export const registerAPI = (data: RegisterForm) => {
  return request({
    url: '/api/v1/user/register',
    method: 'POST',
    data
  })
}

// 登出接口
export const logoutAPI = () => {
  return request({
    url: '/api/v1/user/logout',
    method: 'POST'
  })
}

// 获取用户信息接口
export const getUserInfoAPI = (userId: string) => {
  return request({
    url: `/api/v1/user/info?user_id=${userId}`,
    method: 'GET'
  })
}

// 检查token是否有效
export const checkTokenAPI = () => {
  return request({
    url: '/api/v1/auth/check',
    method: 'GET'
  })
} 