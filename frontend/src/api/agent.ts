import { fetchEventSource } from '@microsoft/fetch-event-source';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// 开始执行 Agent 任务（流式）
export const startAgentTaskAPI = async (
  data: {
    query: string
  },
  onMessage: (data: any) => void,
  onTaskGraph?: (graph: any) => void,  // 处理任务图数据
  onStepResult?: (stepData: { title: string; message: string }) => void,  // 处理步骤结果
  onTaskResult?: (message: string) => void,  // 新增：处理任务最终结果
  onEvaluating?: () => void,  // 处理开始评判事件
  onError?: (error: any) => void,
  onClose?: () => void,
  onSessionStarted?: (session: { sessionId: string; title: string; createTime?: string }) => void,
  onSessionUpdated?: (session: { sessionId: string; title: string }) => void,
  onSessionTitleChunk?: (session: { sessionId: string; title: string }) => void,
  externalAbortController?: AbortController
): Promise<AbortController> => {
  const token = localStorage.getItem('token')

  console.log('开始调用 task_start 接口，参数:', data)

  const ctrl = externalAbortController || new AbortController()

  try {
    await fetchEventSource(`${BASE_URL}/api/v1/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data),
      signal: ctrl.signal,
      openWhenHidden: true,
      async onopen(response) {
        if (response.ok) {
          console.log('✅ task_start 连接成功')
          return
        }
        // 非 2xx 状态码，抛错阻止 fetchEventSource 重试
        const errorText = await response.text().catch(() => '')
        console.error(`❌ task_start 请求失败: ${response.status}`, errorText)
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      },
      onmessage(event) {
        console.log('📨 收到原始消息:', event.data)
        if (event.data) {
          try {
            // 后端返回的是 JSON 格式: { "event": "...", "data": {...} }
            const parsedData = JSON.parse(event.data)
            console.log('📦 解析后的数据:', parsedData)

            // 处理不同类型的事件
            if (parsedData.event === 'session_started' && parsedData.data?.session_id) {
              const d = parsedData.data
              onSessionStarted?.({
                sessionId: d.session_id,
                title: d.title || '新对话',
                createTime: d.create_time,
              })
              return
            } else if (parsedData.event === 'session_title_chunk' && parsedData.data?.session_id) {
              const d = parsedData.data
              onSessionTitleChunk?.({
                sessionId: d.session_id,
                title: d.title
              })
              return
            } else if (parsedData.event === 'session_updated' && parsedData.data?.session_id) {
              const d = parsedData.data
              onSessionUpdated?.({
                sessionId: d.session_id,
                title: d.title
              })
              return
            } else if (parsedData.event === 'generate_tasks' && parsedData.data?.graph) {
              // 处理任务图数据
              console.log('📊 收到任务图数据:', parsedData.data.graph)
              onTaskGraph?.(parsedData.data.graph)
            } else if (parsedData.event === 'step_result' && parsedData.data?.title && parsedData.data?.message) {
              // 处理步骤执行结果
              console.log('✅ 收到步骤结果:', parsedData.data)
              onStepResult?.({ title: parsedData.data.title, message: parsedData.data.message })
            } else if (parsedData.event === 'task_result' && parsedData.data?.message) {
              // 处理任务最终结果（流式）
              console.log('📄 收到任务结果数据块:', parsedData.data.message)
              onTaskResult?.(parsedData.data.message)
            } else if (parsedData.event === 'evaluating_result') {
              // 处理评判阶段开始
              console.log('🔍 收到评判开始事件')
              onEvaluating?.()
            } else if (parsedData.data?.chunk) {
              // 处理文本块数据
              const chunk = parsedData.data.chunk
              console.log('📝 提取的 chunk:', chunk)
              onMessage(chunk)
            } else {
              // 其他类型的数据，直接传递
              onMessage(parsedData)
            }
          } catch (error) {
            console.error('❌ JSON 解析失败:', error, '原始数据:', event.data)
            // 如果解析失败，尝试直接使用原始数据
            onMessage(event.data)
          }
        }
      },
      onerror(err) {
        console.error('Stream 错误:', err)
        onError?.(err)
        ctrl.abort()
      },
      onclose() {
        console.log('Stream 关闭')
        onClose?.()
      }
    })
  } catch (error) {
    console.error('fetchEventSource 异常:', error)
    if (error.name !== 'AbortError') {
      onError?.(error)
    }
  }
  return ctrl
}
