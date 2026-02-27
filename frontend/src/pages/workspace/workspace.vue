<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../../store/user'
import { logoutAPI, getUserInfoAPI } from '../../apis/auth'
import { 
  getWorkspaceSessionsAPI, 
  deleteWorkspaceSessionAPI 
} from '../../apis/workspace'

const router = useRouter()
import { useRoute } from 'vue-router'
const route = useRoute()
const userStore = useUserStore()
const selectedSession = ref('')
const sessions = ref<any[]>([])
const loading = ref(false)

// 操作菜单状态
const activeMenuId = ref<string | null>(null)

const toggleMenu = (sessionId: string, event: Event) => {
  event.stopPropagation()
  activeMenuId.value = activeMenuId.value === sessionId ? null : sessionId
}

const closeMenu = () => {
  activeMenuId.value = null
}

// 用户菜单状态
const showUserMenu = ref(false)

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

// 点击外部关闭菜单
const handleGlobalClick = (e: Event) => {
  activeMenuId.value = null
  // 关闭用户菜单（除非点击在用户菜单区域内）
  const target = e.target as HTMLElement
  if (!target.closest('.user-profile-wrapper')) {
    showUserMenu.value = false
  }
}

// 按时间分组的会话列表
const groupedSessions = computed(() => {
  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterdayStart = new Date(todayStart.getTime() - 86400000)
  const threeDaysStart = new Date(todayStart.getTime() - 3 * 86400000)
  const weekStart = new Date(todayStart.getTime() - 7 * 86400000)
  const monthStart = new Date(todayStart.getTime() - 30 * 86400000)

  // 固定分组
  const fixedGroups: { label: string; items: any[] }[] = [
    { label: '今天', items: [] },
    { label: '昨天', items: [] },
    { label: '3 天内', items: [] },
    { label: '7 天内', items: [] },
    { label: '30 天内', items: [] }
  ]

  // 按月份的动态分组
  const monthGroups: Map<string, any[]> = new Map()

  for (const session of sessions.value) {
    const date = new Date(session.createTime)
    if (isNaN(date.getTime())) {
      // 无效日期放到最后
      const key = '未知'
      if (!monthGroups.has(key)) monthGroups.set(key, [])
      monthGroups.get(key)!.push(session)
    } else if (date >= todayStart) {
      fixedGroups[0].items.push(session)
    } else if (date >= yesterdayStart) {
      fixedGroups[1].items.push(session)
    } else if (date >= threeDaysStart) {
      fixedGroups[2].items.push(session)
    } else if (date >= weekStart) {
      fixedGroups[3].items.push(session)
    } else if (date >= monthStart) {
      fixedGroups[4].items.push(session)
    } else {
      // 超过30天，按月份分组
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const key = `${year}-${month}`
      if (!monthGroups.has(key)) monthGroups.set(key, [])
      monthGroups.get(key)!.push(session)
    }
  }

  // 合并结果
  const result: { label: string; items: any[] }[] = []

  // 先添加固定分组（有数据的）
  for (const g of fixedGroups) {
    if (g.items.length > 0) {
      result.push(g)
    }
  }

  // 再按时间倒序添加月份分组
  const sortedMonthKeys = Array.from(monthGroups.keys())
    .filter(k => k !== '未知')
    .sort((a, b) => b.localeCompare(a))

  for (const key of sortedMonthKeys) {
    result.push({ label: key, items: monthGroups.get(key)! })
  }

  // 最后添加"未知"分组
  if (monthGroups.has('未知')) {
    result.push({ label: '未知', items: monthGroups.get('未知')! })
  }

  return result
})

// 获取会话列表
const fetchSessions = async () => {
  try {
    loading.value = true
    const response = await getWorkspaceSessionsAPI()
    if (response.data.status_code === 200) {
      sessions.value = response.data.data.map((session: any) => ({
        sessionId: session.session_id || session.id,
        title: session.title || '未命名会话',
        createTime: session.create_time || session.created_at || new Date().toISOString(),
        agent: session.agent || 'lingseek',
        contexts: session.contexts || []
      }))
      console.log('工作区会话列表:', sessions.value)
    } else {
      ElMessage.error('获取会话列表失败')
    }
  } catch (error) {
    console.error('获取会话列表出错:', error)
    ElMessage.error('获取会话列表失败')
  } finally {
    loading.value = false
  }
}

// 删除会话确认状态
const sessionToDelete = ref<string | null>(null)

const confirmDeleteSession = (sessionId: string, event: Event) => {
  event.stopPropagation()
  sessionToDelete.value = sessionId
  activeMenuId.value = null
}

const cancelDelete = () => {
  sessionToDelete.value = null
}

// 执行删除会话
const executeDelete = async () => {
  if (!sessionToDelete.value) return
  const sessionId = sessionToDelete.value
  
  try {
    const response = await deleteWorkspaceSessionAPI(sessionId)
    if (response.data.status_code === 200) {
      ElMessage.success('会话删除成功')
      await fetchSessions()
      
      if (selectedSession.value === sessionId) {
        selectedSession.value = ''
        router.push('/workspace')
      }
    } else {
      ElMessage.error('删除会话失败')
    }
  } catch (error) {
    console.error('删除会话出错:', error)
    ElMessage.error('删除会话失败')
  } finally {
    sessionToDelete.value = null
  }
}

// 选择会话
const selectSession = (sessionId: string) => {
  selectedSession.value = sessionId
  const session = sessions.value.find(s => s.sessionId === sessionId)
  if (!session) {
    console.error('未找到会话:', sessionId)
    return
  }
  console.log('选择会话:', sessionId, '类型:', session.agent)
  router.push({
    name: 'taskGraphPage',
    query: { session_id: sessionId }
  })
}

// 用户菜单命令
const handleUserCommand = async (command: string) => {
  showUserMenu.value = false
  switch (command) {
    case 'settings':
      router.push('/model')
      break
    case 'logout':
      await handleLogout()
      break
  }
}

// 退出登录
const handleLogout = async () => {
  try {
    await logoutAPI()
  } catch (error) {
    console.error('调用登出接口失败:', error)
  }
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

// 头像加载错误处理
const handleAvatarError = (event: Event) => {
  const target = event.target as HTMLImageElement
  if (target) {
    target.src = '/src/assets/user.svg'
  }
}

// 开启新对话
const goToHomepage = () => {
  router.push('/workspace')
}

onMounted(async () => {
  userStore.initUserState()
  
  if (userStore.isLoggedIn && userStore.userInfo && !userStore.userInfo.avatar) {
    try {
      const response = await getUserInfoAPI(userStore.userInfo.id)
      if (response.data.status_code === 200 && response.data.data) {
        const userData = response.data.data
        userStore.updateUserInfo({
          avatar: userData.user_avatar || userData.avatar || '/src/assets/user.svg',
          description: userData.user_description || userData.description
        })
      }
    } catch (error) {
      console.error('初始化时获取用户信息失败:', error)
    }
  }
  
  await fetchSessions()
  document.addEventListener('click', handleGlobalClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleGlobalClick)
})
</script>

<template>
  <div class="workspace-container">
    <!-- 工作区主内容 -->
    <div class="workspace-main">
    <!-- 左侧边栏 -->
    <div class="sidebar">
      <!-- 侧边栏顶部 Logo -->
      <div class="sidebar-header">
        <img src="../../assets/toolmind.png" alt="Logo" class="sidebar-logo" />
        <span class="sidebar-brand">ToolMind</span>
      </div>

      <!-- 新对话按钮 -->
      <div class="create-section">
        <button @click="goToHomepage" class="create-btn-native">
          <svg class="btn-icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor">
            <path d="M512 85.333333c235.648 0 426.666667 191.018667 426.666667 426.666667 0 231.68-184.618667 420.181333-414.72 426.496L512 938.666667H165.077333a42.666667 42.666667 0 0 1-35.498666-66.346667l27.52-41.301333 6.528-11.648 5.333333-10.282667 2.218667-4.693333 3.541333-8.277334c3.84-10.24 4.565333-16.981333 2.048-20.181333A424.832 424.832 0 0 1 85.333333 512C85.333333 276.352 276.352 85.333333 512 85.333333z m0 85.333334a341.333333 341.333333 0 0 0-341.333333 341.333333c0 72.917333 22.826667 142.165333 64.512 199.765333l8.576 11.349334c32.768 41.557333 29.312 70.570667 4.181333 119.68L242.304 853.333333H512a341.333333 341.333333 0 0 0 341.162667-330.666666L853.333333 512a341.333333 341.333333 0 0 0-341.333333-341.333333z"></path>
            <path d="M469.333333 298.666667m42.666667 0l0 0q42.666667 0 42.666667 42.666666l0 341.333334q0 42.666667-42.666667 42.666666l0 0q-42.666667 0-42.666667-42.666666l0-341.333334q0-42.666667 42.666667-42.666666Z"></path>
            <path d="M725.333333 469.333333m0 42.666667l0 0q0 42.666667-42.666666 42.666667l-341.333334 0q-42.666667 0-42.666666-42.666667l0 0q0-42.666667 42.666666-42.666667l341.333334 0q42.666667 0 42.666666 42.666667Z"></path>
          </svg>
          <span>开启新对话</span>
        </button>
      </div>

      <!-- 会话列表 -->
      <div class="session-list">
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <div class="loading-text">加载中...</div>
        </div>

        <!-- 空状态 -->
        <div v-else-if="sessions.length === 0" class="empty-state">
          <div class="empty-text">暂无会话记录</div>
        </div>

        <!-- 按时间分组的会话列表 -->
        <template v-else>
          <div v-for="group in groupedSessions" :key="group.label" class="session-group">
            <div class="group-label">{{ group.label }}</div>
            <div
              v-for="session in group.items"
              :key="session.sessionId"
              :class="['session-item', { active: selectedSession === session.sessionId }]"
              @click="selectSession(session.sessionId)"
            >
              <span class="session-title">{{ session.title }}</span>
              <button
                class="more-btn"
                @click="toggleMenu(session.sessionId, $event)"
                title="更多操作"
              >
                ⋯
              </button>
              <!-- 操作菜单 -->
              <transition name="menu-fade">
                <div v-if="activeMenuId === session.sessionId" class="action-menu">
                  <button class="menu-item delete" @click="confirmDeleteSession(session.sessionId, $event)">
                    <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M3 6h18"></path>
                      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                      <line x1="10" y1="11" x2="10" y2="17"></line>
                      <line x1="14" y1="11" x2="14" y2="17"></line>
                    </svg>
                    删除
                  </button>
                </div>
              </transition>
            </div>
          </div>
        </template>
      </div>

      <!-- 底部用户信息 -->
      <div class="sidebar-footer">
        <div class="user-profile-wrapper" @click.stop>
          <!-- 用户菜单弹出层 -->
          <transition name="user-menu-fade">
            <div v-if="showUserMenu" class="user-popup-menu">
              <div class="popup-user-info">
                <img
                  :src="userStore.userInfo?.avatar || '/src/assets/user.svg'"
                  alt="头像"
                  class="popup-avatar"
                  @error="handleAvatarError"
                  referrerpolicy="no-referrer"
                />
                <div class="popup-user-text">
                  <div class="popup-username">{{ userStore.userInfo?.username || '用户' }}</div>
                </div>
              </div>
              <div class="popup-divider"></div>
              <button class="popup-menu-item" @click="handleUserCommand('settings')">
                <svg class="popup-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="3"></circle>
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
                系统设置
              </button>
              <button class="popup-menu-item" @click="handleUserCommand('logout')">
                <svg class="popup-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                  <polyline points="16 17 21 12 16 7"></polyline>
                  <line x1="21" y1="12" x2="9" y2="12"></line>
                </svg>
                退出登录
              </button>
            </div>
          </transition>

          <!-- 用户资料区域（可点击） -->
          <div class="user-profile" @click="toggleUserMenu">
            <img
              :src="userStore.userInfo?.avatar || '/src/assets/user.svg'"
              alt="头像"
              class="profile-avatar"
              @error="handleAvatarError"
              referrerpolicy="no-referrer"
            />
            <span class="profile-name">{{ userStore.userInfo?.username || '用户' }}</span>
            <span class="profile-dots">⋯</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧内容区域 -->
    <div class="content">
      <router-view />
    </div>
    </div>

    <!-- 确认删除对话框 -->
    <transition name="fade">
      <div v-if="sessionToDelete" class="confirm-dialog-overlay" @click="cancelDelete">
        <div class="confirm-dialog" @click.stop>
          <h3 class="dialog-title">永久删除对话</h3>
          <p class="dialog-message">删除后，该对话将不可恢复。确认删除吗？</p>
          <div class="dialog-footer">
            <button class="dialog-btn cancel-btn" @click="cancelDelete">取消</button>
            <button class="dialog-btn delete-btn" @click="executeDelete">删除</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style lang="scss" scoped>
.workspace-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
}

/* ===== 侧边栏 - DeepSeek 白色风格 ===== */
.workspace-main {
  display: flex;
  flex: 1;
  height: 100vh;
  background-color: #ffffff;

  .sidebar {
    height: 100%;
    width: 260px;
    min-width: 260px;
    background: #f7f8fa;
    display: flex;
    flex-direction: column;
    border-right: 1px solid #ebebeb;
    box-shadow: none;

    .sidebar-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 18px 18px 4px;
      user-select: none;

      .sidebar-logo {
        width: 26px;
        height: 26px;
        object-fit: contain;
      }

      .sidebar-brand {
        font-size: 18px;
        font-weight: 700;
        color: #4D6BFE;
        letter-spacing: -0.3px;
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'PingFang SC', sans-serif;
      }
    }

    .create-section {
      padding: 16px 14px 8px;

      .create-btn-native {
        width: 100%;
        height: 42px;
        border-radius: 21px;
        font-weight: 500;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        background: #ffffff;
        color: #333333;
        border: 1px solid #d9d9d9;
        cursor: pointer;
        font-size: 14px;
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif;
        letter-spacing: 0.3px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;

        .btn-icon {
          font-size: 15px;
          font-weight: 400;
          color: #666;
        }

        &:hover {
          background: #fafafa;
          border-color: #c0c0c0;
        }

        &:active {
          transform: scale(0.97);
          background: #f5f5f5;
        }
      }
    }

    .session-list {
      flex: 1;
      padding: 4px 8px 8px;
      overflow-y: auto;
      scrollbar-width: none;
      -ms-overflow-style: none;
      &::-webkit-scrollbar { display: none; }

      .loading-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 120px;
        gap: 12px;

        .loading-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid #e5e5e5;
          border-top-color: #999;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        .loading-text {
          font-size: 13px;
          color: #999;
        }
      }

      .empty-state {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 120px;

        .empty-text {
          font-size: 13px;
          color: #bbb;
        }
      }

      .session-group {
        margin-bottom: 2px;

        .group-label {
          font-size: 12px;
          font-weight: 600;
          color: #8e8e93;
          padding: 14px 10px 6px;
          letter-spacing: 0.3px;
          font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif;
        }

        .session-item {
          display: flex;
          align-items: center;
          padding: 10px 10px;
          border-radius: 10px;
          cursor: pointer;
          transition: all 0.15s ease;
          position: relative;
          margin-bottom: 1px;

          .session-title {
            flex: 1;
            font-size: 14px;
            font-weight: 400;
            color: #1f2937;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            line-height: 1.4;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif;
          }

          .more-btn {
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: transparent;
            border: none;
            color: #999;
            font-size: 16px;
            cursor: pointer;
            border-radius: 8px;
            opacity: 0;
            transition: all 0.15s ease;
            flex-shrink: 0;
            letter-spacing: 2px;

            &:hover {
              background: rgba(0, 0, 0, 0.06);
              color: #666;
            }
          }

          .action-menu {
            position: absolute;
            right: 0;
            top: calc(100% + 4px);
            background: #ffffff;
            border: 1px solid #e5e5e5;
            border-radius: 10px;
            padding: 4px;
            z-index: 100;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
            min-width: 120px;

            .menu-item {
              display: flex;
              align-items: center;
              gap: 8px;
              width: 100%;
              padding: 8px 14px;
              background: transparent;
              border: none;
              color: #333;
              font-size: 13px;
              cursor: pointer;
              border-radius: 6px;
              text-align: left;
              transition: background 0.15s ease;
              font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif;

              .menu-icon {
                width: 16px;
                height: 16px;
                flex-shrink: 0;
              }

              &:hover {
                background: #f5f5f5;
              }

              &.delete {
                color: #ff3b30;

                &:hover {
                  background: #fff0f0;
                }
              }
            }
          }

          &:hover {
            background: rgba(0, 0, 0, 0.04);

            .more-btn {
              opacity: 1;
            }
          }

          &.active {
            background: #e8e8ed;

            .session-title {
              color: #1a1a1a;
              font-weight: 500;
            }

            .more-btn {
              opacity: 1;
            }
          }
        }
      }
    }

    .sidebar-footer {
      padding: 12px 14px;
      border-top: 1px solid #ebebeb;

      .user-profile-wrapper {
        position: relative;
      }

      .user-profile {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 8px;
        border-radius: 10px;
        transition: background 0.15s ease;
        cursor: pointer;
        user-select: none;

        &:hover {
          background: rgba(0, 0, 0, 0.04);

          .profile-dots {
            opacity: 1;
          }
        }

        .profile-avatar {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          object-fit: cover;
          flex-shrink: 0;
        }

        .profile-name {
          flex: 1;
          font-size: 14px;
          font-weight: 500;
          color: #1f2937;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif;
        }

        .profile-dots {
          font-size: 16px;
          color: #999;
          opacity: 0;
          transition: opacity 0.15s ease;
          flex-shrink: 0;
          width: 28px;
          text-align: center;
        }
      }

      /* ChatGPT 风格弹出菜单 */
      .user-popup-menu {
        position: absolute;
        bottom: calc(100% + 8px);
        left: 0;
        right: 0;
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.15), 0 2px 8px rgba(0, 0, 0, 0.06);
        z-index: 2000;
        overflow: hidden;
        padding: 4px;

        .popup-user-info {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px 12px;
          border-radius: 12px;

          .popup-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            object-fit: cover;
            flex-shrink: 0;
          }

          .popup-user-text {
            flex: 1;
            min-width: 0;

            .popup-username {
              font-size: 14px;
              font-weight: 600;
              color: #1a1a1a;
              line-height: 1.3;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
              font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif;
            }
          }
        }

        .popup-divider {
          height: 1px;
          background: #f0f0f0;
          margin: 2px 8px;
        }

        .popup-menu-item {
          display: flex;
          align-items: center;
          gap: 10px;
          width: 100%;
          padding: 10px 12px;
          background: transparent;
          border: none;
          color: #1f2937;
          font-size: 14px;
          cursor: pointer;
          border-radius: 12px;
          text-align: left;
          transition: background 0.15s ease;
          font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif;

          .popup-icon {
            width: 18px;
            height: 18px;
            color: #666;
            flex-shrink: 0;
          }

          &:hover {
            background: #f5f5f5;
          }
        }
      }
    }
  }

  .content {
    flex: 1;
    background-color: #ffffff;
    border-radius: 0;
    margin: 0;
    box-shadow: none;
    overflow: hidden;
  }
}

// 菜单动画
.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: all 0.15s ease;
}
.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.95);
}

// 用户菜单动画
.user-menu-fade-enter-active,
.user-menu-fade-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.user-menu-fade-enter-from,
.user-menu-fade-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.95);
}

// 动画
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .workspace-main {
    .sidebar {
      width: 240px;
    }

    .content {
      margin: 0;
    }
  }
}

@media (max-width: 480px) {
  .workspace-main {
    flex-direction: column;

    .sidebar {
      width: 100%;
      height: auto;
      max-height: 300px;
    }

    .content {
      flex: 1;
      margin: 0;
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
  border-radius: 20px;
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
      border-radius: 20px;
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

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
