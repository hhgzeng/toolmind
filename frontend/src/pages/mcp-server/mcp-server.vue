<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Connection, VideoPlay, Edit, Delete, View, Tools } from '@element-plus/icons-vue'
import * as monaco from 'monaco-editor'
import { 
  createMCPServerAPI, 
  getMCPServersAPI, 
  deleteMCPServerAPI, 
  updateMCPServerAPI,
  type MCPServer, 
  type CreateMCPServerRequest, 
  type MCPServerTool,
  type MCPUserConfigUpdateRequest
} from '../../apis/mcp-server'

const servers = ref<MCPServer[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const toolsDialogVisible = ref(false)
const formLoading = ref(false)
const editingServer = ref<MCPServer | null>(null)
const selectedServerTools = ref<MCPServerTool[]>([])
const selectedServerName = ref('')

const deleteDialogVisible = ref(false)
const serverToDelete = ref<MCPServer | null>(null)
const deleteLoading = ref(false)

const configPlaceholder = `// Example JSON (sse):
// {
//     "mcpServers": {
//         "sse-server-example": {
//             "type": "sse",
//             "url": "http://localhost:3000"
//         }
//     }
// }`

const formData = ref<CreateMCPServerRequest>({
  config: ''
})

// 用户配置已迁移到统一配置中

// 表单验证
const formErrors = ref<Record<string, string>>({})

const validateForm = () => {
  formErrors.value = {}
  
  if (!formData.value.config) {
    formErrors.value.config = '请输入JSON配置'
  } else {
    try {
      const parsed = JSON.parse(formData.value.config as string)
      if (!parsed.mcpServers) {
        formErrors.value.config = '必须包含 mcpServers 字段'
      }
    } catch (e) {
      formErrors.value.config = '请输入有效的 JSON 格式'
    }
  }
  
  return Object.keys(formErrors.value).length === 0
}

const fetchServers = async () => {
  loading.value = true
  try {
    const response = await getMCPServersAPI()
    
    if (response?.data?.status_code === 200) {
      const serverList = response.data.data || []
      // 排序：官方服务器（user_id = 0）在前，其他服务器在后
      servers.value = serverList.sort((a: MCPServer, b: MCPServer) => {
        const aIsOfficial = String(a.user_id) === '0'
        const bIsOfficial = String(b.user_id) === '0'
        
        // 如果一个是官方，一个不是，官方的排在前面
        if (aIsOfficial && !bIsOfficial) return -1
        if (!aIsOfficial && bIsOfficial) return 1
        
        // 如果都是官方或都不是官方，按创建时间排序（新的在前）
        return new Date(b.create_time).getTime() - new Date(a.create_time).getTime()
      })
    } else {
      ElMessage.error(response?.data?.status_message || '获取MCP服务器列表失败')
      servers.value = []
    }
  } catch (error) {
    console.error('获取MCP服务器列表失败:', error)
    ElMessage.error('网络错误：无法获取MCP服务器列表')
    servers.value = []
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  editingServer.value = null
  dialogVisible.value = true
  formErrors.value = {}
  // 阻止背景滚动
  document.body.style.overflow = 'hidden'
  // 重置表单
  formData.value = {
    config: ''
  }
}

const handleEdit = (server: MCPServer) => {
  // 检查是否为官方服务器
  if (String(server.user_id) === '0') {
    ElMessage.warning(`${server.server_name} MCP Server 为官方所有，不能编辑`)
    return
  }
  
  editingServer.value = server
  dialogVisible.value = true
  formErrors.value = {}
  // 阻止背景滚动
  document.body.style.overflow = 'hidden'
  
  formData.value = {
    config: typeof server.config === 'object' ? JSON.stringify(server.config, null, 2) : (server.config || '{\n  "mcpServers": {\n    "bing-cn-mcp-server": {\n      "type": "sse",\n      "url": ""\n    }\n  }\n}')
  }
}

const closeDialog = () => {
  dialogVisible.value = false
  editingServer.value = null
  formErrors.value = {}
  // 恢复背景滚动
  document.body.style.overflow = 'auto'
}

// 移除加载用户配置的函数，编辑时直接使用服务器信息

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }
  
  formLoading.value = true
  try {
    let configData = {}
    if (formData.value.config && typeof formData.value.config === 'string') {
      try {
        configData = JSON.parse(formData.value.config)
      } catch (error) {
        formErrors.value.config = '配置信息格式不正确，请输入有效的 JSON 格式'
        formLoading.value = false
        return
      }
    } else {
      configData = formData.value.config || {}
    }

    if (editingServer.value) {
      const submitData = {
        server_id: editingServer.value.mcp_server_id,
        config: configData
      }
      const response = await updateMCPServerAPI(submitData)
      if (response.data.status_code === 200) {
        closeDialog()
        await fetchServers()
      } else {
        ElMessage.error(response.data.status_message || '更新失败')
      }
    } else {
      const submitData = {
        config: configData
      }
      
      const response = await createMCPServerAPI(submitData)
      if (response.data.status_code === 200) {
        closeDialog()
        await fetchServers()
      } else {
        ElMessage.error(response.data.status_message || '创建失败')
      }
    }
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  } finally {
    formLoading.value = false
  }
}

// removed updateUserConfig as it's no longer used

const handleDelete = (server: MCPServer) => {
  // 检查是否为官方服务器
  if (String(server.user_id) === '0') {
    ElMessage.warning(`${server.server_name} MCP Server 为官方所有，不能删除`)
    return
  }
  
  serverToDelete.value = server
  deleteDialogVisible.value = true
}

const confirmDelete = async () => {
  if (!serverToDelete.value) return
  
  deleteLoading.value = true
  try {
    const response = await deleteMCPServerAPI(serverToDelete.value.mcp_server_id)
    if (response.data.status_code === 200) {
      deleteDialogVisible.value = false
      await fetchServers() // 刷新列表
    } else {
      ElMessage.error(response.data.status_message || '删除失败')
    }
  } catch (error) {
    console.error('删除MCP服务器失败:', error)
    ElMessage.error('删除失败')
  } finally {
    deleteLoading.value = false
  }
}

const cancelDelete = () => {
  deleteDialogVisible.value = false
  serverToDelete.value = null
}

// 查看工具详情
const viewTools = (server: MCPServer) => {
  selectedServerTools.value = server.params || []
  selectedServerName.value = server.server_name
  toolsDialogVisible.value = true
  // 阻止背景滚动
  document.body.style.overflow = 'hidden'
}

const closeToolsDialog = () => {
  toolsDialogVisible.value = false
  // 恢复背景滚动
  document.body.style.overflow = 'auto'
}



onMounted(async () => {
  try {
    await fetchServers()
  } catch (error) {
    console.error('MCP Server 页面初始化失败:', error)
    ElMessage.error('页面初始化失败，请重试')
  }
})

const handleToggleActive = async (server: MCPServer, val: boolean) => {
  try {
    const response = await updateMCPServerAPI({
      server_id: server.mcp_server_id,
      is_active: val
    })
    if (response.data.status_code === 200) {
      // ElMessage.success('状态已切换')
    } else {
      server.is_active = !val // revert
      ElMessage.error(response.data.status_message || '状态切换失败')
    }
  } catch (e) {
    server.is_active = !val // revert
    ElMessage.error('网络错误：状态切换失败')
  }
}

// 从服务器配置中提取连接类型
const getServerType = (server: MCPServer): string => {
  try {
    if (server.config && typeof server.config === 'object') {
      const mcpServers = server.config.mcpServers || server.config
      const serverKeys = Object.keys(mcpServers)
      if (serverKeys.length > 0) {
        const firstServer = mcpServers[serverKeys[0]]
        if (firstServer && firstServer.type) {
          return firstServer.type.toUpperCase()
        }
      }
    }
  } catch (e) {
    // ignore
  }
  return 'MCP 服务'
}

onUnmounted(() => {
  // 页面卸载时恢复背景滚动，防止影响其他页面
  document.body.style.overflow = 'auto'
})

// removed saveUserConfig as it's no longer used
</script>

<template>
  <div class="mcp-server-page">
    <div class="page-header">
      <h2>
        <el-icon class="mcp-icon"><Connection /></el-icon>
        MCP 服务器
      </h2>
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        添加服务器
      </el-button>
    </div>

    <div class="server-list" v-loading="loading">
      <div class="server-table-container" v-if="servers.length > 0">
        <el-table 
          :data="servers || []" 
          style="width: 100%" 
          :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '600' }"
          row-class-name="server-table-row"
        >
          <!-- 头像和名称统一列 -->
          <el-table-column label="服务器名称" min-width="180">
            <template #default="{ row }">
              <div class="server-info-cell">
                <div class="server-avatar">
                  {{ row.server_name ? row.server_name.charAt(0).toUpperCase() : 'M' }}
                </div>
                <div class="server-title">
                  <div class="server-name">{{ row.server_name }}</div>
                  <div class="server-provider">{{ getServerType(row) }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <!-- 可用工具数量列 -->
          <el-table-column label="可用工具" min-width="250">
            <template #default="{ row }">
              <div class="tools-count">
                <el-button 
                  type="primary" 
                  :icon="Tools"
                  size="small"
                  @click="viewTools(row)"
                  :disabled="!row.params || row.params.length === 0"
                  round
                >
                  {{ row.params?.length || 0 }} 个工具
                </el-button>
              </div>
            </template>
          </el-table-column>
          
          <!-- 配置状态列 -->
          <el-table-column label="启用状态" width="120">
            <template #default="{ row }">
              <div class="config-status-align-left">
                <el-switch
                  v-model="row.is_active"
                  @change="(val) => handleToggleActive(row, val as boolean)"
                />
              </div>
            </template>
          </el-table-column>
          
          <!-- 操作列 -->
          <el-table-column label="操作" width="200" align="left">
            <template #default="{ row }">
              <div class="action-buttons-cell">
                <el-button 
                  size="small" 
                  type="primary"
                  @click.stop="handleEdit(row)"
                  title="编辑"
                  class="action-btn edit-btn"
                >
                  <el-icon><Edit /></el-icon>
                  <span>编辑</span>
                </el-button>
                <el-button 
                  size="small" 
                  type="danger" 
                  @click.stop="handleDelete(row)"
                  title="删除"
                  class="action-btn delete-btn"
                >
                  <el-icon><Delete /></el-icon>
                  <span>删除</span>
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <div v-if="servers.length === 0 && !loading" class="empty-state">
        <div class="empty-icon">
          <i class="empty-icon-symbol">📡</i>
        </div>
        <h3>暂无 MCP 服务器</h3>
        <p>添加 MCP 服务器以增强智能体的能力</p>
      </div>
    </div>

    <!-- 纯HTML创建/编辑弹窗 -->
    <Teleport to="body">
      <div v-if="dialogVisible" class="modal-overlay" @click.self="closeDialog">
        <div class="modal-dialog">
          <div class="modal-body">
            <!-- 服务器配置向导 -->
            <div class="config-wizard">


              <form @submit.prevent="handleSubmit" class="mcp-form">
                <!-- 服务器信息 -->
                  
                  <div class="form-grid">
                    <div class="form-group" style="grid-column: 1 / -1;">
                      <label for="config" style="font-size: 18px; font-weight: 600; color: #1c1c1e; margin-bottom: 20px;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <polyline points="10,9 9,9 8,9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        服务器配置 (JSON)
                      </label>
                      <div class="textarea-wrapper">
                        <textarea 
                          id="config"
                          v-model="formData.config as string" 
                          rows="10"
                          :placeholder="configPlaceholder"
                          :class="{ 'error': formErrors.config }"
                          style="font-family: monospace; font-size: 15px; line-height: 1.6;"
                        ></textarea>
                        <div class="json-indicator">
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M16 3l4 4-4 4" stroke="#909399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M8 21l-4-4 4-4" stroke="#909399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M15 14l-6-6" stroke="#909399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          </svg>
                          JSON
                        </div>
                      </div>
                      <span v-if="formErrors.config" class="error-text">{{ formErrors.config }}</span>
                    </div>
                  </div>
              </form>
            </div>
          </div>
          
          <div class="modal-footer">
            <button type="button" @click="closeDialog" class="dialog-btn cancel-btn">
              取消
            </button>
            <button 
              type="button" 
              @click="handleSubmit"
              :disabled="formLoading"
              class="dialog-btn save-btn"
            >
              <span v-if="formLoading" class="loading-spinner" style="border-top-color: #007aff;"></span>
              {{ editingServer ? '保存' : '添加' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 纯HTML工具详情弹窗 -->
    <Teleport to="body">
      <div v-if="toolsDialogVisible" class="modal-overlay" @click.self="closeToolsDialog">
        <div class="modal-dialog tools-dialog">
          <div class="modal-header">
            <h3>{{ selectedServerName }} - 可用工具</h3>
            <button class="close-btn" @click="closeToolsDialog">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
          
          <div class="modal-body tools-content">
            <div v-if="selectedServerTools.length === 0" class="no-tools">
              <div class="empty-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.77 3.77z" stroke="#c0c4cc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="empty-text">
                <h3>暂无可用工具</h3>
                <p>该服务器尚未提供任何工具，或者服务器连接异常</p>
              </div>
            </div>
            <div v-else class="tools-overview">
              <!-- 工具统计 -->
              <div class="tools-stats">
                <div class="stat-card">
                  <div class="stat-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.77 3.77z" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <div class="stat-info">
                    <span class="stat-number">{{ selectedServerTools.length }}</span>
                    <span class="stat-label">可用工具</span>
                  </div>
                </div>
              </div>

              <!-- 工具列表 -->
              <div class="tools-list">
                <div 
                  v-for="(tool, index) in selectedServerTools" 
                  :key="index"
                  class="tool-card"
                >
                  <div class="tool-header">
                    <div class="tool-info">
                      <div class="tool-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.77 3.77z" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                      </div>
                      <div class="tool-text">
                        <h4 class="tool-name">{{ tool.name }}</h4>
                        <span class="tool-tag">Function</span>
                      </div>
                    </div>
                  </div>
                  
                  <div class="tool-description">
                    <p>{{ tool.description || '暂无描述' }}</p>
                  </div>
                  
                  <div class="tool-schema" v-if="tool.input_schema">
                    <div class="schema-header">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <polyline points="16 18 22 12 16 6" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <polyline points="8 6 2 12 8 18" stroke="#409eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      <span>参数结构</span>
                    </div>
                    
                    <div class="schema-content">
                      <div class="schema-meta">
                        <div class="meta-item" v-if="tool.input_schema.type">
                          <span class="meta-label">类型:</span>
                          <span class="meta-value type">{{ tool.input_schema.type }}</span>
                        </div>
                        <div class="meta-item" v-if="tool.input_schema.title">
                          <span class="meta-label">标题:</span>
                          <span class="meta-value">{{ tool.input_schema.title }}</span>
                        </div>
                      </div>
                      
                      <div v-if="tool.input_schema.required?.length" class="required-section">
                        <div class="section-title">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="#f56c6c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M9 12l2 2 4-4" stroke="#f56c6c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          </svg>
                          <span>必填参数</span>
                        </div>
                        <div class="required-params">
                          <span 
                            v-for="param in tool.input_schema.required" 
                            :key="param"
                            class="required-param"
                          >
                            {{ param }}
                          </span>
                        </div>
                      </div>
                      
                      <div v-if="tool.input_schema.properties" class="properties-section">
                        <div class="section-title">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" stroke="#67c23a" stroke-width="2"/>
                            <circle cx="8.5" cy="8.5" r="1.5" stroke="#67c23a" stroke-width="2"/>
                            <path d="M21 15l-5-5L5 21l5-5z" stroke="#67c23a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          </svg>
                          <span>参数详情</span>
                        </div>
                        <div class="properties-grid">
                          <div 
                            v-for="(prop, propName) in tool.input_schema.properties" 
                            :key="propName"
                            class="property-card"
                          >
                            <div class="property-header">
                              <span class="property-name">{{ propName }}</span>
                              <span class="property-type">{{ prop.type }}</span>
                            </div>
                            <div class="property-body">
                              <p v-if="prop.description" class="property-desc">{{ prop.description }}</p>
                              <div v-if="prop.default !== undefined" class="property-default">
                                <span class="default-label">默认值:</span>
                                <code class="default-value">{{ prop.default }}</code>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 删除确认对话框 -->
    <Teleport to="body">
      <transition name="fade">
        <div v-if="deleteDialogVisible" class="confirm-dialog-overlay" @click="cancelDelete">
          <div class="confirm-dialog" @click.stop>
            <h3 class="dialog-title">确认删除服务器</h3>
            <p class="dialog-message" v-if="serverToDelete">确定要删除 MCP 服务器 <strong>"{{ serverToDelete.server_name }}"</strong> 吗？</p>
            <div class="dialog-footer">
              <button class="dialog-btn cancel-btn" @click="cancelDelete" :disabled="deleteLoading">取消</button>
              <button class="dialog-btn delete-btn" @click="confirmDelete" :disabled="deleteLoading">{{ deleteLoading ? '删除中...' : '删除' }}</button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style lang="scss">
// 弹窗样式 - 移除scoped，因为使用了Teleport
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999 !important;
  pointer-events: auto;
  overflow: hidden;
}

.modal-dialog {
  background: white;
  border-radius: 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 8px 32px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  
  &.tools-dialog {
    max-width: 800px;
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  background: transparent;
  
  h3 {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    color: #1c1c1e;
  }
  
  .close-btn {
    width: 32px;
    height: 32px;
    border: none;
    background: rgba(0, 0, 0, 0.05);
    color: #8e8e93;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.2s ease;
    
    &:hover {
      background: rgba(0, 0, 0, 0.1);
      color: #1c1c1e;
    }
  }
}

.modal-body {
  padding: 36px 36px 12px;
  overflow-y: auto;
  flex: 1;
  background: #fafbfc;
}

.modal-footer {
  padding: 0 36px 36px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: #fafbfc;

  .dialog-btn {
    padding: 8px 32px;
    border-radius: 40px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    background: white;
    transition: all 0.2s;
    outline: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;

    &.cancel-btn {
      border: 1px solid #e5e5e5;
      color: #333;

      &:hover {
        background: #f5f5f5;
      }
    }

    &.save-btn {
      border: 1px solid #007aff;
      color: #007aff;

      &:hover {
        background: #ecf5ff;
      }
      
      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
    }
  }
}

// 表单样式


.mcp-form {
  .form-section {
    background: rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.6);
    border-radius: 24px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  }
  
  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    
    @media (max-width: 768px) {
      grid-template-columns: 1fr;
    }
  }
  
  .form-group {
    margin-bottom: 24px;
    
    label {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 12px;
      font-size: 14px;
      
      &[for$="_name"]::after,
      &[for$="_url"]::after,
      &[for$="_type"]::after {
        content: " *";
        color: #f56c6c;
        margin-left: 4px;
      }
      
      svg {
        opacity: 0.7;
      }
    }
    
    input, select, textarea {
      width: 100%;
      padding: 12px 16px;
      border: 1px solid #dcdfe6;
      border-radius: 6px;
      font-size: 14px;
      transition: all 0.2s ease;
      background: white;
      box-sizing: border-box;
      font-family: inherit;
      
      &:focus {
        outline: none;
        border-color: #409eff;
        box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
      }
      
      &:hover {
        border-color: #c0c4cc;
      }
      
      &.error {
        border-color: #f56c6c;
        background-color: #fef0f0;
      }
      
      &::placeholder {
        color: #c0c4cc;
        font-size: 13px;
      }
      
      &:disabled,
      &[readonly] {
        background-color: #f5f7fa;
        border-color: #e4e7ed;
        color: #c0c4cc;
        cursor: not-allowed;
        
        &::placeholder {
          color: #c0c4cc;
        }
      }
    }
    
    textarea {
      resize: vertical;
      min-height: 100px;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      line-height: 1.6;
      font-size: 13px;
      border-radius: 24px;
      padding: 20px 24px;
      scrollbar-width: none; /* Firefox */
      -ms-overflow-style: none; /* IE and Edge */
      
      &::-webkit-scrollbar {
        display: none; /* Chrome, Safari and Opera */
      }
      
      &::placeholder {
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 14px;
        line-height: 1.8;
        color: #b0b4b8;
        white-space: pre;
        opacity: 1;
      }
    }
    
    select {
      cursor: pointer;
      appearance: none;
      background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6,9 12,15 18,9'%3e%3c/polyline%3e%3c/svg%3e");
      background-repeat: no-repeat;
      background-position: right 12px center;
      background-size: 16px;
      padding-right: 40px;
    }
    
    .error-text {
      display: block;
      color: #f56c6c;
      font-size: 12px;
      margin-top: 6px;
      font-weight: 500;
    }
    
    .textarea-wrapper {
      position: relative;
      
      .json-indicator {
        position: absolute;
        top: 16px;
        right: 20px;
        display: flex;
        align-items: center;
        gap: 4px;
        background: rgba(255, 255, 255, 0.9);
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        color: #909399;
        font-weight: 500;
        border: 1px solid #e4e7ed;
        backdrop-filter: blur(4px);
      }
    }
  }
}

// 按钮样式
.btn {
  padding: 12px 24px;
  border-radius: 24px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 80px;
  line-height: 1;
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  &.btn-cancel {
    background: rgba(0, 0, 0, 0.05);
    border-color: transparent;
    color: #1c1c1e;
    
    &:hover:not(:disabled) {
      background-color: rgba(0, 0, 0, 0.1);
    }
  }
  
  &.btn-primary {
    background: #007aff;
    border-color: #007aff;
    color: #fff;
    box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
    
    &:hover:not(:disabled) {
      background: #006ae6;
      border-color: #006ae6;
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(0, 122, 255, 0.4);
    }
    
    &:active:not(:disabled) {
      background: #0056cc;
      transform: translateY(1px);
      box-shadow: 0 2px 8px rgba(0, 122, 255, 0.3);
    }
  }
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

// 页面样式已移至底部scoped样式中，避免重复

// 工具详情样式
.tools-content {
  background: #fafbfc;
  
  .no-tools {
    text-align: center;
    padding: 80px 40px;
    
    .empty-icon {
      margin-bottom: 20px;
      opacity: 0.6;
    }
    
    .empty-text {
      h3 {
        margin: 0 0 8px 0;
        font-size: 18px;
        font-weight: 600;
        color: #909399;
      }
      
      p {
        color: #c0c4cc;
        font-size: 14px;
        margin: 0;
        line-height: 1.5;
      }
    }
  }
  
  .tools-overview {
    .tools-stats {
      margin-bottom: 24px;
      
      .stat-card {
        background: white;
        border: 1px solid #ebeef5;
        border-radius: 20px;
        padding: 20px;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        
        .stat-icon {
          width: 48px;
          height: 48px;
          background: #f0f7ff;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .stat-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
          
          .stat-number {
            font-size: 24px;
            font-weight: 700;
            color: #409eff;
            line-height: 1;
          }
          
          .stat-label {
            font-size: 14px;
            color: #606266;
            font-weight: 500;
          }
        }
      }
    }
    
    .tools-list {
      .tool-card {
        background: white;
        border: 1px solid #ebeef5;
        border-radius: 20px;
        padding: 24px 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease;
        
        &:hover {
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
          transform: translateY(-2px);
        }
        
        .tool-header {
          margin-bottom: 16px;
          
          .tool-info {
            display: flex;
            align-items: center;
            gap: 12px;
            
            .tool-icon {
              width: 40px;
              height: 40px;
              background: #f0f7ff;
              border-radius: 10px;
              display: flex;
              align-items: center;
              justify-content: center;
              flex-shrink: 0;
            }
            
            .tool-text {
              .tool-name {
                margin: 0 0 4px 0;
                font-size: 18px;
                font-weight: 600;
                color: #303133;
              }
              
              .tool-tag {
                background: #ecf5ff;
                color: #409eff;
                border: 1px solid #b3d8ff;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
                display: inline-block;
              }
            }
          }
        }
        
        .tool-description {
          color: #606266;
          line-height: 1.6;
          margin-bottom: 20px;
          font-size: 14px;
          
          p {
            margin: 0;
          }
        }
        
        .tool-schema {
          background: #f8f9fa;
          border: 1px solid #ebeef5;
          border-radius: 16px;
          padding: 20px;
          
          .schema-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid #e4e7ed;
            font-weight: 600;
            color: #303133;
            font-size: 14px;
          }
          
          .schema-content {
            .schema-meta {
              margin-bottom: 16px;
              
              .meta-item {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
                
                .meta-label {
                  font-weight: 500;
                  color: #606266;
                  min-width: 60px;
                }
                
                .meta-value {
                  color: #303133;
                  
                  &.type {
                    background: #f0f2f5;
                    padding: 4px 10px;
                    border-radius: 100px;
                    font-size: 13px;
                    font-weight: 500;
                  }
                }
              }
            }
            
            .required-section {
              margin-bottom: 16px;
              
              .section-title {
                display: flex;
                align-items: center;
                gap: 6px;
                margin-bottom: 12px;
                font-weight: 600;
                color: #f56c6c;
                font-size: 14px;
              }
              
              .required-params {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                
                .required-param {
                  background: #fef0f0;
                  color: #f56c6c;
                  border: 1px solid #fbc4c4;
                  padding: 4px 12px;
                  border-radius: 100px;
                  font-size: 12px;
                  font-weight: 500;
                }
              }
            }
            
            .properties-section {
              .section-title {
                display: flex;
                align-items: center;
                gap: 6px;
                margin-bottom: 12px;
                font-weight: 600;
                color: #67c23a;
                font-size: 14px;
              }
              
              .properties-grid {
                display: grid;
                gap: 12px;
                
                .property-card {
                  background: white;
                  border: 1px solid #ebeef5;
                  border-radius: 16px;
                  padding: 16px;
                  
                  .property-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                    
                    .property-name {
                      font-weight: 600;
                      color: #303133;
                      font-size: 14px;
                    }
                    
                    .property-type {
                      background: #ecf5ff;
                      color: #409eff;
                      padding: 4px 12px;
                      border-radius: 100px;
                      font-size: 12px;
                      font-weight: 500;
                    }
                  }
                  
                  .property-body {
                    .property-desc {
                      color: #606266;
                      font-size: 13px;
                      line-height: 1.5;
                      margin: 0 0 8px 0;
                    }
                    
                    .property-default {
                      display: flex;
                      align-items: center;
                      gap: 6px;
                      
                      .default-label {
                        font-size: 12px;
                        color: #909399;
                      }
                      
                      .default-value {
                        background: #f4f4f5;
                        color: #303133;
                        padding: 4px 10px;
                        border-radius: 100px;
                        font-size: 12px;
                        font-family: 'Monaco', 'Menlo', monospace;
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}

.mcp-server-page {
  padding: 30px;
  min-height: calc(100vh - 60px);
  background-color: #ffffff;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
    background: linear-gradient(to right, #ffffff, #f8fafc);
    padding: 28px;
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
      background: linear-gradient(90deg, #409eff, #3a7be2);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      
      .mcp-icon {
        font-size: 30px;
        width: 32px;
        height: 32px;
        color: #409eff;
      }
    }
    
    .el-button {
      border-radius: 100px;
      padding: 12px 20px;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.3s;
      background: linear-gradient(135deg, #409eff 0%, #3a7be2 100%);
      border: none;
      box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
      
      &:hover {
        transform: translateY(-2px);
        background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
        box-shadow: 0 6px 16px rgba(64, 158, 255, 0.3);
      }
    }
  }
  
  .server-list {
    min-height: 300px;
    position: relative;
    
    .server-table-container {
      /* 与 model.vue 统一的表格样式 */
      border-radius: 24px;
      overflow: hidden;
      
      .el-table {
        border-radius: 24px !important;
        overflow: hidden !important;
        border: 1px solid #ebeef5 !important;
        
        &::before,
        &::after {
          display: none !important;
        }
        
        th.el-table__cell {
          background-color: #f8fafc !important;
          color: #64748b;
          font-weight: 600;
          border-bottom: 2px solid #e2e8f0;
          padding: 12px 16px;
        }
        
        td.el-table__cell {
          border-bottom: 1px solid #f1f5f9;
          padding: 16px;
        }
      }
      
      .server-info-cell {
        display: flex;
        align-items: center;
        
        .server-avatar {
          width: 44px;
          height: 44px;
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 16px;
          flex-shrink: 0;
          color: white;
          font-weight: bold;
          font-size: 20px;
          background: linear-gradient(135deg, #409eff 0%, #3a7be2 100%);
          box-shadow: 0 4px 10px rgba(64, 158, 255, 0.2);
        }
        
        .server-title {
          .server-name {
            font-size: 15px;
            font-weight: 600;
            color: #303133;
            margin-bottom: 4px;
          }
          .server-provider {
            font-size: 13px;
            color: #909399;
          }
        }
      }
      
      .tools-count {
        .el-button {
          font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
          color: #409eff;
          background-color: rgba(64, 158, 255, 0.1);
          padding: 4px 12px;
          border-radius: 100px;
          font-size: 13px;
          border: 1px dashed rgba(64, 158, 255, 0.3);
          
          &:hover {
            background-color: rgba(64, 158, 255, 0.15);
            border-color: rgba(64, 158, 255, 0.5);
          }
        }
      }
      
      .config-status-align-left {
        display: flex;
        justify-content: flex-start;
        align-items: center;
      }
      
      .action-buttons-cell {
        display: flex;
        justify-content: flex-start;
        gap: 8px;
        
        .action-btn {
          border-radius: 100px;
          transition: all 0.3s;
        }
      }
    }
    
    .empty-state {
      text-align: center;
      padding: 80px 20px;

      h3 {
        font-size: 22px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 16px;
      }

      p {
        font-size: 16px;
        color: #606266;
        margin-bottom: 32px;
        max-width: 500px;
        margin-left: auto;
        margin-right: auto;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .mcp-server-page {
    padding: 16px;
    
    .page-header {
      flex-direction: column;
      gap: 16px;
      align-items: stretch;
    }
  }
  
  // 配置对话框样式
  .config-dialog {
    max-width: 600px;
    
    .config-info {
      margin-bottom: 24px;
      
      .info-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 1px solid #bae6fd;
        border-radius: 12px;
        padding: 16px;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        
        .info-icon {
          flex-shrink: 0;
          width: 40px;
          height: 40px;
          background: rgba(64, 158, 255, 0.1);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .info-text {
          flex: 1;
          
          h4 {
            margin: 0 0 6px 0;
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
          }
          
          p {
            margin: 0;
            font-size: 14px;
            color: #64748b;
            line-height: 1.6;
          }
        }
      }
    }
    
    .form-section .form-group textarea {
      min-height: 240px;
    }
    
    .json-indicator {
      span {
        color: #e67e22;
        font-weight: 500;
      }
    }
  }
}

// 配置对话框样式改进
.config-dialog {
  max-width: 800px;
  
  .modal-header h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .config-server-name {
      font-weight: 700;
      color: #1e293b;
    }
    
    .config-title {
      color: #64748b;
      font-weight: 500;
    }
    
    &::before {
      content: '';
      display: inline-block;
      width: 4px;
      height: 18px;
      background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
      border-radius: 2px;
      margin-right: 8px;
    }
  }
  
  .config-info {
    margin-bottom: 20px;
    
    .info-card {
      background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
      border: 1px solid #bae6fd;
      border-radius: 12px;
      padding: 16px;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      
      .info-icon {
        flex-shrink: 0;
        width: 40px;
        height: 40px;
        background: rgba(59, 130, 246, 0.1);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .info-text {
        flex: 1;
        
        h4 {
          margin: 0 0 6px 0;
          font-size: 16px;
          font-weight: 600;
          color: #1e293b;
        }
        
        p {
          margin: 0;
          font-size: 14px;
          color: #64748b;
          line-height: 1.6;
        }
      }
    }
  }
  
  // 编辑器工具栏
  .editor-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 12px;
    
    .toolbar-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      border: none;
      background: #f1f5f9;
      color: #475569;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      
      &:hover {
        background: #e2e8f0;
        color: #334155;
      }
      
      svg {
        width: 16px;
        height: 16px;
      }
    }
    
    .validation-status {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      padding: 6px 12px;
      border-radius: 6px;
      
      &.is-valid {
        background: rgba(34, 197, 94, 0.1);
        color: #16a34a;
      }
      
      &.is-invalid {
        background: rgba(239, 68, 68, 0.1);
        color: #dc2626;
      }
    }
  }
  
  // 编辑器容器
  .editor-container {
    height: 300px;
    border: 1px solid #e2e8f0;
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
    overflow: hidden;
    
    .json-editor {
      height: 100%;
      width: 100%;
    }
  }
  
  // 帮助说明
  .config-help {
    margin-top: 24px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    overflow: hidden;
    
    .help-title {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
      padding: 12px 16px;
      background: #f1f5f9;
      color: #1e293b;
      font-size: 14px;
      font-weight: 600;
      border-bottom: 1px solid #e2e8f0;
    }
    
    .help-content {
      padding: 16px;
      
      .help-item {
        margin-bottom: 16px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        h5 {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #334155;
          font-weight: 600;
        }
        
        p {
          margin: 0 0 8px 0;
          font-size: 13px;
          color: #475569;
          line-height: 1.5;
        }
        
        ul {
          margin: 0;
          padding-left: 20px;
          
          li {
            font-size: 13px;
            color: #475569;
            margin-bottom: 4px;
            
            code {
              background: #e2e8f0;
              padding: 2px 4px;
              border-radius: 4px;
              color: #334155;
              font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
              font-size: 12px;
            }
          }
        }
        
        .shortcut-list {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 8px;
          list-style-type: none;
          padding: 0;
          
          li {
            display: flex;
            align-items: center;
            gap: 8px;
            
            .key {
              background: #e2e8f0;
              padding: 2px 6px;
              border-radius: 4px;
              color: #475569;
              font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
              font-size: 12px;
              border: 1px solid #cbd5e1;
              box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
            }
          }
        }
      }
    }
  }
  
  .modal-footer {
    .btn-primary {
      &:disabled {
        opacity: 0.7;
        cursor: not-allowed;
      }
    }
  }
}

@media (max-width: 768px) {
  .config-dialog {
    .editor-container {
      height: 250px;
    }
    
    .config-help {
      .help-content {
        .help-item {
          .shortcut-list {
            grid-template-columns: 1fr;
          }
        }
      }
    }
  }
}

/* 空状态样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  margin: 20px auto;
  max-width: 600px;
  
  .empty-icon {
    width: 120px;
    height: 120px;
    display: flex;
    justify-content: center;
    align-items: center;
    background: rgba(64, 158, 255, 0.1);
    border-radius: 50%;
    margin-bottom: 20px;
    
    .empty-icon-symbol {
      font-size: 60px;
    }
  }
  
  h3 {
    font-size: 20px;
    color: #303133;
    margin: 0 0 16px;
  }
  
  p {
    margin: 0 0 20px;
    font-size: 16px;
    color: #909399;
    max-width: 300px;
  }
  

}

/* 确认对话框样式 */
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

<!-- 页面本身的样式使用scoped -->
<style lang="scss" scoped>
// 页面样式已移至底部scoped样式中，避免重复
</style>