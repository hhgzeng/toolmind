<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Connection, Cpu, Search, Refresh, Calendar, ChatDotRound, RefreshRight, Star, Link, Timer } from '@element-plus/icons-vue'
import { 
  getVisibleLLMsAPI, 
  createLLMAPI, 
  deleteLLMAPI,
  getLingseekConfigAPI,
  updateLingseekConfigAPI,
  type LLMResponse,
  type CreateLLMRequest,
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
      ElMessage.success('Lingseek 引擎配置已保存')
      lingseekConfig.value = res.data.data
    } else {
      ElMessage.error(res.data.status_message || '保存配置失败')
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

// 跳转到模型编辑器
const goToModelEditor = (model: LLMResponse) => {
  router.push({
    name: 'model-editor',
    query: { id: model.llm_id }
  })
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
    ElMessage.success(`${model.model} 连接测试完成`)
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



          <!-- 基础URL列 -->
          <el-table-column label="基础URL" min-width="250">
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
                  @click.stop="goToModelEditor(row)"
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
      
      <div class="save-actions">
        <el-button 
          type="primary" 
          size="large" 
          @click="saveLingseekConfig" 
          :loading="savingLingseek"
          class="save-config-btn"
        >
          📝 保存引擎配置
        </el-button>
      </div>
    </div>

    <!-- 创建模型对话框 -->
    <div v-if="createDialogVisible" class="dialog-overlay" @click="createDialogVisible = false">
      <div class="dialog-container" @click.stop>
        <!-- 对话框主体 -->
        <div class="dialog-body">
          <div class="form-grid">
            <!-- 基本信息区域 -->
            <div class="form-section">
              <div class="section-header">
                <h4>📝 基本信息</h4>
              </div>
              
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
              
            </div>
            
            <!-- 连接配置区域 -->
            <div class="form-section">
              <div class="section-header">
                <h4>🔧 连接配置</h4>
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
          </div>
        </div>
        
        <!-- 对话框底部 -->
        <div class="dialog-footer">
          <button 
            class="dialog-btn cancel-btn" 
            @click.stop="createDialogVisible = false"
          >
            <span class="btn-icon">❌</span>
            <span class="btn-text">取消</span>
          </button>
          <button 
            class="dialog-btn confirm-btn" 
            :class="{ 'disabled': !createForm.model || !createForm.api_key || !createForm.base_url || !createForm.provider }"
            :disabled="!createForm.model || !createForm.api_key || !createForm.base_url || !createForm.provider || createLoading"
            @click.stop="handleCreate"
          >
            <span v-if="createLoading" class="btn-icon loading">⏳</span>
            <span v-else class="btn-icon">✅</span>
            <span class="btn-text">{{ createLoading ? '创建中...' : '确定创建' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="deleteDialogVisible" class="dialog-overlay" @click="cancelDelete">
      <div class="delete-dialog-container" @click.stop>
        <!-- 对话框主体 -->
        <div class="delete-dialog-body">
          <p v-if="modelToDelete">
            确定要删除模型 <strong>"{{ modelToDelete.model }}"</strong> 吗？
          </p>
        </div>
        
        <!-- 对话框底部 -->
        <div class="delete-dialog-footer">
          <button 
            class="delete-dialog-btn cancel-btn" 
            @click="cancelDelete"
            :disabled="deleteLoading"
          >
            取消
          </button>
          <button 
            class="delete-dialog-btn confirm-btn" 
            :disabled="deleteLoading"
            @click="confirmDelete"
          >
            {{ deleteLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.model-page {
  padding: 30px;
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
  
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
  
  .save-actions {
    display: flex;
    justify-content: flex-end;
    padding-top: 20px;
    border-top: 1px solid #ebeef5;
    
    .save-config-btn {
      padding: 12px 28px;
      font-size: 16px;
      border-radius: 100px;
      background: linear-gradient(135deg, #409eff 0%, #3a7be2 100%);
      border: none;
      
      &:hover {
        background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
        box-shadow: 0 6px 16px rgba(64, 158, 255, 0.3);
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
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.9) translateY(20px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1) translateY(0);
  }
}

.dialog-container {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: 24px;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.3),
    0 8px 32px rgba(0, 0, 0, 0.15);
  width: 88%;
  max-width: 750px;
  max-height: 88vh;
  overflow: hidden;
  animation: slideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}



/* 对话框主体 */
.dialog-body {
  padding: 36px;
  max-height: 65vh;
  overflow-y: auto;
  background: #fafbfc;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 36px;
}

.form-section {
  background: white;
  border-radius: 20px;
  padding: 22px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
}

.section-header {
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 2px solid #f1f5f9;
}

.section-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #1a202c;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-item {
  margin-bottom: 20px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 600;
  color: #2d3748;
}

.label-text {
  color: #374151;
}

.required-mark {
  color: #ef4444;
  font-weight: 700;
  font-size: 16px;
}

.input-wrapper,
.select-wrapper {
  position: relative;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 100px;
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  background: white;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

/* 如果使用 el-input 组件则需要对它覆盖 */
:deep(.el-input__wrapper) {
  border-radius: 100px;
}

.form-input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1);
  transform: translateY(-1px);
}

.form-input::placeholder {
  color: #9ca3af;
  font-weight: 400;
}

.form-select {
  width: 100%;
  padding: 12px 40px 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 100px;
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  appearance: none;
  box-sizing: border-box;
}

.form-select:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1);
}

.select-arrow {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: #6b7280;
  font-size: 12px;
  transition: transform 0.3s ease;
}

.select-wrapper:hover .select-arrow {
  transform: translateY(-50%) rotate(180deg);
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  padding: 20px 36px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.dialog-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border: none;
  border-radius: 100px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 100px;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.dialog-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.dialog-btn:hover::before {
  left: 100%;
}

.cancel-btn {
  background: #f1f5f9;
  color: #64748b;
  border: 2px solid #e2e8f0;
}

.cancel-btn:hover {
  background: #e2e8f0;
  color: #475569;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.confirm-btn {
  background: #f1f5f9;
  color: #64748b;
  border: 2px solid #e2e8f0;
}

.confirm-btn:hover:not(.disabled) {
  background: #e2e8f0;
  color: #475569;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.confirm-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #9ca3af;
}

.btn-icon {
  font-size: 16px;
  display: flex;
  align-items: center;
}

.btn-icon.loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.btn-text {
  font-weight: 600;
}

/* 对话框响应式设计 */
@media (max-width: 768px) {
  .dialog-container {
    width: 95%;
    margin: 10px;
    max-height: 95vh;
  }
  
  .dialog-body {
    padding: 24px 20px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .form-section {
    padding: 16px;
  }
  
  .dialog-footer {
    padding: 16px;
    flex-direction: column;
  }
  
  .dialog-btn {
    width: 100%;
  }
}

/* 删除确认对话框样式 */
.delete-dialog-container {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 400px;
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
  border: 1px solid #e5e7eb;
}

.delete-dialog-body {
  padding: 32px 28px 24px;
  text-align: center;
  
  p {
    margin: 0;
    font-size: 16px;
    color: #374151;
    line-height: 1.5;
    
    strong {
      color: #1f2937;
      font-weight: 600;
    }
  }
}

.delete-dialog-footer {
  display: flex;
  gap: 12px;
  padding: 0 28px 28px;
}

.delete-dialog-btn {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 100px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.delete-dialog-btn.cancel-btn {
  background: #f9fafb;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.delete-dialog-btn.cancel-btn:hover:not(:disabled) {
  background: #f3f4f6;
  color: #374151;
}

.delete-dialog-btn.confirm-btn {
  background: #3b82f6;
  color: white;
  border: 1px solid #3b82f6;
}

.delete-dialog-btn.confirm-btn:hover:not(:disabled) {
  background: #2563eb;
  border-color: #2563eb;
}

.delete-dialog-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 删除对话框响应式设计 */
@media (max-width: 768px) {
  .delete-dialog-container {
    width: 95%;
    margin: 10px;
  }
  
  .delete-dialog-body {
    padding: 24px 20px 20px;
    
    p {
      font-size: 15px;
    }
  }
  
  .delete-dialog-footer {
    padding: 0 20px 24px;
  }
}
</style>