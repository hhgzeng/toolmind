import { request } from "../utils/request"

export interface ApiResponse<T> {
  status_code: number
  status_message: string
  data: T
}

export interface WebSearchSettings {
  api_key: string
}

export function getWebSearchAPI() {
  return request<ApiResponse<WebSearchSettings>>({
    url: "/api/v1/tools/web_search",
    method: "GET"
  })
}

export function updateWebSearchAPI(data: WebSearchSettings) {
  return request<ApiResponse<WebSearchSettings>>({
    url: "/api/v1/tools/web_search",
    method: "POST",
    data
  })
}

