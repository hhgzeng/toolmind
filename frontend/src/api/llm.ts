import { request } from "../utils/request"

// 大模型相关接口类型定义
export interface LLMResponse {
  llm_id: string
  model: string
  provider: string
  base_url: string
  api_key: string
  user_id: string
}

export interface CreateLLMRequest {
  model: string
  api_key: string
  base_url: string
  provider: string
}

export interface UpdateLLMRequest {
  llm_id: string
  model?: string
  api_key?: string
  base_url?: string
  provider?: string
}

export interface AgentModelConfig {
  config_id?: string
  user_id?: string
  conversation_model_id?: string | null
  tool_call_model_id?: string | null
  reasoning_model_id?: string | null
}

export interface ApiResponse<T> {
  status_code: number
  status_message: string
  data: T
}

// 获取可见大模型
export function getVisibleLLMsAPI() {
  return request<ApiResponse<Record<string, LLMResponse[]>>>({
    url: '/api/v1/llms/visible',
    method: 'GET'
  })
}

// 创建大模型
export function createLLMAPI(data: CreateLLMRequest) {
  return request<ApiResponse<null>>({
    url: '/api/v1/llms',
    method: 'POST',
    data
  })
}

// 更新大模型
export function updateLLMAPI(data: UpdateLLMRequest) {
  return request<ApiResponse<null>>({
    url: `/api/v1/llms/${data.llm_id}`,
    method: 'PUT',
    data
  })
}

// 删除大模型
export function deleteLLMAPI(data: { llm_id: string }) {
  return request<ApiResponse<null>>({
    url: `/api/v1/llms/${data.llm_id}`,
    method: 'DELETE'
  })
}

// 获取 Agent 模型配置
export function getAgentConfigAPI() {
  return request<ApiResponse<AgentModelConfig>>({
    url: '/api/v1/agent-config',
    method: 'get'
  })
}

// 更新 Agent 模型配置
export function updateAgentConfigAPI(data: AgentModelConfig) {
  return request<ApiResponse<AgentModelConfig>>({
    url: '/api/v1/agent-config',
    method: 'put',
    data
  })
}