import { request } from '../utils/request'
import { fetchEventSource } from '@microsoft/fetch-event-source'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// 获取工作区插件列表
export const getWorkspacePluginsAPI = async () => {
  return request({
    url: '/api/v1/workspace/plugins',
    method: 'get'
  })
}

// 获取工作区会话列表
export const getWorkspaceSessionsAPI = async () => {
  return request({
    url: '/api/v1/workspace/session',
    method: 'get'
  })
}

// 创建工作区会话
export const createWorkspaceSessionAPI = async (data: { title?: string, contexts?: any }) => {
  return request({
    url: '/api/v1/workspace/session',
    method: 'post',
    data
  })
}

// 获取工作区会话信息
export const getWorkspaceSessionInfoAPI = async (sessionId: string) => {
  return request({
    url: `/api/v1/workspace/session/${sessionId}`,
    method: 'post'
  })
}

// 删除工作区会话  
export const deleteWorkspaceSessionAPI = async (sessionId: string) => {
  return request({
    url: `/api/v1/workspace/session`,
    method: 'delete',
    params: {
      session_id: sessionId
    }
  })
}

// 更新工作区会话 (例如重命名)
export const updateWorkspaceSessionAPI = async (sessionId: string, data: { title?: string, is_pinned?: boolean }) => {
  return request({
    url: `/api/v1/workspace/session/${sessionId}`,
    method: 'patch',
    data
  })
}

