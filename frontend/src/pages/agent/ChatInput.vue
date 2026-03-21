<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()
const inputMessage = ref('')
const selectedMcpServers = ref<string[]>([])
const webSearchEnabled = ref(true)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
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
})


</script>

<template>
  <div class="chat-page">
    <div class="chat-container">
      <!-- 欢迎区域 -->
      <div class="welcome-section">
        <img src="../../assets/toolmind.png" alt="ToolMind" class="welcome-avatar" />
        <h1 class="welcome-title">今天有什么可以帮到你？</h1>
      </div>

      <!-- 输入区域 -->
      <div class="input-section">
        <div class="input-wrapper">
          <textarea ref="textareaRef" v-model="inputMessage" placeholder="给 ToolMind 发送消息" class="message-input"
            rows="2" @keydown="handleKeydown" @input="autoResize"></textarea>
          <div class="input-footer">
            <div class="footer-right">
              <!-- 发送按钮 -->
              <button class="send-btn"
                :class="{ 'btn-disabled': isGenerating, 'btn-inactive': !inputMessage.trim() && !isGenerating }"
                :disabled="isGenerating" @click="handleSend">
                <svg v-if="!isGenerating" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                  fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 20V4M5 11l7-7 7 7" />
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
  background: #ffffff;
  padding: 0;
  overflow-y: auto;
}

.chat-container {
  max-width: 820px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 20px 80px;
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

.input-section {
  width: 100%;
  max-width: 760px;
  animation: fadeInUp 0.6s ease 0.2s both;

  .input-wrapper {
    background: #f4f4f4;
    border: 1px solid transparent;
    border-radius: 24px;
    padding: 14px 18px 16px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    z-index: 1;

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
      justify-content: flex-end;
      align-items: center;

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
            width: 16px;
            height: 16px;
            border: 2px solid #ffffff;
            border-top: 2px solid transparent;
            border-radius: 50%;
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

/* 深色模式 */
.theme-dark {
  .chat-page {
    background: #1c1c1e;
  }

  .chat-container {
    .welcome-section {
      .welcome-title {
        background: none;
        -webkit-text-fill-color: #f5f5f7;
        color: #f5f5f7;
      }
    }
  }

  .input-section {
    .input-wrapper {
      background: #2c2c2e;
      border-color: #3a3a3c;

      .message-input {
        color: #f5f5f7;

        &::placeholder {
          color: rgba(235, 235, 245, 0.6);
        }

        &::-webkit-scrollbar-thumb {
          background: #4b5563;
        }
      }

      .input-footer {
        .footer-right {
          .send-btn {
            &.btn-disabled {
              background: #3a3a3c;
              color: rgba(235, 235, 245, 0.5);
            }
          }
        }
      }
    }
  }
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

  .input-section {
    .input-wrapper {
      padding: 18px;
    }
  }
}
</style>
