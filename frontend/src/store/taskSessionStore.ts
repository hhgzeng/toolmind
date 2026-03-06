/**
 * 全局任务会话状态管理
 * 保存运行中会话的完整状态，使切换会话时不丢失 SSE 连接和运行状态。
 */
import { reactive } from 'vue'

interface GraphNode {
  start: string
  end: string
}

interface NodeStatus {
  status: 'pending' | 'executing' | 'completed'
  message?: string
}

export interface TaskSessionState {
  // 核心数据
  taskGraph: GraphNode[]
  nodeStatusMap: Map<string, NodeStatus>
  taskResultContent: string
  resultBuffer: string
  userQuery: string

  // 实时模式下的多轮结果分页（自我反馈未通过时产生多轮）
  liveResultPages: string[]
  liveResultPageIndex: number
  liveLatestContent: string

  // UI 状态
  showGraph: boolean
  showTaskResult: boolean
  isTaskRunning: boolean
  isTaskFinished: boolean
  isReceivingResult: boolean
  isJudging: boolean
  isJudgeSuccess: boolean
  isDraining: boolean

  // SSE 控制
  abortController: AbortController | null

  // 回调代理：SSE 事件通过这些函数写入数据，
  // 当组件活跃时指向 ref，切走后指向 store 缓存
  callbacks: {
    onMessage: (data: any) => void
    onTaskGraph: (graph: any) => void
    onStepResult: (stepData: { title: string; message: string }) => void
    onTaskResult: (message: string) => void
    onEvaluating: () => void
    onError: (error: any) => void
    onClose: () => void
    onSessionStarted: (session: { sessionId: string; title: string; createTime?: string; agent?: string }) => void
    onSessionTitleChunk: (session: { sessionId: string; title: string }) => void
    onSessionUpdated: (session: { sessionId: string; title: string }) => void
  } | null
}

function createEmptyState(): TaskSessionState {
  return {
    taskGraph: [],
    nodeStatusMap: new Map(),
    taskResultContent: '',
    resultBuffer: '',
    userQuery: '',
    liveResultPages: [],
    liveResultPageIndex: 0,
    liveLatestContent: '',
    showGraph: false,
    showTaskResult: false,
    isTaskRunning: false,
    isTaskFinished: false,
    isReceivingResult: false,
    isJudging: false,
    isJudgeSuccess: false,
    isDraining: false,
    abortController: null,
    callbacks: null,
  }
}

// 全局 store：按 sessionId 保存运行中会话的状态
const sessions = reactive<Map<string, TaskSessionState>>(new Map())

export const taskSessionStore = {
  /** 判断某会话是否在后台运行 */
  hasRunningSession(sessionId: string): boolean {
    const s = sessions.get(sessionId)
    return !!s && s.isTaskRunning
  },

  /** 判断某会话是否有保存的状态（运行中或已完成但尚未被组件消费） */
  hasSession(sessionId: string): boolean {
    return sessions.has(sessionId)
  },

  /** 获取某会话的保存状态 */
  getSession(sessionId: string): TaskSessionState | undefined {
    return sessions.get(sessionId)
  },

  /** 保存会话状态到 store */
  saveSession(sessionId: string, state: TaskSessionState): void {
    sessions.set(sessionId, state)
  },

  /** 删除会话状态 */
  removeSession(sessionId: string): void {
    sessions.delete(sessionId)
  },

  /** 获取或创建会话状态 */
  getOrCreate(sessionId: string): TaskSessionState {
    if (!sessions.has(sessionId)) {
      sessions.set(sessionId, createEmptyState())
    }
    return sessions.get(sessionId)!
  },

  /** 获取所有运行中的 sessionId 列表 */
  getRunningSessionIds(): string[] {
    const ids: string[] = []
    sessions.forEach((state, id) => {
      if (state.isTaskRunning) ids.push(id)
    })
    return ids
  },
}

export default taskSessionStore
