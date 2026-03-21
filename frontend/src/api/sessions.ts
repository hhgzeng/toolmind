import { request } from '../utils/request'

// 获取会话列表
export const getSessionsAPI = async () => {
  return request({
    url: '/api/v1/sessions',
    method: 'get'
  })
}

// 获取会话信息
export const getSessionInfoAPI = async (sessionId: string) => {
  return request({
    url: `/api/v1/sessions/${sessionId}`,
    method: 'get'
  })
}

// 删除会话
export const deleteSessionAPI = async (sessionId: string) => {
  return request({
    url: `/api/v1/sessions/${sessionId}`,
    method: 'delete'
  })
}

// 更新会话（例如重命名/置顶）
export const updateSessionAPI = async (sessionId: string, data: { title?: string, is_pinned?: boolean }) => {
  return request({
    url: `/api/v1/sessions/${sessionId}`,
    method: 'patch',
    data
  })
}
