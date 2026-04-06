<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import {
  startAgentTaskAPI
} from '../../api/agent'
import { deleteSessionAPI, getSessionInfoAPI } from '../../api/sessions'

const route = useRoute()
const router = useRouter()

interface GraphNode {
  start: string
  end: string
}

interface NodeStatus {
  status: 'pending' | 'executing' | 'completed'
  message?: string
}

interface HistoryContext {
  query: string
  task_graph?: GraphNode[]
  // 每个子任务的详细执行结果（由后端持久化在 workspace_session.contexts.task 中）
  task?: {
    title: string
    result?: string
  }[]
  answer: string
}

// 状态管理
const taskGraph = ref<GraphNode[]>([])
const showGraph = ref(false)
const nodeStatusMap = ref<Map<string, NodeStatus>>(new Map())
const selectedNode = ref<string | null>(null)
const showNodeDetail = ref(false)
const taskResultContent = ref('')
const showTaskResult = ref(false)
const resultContainer = ref<HTMLElement>()
const currentContextIndex = ref(0)
// 实时模式下的多轮结果分页（自我反馈未通过时会产生多轮）
const liveResultPages = ref<string[]>([])
const liveResultPageIndex = ref(0)
// 最新一轮的实时生成内容（drain 始终写入此变量，避免与历史页浏览冲突）
const liveLatestContent = ref('')
// 标记当前是否处于任务执行阶段，用于推导“执行中”子任务
const isTaskRunning = ref(false)
// 标记任务流程是否已结束（用于判断何时进入“评判计算期”）
const isTaskFinished = ref(false)
// 加载状态，用于历史会话切换时防止闪烁
const isLoading = ref(false)

// 用于保存当前任务的 AbortController，便于中止任务
const currentTaskAbortController = ref<AbortController | null>(null)

// 退出确认弹窗状态
const showExitConfirm = ref(false)
let exitConfirmPromiseResolve: ((value: boolean) => void) | null = null

const promptExitConfirm = async (): Promise<boolean> => {
  showExitConfirm.value = true
  return new Promise<boolean>((resolve) => {
    exitConfirmPromiseResolve = resolve
  })
}

const onConfirmExit = () => {
  showExitConfirm.value = false
  if (exitConfirmPromiseResolve) exitConfirmPromiseResolve(true)
}

const onCancelExit = () => {
  showExitConfirm.value = false
  if (exitConfirmPromiseResolve) exitConfirmPromiseResolve(false)
}

// 基于任务图推导严格串行的 To-dos 列表（用户问题 -> step_1 -> step_2 -> ...）
const todos = computed(() => {
  const graph = taskGraph.value
  if (!graph.length) return []

  const nextMap = new Map<string, string>()
  const allStarts = new Set<string>()
  const allEnds = new Set<string>()

  graph.forEach((item) => {
    nextMap.set(item.start, item.end)
    allStarts.add(item.start)
    allEnds.add(item.end)
  })

  // 优先从“用户问题”开始；如果不存在，则从任意没有入边的起点开始
  let current = '用户问题'
  if (!nextMap.has(current)) {
    const candidates = Array.from(allStarts).filter((s) => !allEnds.has(s))
    if (candidates.length > 0) {
      current = candidates[0]
    }
  }

  const ordered: string[] = []
  const visited = new Set<string>()
  while (nextMap.has(current)) {
    const next = nextMap.get(current)!
    if (visited.has(next)) break
    visited.add(next)
    ordered.push(next)
    current = next
  }

  return ordered
})

// 历史运行轮次信息
const totalContexts = computed(() => historyContexts.value.length)
const currentRunLabel = computed(() => {
  // 实时模式下的多轮分页
  if (!isHistoryMode.value && liveResultPages.value.length > 0) {
    const total = liveResultPages.value.length + 1 // 已归档页 + 当前正在生成的页
    return `${liveResultPageIndex.value + 1} / ${total}`
  }
  // 历史模式
  if (!totalContexts.value) return ''
  return `${currentContextIndex.value + 1} / ${totalContexts.value}`
})

// 是否显示分页控件
const showPagination = computed(() => {
  return (isHistoryMode.value && totalContexts.value > 1) ||
    (!isHistoryMode.value && liveResultPages.value.length > 0)
})

/** 归档当前任务结果到 liveResultPages（自我反馈未通过重试时调用） */
const archiveCurrentResult = () => {
  // 将未排空的 buffer 和最新内容一并归入当前页面
  const fullContent = liveLatestContent.value + resultBuffer.value
  if (fullContent) {
    liveResultPages.value.push(fullContent)
  }
  // 清空当前结果状态，为新一轮结果做准备
  taskResultContent.value = ''
  resultBuffer.value = ''
  liveLatestContent.value = ''
  isReceivingResult.value = false
  isJudging.value = false
  isJudgeSuccess.value = false
  isTaskFinished.value = false
  isDraining.value = false
  showTaskResult.value = false
  if (drainTimer !== null) {
    window.clearInterval(drainTimer)
    drainTimer = null
  }
  // 将分页索引指向新页面（即最后一个 + 1 = 当前正在生成的页）
  liveResultPageIndex.value = liveResultPages.value.length
}

// 计算属性：分离 markdown 正文与自我反馈区块，独立呈现以自定义样式提取展示
const parsedTaskResult = computed(() => {
  let text = taskResultContent.value || '';
  const feedbacks: { title: string; isSuccess: boolean; content: string }[] = [];

  // 匹配后端的 blockquote 原始字符串 (✅ 或 ⚠️)
  const blockquoteRegex = /(?:\n\n|\n)*> \*\*(✅ 自我反馈通过|⚠️ 自我反馈未通过)\*\* \((匹配度:\s*\d+\/100)\)\n> \*\*理由\*\*: ([\s\S]*?)(?=\n> __|\n\n---|\n*$)(?:\n> __.*)?(?:\n\n---)?/g;
  text = text.replace(blockquoteRegex, (match, status, score, reasonText) => {
    feedbacks.push({
      title: `${status} (${score})`,
      isSuccess: status.includes('通过'),
      content: reasonText.replace(/^>\s?/gm, '').trim()
    });
    return '';
  });

  // 匹配 HTML details tag (处理前置历史任务数据兼容)
  const htmlRegex = /(?:\n\n|\n)*<details class="feedback-card (success|error)">\n<summary>(✅|⚠️) <strong>(自我反馈通过|自我反馈未通过)<\/strong> \((匹配度:\s*\d+\/100)\)<\/summary>\n\n\*\*理由\*\*: ([\s\S]*?)(?:\n\n\*系统.*)?\n\n<\/details>(?:\n\n)?/g;
  text = text.replace(htmlRegex, (match, type, icon, statusText, score, reasonText) => {
    feedbacks.push({
      title: `${icon} ${statusText} (${score})`,
      isSuccess: type === 'success',
      content: reasonText.trim()
    });
    return '';
  });

  text = text.replace(/(?:\n\n---|\n)+$/, '');

  return { text, feedbacks };
});

// 结果接收控制（任务流程结束后才开始）
const isReceivingResult = ref(false)
// 评判阶段：主结果输出完毕后的“计算期”（直到评判结果开始输出）
const isJudging = ref(false)
const isJudgeSuccess = ref(false)
const resultBuffer = ref('')
const isDraining = ref(false)
let drainTimer: number | null = null
const drainChunkSize = 120  // 增大块大小减少渲染频率
const drainIntervalMs = 80  // 降低刷新频率，减少抖动
let scrollPending = false

// “评判中”动画：仅在实时新任务（非历史）且处于评判计算期时展示
const showJudgingAnimation = computed(() => {
  return !isHistoryMode.value && isJudging.value
})

const exitJudging = () => {
  if (isJudging.value && !isJudgeSuccess.value) {
    if (parsedTaskResult.value.feedbacks.length > 0) {
      isJudgeSuccess.value = true
      setTimeout(() => {
        isJudging.value = false
        isJudgeSuccess.value = false
      }, 1500)
    } else {
      isJudging.value = false
    }
  }
}

// 一旦反馈卡片解析出来，说明评判结果开始输出/已输出，结束评判动效
watch(
  () => parsedTaskResult.value.feedbacks.length,
  (len) => {
    if (len > 0) exitJudging()
  }
)

// 当前这次 Agent 任务对应的工作区会话 ID（由后端在任务启动时创建）
const currentSessionId = ref<string | null>(null)

// 启动结果接收并流式回放缓冲
const startReceivingResults = () => {
  console.log('🚀 [startReceivingResults] 被调用')
  console.log('  - isReceivingResult:', isReceivingResult.value)
  console.log('  - showTaskResult:', showTaskResult.value)
  console.log('  - resultBuffer 长度:', resultBuffer.value.length)
  console.log('  - resultBuffer 前100字符:', resultBuffer.value.substring(0, 100))

  if (isReceivingResult.value) {
    console.log('⚠️ [startReceivingResults] 已在接收中，跳过')
    return
  }
  isReceivingResult.value = true
  if (!showTaskResult.value) {
    showTaskResult.value = true
  }
  console.log('✅ [startReceivingResults] 状态已更新，准备启动排空')
  // 启动排空
  startDrain()
}

const startDrain = () => {
  console.log('🔄 [startDrain] 被调用')
  console.log('  - isDraining:', isDraining.value)
  console.log('  - drainTimer:', drainTimer)
  console.log('  - resultBuffer 长度:', resultBuffer.value.length)

  if (isDraining.value) {
    console.log('⚠️ [startDrain] 已在排空中，跳过')
    return
  }
  isDraining.value = true
  if (drainTimer !== null) {
    window.clearInterval(drainTimer)
    drainTimer = null
  }

  console.log('✅ [startDrain] 开始设置定时器，间隔:', drainIntervalMs, 'ms，块大小:', drainChunkSize)
  const tick = () => {
    if (!resultBuffer.value.length) {
      // 缓冲已空，结束接收
      console.log('⏹️ [tick] 缓冲已空，结束接收')
      if (drainTimer !== null) {
        window.clearInterval(drainTimer)
        drainTimer = null
      }
      isDraining.value = false
      isReceivingResult.value = false
      return
    }
    const chunk = resultBuffer.value.slice(0, drainChunkSize)
    resultBuffer.value = resultBuffer.value.slice(drainChunkSize)
    // 始终写入 liveLatestContent（保留最新一轮的完整内容）
    liveLatestContent.value += chunk
    // 仅在用户正在查看最新页时，同步到 taskResultContent 以驱动视图
    if (liveResultPageIndex.value === liveResultPages.value.length) {
      taskResultContent.value += chunk
    }
    console.log('📤 [tick] 输出块:', chunk.length, '字符，剩余缓冲:', resultBuffer.value.length, '，当前总内容:', liveLatestContent.value.length)
    scrollResultToBottom()
  }
  drainTimer = window.setInterval(tick, drainIntervalMs)
  console.log('✅ [startDrain] 定时器已启动，ID:', drainTimer)
}

// 历史记录相关
const isHistoryMode = ref(false)
const isHistorySwitching = ref(false)
const historyContexts = ref<HistoryContext[]>([])

// 用户问题
const userQuery = ref('')

// 保存任务参数
const taskParams = ref({
  query: '',
  plugins: [] as string[]
})



// 获取当前选中节点的详情
const selectedNodeDetail = computed(() => {
  if (!selectedNode.value) return null
  const status = nodeStatusMap.value.get(selectedNode.value)
  return {
    title: selectedNode.value,
    status: status?.status || 'pending',
    message: status?.message || '该节点尚未执行'
  }
})

// 当前“执行中”的任务节点：在任务运行时，第一个尚未完成的子任务
const executingNodeTitle = computed(() => {
  if (!isTaskRunning.value) return null
  for (const title of todos.value) {
    const status = nodeStatusMap.value.get(title)?.status || 'pending'
    if (status !== 'completed') {
      return title
    }
  }
  return null
})

// 根据节点状态和当前执行节点，返回 To-do 列表中每条任务的样式 class
const getTodoStatusClass = (title: string) => {
  const baseStatus = nodeStatusMap.value.get(title)?.status || 'pending'
  if (isTaskRunning.value && baseStatus !== 'completed' && executingNodeTitle.value === title) {
    return 'executing'
  }
  return baseStatus
}

// 初始化
onMounted(async () => {
  console.log('=== taskGraphPage onMounted ===')
  console.log('路由参数:', route.query)

  const sessionId = (route.params.session_id || route.query.session_id) as string

  if (sessionId) {
    // 正常历史会话模式：加载后端数据
    console.log('历史会话模式，session_id:', sessionId)
    isLoading.value = true
    isHistoryMode.value = true
    await loadSessionInfo(sessionId)
    isLoading.value = false
  } else {
    // 新任务模式：直接开始执行任务
    console.log('新任务模式')

    // 保存参数
    const queryStr = route.query.query as string || ''
    const toolsStr = route.query.tools as string
    const parsedTools = toolsStr ? JSON.parse(toolsStr) : []

    taskParams.value.query = queryStr
    taskParams.value.plugins = parsedTools

    // 保存用户问题用于显示
    userQuery.value = queryStr

    console.log('✅ 用户问题:', queryStr)
    console.log('✅ 选中工具:', parsedTools)

    // 清理 URL 参数（保留功能，隐藏参数）
    router.replace({ path: '/sessions' })

    // 直接开始执行任务（AI 自行分解）
    if (queryStr) {
      console.log('🚀 开始自动执行任务...')
      startTask()
    } else {
      console.warn('⚠️ 缺少用户问题，无法执行任务')
    }
  }

  console.log('=== taskGraphPage onMounted 结束 ===')
})

const resetPageState = () => {
  taskGraph.value = []
  nodeStatusMap.value.clear()
  taskResultContent.value = ''
  resultBuffer.value = ''
  showGraph.value = false
  showTaskResult.value = false
  selectedNode.value = null
  showNodeDetail.value = false
  isReceivingResult.value = false
  isJudging.value = false
  isJudgeSuccess.value = false
  isTaskFinished.value = false
  isDraining.value = false
  userQuery.value = ''
  isHistorySwitching.value = false
  liveResultPages.value = []
  liveResultPageIndex.value = 0
  liveLatestContent.value = ''
  if (drainTimer !== null) {
    window.clearInterval(drainTimer)
    drainTimer = null
  }
  isTaskRunning.value = false
}

watch(
  () => route.params.session_id || route.query.session_id,
  async (newSessionId, oldSessionId) => {
    if (newSessionId === oldSessionId) return
    // 如果是当前运行中的任务首次获得 session_id（URL 更新），不要重置
    if (isTaskRunning.value && newSessionId === currentSessionId.value) return
    console.log('🔄 会话切换:', oldSessionId, '->', newSessionId)

    // ---- 离开旧会话 ----
    const leavingSessionId = currentSessionId.value || (oldSessionId as string)
    if (leavingSessionId && isTaskRunning.value) {
      if (drainTimer !== null) {
        window.clearInterval(drainTimer)
        drainTimer = null
      }
    }

    // ---- 进入新会话 ----
    if (newSessionId) {
      const sid = newSessionId as string
      resetPageState()
      isLoading.value = true
      isHistoryMode.value = true
      await loadSessionInfo(sid)
      isLoading.value = false
    } else {
      resetPageState()
      isHistoryMode.value = false
    }
  }
)

// 加载历史会话信息
const loadSessionInfo = async (sessionId: string) => {
  try {
    isHistoryMode.value = true
    const response = await getSessionInfoAPI(sessionId)

    console.log('📦 会话信息响应:', response.data)

    if (response.data.status_code === 200) {
      const sessionData = response.data.data
      console.log('📦 会话数据:', sessionData)

      // 加载历史上下文
      if (sessionData.contexts && Array.isArray(sessionData.contexts) && sessionData.contexts.length > 0) {
        historyContexts.value = sessionData.contexts
        currentContextIndex.value = 0
        console.log('📦 contexts 数组:', historyContexts.value)
        applyContextByIndex(currentContextIndex.value)
      } else {
        // contexts 为空：会话可能仍在运行（刷新页面后 SSE 断开），显示等待状态
        console.warn('⚠️ contexts 为空，显示等待状态')
        userQuery.value = sessionData.title || ''
        isHistoryMode.value = false
      }
    } else {
      ElMessage.error('获取会话信息失败')
    }
  } catch (error) {
    console.error('❌ 加载会话信息出错:', error)
    ElMessage.error('加载会话信息出错')
  }
}

// 按索引应用某一轮上下文，刷新任务流程与任务结果
const applyContextByIndex = (index: number) => {
  if (index < 0 || index >= historyContexts.value.length) {
    console.warn('⚠️ applyContextByIndex 索引越界:', index)
    return
  }

  const context = historyContexts.value[index]
  console.log('📦 应用 context 索引:', index, '内容:', context)

  // 加载用户问题
  if (context.query) {
    userQuery.value = context.query
    console.log('✅ 用户问题已加载:', userQuery.value)
  }

  // 重建任务图与节点状态
  taskGraph.value = []
  nodeStatusMap.value.clear()

  if (context.task_graph && Array.isArray(context.task_graph) && context.task_graph.length > 0) {
    console.log('✅ 任务图数据 (task_graph):', JSON.stringify(context.task_graph, null, 2))

    taskGraph.value = context.task_graph
    const nodeSet = new Set<string>()
    context.task_graph.forEach((edge: GraphNode) => {
      nodeSet.add(edge.start)
      nodeSet.add(edge.end)
    })

    console.log('✅ 提取的节点集合:', Array.from(nodeSet))

    // 如果有持久化的 task 详情，则优先使用其中的结果作为节点详情；
    // 否则回退为“已执行完成”的通用提示。
    const stepDetailMap = new Map<string, string>()
    if (context.task && Array.isArray(context.task)) {
      context.task.forEach((step) => {
        if (step && step.title) {
          stepDetailMap.set(step.title, step.result || '已执行完成')
        }
      })
    }

    nodeSet.forEach((nodeId: string) => {
      const message = stepDetailMap.get(nodeId) || '已执行完成'
      updateNodeStatus(nodeId, 'completed', message)
    })

    showGraph.value = true
  } else {
    console.warn('⚠️ 未找到 task_graph 字段或为空数组')
    showGraph.value = false
  }

  // 切换结果内容
  taskResultContent.value = context.answer || ''
  resultBuffer.value = ''
  isReceivingResult.value = false
  isJudging.value = false
  isJudgeSuccess.value = false
  isTaskFinished.value = true
  isDraining.value = false
  if (drainTimer !== null) {
    window.clearInterval(drainTimer)
    drainTimer = null
  }
  showTaskResult.value = !!context.answer
  console.log('✅ 执行结果已加载，长度:', taskResultContent.value.length)
}

// 历史运行结果切换
const switchToPrevRun = () => {
  if (!isHistoryMode.value && liveResultPages.value.length > 0) {
    // 实时模式下切换分页
    if (liveResultPageIndex.value <= 0) return
    liveResultPageIndex.value -= 1
    taskResultContent.value = liveResultPages.value[liveResultPageIndex.value]
    return
  }
  if (currentContextIndex.value <= 0) return

  isHistorySwitching.value = true
  taskResultContent.value = ''

  setTimeout(() => {
    currentContextIndex.value -= 1
    applyContextByIndex(currentContextIndex.value)
    setTimeout(() => { isHistorySwitching.value = false }, 300)
  }, 50)
}

const switchToNextRun = () => {
  if (!isHistoryMode.value && liveResultPages.value.length > 0) {
    // 实时模式下切换分页
    const maxIndex = liveResultPages.value.length
    if (liveResultPageIndex.value >= maxIndex) return
    liveResultPageIndex.value += 1
    if (liveResultPageIndex.value < liveResultPages.value.length) {
      // 查看已归档的历史页
      taskResultContent.value = liveResultPages.value[liveResultPageIndex.value]
    } else {
      // 回到当前正在生成的最新页，从 liveLatestContent 恢复内容
      taskResultContent.value = liveLatestContent.value
    }
    return
  }
  if (currentContextIndex.value >= historyContexts.value.length - 1) return

  isHistorySwitching.value = true
  taskResultContent.value = ''

  setTimeout(() => {
    currentContextIndex.value += 1
    applyContextByIndex(currentContextIndex.value)
    setTimeout(() => { isHistorySwitching.value = false }, 300)
  }, 50)
}

// 更新节点状态
const updateNodeStatus = (title: string, status: 'pending' | 'executing' | 'completed', message?: string) => {
  nodeStatusMap.value.set(title, { status, message })
}

// 处理节点点击
const handleNodeClick = (nodeId: string) => {
  selectedNode.value = nodeId
  const nodeStatus = nodeStatusMap.value.get(nodeId)

  if (nodeStatus && nodeStatus.status === 'completed' && nodeStatus.message) {
    showNodeDetail.value = true
  } else if (nodeStatus && nodeStatus.status === 'executing') {
    ElMessage.info('该节点正在执行中...')
  } else {
    ElMessage.info('该节点尚未执行')
  }
}

// 关闭节点详情弹窗
const closeNodeDetail = () => {
  showNodeDetail.value = false
  selectedNode.value = null
}

const handleBeforeUnload = (e: BeforeUnloadEvent) => {
  if (isTaskRunning.value) {
    e.preventDefault()
    e.returnValue = ''
  }
}

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  if (drainTimer !== null) {
    window.clearInterval(drainTimer)
    drainTimer = null
  }
})

const abortCurrentTask = async () => {
  if (currentTaskAbortController.value) {
    currentTaskAbortController.value.abort()
    currentTaskAbortController.value = null
  }
  if (currentSessionId.value) {
    try {
      await deleteSessionAPI(currentSessionId.value)
      // 如果侧边栏有监听删除事件可以自动刷新，或者通过重新加载实现
      window.dispatchEvent(
        new CustomEvent('session:session-deleted', {
          detail: { sessionId: currentSessionId.value }
        })
      )
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }
  isTaskRunning.value = false
}

onBeforeRouteLeave(async (to, from, next) => {
  if (isTaskRunning.value) {
    const isConfirmed = await promptExitConfirm()
    if (isConfirmed) {
      await abortCurrentTask()
      next()
    } else {
      next(false)
    }
  } else {
    next()
  }
})

onBeforeRouteUpdate(async (to, from, next) => {
  // 仅当我们确实离开当前运行中的会话时才弹窗，如果是首次新建任务并赋予URL，不应弹窗拦截
  const toSessionId = to.params.session_id || ''
  const fromSessionId = from.params.session_id || ''
  const currentId = currentSessionId.value || ''

  if (isTaskRunning.value && toSessionId !== fromSessionId && toSessionId !== currentId) {
    const isConfirmed = await promptExitConfirm()
    if (isConfirmed) {
      await abortCurrentTask()
      next()
    } else {
      next(false)
    }
  } else {
    next()
  }
})

// 滚动结果区域到底部（优化：使用 requestAnimationFrame 防抖）
const scrollResultToBottom = () => {
  if (scrollPending) return
  scrollPending = true
  requestAnimationFrame(() => {
    if (resultContainer.value) {
      resultContainer.value.scrollTop = resultContainer.value.scrollHeight
    }
    scrollPending = false
  })
}

// 开始执行任务
const startTask = async () => {
  console.log('开始执行任务')

  taskGraph.value = []
  nodeStatusMap.value.clear()
  taskResultContent.value = ''
  resultBuffer.value = ''
  liveLatestContent.value = ''
  liveResultPages.value = []
  liveResultPageIndex.value = 0
  showTaskResult.value = false
  isReceivingResult.value = false
  isJudging.value = false
  isJudgeSuccess.value = false
  isTaskFinished.value = false
  showGraph.value = false
  isTaskRunning.value = true
  currentTaskAbortController.value = null
  // 清理可能遗留的回放定时器
  if (drainTimer !== null) {
    window.clearInterval(drainTimer)
    drainTimer = null
  }
  isDraining.value = false

  // 创建回调对象：SSE 事件通过这些函数写入数据
  const proxyCallbacks = {
    onMessage: (data: any) => {
      console.log('📨 接收到文本数据:', data)
      if (typeof data === 'string' && data) {
        exitJudging()
        resultBuffer.value += data
        if (isReceivingResult.value && !isDraining.value) {
          startDrain()
        }
      }
    },
    onTaskGraph: (graph: any) => {
      console.log('📊 接收到任务图数据:', graph)
      // 检测 retry：如果已有结果内容，说明是第二轮重跑，归档当前结果
      if (taskResultContent.value || resultBuffer.value) {
        archiveCurrentResult()
      }
      taskGraph.value = graph
      const nodeSet = new Set<string>()
      const endNodes = new Set<string>()
      graph.forEach((item: GraphNode) => {
        nodeSet.add(item.start)
        nodeSet.add(item.end)
        endNodes.add(item.end)
      })
      const startNodes = new Set<string>()
      nodeSet.forEach(node => {
        if (!endNodes.has(node)) startNodes.add(node)
      })
      nodeSet.forEach(node => {
        if (startNodes.has(node)) {
          updateNodeStatus(node, 'completed', '用户问题已提交')
        } else {
          updateNodeStatus(node, 'pending')
        }
      })
      showGraph.value = true
    },
    onStepResult: (stepData: { title: string; message: string }) => {
      console.log('✅ 收到步骤结果:', stepData)
      updateNodeStatus(stepData.title, 'completed', stepData.message)
    },
    onTaskResult: (messageChunk: string) => {
      if (typeof messageChunk === 'string') {
        console.log('📄 收到任务结果数据块:', messageChunk)
        exitJudging()
        resultBuffer.value += messageChunk
      }
      if (!isReceivingResult.value) {
        startReceivingResults()
        return
      }
      if (isReceivingResult.value && !isDraining.value) {
        startDrain()
      }
    },
    onEvaluating: () => {
      console.log('🔍 收到评判开始事件, isJudging变为true')
      isJudging.value = true
      if (!isReceivingResult.value && resultBuffer.value.length === 0) {
        isReceivingResult.value = true
      }
    },
    onError: (error: any) => {
      console.error('❌ 任务执行出错:', error)
      ElMessage.error('任务执行失败')
      isTaskRunning.value = false
      isTaskFinished.value = true
    },
    onClose: () => {
      console.log('✅ 任务执行完成')
      startReceivingResults()
      isTaskRunning.value = false
      isTaskFinished.value = true
    },
    onSessionStarted: (sessionInfo) => {
      currentSessionId.value = sessionInfo.sessionId
      // 将 session_id 更新到 URL
      router.replace({
        name: 'Sessions',
        params: { session_id: sessionInfo.sessionId }
      })
      window.dispatchEvent(
        new CustomEvent('session:new-session', {
          detail: {
            sessionId: sessionInfo.sessionId,
            title: sessionInfo.title,
            createTime: sessionInfo.createTime,
          }
        })
      )
      isTaskRunning.value = true
      userQuery.value = userQuery.value
    },
    onSessionTitleChunk: (sessionInfo) => {
      window.dispatchEvent(
        new CustomEvent('session:session-updated', {
          detail: {
            sessionId: sessionInfo.sessionId,
            title: sessionInfo.title
          }
        })
      )
    },
    onSessionUpdated: (sessionInfo) => {
      window.dispatchEvent(
        new CustomEvent('session:session-updated', {
          detail: {
            sessionId: sessionInfo.sessionId,
            title: sessionInfo.title
          }
        })
      )
    },
  }

  try {
    // SSE 回调全部通过 proxy 间接调用，支持后台状态切换
    const ctrl = await startAgentTaskAPI(
      taskParams.value,
      (data) => proxyCallbacks.onMessage(data),
      (graph) => proxyCallbacks.onTaskGraph(graph),
      (stepData) => proxyCallbacks.onStepResult(stepData),
      (messageChunk) => proxyCallbacks.onTaskResult(messageChunk),
      () => proxyCallbacks.onEvaluating(),
      (error) => proxyCallbacks.onError(error),
      () => proxyCallbacks.onClose(),
      (sessionInfo) => proxyCallbacks.onSessionStarted(sessionInfo),
      (sessionInfo) => proxyCallbacks.onSessionUpdated(sessionInfo),
      (sessionInfo) => proxyCallbacks.onSessionTitleChunk(sessionInfo),
    )
    currentTaskAbortController.value = ctrl
  } catch (error) {
    console.error('任务执行异常:', error)
    ElMessage.error('请求失败，请检查网络连接')
  }
}

</script>

<template>
  <div class="task-graph-page">
    <!-- 两列布局容器 -->
    <div class="two-column-layout">
      <!-- 左侧容器 -->
      <div class="left-wrapper">
        <!-- 用户问题卡片独立出来 -->
        <div v-show="userQuery || isLoading" class="user-query-card column">
          <div class="column-header">
            <span class="header-icon">
              <!-- 统一的聊天图标 -->
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"
                style="width: 20px; height: 20px; color: white;">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </span>
            <h2 class="header-title">用户问题</h2>
          </div>
          <div class="column-content query-card-body">
            <p v-if="userQuery" class="query-text">{{ userQuery }}</p>
            <p v-else-if="isLoading" class="query-text" style="color: transparent; user-select: none;">加载中...</p>
          </div>
        </div>

        <!-- 第一列：任务流程（To-dos + 简化流程图） -->
        <div class="column column-graph">
          <div class="column-header">
            <span class="header-icon">
              <!-- 系统内置流程图标 -->
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"
                style="width: 20px; height: 20px; color: white;">
                <rect x="3" y="3" width="7" height="7" rx="2" />
                <rect x="14" y="3" width="7" height="7" rx="2" />
                <rect x="14" y="14" width="7" height="7" rx="2" />
                <rect x="3" y="14" width="7" height="7" rx="2" />
                <path d="M9 17.5h5" />
                <path d="M9 6.5h5" />
                <path d="M6.5 9v5" />
                <path d="M17.5 9v5" />
              </svg>
            </span>
            <h2 class="header-title">任务流程</h2>

          </div>

          <div class="column-content">
            <!-- To-dos 列表：按串行步骤顺序展示每个子任务 -->
            <div v-if="showGraph && todos.length" class="todos-list">
              <div v-for="(title, index) in todos" :key="title + index" class="todo-item"
                :class="getTodoStatusClass(title)" @click="handleNodeClick(title)">
                <div class="todo-status-dot" />
                <div class="todo-main">
                  <div class="todo-title-row">
                    <span class="todo-index">Step {{ index + 1 }}</span>
                    <span class="todo-title">{{ title }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="!isLoading" class="empty-placeholder">
              <span class="empty-icon">🔄</span>
              <p>等待任务流程生成...</p>
            </div>
            <div v-else class="empty-placeholder"></div>
          </div>
        </div>
        <!-- 结束左侧容器 -->
      </div>

      <!-- 第二列：任务执行结果 -->
      <div class="column column-result">
        <div class="column-header">
          <span class="header-icon">
            <!-- 系统内置文档图标 -->
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"
              style="width: 20px; height: 20px; color: white;">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          </span>
          <h2 class="header-title">任务结果</h2>
          <div v-if="showPagination" class="run-toggle">
            <button class="run-arrow" :disabled="isHistoryMode ? currentContextIndex === 0 : liveResultPageIndex === 0"
              @click.stop="switchToPrevRun">
              ‹
            </button>
            <span class="run-label">{{ currentRunLabel }}</span>
            <button class="run-arrow"
              :disabled="isHistoryMode ? currentContextIndex === totalContexts - 1 : liveResultPageIndex >= liveResultPages.length"
              @click.stop="switchToNextRun">
              ›
            </button>
          </div>
        </div>
        <div class="column-content">
          <div v-if="showTaskResult" class="result-wrapper" ref="resultContainer">
            <MdPreview editorId="task-result-preview" :modelValue="parsedTaskResult.text" :showCodeRowNumber="true" />

            <!-- 独立呈现的反馈卡片(从Markdown中抽离的iOS 26圆角风格卡片) -->
            <Transition :name="isHistorySwitching ? '' : 'feedback-container'">
              <div v-if="parsedTaskResult.feedbacks.length > 0" class="feedback-cards-container">
                <!-- 动态绑定 name，如果是历史上下轮次切换则取消入场动画避免闪烁 -->
                <TransitionGroup :name="isHistorySwitching ? '' : 'feedback-reveal'" tag="div"
                  class="feedback-cards-list">
                  <details v-for="(fb, i) in parsedTaskResult.feedbacks" :key="fb.title + i"
                    class="feedback-card-native" :class="fb.isSuccess ? 'success' : 'error'">
                    <summary>
                      <span class="summary-title">{{ fb.title }}</span>
                    </summary>
                    <div class="feedback-content-native">
                      <MdPreview :editorId="'fb-preview-' + i" :modelValue="fb.content" />
                    </div>
                  </details>
                </TransitionGroup>
              </div>
            </Transition>

            <!-- 任务结果评判动效（底部悬浮，不干扰阅读与滚动） -->
            <Transition name="judge-fade">
              <div v-if="showJudgingAnimation" class="judge-overlay" aria-live="polite">
                <div class="judge-surface" :class="{ 'is-success': isJudgeSuccess }">
                  <div class="judge-icon-wrapper" v-if="isJudgeSuccess">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                      stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="success-icon">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                  </div>
                  <div class="judge-text">
                    <div class="judge-title" :class="{ 'success-text': isJudgeSuccess }">{{ isJudgeSuccess ? '评判完成' :
                      '正在评判任务结果' }}</div>
                    <div class="judge-subtitle" :class="{ 'success-text': isJudgeSuccess }">{{ isJudgeSuccess ?
                      '已生成评估与反馈' : '匹配度分析与理由生成中…' }}</div>
                  </div>
                  <div v-if="!isJudgeSuccess" class="judge-meter" aria-hidden="true">
                    <div class="judge-meter-track">
                      <div class="judge-meter-bar" />
                    </div>
                  </div>
                </div>
              </div>
            </Transition>
          </div>
          <div v-else-if="!isLoading" class="empty-placeholder">
            <span class="empty-icon">📝</span>
            <p>等待任务结果...</p>
          </div>
          <div v-else class="empty-placeholder"></div>
        </div>
      </div>
    </div>

    <!-- 节点详情弹窗 -->
    <div v-if="showNodeDetail" class="node-detail-modal" @click="closeNodeDetail">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">节点详情</h3>
          <button class="modal-close" @click="closeNodeDetail">✕</button>
        </div>
        <div class="modal-body">
          <div class="detail-item">
            <label class="detail-label">节点名称</label>
            <div class="detail-value">{{ selectedNodeDetail?.title }}</div>
          </div>
          <div class="detail-item">
            <label class="detail-label">执行结果</label>
            <div class="detail-value message-content">
              <MdPreview editorId="node-detail-preview" :modelValue="selectedNodeDetail?.message || '该节点尚未执行'" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 确认本页离开会话弹窗 -->
    <transition name="fade">
      <div v-if="showExitConfirm" class="confirm-dialog-overlay" @click="onCancelExit">
        <div class="confirm-dialog" @click.stop>
          <h3 class="dialog-title">终止当前会话</h3>
          <p class="dialog-message">当前会话正在运行中，离开页面将终止该会话。确认离开吗？</p>
          <div class="dialog-footer">
            <button class="dialog-btn cancel-btn" @click="onCancelExit">取消</button>
            <button class="dialog-btn delete-btn" @click="onConfirmExit">离开</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style lang="scss" scoped>
@use "sass:color";
// 全局颜色变量
$primary-start: #06b6d4;
$primary-end: #3b82f6;
$secondary-start: #8b5cf6;
$secondary-end: #ec4899;
$accent: #f59e0b;
$success: #10b981;
$warning: #f59e0b;
$error: #ef4444;

.task-graph-page {
  /* 主题变量（该页作用域内） */
  --bg: #ffffff;
  --panel: #ffffff;
  --border: #e5e7eb;
  --border-strong: #d1d5db;
  --text: #111827;
  --muted: #6b7280;
  --primary: #2563eb;
  --primary-600: #1d4ed8;
  --success: #16a34a;
  --warning: #d97706;
  --pending: #94a3b8;

  box-sizing: border-box;
  width: 100%;
  height: 100%;
  background-color: var(--bg);
  overflow: hidden;
  position: relative;
}

// 三列布局
.two-column-layout {
  box-sizing: border-box;
  display: flex;
  width: 100%;
  height: 100%;
  gap: 12px;
  padding: 12px;
  position: relative;
  z-index: 1;
}

.left-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.column {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  }

  .column-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 20px;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
    position: relative;
    overflow: hidden;

    .header-icon {
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      background: var(--primary);
      color: #fff;
      border-radius: 12px;
      flex-shrink: 0;
      position: relative;
      transition: all 0.3s ease;
    }

    .header-title {
      margin: 0;
      font-size: 19px;
      font-weight: 700;
      flex: 1;
      color: var(--text);
      letter-spacing: -0.5px;
    }
  }

  .column-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    overflow-x: hidden;
    background: var(--panel);

    // 添加内边距以便给内部卡片留出空间
    padding: 0 20px 20px;

    // 隐藏滚动条但保持滚动功能
    scrollbar-width: none; // Firefox
    -ms-overflow-style: none; // IE/Edge

    &::-webkit-scrollbar {
      display: none; // Chrome/Safari/Edge
    }
  }
}


// 用户问题卡片
.user-query-card {
  flex: 0 0 auto;

  .query-card-body {
    .query-text {
      margin: 12px 0;
      font-size: 15px;
      line-height: 1.8;
      color: #374151;
      word-break: break-word;
    }
  }
}

// To-dos 列表样式
.todos-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 14px 6px 14px;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: 24px;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
  min-height: 40px;

  &:hover {
    border-color: #d1d5db;
    background-color: #f9fafb;
    box-shadow: 0 4px 10px rgba(15, 23, 42, 0.06);
  }

  &.completed {
    border-color: #bbf7d0;
    background-color: #f0fdf4;
  }

  &.executing {
    border-color: #fed7aa;
    background-color: #fff7ed;
  }

  &.pending {
    border-color: #e5e7eb;
    background-color: #ffffff;
  }
}

.todo-status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background-color: #cbd5e1;
}

.todo-item.completed .todo-status-dot {
  background-color: #16a34a;
}

.todo-item.executing .todo-status-dot {
  background-color: #f59e0b;
}

.todo-item.pending .todo-status-dot {
  background-color: #9ca3af;
}

.todo-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.todo-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.todo-index {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  padding: 2px 6px;
  border-radius: 999px;
  background-color: #f3f4f6;
}

.todo-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.todo-status-text {
  font-size: 12px;
  color: #6b7280;
}

// 第三列：执行结果
.column-result {
  .column-content {
    padding: 0; // 移除外层 padding，以便滚动层贴近边缘
  }

  .column-header {
    display: flex;
    align-items: center;
  }

  .run-toggle {
    margin-left: auto;
    display: inline-flex;
    align-items: center;
    gap: 3px;
    padding: 0;
    background: transparent;
    border: none;
    border-radius: 0;
    font-size: 14px;
    color: var(--muted, #6b7280);
  }

  .run-arrow {
    border: none;
    background: transparent;
    padding: 0 2px;
    font-size: 18px;
    line-height: 1;
    color: var(--muted, #6b7280);
    cursor: pointer;
    border-radius: 8px;
    min-width: 18px;
  }

  .run-arrow:hover:not(:disabled) {
    background-color: rgba(148, 163, 184, 0.15);
  }

  .run-arrow:disabled {
    color: rgba(107, 114, 128, 0.35);
    cursor: default;
  }

  .run-label {
    min-width: 40px;
    text-align: center;
    font-variant-numeric: tabular-nums;
    color: var(--text, #111827);
  }

  .result-wrapper {
    flex: 1;
    height: 100%;
    padding: 0 20px 20px; // 内边距转移到这里，调整上下左右边距与用户问题一致
    margin-top: 0; // 移除上方负边距，让文本距离顶部有适呼吸空间
    overflow-y: auto;
    overflow-x: hidden; // 防止水平滚动条由于代码块溢出导致整个卡片可滚动
    position: relative;
    will-change: scroll-position; // 提示浏览器优化滚动性能
    contain: layout style paint; // 隔离渲染层，减少重排

    // 移除滚动条显示
    scrollbar-width: none;
    -ms-overflow-style: none;

    &::-webkit-scrollbar {
      display: none;
    }

    :deep(.md-editor-preview) {
      background: transparent;
      padding: 0;
      border-radius: 0;
      margin-top: 0;
      box-shadow: none;
      border: none;
      position: relative;
      will-change: contents; // 提示浏览器内容会频繁变化

      &::before {
        display: none !important;
      }

      p {
        margin: 12px 0;
        line-height: 1.8;
        color: var(--text);
      }

      h1,
      h2,
      h3,
      h4,
      h5,
      h6 {
        margin: 20px 0 12px 0;
        font-weight: 600;
        color: #1f2937;
      }

      code {
        background: #f3f4f6;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.9em;
        color: #e11d48;
      }

      pre {
        background: #1f2937;
        color: #f9fafb;
        padding: 16px;
        border-radius: 8px;
        overflow-x: auto;
        margin: 16px 0;

        code {
          background: none;
          color: inherit;
          padding: 0;
        }
      }
    }


  }
}

/* 评判动效：随文档流展示在文本底部 */
.judge-overlay {
  margin: 16px 0 24px 0;
  display: flex;
  justify-content: center;
  pointer-events: none;
  /* 不阻挡滚动、选择文本 */
  z-index: 3;
}

.judge-surface {
  width: min(560px, 100%);
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  border-radius: 24px;
  background: var(--panel, #ffffff);
  border: 1px solid var(--border, #e5e7eb);
  transition: all 0.3s ease;
}

.judge-surface.is-success {
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.judge-icon-wrapper {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--border, #e5e7eb);
  border-top-color: var(--primary, #2563eb);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.success-icon {
  width: 22px;
  height: 22px;
  color: var(--success, #16a34a);
  animation: successPop 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) both;
}

@keyframes successPop {
  0% {
    transform: scale(0.5);
    opacity: 0;
  }

  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.judge-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.judge-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text, #111827);
  line-height: 1.2;
  transition: color 0.3s ease;
}

.judge-title.success-text {
  color: var(--success, #16a34a);
}

.judge-subtitle {
  font-size: 12px;
  color: var(--muted, #6b7280);
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.3s ease;
}

.judge-subtitle.success-text {
  color: var(--success, #16a34a);
}

.judge-meter {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.judge-meter-track {
  width: 100px;
  height: 6px;
  border-radius: 999px;
  background: var(--border, #e5e7eb);
  overflow: hidden;
  position: relative;
}

.judge-meter-bar {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 40%;
  border-radius: 999px;
  background: var(--primary, #2563eb);
  animation: judgeIndeterminate 1.5s ease-in-out infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes judgeIndeterminate {
  0% {
    transform: translateX(-100%);
    opacity: 0.85;
  }

  50% {
    transform: translateX(150%);
    opacity: 1;
  }

  100% {
    transform: translateX(-100%);
    opacity: 0.85;
  }
}

/* 过渡：悬浮评判层淡入淡出 */
.judge-fade-enter-active,
.judge-fade-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease, filter 0.22s ease;
}

.judge-fade-enter-from,
.judge-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
  filter: blur(6px);
}

/* 反馈卡片出现时的微动效（Apple 式：低幅度、柔和） */
.feedback-container-enter-active,
.feedback-container-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.feedback-container-enter-from,
.feedback-container-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

.feedback-cards-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feedback-reveal-enter-active {
  transition: opacity 0.26s ease, transform 0.26s ease;
}

.feedback-reveal-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.feedback-reveal-move {
  transition: transform 0.26s ease;
}

@media (prefers-reduced-motion: reduce) {

  .judge-meter-bar,
  .empty-placeholder .empty-icon {
    animation: none !important;
  }

  .judge-fade-enter-active,
  .judge-fade-leave-active,
  .feedback-container-enter-active,
  .feedback-container-leave-active,
  .feedback-reveal-enter-active,
  .feedback-reveal-move {
    transition: none !important;
  }
}

// 空状态占位符
.empty-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 60px 40px;
  position: relative;

  .empty-icon {
    font-size: 72px;
    margin-bottom: 24px;
    opacity: 0.3;
    animation: float 3s ease-in-out infinite;
    filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
  }

  p {
    font-size: 15px;
    margin: 8px 0;
    color: var(--muted);
    font-weight: 500;
  }
}

@keyframes float {

  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-10px);
  }
}

// 节点详情弹窗
.node-detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.3s ease;

  .modal-content {
    background: var(--panel);
    border-radius: 24px;
    width: 90%;
    max-width: 700px;
    max-height: 80vh;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    animation: slideUp 0.3s ease;

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      background: var(--panel);
      color: var(--text);
      border-bottom: 1px solid var(--border);

      .modal-title {
        margin: 0;
        font-size: 18px;
        font-weight: 700;
      }

      .modal-close {
        background: none;
        border: none;
        color: var(--muted);
        font-size: 24px;
        cursor: pointer;
        padding: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: background 0.2s ease;

        &:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      }
    }

    .modal-body {
      padding: 20px;
      overflow-y: auto;
      max-height: calc(80vh - 80px);
      background: var(--panel);

      .detail-item {
        margin-bottom: 20px;

        &:last-child {
          margin-bottom: 0;
        }

        .detail-label {
          display: block;
          font-size: 12px;
          font-weight: 600;
          color: var(--muted);
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .detail-value {
          font-size: 14px;
          color: var(--text) !important;
          line-height: 1.6;

          &.message-content {
            background: rgba(148, 163, 184, 0.06);
            padding: 16px;
            border-radius: 24px;
            border: 1px solid var(--border);
            max-height: 400px;
            overflow-y: auto;

            /* 隐藏滚动条但保留滚动能力 */
            scrollbar-width: none; // Firefox
            -ms-overflow-style: none; // IE/Edge

            &::-webkit-scrollbar {
              display: none; // WebKit
            }

            /* 减小子任务总结内容与卡片顶部的间距 */
            :deep(.md-editor-preview) {
              background: transparent;
              padding: 0;
              border: none;
              box-shadow: none;
              margin-top: 0;

              p,
              h1,
              h2,
              h3,
              h4,
              h5,
              h6 {
                margin-top: 4px;
              }
            }
          }
        }
      }
    }
  }
}


// 确认对话框样式
.confirm-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
}

.confirm-dialog {
  background: white;
  border-radius: 24px;
  padding: 24px;
  width: 90%;
  max-width: 320px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  animation: dialog-scale-in 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);

  .dialog-title {
    margin: 0 0 12px 0;
    font-size: 18px;
    font-weight: 600;
    color: #1a1a1a;
  }

  .dialog-message {
    margin: 0 0 24px 0;
    font-size: 14px;
    color: #666;
    line-height: 1.5;
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;

    .dialog-btn {
      padding: 8px 24px;
      border-radius: 24px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      background: white;
      transition: all 0.2s;
      outline: none;

      &.cancel-btn {
        border: 1px solid #e5e5e5;
        color: #333;

        &:hover {
          background: #f5f5f5;
        }
      }

      &.delete-btn {
        border: 1px solid #ff3b30;
        color: #ff3b30;

        &:hover {
          background: #fff0f0;
        }
      }
    }
  }
}

@keyframes dialog-scale-in {
  from {
    transform: scale(0.9);
    opacity: 0;
  }

  to {
    transform: scale(1);
    opacity: 1;
  }
}

// 动画
@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }

  to {
    transform: translateY(0);
    opacity: 1;
  }
}


/* 自我反馈折叠卡片 (iOS 26 风格) - 抽离原生渲染 */
.feedback-cards-container {
  margin: 16px 0 20px 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feedback-card-native {
  border-radius: 24px;
  background-color: #f2f2f7;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.feedback-card-native summary {
  padding: 16px 20px;
  font-weight: 600;
  font-size: 15px;
  color: #1c1c1e;
  cursor: pointer;
  list-style: none;
  /* remove default triangle in some browsers */
  position: relative;
  user-select: none;
  display: flex;
  align-items: center;
  background-color: transparent;
  outline: none;
  border: none;
}

.feedback-card-native summary::-webkit-details-marker {
  display: none;
  /* remove default triangle in safari */
}

/* Custom icon for details */
.feedback-card-native summary::after {
  content: "›";
  display: inline-block;
  font-size: 22px;
  line-height: 1;
  margin-left: auto;
  transition: transform 0.3s ease;
  color: #8e8e93;
  font-family: monospace;
}

.feedback-card-native[open] summary::after {
  transform: rotate(90deg);
}

.feedback-content-native {
  padding: 0 20px 20px 20px;
}

.feedback-content-native :deep(.md-editor-preview) {
  background: transparent !important;
  padding: 0;
}

.feedback-content-native :deep(.md-editor-preview) p {
  color: #3a3a3c;
  font-size: 14.5px;
  line-height: 1.6;
}

.feedback-card-native.success {
  background-color: #f2fcf5;
  border-color: #d1f4e0;
}

.feedback-card-native.success summary {
  color: #0b6833;
}

.feedback-card-native.error {
  background-color: #fff8f8;
  border-color: #ffe5e5;
}

.feedback-card-native.error summary {
  color: #c92a2a;
}

/* 深色模式：对齐通用设置页配色 */
.theme-dark {
  .task-graph-page {
    --bg: #1c1c1e;
    --panel: #242426;
    --border: #2c2c2e;
    --border-strong: #3a3a3c;
    --text: #f5f5f7;
    --muted: rgba(235, 235, 245, 0.6);
    --primary: #4d6bfe;
    --primary-600: #4d6bfe;
    --success: #30d158;
    --warning: #ffd60a;
    --pending: #636366;

    background: var(--bg);
  }


  .two-column-layout {
    padding: 12px;
  }

  .column {
    background: var(--panel);
    border-color: var(--border);
    box-shadow: none;
  }

  .column .column-header {
    background: #242426;
    border-bottom-color: var(--border);
  }

  .column .column-header .header-icon {
    background: var(--primary);
  }

  .column .column-header .header-title {
    color: var(--text);
  }

  .column .column-content {
    background: var(--panel);
  }

  .user-query-card .query-card-body .query-text {
    color: var(--text);
  }

  .todos-list {
    .todo-item {
      border-color: var(--border);
      background-color: #242426;

      &.completed {
        background-color: rgba(48, 209, 88, 0.12);
        border-color: rgba(48, 209, 88, 0.6);
      }

      &.executing {
        background-color: rgba(255, 214, 10, 0.14);
        border-color: rgba(255, 214, 10, 0.7);
      }

      &.pending {
        background-color: #242426;
      }
    }

    .todo-index {
      background-color: #2c2c2e;
      color: var(--muted);
    }

    .todo-title {
      color: var(--text);
    }

    .todo-status-text {
      color: var(--muted);
    }
  }

  .todo-status-dot {
    background-color: #3a3a3c;
  }

  .todo-item.completed .todo-status-dot {
    background-color: var(--success);
  }

  .todo-item.executing .todo-status-dot {
    background-color: var(--warning);
  }

  .todo-item.pending .todo-status-dot {
    background-color: var(--pending);
  }

  .column-result .result-wrapper {
    :deep(.md-editor-preview) {
      background: transparent;
      color: var(--text);

      p,
      ul,
      ol,
      li,
      strong,
      b,
      em,
      i,
      a,
      span,
      table,
      th,
      td {
        color: var(--text);
      }

      blockquote {
        background: #2c2c2e;
        border-left-color: var(--primary);
        color: var(--text);
        padding: 12px 16px;
        border-radius: 4px;

        p,
        span,
        strong,
        b,
        em,
        i,
        a,
        ul,
        ol,
        li {
          color: var(--text);
        }
      }

      h1,
      h2,
      h3,
      h4,
      h5,
      h6 {
        color: var(--text);
      }

      code {
        background: #2c2c2e;
        color: #ff9f0a;
      }

      pre {
        background: #111827;
        color: #f9fafb;
      }
    }
  }

  .empty-placeholder {
    .empty-icon {
      opacity: 0.4;
    }

    p {
      color: var(--muted);
    }
  }

  .node-detail-modal .modal-content {
    background: #1c1c1e;
    border-radius: 24px;

    .modal-header {
      background: #242426;
      border-bottom-color: var(--border);

      .modal-title {
        color: var(--text);
      }

      .modal-close {
        color: var(--muted);
      }
    }

    .modal-body {
      background: #1c1c1e;

      .detail-label {
        color: var(--muted) !important;
      }

      .detail-value {
        color: var(--text) !important;
        background: transparent;

        &.message-content {
          background: #242426;
          border-color: var(--border);
          border-radius: 24px;

          /* 深色模式下节点详情 Markdown 适配 */
          :deep(.md-editor-preview) {
            background: transparent;
            padding: 0;
            border: none;
            box-shadow: none;
            color: var(--text);

            p,
            ul,
            ol,
            li,
            strong,
            b,
            em,
            i,
            a,
            span,
            table,
            th,
            td {
              color: var(--text);
            }

            blockquote {
              background: #2c2c2e;
              border-left-color: var(--primary);
              color: var(--text);
              padding: 12px 16px;
              border-radius: 4px;

              p,
              span,
              strong,
              b,
              em,
              i,
              a,
              ul,
              ol,
              li {
                color: var(--text);
              }
            }

            h1,
            h2,
            h3,
            h4,
            h5,
            h6 {
              color: var(--text);
            }

            code {
              background: #2c2c2e;
              color: #ff9f0a;
            }

            pre {
              background: #111827;
              color: #f9fafb;
            }
          }
        }
      }
    }
  }

  .feedback-card-native {
    background-color: #2c2c2e;
    border-color: #3a3a3c;
  }

  .feedback-card-native summary {
    color: var(--text);
  }

  .feedback-card-native summary::after {
    color: #8e8e93;
  }

  .feedback-content-native :deep(.md-editor-preview) p {
    color: rgba(235, 235, 245, 0.8);
  }

  .feedback-card-native.success {
    background-color: rgba(48, 209, 88, 0.12);
    border-color: rgba(48, 209, 88, 0.6);
  }

  .feedback-card-native.success summary {
    color: #30d158;
  }

  .feedback-card-native.error {
    background-color: rgba(255, 69, 58, 0.14);
    border-color: rgba(255, 69, 58, 0.7);
  }

  .feedback-card-native.error summary {
    color: #ff453a;
  }

  /* 深色模式下的“评判中”悬浮层 */
  .judge-surface {
    background: rgba(36, 36, 38, 0.78);
    border-color: rgba(245, 245, 247, 0.10);
  }

  .judge-title {
    color: rgba(245, 245, 247, 0.92);
  }

  .judge-subtitle {
    color: rgba(235, 235, 245, 0.62);
  }

  .judge-meter-track {
    background: rgba(148, 163, 184, 0.22);
  }

  .confirm-dialog {
    background: #242426;
    box-shadow: 0 18px 46px rgba(0, 0, 0, 0.7);

    .dialog-title {
      color: #f5f5f7;
    }

    .dialog-message {
      color: rgba(235, 235, 245, 0.6);
    }

    .dialog-footer {
      .dialog-btn {
        &.cancel-btn {
          background: transparent;
          border-color: #3a3a3c;
          color: #f5f5f7;

          &:hover {
            background: #3a3a3c;
          }
        }

        &.delete-btn {
          background: transparent;
          border-color: #ff453a;
          color: #ff453a;

          &:hover {
            background: rgba(255, 69, 58, 0.12);
          }
        }
      }
    }
  }
}
</style>
