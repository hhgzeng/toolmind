<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Connection, Cpu, Search, Refresh, Calendar, ChatDotRound, RefreshRight, Star, Link, Timer } from '@element-plus/icons-vue'
import { 
  getVisibleLLMsAPI, 
  createLLMAPI, 
  updateLLMAPI,
  deleteLLMAPI,
  getLingseekConfigAPI,
  updateLingseekConfigAPI,
  type LLMResponse,
  type CreateLLMRequest,
  type UpdateLLMRequest,
  type LingseekModelConfig
} from '../../apis/llm'

const router = useRouter()

// 响应式数据
const models = ref<LLMResponse[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const llmTypes = ref<string[]>(['LLM', 'Embedding', 'Rerank'])

// Lingseek 配置数据
const lingseekConfig = ref<LingseekModelConfig>({
  conversation_model_id: null,
  tool_call_model_id: null,
  reasoning_model_id: null
})
const savingLingseek = ref(false)

// 创建对话框控制
const createDialogVisible = ref(false)
const createLoading = ref(false)

// 删除确认对话框控制
const deleteDialogVisible = ref(false)
const deleteLoading = ref(false)
const modelToDelete = ref<LLMResponse | null>(null)

// 表单相关
const createForm = ref<CreateLLMRequest>({
  model: '',
  api_key: '',
  base_url: '',
  provider: '',
  llm_type: 'LLM'
})

// 编辑相关
const editDialogVisible = ref(false)
const editLoading = ref(false)
const editForm = ref<UpdateLLMRequest>({
  llm_id: '',
  model: '',
  api_key: '',
  base_url: '',
  provider: '',
  llm_type: 'LLM'
})

// 获取模型列表
const fetchModels = async () => {
  loading.value = true
  try {
    const response = await getVisibleLLMsAPI()
    
    if (response.data.status_code === 200) {
      const data = response.data.data || {}
      const allModels: LLMResponse[] = []
      
      Object.values(data).forEach((typeModels: any) => {
        if (Array.isArray(typeModels)) {
          allModels.push(...typeModels)
        }
      })
      
      models.value = allModels
    } else {
      ElMessage.error(response.data.status_message || '获取模型列表失败')
    }
  } catch (error) {
    ElMessage.error('获取模型列表失败')
  } finally {
    loading.value = false
  }

  try {
    const configRes = await getLingseekConfigAPI()
    if (configRes.data.status_code === 200) {
      if (Object.keys(configRes.data.data).length > 0) {
        lingseekConfig.value = configRes.data.data
      }
    }
  } catch (error) {
    console.error('获取 Lingseek 配置失败', error)
  }
}

// 保存 Lingseek 配置
const saveLingseekConfig = async () => {
  savingLingseek.value = true
  try {
    const res = await updateLingseekConfigAPI(lingseekConfig.value)
    if (res.data.status_code === 200) {
      if (res.data.data && Object.keys(res.data.data).length > 0) {
        lingseekConfig.value = res.data.data
      }
    }
  } catch (error) {
    ElMessage.error('保存 Lingseek 配置失败')
  } finally {
    savingLingseek.value = false
  }
}

// 模型过滤（搜索功能）
const filteredModels = computed(() => {
  if (!searchKeyword.value) {
    return models.value
  }
  
  const keyword = searchKeyword.value.toLowerCase()
  return models.value.filter(model => {
    return (
      (model.model && model.model.toLowerCase().includes(keyword)) ||
      (model.provider && model.provider.toLowerCase().includes(keyword))
    )
  })
})

// 清空搜索
const clearSearch = () => {
  searchKeyword.value = ''
}

// 打开创建对话框
const openCreateDialog = () => {
  createDialogVisible.value = true
  // 重置表单
  Object.assign(createForm.value, {
    model: '',
    api_key: '',
    base_url: '',
    provider: '',
    llm_type: 'LLM'
  })
}

// 创建模型
const handleCreate = async () => {
  // 检查必填字段
  if (!createForm.value.model || !createForm.value.api_key || !createForm.value.base_url || !createForm.value.provider || !createForm.value.llm_type) {
    ElMessage.error('请填写所有必填字段')
    return
  }
  
  createLoading.value = true
  try {
    const response = await createLLMAPI(createForm.value)
    
    if (response.data.status_code === 200) {
      createDialogVisible.value = false
      fetchModels()
    } else {
      ElMessage.error('创建失败: ' + (response.data.status_message || '未知错误'))
    }
  } catch (error) {
    ElMessage.error('创建失败，请检查输入并稍后重试')
  } finally {
    createLoading.value = false
  }
}

// 打开编辑模型对话框
const openEditDialog = (model: LLMResponse) => {
  editDialogVisible.value = true
  Object.assign(editForm.value, {
    llm_id: model.llm_id,
    model: model.model || '',
    api_key: '', // 不回显原有 API 密钥
    base_url: model.base_url || '',
    provider: model.provider || '',
    llm_type: model.llm_type || 'LLM'
  })
}

// 编辑模型
const handleEdit = async () => {
  if (!editForm.value.model || !editForm.value.base_url || !editForm.value.provider) {
    ElMessage.error('请填写所有必填字段')
    return
  }
  
  editLoading.value = true
  try {
    const response = await updateLLMAPI(editForm.value)
    
    if (response.data.status_code === 200) {
      editDialogVisible.value = false
      fetchModels()
    } else {
      ElMessage.error('修改失败: ' + (response.data.status_message || '未知错误'))
    }
  } catch (error) {
    ElMessage.error('修改失败，请检查输入并稍后重试')
  } finally {
    editLoading.value = false
  }
}

// 删除模型
const deleteModel = async (model: LLMResponse) => {
  // 显示删除确认对话框
  modelToDelete.value = model
  deleteDialogVisible.value = true
}

// 确认删除模型
const confirmDelete = async () => {
  if (!modelToDelete.value) return
  
  deleteLoading.value = true
  try {
    const response = await deleteLLMAPI({ llm_id: modelToDelete.value.llm_id })
    
    if (response.data.status_code === 200) {
      deleteDialogVisible.value = false
      fetchModels()
    } else {
      ElMessage.error('删除失败: ' + (response.data.status_message || '未知错误'))
    }
  } catch (err) {
    ElMessage.error('删除失败，请稍后重试')
  } finally {
    deleteLoading.value = false
  }
}

// 取消删除
const cancelDelete = () => {
  deleteDialogVisible.value = false
  modelToDelete.value = null
}



// 测试模型连接
const testModel = async (model: LLMResponse) => {
  ElMessage.info(`正在测试 ${model.model} 连接...`)
  // 这里可以添加实际的测试逻辑
  setTimeout(() => {
  }, 2000)
}

// 获取提供商颜色
const getProviderColor = (provider: string) => {
  const colors: Record<string, string> = {
    'OpenAI': 'primary',
    'Anthropic': 'success',
    '阿里云': 'warning',
    '百度': 'info',
    'Google': 'danger'
  }
  return colors[provider] || 'info'
}



// 截断URL函数
const truncateUrl = (url: string, maxLength: number): string => {
  if (!url) return '';
  if (url.length <= maxLength) return url;
  
  const protocol = url.includes('://') ? url.split('://')[0] + '://' : '';
  const domainPath = url.replace(protocol, '');
  
  // 如果协议+3个点+最后15个字符超过了最大长度，就只显示开头和结尾
  if (protocol.length + 3 + 15 >= maxLength) {
    const start = protocol + domainPath.substring(0, Math.floor((maxLength - protocol.length - 3) / 2));
    const end = domainPath.substring(domainPath.length - Math.floor((maxLength - protocol.length - 3) / 2));
    return start + '...' + end;
  }
  
  // 否则显示协议+域名开头+...+路径结尾
  const visibleLength = maxLength - protocol.length - 3;
  const start = domainPath.substring(0, Math.floor(visibleLength / 2));
  const end = domainPath.substring(domainPath.length - Math.floor(visibleLength / 2));
  
  return protocol + start + '...' + end;
};

onMounted(() => {
  fetchModels()
})
</script>

<template>
  <div class="model-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>
        <el-icon class="model-icon"><Cpu /></el-icon>
        模型管理
      </h2>
      <div class="header-actions">
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索模型名称或提供商..."
            :prefix-icon="Search"
            clearable
            @clear="clearSearch"
            style="width: 300px"
          />
        </div>
        
        <div class="action-buttons">

          <el-button 
            type="primary" 
            :icon="Plus"
            @click="openCreateDialog"
            class="add-btn"
          >
            添加模型
          </el-button>
        </div>
      </div>
    </div>

    <!-- 模型列表 -->
    <div class="model-list" v-loading="loading">
      <!-- 模型列表 (表格视图) -->
      <div class="model-table-container" v-if="filteredModels.length > 0">
        <el-table 
          :data="filteredModels" 
          style="width: 100%" 
          :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '600' }"
          row-class-name="model-table-row"
        >
          <!-- 模型信息列 -->
          <el-table-column label="模型" min-width="180">
            <template #default="{ row }">
              <div class="model-info-cell">
                <div class="model-avatar" :class="row.llm_type.toLowerCase()">
                  <span v-if="row.provider === 'OpenAI'" class="provider-icon">O</span>
                  <span v-else-if="row.provider === 'Anthropic'" class="provider-icon">A</span>
                  <span v-else-if="row.provider === 'Google'" class="provider-icon">G</span>
                  <span v-else class="provider-icon">{{ row.provider[0] }}</span>
                </div>
                <div class="model-title">
                  <div class="model-name">{{ row.model }}</div>
                  <div class="model-provider">{{ row.provider }}</div>
                </div>
              </div>
            </template>
          </el-table-column>



          <!-- 基础 URL 列 -->
          <el-table-column label="基础 URL" min-width="250">
            <template #default="{ row }">
              <div class="url-value">{{ truncateUrl(row.base_url, 38) }}</div>
            </template>
          </el-table-column>

          <!-- 操作列 -->
          <el-table-column label="操作" width="200" align="left">
            <template #default="{ row }">
              <div class="action-buttons-cell">
                <el-button 
                  size="small" 
                  type="primary"
                  @click.stop="openEditDialog(row)"
                  title="编辑模型"
                  class="action-btn edit-btn"
                >
                  <el-icon><Edit /></el-icon>
                  <span>编辑</span>
                </el-button>
                <el-button 
                  size="small" 
                  type="danger"
                  @click.stop="deleteModel(row)"
                  title="删除模型"
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
      
      <!-- 空状态 -->
      <div v-else-if="!loading" class="empty-state">
        <div class="empty-icon">
          <span class="empty-emoji">🤖</span>
        </div>
        <h3>🎉 暂无模型</h3>
        <p>🌟 点击下方按钮创建您的第一个AI模型吧！</p>
        <el-button 
          type="primary" 
          :icon="Plus"
          @click="openCreateDialog"
          size="large"
        >
          🚀 立即创建
        </el-button>
      </div>
    </div>

    <!-- Lingseek 引擎配置区域 -->
    <div class="lingseek-config-section">
      <div class="section-title">
        <h3>🚀 Lingseek 核心引擎配置</h3>
        <p>为 Lingseek 的不同功能组件配置专属的 AI 模型</p>
      </div>
      
      <div class="config-grid">
        <div class="config-card">
          <div class="config-icon"><el-icon><ChatDotRound /></el-icon></div>
          <div class="config-info">
            <h4>对话与任务生成模型</h4>
            <p>负责理解用户意图并规划任务执行路径</p>
          </div>
          <el-select 
            v-model="lingseekConfig.conversation_model_id" 
            placeholder="请选择会话模型" 
            class="model-select"
            clearable
            @change="saveLingseekConfig"
          >
            <el-option
              v-for="m in models"
              :key="m.llm_id"
              :label="m.model + ' (' + m.provider + ')'"
              :value="m.llm_id"
            />
          </el-select>
        </div>
        
        <div class="config-card">
          <div class="config-icon"><el-icon><Connection /></el-icon></div>
          <div class="config-info">
            <h4>工具调用模型</h4>
            <p>负责执行 MCP 协议和外部工具调用</p>
          </div>
          <el-select 
            v-model="lingseekConfig.tool_call_model_id" 
            placeholder="请选择工具模型" 
            class="model-select"
            clearable
            @change="saveLingseekConfig"
          >
            <el-option
              v-for="m in models"
              :key="m.llm_id"
              :label="m.model + ' (' + m.provider + ')'"
              :value="m.llm_id"
            />
          </el-select>
        </div>
        
        <div class="config-card">
          <div class="config-icon"><el-icon><Cpu /></el-icon></div>
          <div class="config-info">
            <h4>结果推理与评估模型</h4>
            <p>对任务执行的最终结果进行自我验证和评估</p>
          </div>
          <el-select 
            v-model="lingseekConfig.reasoning_model_id" 
            placeholder="请选择评估模型" 
            class="model-select"
            clearable
            @change="saveLingseekConfig"
          >
            <el-option
              v-for="m in models.filter(m => m.llm_type === 'LLM' || m.llm_type === 'Rerank')"
              :key="m.llm_id"
              :label="m.model + ' (' + m.provider + ')'"
              :value="m.llm_id"
            />
          </el-select>
        </div>
      </div>

    </div>

    <!-- 创建模型对话框 -->
    <Teleport to="body">
      <transition name="fade">
        <div v-if="createDialogVisible" class="dialog-overlay" @click="createDialogVisible = false">
          <div class="dialog-container" @click.stop>
            <!-- 对话框主体 -->
            <div class="dialog-body">
              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">模型名称</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    v-model="createForm.model"
                    type="text" 
                    placeholder="例如：gpt-4, claude-3.5-sonnet"
                    maxlength="50"
                    class="form-input"
                  />
                </div>
              </div>
              
              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">提供商</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    v-model="createForm.provider"
                    type="text" 
                    placeholder="例如：OpenAI, Anthropic, 阿里云"
                    maxlength="50"
                    class="form-input"
                  />
                </div>
              </div>
              
              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">基础URL</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    v-model="createForm.base_url"
                    type="text" 
                    placeholder="例如：https://api.openai.com/v1"
                    maxlength="200"
                    class="form-input"
                  />
                </div>
              </div>
              
              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">API密钥</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    v-model="createForm.api_key"
                    type="password" 
                    placeholder="请输入您的API密钥"
                    maxlength="200"
                    class="form-input"
                  />
                </div>
              </div>
            </div>
            
            <!-- 对话框底部 -->
            <div class="dialog-footer">
              <button 
                class="dialog-btn cancel-btn" 
                @click.stop="createDialogVisible = false"
              >取消</button>
              <button 
                class="dialog-btn confirm-btn" 
                :class="{ 'disabled': !createForm.model || !createForm.api_key || !createForm.base_url || !createForm.provider }"
                :disabled="!createForm.model || !createForm.api_key || !createForm.base_url || !createForm.provider || createLoading"
                @click.stop="handleCreate"
              >{{ createLoading ? '创建中...' : '创建' }}</button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- 编辑模型对话框 -->
    <Teleport to="body">
      <transition name="fade">
        <div v-if="editDialogVisible" class="dialog-overlay" @click="editDialogVisible = false">
          <div class="dialog-container" @click.stop>
            <!-- 对话框主体 -->
            <div class="dialog-body">
              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">模型名称</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    v-model="editForm.model"
                    type="text" 
                    placeholder="例如：gpt-4, claude-3.5-sonnet"
                    maxlength="50"
                    class="form-input"
                  />
                </div>
              </div>
              
              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">提供商</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    v-model="editForm.provider"
                    type="text" 
                    placeholder="例如：OpenAI, Anthropic, 阿里云"
                    maxlength="50"
                    class="form-input"
                  />
                </div>
              </div>
              
              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">基础URL</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    v-model="editForm.base_url"
                    type="text" 
                    placeholder="例如：https://api.openai.com/v1"
                    maxlength="200"
                    class="form-input"
                  />
                </div>
              </div>
              
              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">API密钥</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    v-model="editForm.api_key"
                    type="password" 
                    placeholder="请输入您的API密钥(留空则不修改)"
                    maxlength="200"
                    class="form-input"
                  />
                </div>
              </div>
            </div>
            
            <!-- 对话框底部 -->
            <div class="dialog-footer">
              <button 
                class="dialog-btn cancel-btn" 
                @click.stop="editDialogVisible = false"
              >取消</button>
              <button 
                class="dialog-btn confirm-btn" 
                :class="{ 'disabled': !editForm.model || !editForm.base_url || !editForm.provider }"
                :disabled="!editForm.model || !editForm.base_url || !editForm.provider || editLoading"
                @click.stop="handleEdit"
              >{{ editLoading ? '保存中...' : '保存' }}</button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- 删除确认对话框 -->
    <Teleport to="body">
      <transition name="fade">
        <div v-if="deleteDialogVisible" class="confirm-dialog-overlay" @click="cancelDelete">
          <div class="confirm-dialog" @click.stop>
            <h3 class="dialog-title">确认删除模型</h3>
            <p class="dialog-message" v-if="modelToDelete">确定要删除模型 <strong>"{{ modelToDelete.model }}"</strong> 吗？</p>
            <div class="confirm-dialog-footer">
              <button class="confirm-dialog-btn confirm-cancel-btn" @click="cancelDelete" :disabled="deleteLoading">取消</button>
              <button class="confirm-dialog-btn confirm-delete-btn" @click="confirmDelete" :disabled="deleteLoading">{{ deleteLoading ? '删除中...' : '删除' }}</button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style lang="scss" scoped>
.model-page {
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
      background: linear-gradient(90deg, #409eff, #3a7be2); // 添加渐变效果，蓝色系
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      
      .model-icon {
        font-size: 30px;
        width: 32px;
        height: 32px;
        color: #409eff;
      }
      
      &::before {
        content: '';
        display: none; // 隐藏原来的表情符号
      }
    }
    
    .header-actions {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .search-box {
        margin-right: 12px;
        
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
      
      .action-buttons {
        display: flex;
        gap: 12px;
        
        .el-button {
          border-radius: 100px;
          padding: 12px 20px;
          font-size: 14px;
          font-weight: 500;
          transition: all 0.3s;
          
          &:hover {
            transform: translateY(-2px);
          }
          
          &.refresh-btn {
            &:hover {
              background-color: #67c23a;
              border-color: #67c23a;
              color: white;
            }
          }
          
          &.add-btn {
            background: linear-gradient(135deg, #409eff 0%, #3a7be2 100%);
            border: none;
            box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
            
            &:hover {
              background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
              box-shadow: 0 6px 16px rgba(64, 158, 255, 0.3);
            }
          }
        }
      }
    }
  }
  
  .model-list {
    min-height: 300px;
    position: relative;
    
    .model-table-container {
      /* Custom Table Styles */
      :deep(.el-table) {
        border-radius: 24px;
        overflow: hidden;
        border: 1px solid #ebeef5;
        
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
      
      .model-info-cell {
        display: flex;
        align-items: center;
        
        .model-avatar {
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
          
          &.llm {
            background: linear-gradient(135deg, #409eff 0%, #3a7be2 100%);
            box-shadow: 0 4px 10px rgba(64, 158, 255, 0.2);
          }
          &.embedding {
            background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
            box-shadow: 0 4px 10px rgba(103, 194, 58, 0.2);
          }
          &.rerank {
            background: linear-gradient(135deg, #e6a23c 0%, #d9b55b 100%);
            box-shadow: 0 4px 10px rgba(230, 162, 60, 0.2);
          }
        }
        
        .model-title {
          .model-name {
            font-size: 15px;
            font-weight: 600;
            color: #303133;
            margin-bottom: 4px;
          }
          .model-provider {
            font-size: 13px;
            color: #909399;
          }
        }
      }
      
      .url-value {
        font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
        color: #409eff;
        background-color: rgba(64, 158, 255, 0.1);
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 13px;
        display: inline-block;
        border: 1px dashed rgba(64, 158, 255, 0.3);
        
        &:hover {
          background-color: rgba(64, 158, 255, 0.15);
          border-color: rgba(64, 158, 255, 0.5);
        }
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
      padding: 80px 30px;
      position: relative;
      overflow: hidden;
      
      .empty-icon {
        margin-bottom: 24px;
        position: relative;
        
        &::after {
          content: '';
          position: absolute;
          bottom: -10px;
          left: 50%;
          transform: translateX(-50%);
          width: 60px;
          height: 4px;
          background: linear-gradient(90deg, #409eff, #67c23a);
          border-radius: 2px;
        }
        
        .empty-emoji {
          font-size: 64px;
          opacity: 0.8;
        }
      }
      
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
      
      .el-button {
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 500;
        border-radius: 100px;
        background: linear-gradient(135deg, #409eff 0%, #3a7be2 100%);
        border: none;
        box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
        transition: all 0.3s;
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 16px rgba(64, 158, 255, 0.3);
          background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
        }
      }
    }
  }
}

/* Lingseek 引擎配置样式 */
.lingseek-config-section {
  margin-top: 40px;
  background: white;
  border-radius: 24px;
  padding: 32px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
  border: 1px solid #ebeef5;


  .section-title {
    margin-bottom: 24px;
    
    h3 {
      font-size: 22px;
      font-weight: 700;
      color: #303133;
      margin: 0 0 8px 0;
    }
    
    p {
      color: #909399;
      font-size: 14px;
      margin: 0;
    }
  }

  .config-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 24px;
  }

  .config-card {
    background: #f8f9fa;
    border-radius: 24px;
    padding: 24px;
    border: 1px solid #ebeef5;
    transition: all 0.3s;
    
    &:hover {
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.05);
      transform: translateY(-2px);
      border-color: #c6e2ff;
    }
    
    .config-icon {
      width: 48px;
      height: 48px;
      background: rgba(64, 158, 255, 0.1);
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 16px;
      
      .el-icon {
        font-size: 24px;
        color: #409eff;
      }
    }
    
    .config-info {
      margin-bottom: 20px;
      
      h4 {
        margin: 0 0 8px 0;
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }
      
      p {
        margin: 0;
        font-size: 13px;
        color: #606266;
        line-height: 1.5;
      }
    }
    
    .model-select {
      width: 100%;
      
      :deep(.el-select__wrapper) {
        border-radius: 100px !important;
      }
      
      :deep(.el-popper.is-light) {
        border-radius: 16px !important;
      }
      
      :deep(.el-select-dropdown__item) {
        border-radius: 8px !important;
        margin: 0 8px;
        width: calc(100% - 16px);
      }
    }
  }

}

/* 添加URL工具提示样式 */
:deep(.url-tooltip) {
  max-width: 400px;
  word-break: break-all;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  padding: 10px 14px;
}

// 响应式调整
@media (max-width: 768px) {
  .model-page {
    padding: 20px;
    
    .page-header {
      flex-direction: column;
      align-items: stretch;
      gap: 16px;
      padding: 20px;
      
      h2 {
        text-align: center;
        justify-content: center;
      }
      
      .header-actions {
        flex-direction: column;
        align-items: stretch;
        
        .search-box {
          margin-right: 0;
          margin-bottom: 12px;
        }
        
        .action-buttons {
          justify-content: center;
        }
      }
    }
    
    .model-list .model-grid {
      grid-template-columns: 1fr;
    }
  }
}

/* 添加模型对话框样式 */
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
  background: white;
  border-radius: 24px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: dialog-scale-in 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

/* 对话框主体 */
.dialog-body {
  padding: 36px 36px 24px 36px;
  background: white;
}

.form-item {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  width: 90px;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 0;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  flex-shrink: 0;
}

.label-text {
  color: #333;
}

.required-mark {
  color: #ff3b30;
  font-weight: 500;
  font-size: 14px;
}

.input-wrapper {
  flex: 1;
  position: relative;
}

.form-input {
  width: 100%;
  padding: 10px 16px;
  border: 1px solid #e5e5e5;
  border-radius: 100px;
  font-size: 14px;
  color: #333;
  background: white;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

/* 如果使用 el-input 组件则需要对它覆盖 */
:deep(.el-input__wrapper) {
  border-radius: 100px;
}

.form-input:focus {
  outline: none;
  border-color: #409eff;
  background: white;
}

.form-input::placeholder {
  color: #999;
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 36px 36px 36px;
  background: transparent;
  border-top: none;
}

.dialog-btn {
  padding: 8px 24px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  background: white;
  transition: all 0.2s;
  outline: none;
  display: inline-block;
  min-width: auto;
  border: none;
}

.cancel-btn {
  border: 1px solid #e5e5e5;
  color: #333;
}

.cancel-btn:hover {
  background: #f5f5f5;
}

.confirm-btn {
  border: 1px solid #409eff;
  color: #409eff;
}

.confirm-btn:hover:not(.disabled) {
  background: #f0f7ff;
}

.confirm-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  border-color: #a0cfff;
  color: #a0cfff;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 对话框响应式设计 */
@media (max-width: 768px) {
  .dialog-container {
    width: 95%;
    margin: 10px;
    max-height: 95vh;
  }
  
  .dialog-body {
    padding: 24px 20px 16px 20px;
  }
  
  .form-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .form-label {
    width: 100%;
  }
  
  .dialog-footer {
    padding: 0 20px 24px 20px;
    flex-direction: row;
    justify-content: flex-end;
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

  .confirm-dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 0;
    background: transparent;
    border-top: none;

    .confirm-dialog-btn {
      padding: 8px 24px;
      border-radius: 24px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      background: white;
      transition: all 0.2s;
      outline: none;
      display: inline-block;
      min-width: auto;
      border: none;

      &.confirm-cancel-btn {
        border: 1px solid #e5e5e5;
        color: #333;
        background: white;

        &:hover {
          background: #f5f5f5;
        }
      }

      &.confirm-delete-btn {
        border: 1px solid #ff3b30;
        color: #ff3b30;
        background: white;

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