import { request } from '../utils/request'

export const getUserListAPI = (page: number = 1, limit: number = 20) => {
  return request({
    url: '/api/v1/users',
    method: 'GET',
    params: { page, limit }
  })
}

export const updateUserRoleAPI = (user_id: string, role: string) => {
  return request({
    url: `/api/v1/users/${user_id}/role`,
    method: 'PUT',
    data: { role }
  })
}

export const toggleUserStatusAPI = (user_id: string, enable: boolean) => {
  return request({
    url: `/api/v1/users/${user_id}/status`,
    method: 'PATCH',
    data: { enable }
  })
}
