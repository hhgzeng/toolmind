import { request } from '../utils/request'

export const getUserListAPI = (page: number = 1, limit: number = 20) => {
  return request({
    url: '/api/v1/user/list',
    method: 'GET',
    params: { page, limit }
  })
}

export const updateUserRoleAPI = (user_id: string, role: string) => {
  return request({
    url: '/api/v1/user/role',
    method: 'POST',
    data: { user_id, role }
  })
}

export const toggleUserStatusAPI = (user_id: string, enable: boolean) => {
  return request({
    url: '/api/v1/user/toggle_status',
    method: 'POST',
    data: { user_id, enable }
  })
}
