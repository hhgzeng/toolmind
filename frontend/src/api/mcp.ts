import { request } from '../utils/request'

export interface CreateMCPServerRequest {
  config?: any | string
}

export interface MCPServerTool {
  name: string
  description: string
  input_schema: {
    type: string
    title: string
    required?: string[]
    properties?: any
    description?: string
  }
}

export interface MCPServerConfig {
  key: string
  label: string
  value: string
}

export interface MCPServer {
  mcp_server_id: string
  server_name: string
  config?: MCPServerConfig[] | any
  is_active: boolean
  tools: string[]
  params: MCPServerTool[]
  user_id: string
}

export interface MCPServerResponse {
  status_code: number
  status_message: string
  data: MCPServer[] | null
}

export interface MCPServerSingleResponse {
  status_code: number
  status_message: string
  data: null
}

// 创建MCP服务器
export const createMCPServerAPI = (data: CreateMCPServerRequest) => {
  return request<MCPServerSingleResponse>({
    url: '/api/v1/mcp-servers',
    method: 'POST',
    data
  })
}

// 获取MCP服务器列表
export const getMCPServersAPI = () => {
  return request<MCPServerResponse>({
    url: '/api/v1/mcp-servers',
    method: 'GET'
  })
}

// 删除MCP服务器
export const deleteMCPServerAPI = (server_id: string) => {
  return request<MCPServerSingleResponse>({
    url: `/api/v1/mcp-servers/${server_id}`,
    method: 'DELETE'
  })
}

// 更新MCP服务器
export const updateMCPServerAPI = (data: { server_id: string; config?: any; is_active?: boolean; tools?: string[] }) => {
  const { server_id, ...rest } = data;
  return request<MCPServerSingleResponse>({
    url: `/api/v1/mcp-servers/${server_id}`,
    method: 'PUT',
    data: rest
  })
}