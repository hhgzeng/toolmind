<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { User, Search, Edit, CloseBold } from '@element-plus/icons-vue'
import { getUserListAPI, updateUserRoleAPI, toggleUserStatusAPI } from '../../apis/user-management'

const loading = ref(false)
const users = ref<any[]>([])
const searchKeyword = ref('')

// 更改角色弹窗
const roleDialogVisible = ref(false)
const roleLoading = ref(false)
const roleTargetUser = ref<any | null>(null)
const roleNewRole = ref<'admin' | 'user'>('user')

// 启用/禁用弹窗
const statusDialogVisible = ref(false)
const statusLoading = ref(false)
const statusTargetUser = ref<any | null>(null)
const statusNewStatus = ref<boolean>(false)
const statusActionName = ref<'禁用' | '解禁'>('禁用')

const filteredUsers = computed(() => {
  if (!searchKeyword.value) {
    return users.value
  }
  const keyword = searchKeyword.value.toLowerCase()
  return users.value.filter((user) => {
    const name = user.user_name ? String(user.user_name).toLowerCase() : ''
    const id = user.user_id != null ? String(user.user_id) : ''
    return name.includes(keyword) || id.includes(keyword)
  })
})

const clearSearch = () => {
  searchKeyword.value = ''
}

// 获取用户列表
const fetchUsers = async () => {
  try {
    loading.value = true
    const res = await getUserListAPI(1, 1000)
    if (res.data.status_code === 200) {
      users.value = res.data.data.items
    } else {
      ElMessage.error(res.data.status_message || '获取用户列表失败')
    }
  } catch (error: any) {
    if (error?.response?.status === 403) {
      ElMessage.error('权限不足，仅管理员可访问')
    } else {
      ElMessage.error('获取用户列表出错')
    }
  } finally {
    loading.value = false
  }
}

// 打开更改角色弹窗
const handleRoleChange = (user: any) => {
  if (String(user.user_id) === '1') {
    ElMessage.warning('不能修改超级管理员的角色')
    return
  }
  roleTargetUser.value = user
  roleNewRole.value = user.role === 'admin' ? 'user' : 'admin'
  roleDialogVisible.value = true
}

const confirmRoleChange = async () => {
  if (!roleTargetUser.value) return
  roleLoading.value = true
  try {
    const res = await updateUserRoleAPI(roleTargetUser.value.user_id, roleNewRole.value)
    if (res.data.status_code === 200) {
      ElMessage.success('角色更改成功')
      roleDialogVisible.value = false
      roleTargetUser.value = null
      fetchUsers()
    } else {
      ElMessage.error(res.data.status_message || '角色更改失败')
    }
  } catch (error) {
    ElMessage.error('角色更改出错')
  } finally {
    roleLoading.value = false
  }
}

const cancelRoleChange = () => {
  if (roleLoading.value) return
  roleDialogVisible.value = false
  roleTargetUser.value = null
}

// 打开启用/禁用弹窗
const handleToggleStatus = (user: any) => {
  if (String(user.user_id) === '1') {
    ElMessage.warning('不能禁用/启用超级管理员账号')
    return
  }

  statusTargetUser.value = user
  // 后端接口入参叫 enable（是否启用/解禁），与前端展示字段 is_disabled 语义相反
  // - 当前已禁用 -> enable=true（解禁）
  // - 当前正常   -> enable=false（禁用）
  statusNewStatus.value = Boolean(user.is_disabled)
  statusActionName.value = user.is_disabled ? '解禁' : '禁用'
  statusDialogVisible.value = true
}

const confirmToggleStatus = async () => {
  if (!statusTargetUser.value) return
  statusLoading.value = true
  try {
    const res = await toggleUserStatusAPI(statusTargetUser.value.user_id, statusNewStatus.value)
    if (res.data.status_code === 200) {
      ElMessage.success(`已成功${statusActionName.value}`)
      statusDialogVisible.value = false
      statusTargetUser.value = null
      fetchUsers()
    } else {
      ElMessage.error(res.data.status_message || `${statusActionName.value}失败`)
    }
  } catch (error) {
    ElMessage.error(`${statusActionName.value}出错`)
  } finally {
    statusLoading.value = false
  }
}

const cancelToggleStatus = () => {
  if (statusLoading.value) return
  statusDialogVisible.value = false
  statusTargetUser.value = null
}

onMounted(() => {
  fetchUsers()
})
</script>

<template>
  <div class="user-management-page">
    <div class="page-header">
      <h2>
        <el-icon class="page-icon">
          <User />
        </el-icon>
        用户管理
      </h2>
      <div class="header-actions">
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索用户名或ID..."
            :prefix-icon="Search"
            clearable
            @clear="clearSearch"
            style="width: 260px"
          />
        </div>
      </div>
    </div>

    <div class="user-card-list" v-loading="loading">
      <div class="list-header">
        <div class="header-col col-user">用户</div>
        <div class="header-col col-role">角色</div>
        <div class="header-col col-status">状态</div>
        <div class="header-col col-created">创建时间</div>
        <div class="header-col col-actions">操作</div>
      </div>
      <div class="list-body" v-if="filteredUsers.length > 0">
        <div
          v-for="user in filteredUsers"
          :key="user.user_id"
          class="list-row"
        >
          <div class="cell col-user">
            <div class="user-info">
              <div class="avatar">
                {{ user.user_name ? String(user.user_name).charAt(0).toUpperCase() : 'U' }}
              </div>
              <div class="user-meta">
                <div class="user-name">
                  {{ user.user_name }}
                  <el-tag
                    v-if="String(user.user_id) === '1'"
                    size="small"
                    type="warning"
                    effect="plain"
                    class="super-admin-tag"
                  >
                    超级管理员
                  </el-tag>
                </div>
                <div class="user-id">ID：{{ user.user_id }}</div>
              </div>
            </div>
          </div>

          <div class="cell col-role">
            <el-tag
              :type="user.role === 'admin' ? 'success' : 'info'"
              size="small"
              effect="plain"
              :class="['role-tag-card', { 'admin-tag': user.role === 'admin' }]"
            >
              {{ user.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </div>

          <div class="cell col-status">
            <el-tag
              :type="user.is_disabled ? 'danger' : 'primary'"
              size="small"
              effect="plain"
              :class="['status-tag-card', { 'is-disabled': user.is_disabled }]"
            >
              {{ user.is_disabled ? '已禁用' : '正常' }}
            </el-tag>
          </div>

          <div class="cell col-created">
            <span class="created-time">
              {{ user.create_time ? new Date(user.create_time).toLocaleString() : '-' }}
            </span>
          </div>

          <div class="cell col-actions">
            <div class="action-buttons">
              <el-button
                :type="user.role === 'admin' ? 'warning' : 'primary'"
                size="small"
                @click.stop="handleRoleChange(user)"
                class="action-btn role-btn"
              >
                <el-icon class="action-icon">
                  <Edit />
                </el-icon>
                <span>更改角色</span>
              </el-button>
              <el-button
                :type="user.is_disabled ? 'success' : 'danger'"
                size="small"
                @click.stop="handleToggleStatus(user)"
                class="action-btn status-btn"
              >
                <el-icon class="action-icon">
                  <CloseBold />
                </el-icon>
                <span>{{ user.is_disabled ? '启用账号' : '禁用账号' }}</span>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!loading && filteredUsers.length === 0" class="empty-state">
        <h3>暂无成员</h3>
        <p>当前没有可显示的成员，可以调整搜索关键词再试试</p>
      </div>
    </div>

    <!-- 更改角色弹窗 -->
    <Teleport to="body">
      <transition name="fade">
        <div
          v-if="roleDialogVisible"
          class="dialog-overlay"
          @click="cancelRoleChange"
        >
          <div class="dialog-container" @click.stop>
            <div class="dialog-body">
              <div class="dialog-title-row">
                <h3 class="dialog-title">更改角色</h3>
                <button class="dialog-close" @click="cancelRoleChange">
                  ×
                </button>
              </div>
              <p class="dialog-message" v-if="roleTargetUser">
                确定要将用户
                <strong>「{{ roleTargetUser.user_name || roleTargetUser.user_id }}」</strong>
                的角色更改为
                <strong>
                  {{ roleNewRole === 'admin' ? '管理员' : '普通用户' }}
                </strong>
                吗？
              </p>
            </div>
            <div class="dialog-footer">
              <button
                class="dialog-btn cancel-btn"
                @click.stop="cancelRoleChange"
                :disabled="roleLoading"
              >
                取消
              </button>
              <button
                class="dialog-btn confirm-btn"
                @click.stop="confirmRoleChange"
                :disabled="roleLoading"
              >
                {{ roleLoading ? '保存中...' : '确认更改' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- 启用 / 禁用弹窗 -->
    <Teleport to="body">
      <transition name="fade">
        <div
          v-if="statusDialogVisible"
          class="confirm-dialog-overlay"
          @click="cancelToggleStatus"
        >
          <div class="confirm-dialog" @click.stop>
            <h3 class="dialog-title">
              {{ statusActionName }}账号
            </h3>
            <p class="dialog-message" v-if="statusTargetUser">
              确定要{{ statusActionName }}用户
              <strong>「{{ statusTargetUser.user_name || statusTargetUser.user_id }}」</strong>
              吗？
            </p>
            <div class="confirm-dialog-footer">
              <button
                class="confirm-dialog-btn confirm-cancel-btn"
                @click="cancelToggleStatus"
                :disabled="statusLoading"
              >
                取消
              </button>
              <button
                class="confirm-dialog-btn confirm-delete-btn"
                @click="confirmToggleStatus"
                :disabled="statusLoading"
              >
                {{ statusLoading ? '处理中...' : `确认${statusActionName}` }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style lang="scss" scoped>
.user-management-page {
  padding: 30px;
  min-height: calc(100vh - 60px);
  background-color: #ffffff;

  .page-header {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 24px;
    background: linear-gradient(to right, #ffffff, #f8fafc);
    padding: 24px 28px;
    border-radius: 24px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    position: relative;
    overflow: hidden;

    h2 {
      font-size: 26px;
      font-weight: 700;
      margin: 0;
      display: flex;
      align-items: center;
      gap: 12px;
      color: #303133;

      .page-icon {
        font-size: 30px;
        width: 32px;
        height: 32px;
        color: #303133;
      }
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 16px;

      .search-box {
        :deep(.el-input__wrapper) {
          border-radius: 100px;
          transition: all 0.3s;
          border: 1px solid #dcdfe6;

          &:hover {
            border-color: #409eff;
            box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.2);
          }
        }
      }
    }
  }

  .user-card-list {
    border-radius: 24px;
    overflow: hidden;
    border: 1px solid #ebeef5;
    background: #ffffff;

    .list-header {
      display: flex;
      background-color: #f8fafc;
      border-bottom: 2px solid #e2e8f0;

      .header-col {
        padding: 12px 16px;
        color: #64748b;
        font-weight: 600;
        font-size: 14px;
        text-align: left;
        box-sizing: border-box;
        flex-shrink: 0;
      }
    }

    .list-body {
      .list-row {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #f1f5f9;
        transition: background-color 0.2s;

        &:hover {
          background-color: #f8fafc;
        }

        &:last-child {
          border-bottom: none;
        }

        .cell {
          padding: 16px;
          box-sizing: border-box;
          flex-shrink: 0;
        }
      }
    }

    .col-user {
      width: 25%;
    }

    .col-role {
      width: 15%;
      padding-left: 40px;
    }

    .col-status {
      width: 15%;
      padding-left: 40px;
    }

    .col-created {
      flex: 1;
      padding-left: 40px;
    }

    .col-actions {
      width: 240px;
      padding-left: 40px;
    }

    .user-info {
      display: flex;
      align-items: center;

      .avatar {
        width: 44px;
        height: 44px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 16px;
        flex-shrink: 0;
        color: #ffffff;
        font-weight: 600;
        font-size: 20px;
        background: linear-gradient(135deg, #409eff 0%, #3a7be2 100%);
      }

      .user-meta {
        .user-name {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 15px;
          font-weight: 600;
          color: #303133;
          margin-bottom: 4px;
        }

        .user-id {
          font-size: 13px;
          color: #909399;
        }
      }
    }

    .created-time {
      font-size: 14px;
      color: #909399;
    }

    .action-buttons {
      display: flex;
      align-items: center;
      flex-wrap: nowrap;
      justify-content: flex-end;
      gap: 8px;

      .action-icon {
        margin-right: 4px;
      }

      .action-btn {
        border-radius: 100px;
        padding: 6px 12px;
        font-size: 12px;

        &.role-btn {
          background: linear-gradient(135deg, #f6ad55, #ed8936);
          border: none;
          box-shadow: 0 4px 10px rgba(237, 137, 54, 0.2);

          &:hover {
            background: linear-gradient(135deg, #fbd38d, #f6ad55);
            box-shadow: 0 6px 16px rgba(237, 137, 54, 0.28);
          }
        }

        &.status-btn {
          background: linear-gradient(135deg, #ff6b6b, #f56565);
          border: none;
          box-shadow: 0 4px 10px rgba(245, 101, 101, 0.2);

          &:hover {
            background: linear-gradient(135deg, #feb2b2, #fc8181);
            box-shadow: 0 6px 16px rgba(245, 101, 101, 0.28);
          }
        }
      }
    }
  }

  .empty-state {
    text-align: center;
    padding: 60px 20px 20px;

    h3 {
      font-size: 20px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 8px;
    }

    p {
      font-size: 14px;
      color: #606266;
      margin: 0;
    }
  }
}

:deep(.admin-tag) {
  font-weight: 600;
  border-color: rgba(245, 158, 11, 0.55) !important;
  background-color: rgba(245, 158, 11, 0.12) !important;
  color: #d97706 !important;
}

.role-tag-card,
.status-tag-card {
  border-radius: 999px;
  padding: 4px 14px;
  font-size: 12px;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  border: 1px dashed rgba(64, 158, 255, 0.45);
  background-color: rgba(64, 158, 255, 0.08);
  color: #409eff;
}

.status-tag-card {
  border-color: rgba(16, 185, 129, 0.55);
  background-color: rgba(16, 185, 129, 0.12);
  color: #059669;
}

.status-tag-card.is-disabled {
  border-color: rgba(248, 113, 113, 0.55);
  background-color: rgba(248, 113, 113, 0.12);
  color: #dc2626;
}

.super-admin-tag {
  border-radius: 24px;
  height: 24px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

/* 刷新时禁用 el-tag 的入场/过渡缩放效果（仅本页这三类标签） */
:deep(.super-admin-tag.el-tag),
:deep(.role-tag-card.el-tag),
:deep(.status-tag-card.el-tag) {
  transition: none !important;
  animation: none !important;
  transform: none !important;
}

@media (max-width: 768px) {
  .user-management-page {
    padding: 20px;

    .page-header {
      padding: 20px;
      flex-direction: column;
      align-items: stretch;

      h2 {
        text-align: center;
        justify-content: center;
      }

      .header-actions {
        justify-content: center;
      }
    }

    .user-card-list {
      border-radius: 20px;
    }
  }
}

/* 弹窗样式（参考模型管理页） */
.dialog-overlay {
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

.dialog-container {
  background: #ffffff;
  border-radius: 24px;
  width: 90%;
  max-width: 480px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: dialog-scale-in 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.dialog-body {
  padding: 28px 28px 20px;
  background: #ffffff;
}

.dialog-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.dialog-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2933;
}

.dialog-close {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
  padding: 0;
  color: #9ca3af;

  &:hover {
    color: #4b5563;
  }
}

.dialog-desc {
  margin: 4px 0 20px;
  font-size: 14px;
  color: #6b7280;
}

.dialog-message {
  margin: 12px 0 24px;
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
}

.form-item {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  width: 80px;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 0;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  flex-shrink: 0;
}

.label-text {
  color: #374151;
}

.required-mark {
  color: #ef4444;
  font-weight: 500;
  font-size: 14px;
}

.input-wrapper {
  flex: 1;
}

.form-input {
  width: 100%;
  padding: 9px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  font-size: 14px;
  color: #111827;
  background: #ffffff;
  transition: all 0.2s ease;
  box-sizing: border-box;

  &:focus {
    outline: none;
    border-color: #409eff;
    box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.15);
  }

  &::placeholder {
    color: #9ca3af;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 28px 24px;
  background: transparent;
  border-top: none;
}

.dialog-btn {
  padding: 8px 22px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  background: #ffffff;
  transition: all 0.2s;
  outline: none;
  border: none;
}

.cancel-btn {
  border: 1px solid #e5e7eb;
  color: #374151;

  &:hover {
    background: #f3f4f6;
  }
}

.confirm-btn {
  border: 1px solid #409eff;
  color: #409eff;

  &:hover:not(.disabled) {
    background: #eff6ff;
  }

  &.disabled {
    opacity: 0.6;
    cursor: not-allowed;
    border-color: #93c5fd;
    color: #93c5fd;
  }
}

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
  background: #ffffff;
  border-radius: 24px;
  padding: 22px 24px 20px;
  width: 90%;
  max-width: 340px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  animation: dialog-scale-in 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.confirm-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}

.confirm-dialog-btn {
  padding: 7px 20px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  background: #ffffff;
  transition: all 0.2s;
  outline: none;
  border: none;

  &.confirm-cancel-btn {
    border: 1px solid #e5e7eb;
    color: #374151;

    &:hover {
      background: #f3f4f6;
    }
  }

  &.confirm-delete-btn {
    border: 1px solid #ef4444;
    color: #ef4444;

    &:hover {
      background: #fef2f2;
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

/* 深色模式 */
.theme-dark {
  .user-management-page {
    background-color: #1c1c1e;

    .page-header {
      background: #242426;
      box-shadow: none;

      h2 {
        color: #f5f5f7;

        .page-icon {
          color: #f5f5f7;
        }
      }

      .header-actions {
        .search-box {
          :deep(.el-input__wrapper) {
            background-color: #2c2c2e;
            border-color: #3a3a3c;
            box-shadow: none;

            .el-input__inner {
              color: #f5f5f7;
            }

            .el-input__prefix,
            .el-input__suffix {
              color: rgba(255, 255, 255, 0.55);
            }
          }
        }
      }
    }
    
    .user-card-list {
      background-color: #1c1c1e;
      border-color: #2c2c2e;

      .list-header {
        background-color: #2c2c2e;
        border-bottom-color: #3a3a3c;

        .header-col {
          color: #e5e5ea;
        }
      }

      .list-body {
        .list-row {
          border-bottom-color: #2c2c2e;

          &:hover {
            background-color: #2c2c2e;
          }

          .cell {
            color: #f5f5f7;
          }
        }
      }

      .user-info {
        .user-meta {
          .user-name {
            color: #f5f5f7;
          }

          .user-id {
            color: rgba(255, 255, 255, 0.55);
          }
        }
      }
    }

    .empty-state {
      h3 {
        color: #f5f5f7;
      }

      p {
        color: rgba(255, 255, 255, 0.65);
      }
    }
    
    :deep(.el-pagination) {
      --el-pagination-bg-color: transparent;
      --el-pagination-text-color: #f5f5f7;
      --el-pagination-button-color: #f5f5f7;
      --el-pagination-button-disabled-bg-color: transparent;
      button:disabled {
        background-color: transparent;
      }
      .el-input__wrapper {
        background-color: #2c2c2e;
        box-shadow: 0 0 0 1px #3a3a3c inset;
      }
      .el-input__inner {
        color: #f5f5f7;
      }
    }
  }

  /* 自定义弹窗深色模式 */
  .dialog-overlay {
    background-color: rgba(0, 0, 0, 0.6);

    .dialog-container {
      background: #1c1c1e;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
    }

    .dialog-body {
      background: #1c1c1e;
    }

    .dialog-title {
      color: #f5f5f7;
    }

    .dialog-desc,
    .dialog-message {
      color: rgba(255, 255, 255, 0.75);
    }

    .form-label {
      color: #e5e5ea;
    }

    .label-text {
      color: #e5e5ea;
    }

    .form-input {
      background: #2c2c2e;
      border-color: #3a3a3c;
      color: #f5f5f7;

      &::placeholder {
        color: rgba(255, 255, 255, 0.4);
      }

      &:focus {
        border-color: #4d6bfe;
        background: #2c2c2e;
      }
    }

    .dialog-footer {
      .dialog-btn {
        background: transparent;
      }

      .cancel-btn {
        border-color: #3a3a3c;
        color: #e5e5ea;

        &:hover {
          background: #2c2c2e;
        }
      }

      .confirm-btn {
        border-color: #4d6bfe;
        color: #4d6bfe;

        &:hover:not(.disabled) {
          background: rgba(77, 107, 254, 0.16);
        }

        &.disabled {
          border-color: rgba(77, 107, 254, 0.45);
          color: rgba(77, 107, 254, 0.7);
        }
      }
    }
  }

  .confirm-dialog-overlay {
    background-color: rgba(0, 0, 0, 0.6);

    .confirm-dialog {
      background: #1c1c1e;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);

      .dialog-title {
        color: #f5f5f7;
      }

      .dialog-message {
        color: rgba(255, 255, 255, 0.75);
      }

      .confirm-dialog-btn {
        background: transparent;

        &.confirm-cancel-btn {
          border-color: #3a3a3c;
          color: #e5e5ea;

          &:hover {
            background: #2c2c2e;
          }
        }

        &.confirm-delete-btn {
          border-color: #ff453a;
          color: #ff453a;

          &:hover {
            background: rgba(255, 69, 58, 0.16);
          }
        }
      }
    }
  }
}
</style>
