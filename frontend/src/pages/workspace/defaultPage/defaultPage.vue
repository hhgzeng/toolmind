<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MdPreview } from "md-editor-v3"
import "md-editor-v3/lib/style.css"
import { getWorkspacePluginsAPI } from '../../../apis/workspace'
import { useUserStore } from '../../../store/user'

const userStore = useUserStore()

const router = useRouter()
const route = useRoute()
const inputMessage = ref('')
const selectedTools = ref<string[]>([])
const selectedMcpServers = ref<string[]>([])
const mcpServers = ref<any[]>([])
const webSearchEnabled = ref(true)
const fileInputRef = ref<HTMLInputElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const currentSessionId = ref<string>('')  // 当前会话ID
const chatConversationRef = ref<HTMLElement | null>(null)  // 聊天容器引用
const isGenerating = ref(false)  // 是否正在生成回复

// 自动调整 textarea 高度（2行起，最多10行）
const autoResize = () => {
  const textarea = textareaRef.value
  if (!textarea) return
  textarea.style.height = 'auto'
  const lineHeight = 24 // 1.6 * 15px
  const minHeight = lineHeight * 2 // 2行
  const maxHeight = lineHeight * 10 // 10行
  const scrollH = textarea.scrollHeight
  textarea.style.height = Math.min(Math.max(scrollH, minHeight), maxHeight) + 'px'
}



// 头像加载错误处理
const handleAvatarError = (event: Event) => {
  const target = event.target as HTMLImageElement
  if (target) {
    target.src = '/src/assets/user.svg'
  }
}



// 切换工具选择
// const toggleTool = (toolId: string) => {
//   const index = selectedTools.value.indexOf(toolId)
//   if (index > -1) {
//     selectedTools.value.splice(index, 1)
//   } else {
//     selectedTools.value.push(toolId)
//   }
// }


// 触发文件选择
const triggerFileInput = () => {
  fileInputRef.value?.click()
}

// 处理文件选择
const onFileChange = (e: Event) => {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (files && files.length > 0) {
    ElMessage.success(`已选择 ${files.length} 个文件`)
  }
  if (input) input.value = ''
}


// 生成UUID（模拟Python的uuid4().hex）
const generateSessionId = (): string => {
  // 使用crypto.randomUUID()生成UUID，然后移除横杠
  return crypto.randomUUID().replace(/-/g, '')
}



// 发送消息
const handleSend = async () => {
  if (!inputMessage.value.trim()) {
    ElMessage.warning('请输入消息内容')
    return
  }

  // 如果正在生成回复，不允许发送新消息
  if (isGenerating.value) {
    ElMessage.warning('请等待当前回复完成')
    return
  }
  
  const query = inputMessage.value.trim()
  
  // 直接跳转到任务流程图页面（三列布局）
  console.log('跳转到灵寻任务页面')
  console.log('query:', query)
  console.log('webSearch:', webSearchEnabled.value)
  
  // 立即清空输入框
  inputMessage.value = ''
  nextTick(autoResize)
  
  router.push({
    name: 'taskGraphPage',
    query: {
      query: query,
      webSearch: webSearchEnabled.value.toString(),
      mcp_servers: JSON.stringify(selectedMcpServers.value)
    }
  })
}

// 键盘事件处理
const handleKeydown = (event: KeyboardEvent) => {
  // 如果正在使用输入法，不处理回车事件
  if (event.isComposing) {
    return
  }

  // 直接回车发送，Shift+Enter 换行
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    // 如果正在生成，不响应回车
    if (!isGenerating.value) {
      handleSend()
    }
  }
}

onMounted(async () => {
  // 检查是否有 session_id 参数，如果有则加载会话历史
  const sessionId = route.query.session_id as string
  if (sessionId) {
    console.log('加载已有会话:', sessionId)
    currentSessionId.value = sessionId  // 设置当前会话ID
  } else {
    // 如果没有session_id，生成一个新的
    currentSessionId.value = generateSessionId()
    console.log('生成新会话ID:', currentSessionId.value)
  }
  
  // 懒加载 MCP 列表（用于选择）
  import('../../../apis/mcp-server').then(async ({ getMCPServersAPI }) => {
    try {
      const res = await getMCPServersAPI()
      if (res.data && res.data.status_code === 200 && Array.isArray(res.data.data)) {
        mcpServers.value = res.data.data.filter((mcp: any) => mcp.is_active)
        selectedMcpServers.value = mcpServers.value.map((mcp: any) => mcp.mcp_server_id)
      }
    } catch (e) {
      console.error('加载 MCP 服务器失败', e)
    }
  })
})

// 监听路由参数变化
watch(
  () => route.query.session_id,
  async (newSessionId, oldSessionId) => {
    if (newSessionId && newSessionId !== oldSessionId) {
      console.log('检测到会话ID变化:', oldSessionId, '->', newSessionId)
      // 更新当前会话ID
      currentSessionId.value = newSessionId as string
    } else if (!newSessionId && oldSessionId) {
      // 如果从有session_id变为没有，生成新的session_id
      currentSessionId.value = generateSessionId()
      console.log('生成新会话ID:', currentSessionId.value)
    }
  }
)
</script>

<template>
  <div class="chat-page">
    <div class="chat-container">
      <!-- 欢迎区域 -->
      <div class="welcome-section">
        <img src="../../../assets/toolmind.png" alt="ToolMind" class="welcome-avatar" />
        <h1 class="welcome-title">今天有什么可以帮到你？</h1>
      </div>

      <!-- 输入区域 -->
      <div class="input-section">
        <div class="input-wrapper">
          <textarea
            ref="textareaRef"
            v-model="inputMessage"
            placeholder="给 ToolMind 发送消息"
            class="message-input"
            rows="2"
            @keydown="handleKeydown"
            @input="autoResize"
          ></textarea>
          
          <!-- 底部控制栏 -->
          <div class="input-footer">
            <div class="footer-left">
              <!-- 附件按钮 -->
              <button class="attach-btn" title="上传附件" @click="triggerFileInput">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                </svg>
              </button>
              <input
                type="file"
                ref="fileInputRef"
                class="hidden-file-input"
                multiple
                @change="onFileChange"
              />
            </div>
            
            <div class="footer-right">
              <!-- 发送按钮 -->
              <button 
                class="send-btn" 
                :class="{ 'btn-disabled': isGenerating, 'btn-inactive': !inputMessage.trim() && !isGenerating }" 
                :disabled="isGenerating" 
                @click="handleSend"
              >
                <svg v-if="!isGenerating" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 20V4M5 11l7-7 7 7"/>
                </svg>
                <span v-else class="loading-spinner"></span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.chat-page {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #fafbfc 0%, #ffffff 100%);
  padding: 0;
  overflow-y: auto;

  &.chat-active {
    padding: 0;
    overflow: hidden;
    background-color: #f7f8fa;
  }
}

.chat-container {
  max-width: 820px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 20px 80px;

  .chat-active & {
    max-width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 0;
  }
}

.welcome-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-bottom: 30px;
  animation: fadeInUp 0.6s ease;

  .welcome-avatar {
    width: 44px;
    height: 44px;
    object-fit: contain;
    filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.08));
    flex-shrink: 0;
  }

  .welcome-title {
    font-size: 24px;
    font-weight: 700;
    background: linear-gradient(135deg, #1f2937 0%, #4b5563 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -0.3px;
    white-space: nowrap;
  }
}

.mode-selector {
  display: flex;
  gap: 14px;
  margin-bottom: 36px;
  animation: fadeInUp 0.6s ease 0.1s both;

  .mode-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 24px;
    border: 2px solid #e5e7eb;
    border-radius: 24px;
    background: white;
    color: #6b7280;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);

    .mode-icon {
      font-size: 18px;
      transition: transform 0.3s ease;
    }

    .mode-label {
      font-weight: 600;
    }

    &:hover {
      border-color: #667eea;
      background: #f8f9ff;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);

      .mode-icon {
        transform: scale(1.1);
      }
    }

    &.active {
      border-color: #667eea;
      background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
      color: #667eea;
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
      transform: translateY(-2px);

      .mode-icon {
        transform: scale(1.15);
      }
    }
  }
}

// 动画
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes rotate {
  from {
    transform: translate(-50%, -50%) rotate(0deg);
  }
  to {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0) translateY(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1.2) translateY(-8px);
    opacity: 1;
  }
}

// 输入框聚焦动画（简洁）

// 移除彩虹动画（不再需要）

.input-section {
  width: 100%;
  max-width: 760px;
  animation: fadeInUp 0.6s ease 0.2s both;

  &.input-fixed {
    max-width: 100%;
    padding: 10px 20px 20px 20px;
    background: #f7f8fa;
    animation: none;

    .input-wrapper {
      max-width: 900px;
      margin: 0 auto;
    }
  }

  .input-wrapper {
    background: #f4f4f4;
    border: 1px solid transparent;
    border-radius: 24px;
    padding: 14px 18px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: none;
    position: relative;
    z-index: 1;

    &:focus-within {
      background: #f4f4f4;
    }

    .message-input {
      width: 100%;
      border: none;
      background: transparent;
      font-size: 15px;
      line-height: 24px;
      color: #1f2937;
      resize: none;
      outline: none;
      font-family: inherit;
      min-height: 48px;
      max-height: 240px;
      overflow-y: auto;
      margin-bottom: 8px;

      &::placeholder {
        color: #9ca3af;
      }

      &::-webkit-scrollbar {
        width: 4px;
      }

      &::-webkit-scrollbar-track {
        background: transparent;
      }

      &::-webkit-scrollbar-thumb {
        background: #d1d5db;
        border-radius: 2px;
      }
    }

    .input-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .footer-left {
        display: flex;
        gap: 10px;

          .selector-dropdown {
          position: relative;

          .selector-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: rgba(0, 0, 0, 0.03);
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 20px;
            font-size: 13px;
            color: #4b5563;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            user-select: none;

            .selector-icon {
              font-size: 16px;
            }

            .selector-icon-img {
              width: 20px;
              height: 20px;
              object-fit: contain;
              display: inline-block;
            }

            .selector-text {
              font-weight: 500;
            }

            .selector-arrow {
              font-size: 10px;
              opacity: 0.5;
              transition: transform 0.2s ease;
            }

            &.open {
              .selector-arrow {
                transform: rotate(180deg);
              }
            }

            .selector-check {
              font-size: 14px;
              color: #667eea;
              font-weight: 600;
            }

            &:hover {
              border-color: #667eea;
              background: #f0f4ff;
              color: #667eea;
            }

            &.active {
              background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
              border-color: #667eea;
              color: #667eea;
              box-shadow: 0 2px 6px rgba(102, 126, 234, 0.15);
            }

            &:active {
              transform: scale(0.96);
            }
          }

          .dropdown-menu {
            position: absolute;
            bottom: calc(100% + 8px);
            left: 0;
            min-width: 200px;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            max-height: 320px;
            overflow: hidden;
            display: flex;
            flex-direction: column;

            &.tool-menu {
              min-width: 360px;
              max-height: 450px;
            }

            // 模型下拉尺寸与工具列表保持一致
            &.model-menu {
              min-width: 180px;
              max-height: 450px;

              .dropdown-item {
                .item-content {
                  .item-text {
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                  }
                }
              }
            }

            .dropdown-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              padding: 12px 16px;
              background: linear-gradient(135deg, #f8f9fa 0%, #f0f2f5 100%);
              border-bottom: 1px solid #e5e7eb;

              .header-title {
                font-size: 14px;
                font-weight: 600;
                color: #1f2937;
              }

              .header-count {
                font-size: 12px;
                color: #6b7280;
                background: white;
                padding: 2px 8px;
                border-radius: 10px;
                border: 1px solid #e5e7eb;
              }
            }

            .dropdown-list {
              flex: 1;
              overflow-y: auto;
              padding: 8px;

              &::-webkit-scrollbar {
                width: 8px;
              }

              &::-webkit-scrollbar-track {
                background: transparent;
              }

              &::-webkit-scrollbar-thumb {
                background: #e0e0e0;
                border-radius: 4px;

                &:hover {
                  background: #bdbdbd;
                }
              }
            }

            .dropdown-empty {
              padding: 48px 20px;
              text-align: center;
              color: #9ca3af;
              display: flex;
              flex-direction: column;
              align-items: center;
              gap: 12px;

              .empty-icon {
                font-size: 48px;
                opacity: 0.3;
              }

              .empty-icon-img {
                width: 48px;
                height: 48px;
                opacity: 0.35;
                object-fit: contain;
              }

              .empty-text {
                font-size: 14px;
                color: #6b7280;
              }
            }

            .dropdown-item {
              display: flex;
              align-items: center;
              justify-content: space-between;
              gap: 12px;
              padding: 14px 12px;
              border-radius: 10px;
              cursor: pointer;
              transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
              margin-bottom: 4px;
              border: 2px solid transparent;
              background: #fafafa;

              .item-left {
                display: flex;
                align-items: center;
                gap: 12px;
                flex: 1;
                min-width: 0;
              }

              .item-icon-wrapper {
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
                border-radius: 10px;
                flex-shrink: 0;
                transition: all 0.3s ease;
                overflow: hidden;

                .item-icon-img {
                  width: 100%;
                  height: 100%;
                  object-fit: cover;
                }

                .item-icon {
                  font-size: 20px;
                }
              }

              .item-content {
                flex: 1;
                min-width: 0;

                .item-text {
                  font-size: 15px;
                  font-weight: 600;
                  color: #1f2937;
                  margin-bottom: 4px;
                  line-height: 1.3;
                }

                .item-desc {
                  font-size: 12px;
                  color: #6b7280;
                  overflow: hidden;
                  text-overflow: ellipsis;
                  display: -webkit-box;
                  -webkit-line-clamp: 2;
                  line-clamp: 2;
                  -webkit-box-orient: vertical;
                  line-height: 1.5;
                }
              }

              .item-check-wrapper {
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                flex-shrink: 0;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);

                .item-check {
                  font-size: 16px;
                  color: white;
                  font-weight: 700;
                }
              }

              &:hover {
                background: #f5f7fa;
                transform: translateX(2px);
                border-color: #e5e7eb;

                .item-icon-wrapper {
                  background: linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%);
                  transform: scale(1.05);
                }
              }

              &.selected {
                background: linear-gradient(135deg, #eff6ff 0%, #e0f2fe 100%);
                border-color: #667eea;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.12);

                .item-icon-wrapper {
                  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                  
                  .item-icon-img {
                    filter: brightness(1.2);
                  }

                  .item-icon {
                    filter: brightness(0) invert(1);
                  }
                }

                .item-text {
                  color: #667eea;
                }
              }

              &:active {
                transform: scale(0.98) translateX(2px);
              }
            }

            .dropdown-footer {
              display: flex;
              justify-content: space-between;
              align-items: center;
              padding: 12px 16px;
              border-top: 2px solid #f0f0f0;
              background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);

              .clear-btn {
                padding: 8px 16px;
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                font-size: 13px;
                color: #6b7280;
                cursor: pointer;
                transition: all 0.25s ease;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 6px;

                &:hover {
                  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                  border-color: #ef4444;
                  color: #dc2626;
                  transform: translateY(-1px);
                  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.2);
                }

                &:active {
                  transform: translateY(0);
                }
              }

              .selected-info {
                display: flex;
                align-items: center;
                gap: 8px;

                .selected-count {
                  font-size: 13px;
                  color: #667eea;
                  font-weight: 600;
                  padding: 4px 12px;
                  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                  border-radius: 12px;
                  border: 1px solid #667eea;
                }
              }
            }
          }
        }
      }

      .footer-left {
        display: flex;
        align-items: center;

        .attach-btn {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: transparent;
          border: none;
          border-radius: 50%;
          cursor: pointer;
          color: #374151;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

          &:hover {
            color: #111827;
            background: rgba(0, 0, 0, 0.06);
          }

          &:active {
            transform: scale(0.92);
          }
        }

        .hidden-file-input {
          display: none;
        }
      }

      .footer-right {
        display: flex;
        align-items: center;

        .send-btn {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #4d6bfe;
          border: none;
          border-radius: 50%;
          color: white;
          cursor: pointer;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          font-size: 16px;

          &:hover:not(.btn-disabled):not(.btn-inactive) {
            background: #3e5be0;
            transform: scale(1.05);
          }

          &:active:not(.btn-disabled):not(.btn-inactive) {
            transform: scale(0.92);
          }

          &.btn-inactive {
            background: #b1c1ff;
            color: white;
            cursor: default;
          }

          &.btn-disabled {
            background: #e5e7eb;
            cursor: not-allowed;
            color: #9ca3af;
          }

          .loading-spinner {
            animation: spin 1s linear infinite;
          }
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      }
    }
  }
}

.chat-conversation {
  flex: 1;
  padding: 0;
  overflow-y: auto;
  width: 100%;
  background-color: #f7f8fa;
  scroll-behavior: smooth;  // 平滑滚动
  
  .message-group {
    margin-bottom: 20px;
    padding: 0 20px;
    
    &:first-child {
      padding-top: 20px;
    }
  }

  .ai-message {
    display: flex;
    align-items: flex-start;
    justify-content: flex-start;

    .avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      margin-right: 15px;
      flex-shrink: 0;
      border: 1px solid #eee;
    }

    .message-content {
      background-color: #ffffff;
      border-radius: 18px;
      padding: 12px 18px;
      max-width: 70%;
      color: #333;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
      word-break: break-word;

      // 加载转圈器样式
      .loading-spinner-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 4px 0;
        color: #6b7280;
        font-size: 14px;

        .loading-spinner {
          width: 16px;
          height: 16px;
          border: 2px solid #d1d5db;
          border-top: 2px solid transparent;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        .loading-text {
          font-weight: 500;
          color: #9ca3af;
        }
      }
    }
  }

  .user-message {
    display: flex;
    justify-content: flex-end;
    align-items: flex-start;

    .avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      margin-left: 12px;
      flex-shrink: 0;
      border: 1px solid #eee;
    }

    .message-content {
      display: flex;
      align-items: center;
      background: linear-gradient(135deg, #6e8efb, #a777e3);
      color: white;
      border-radius: 18px;
      padding: 12px 18px;
      max-width: 70%;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
  }
}

// 下拉菜单动画（向上展开）
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

// Override MdPreview background
:deep(.md-editor-preview-wrapper) {
    background-color: transparent !important;
}

@media (max-width: 768px) {
  .chat-page {
    padding: 40px 16px 20px;
  }

  .welcome-section {
    margin-bottom: 32px;

    .welcome-avatar {
      width: 36px;
      height: 36px;
    }

    .welcome-title {
      font-size: 20px;
    }
  }

  .mode-selector {
    margin-bottom: 28px;
    
    .mode-btn {
      padding: 10px 18px;
      font-size: 13px;
    }
  }

  .input-section {
    .input-wrapper {
      padding: 18px;

      .input-footer {
        .footer-left {
          flex-wrap: wrap;
        }
      }
    }
  }
}
</style>

