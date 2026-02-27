<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Check, Close, Setting, Cpu } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { 
  getVisibleLLMsAPI, 
  updateLLMAPI, 
  deleteLLMAPI, 
  getLLMSchemaAPI,
  type LLMResponse,
  type UpdateLLMRequest
} from '../../apis/llm'

const router = useRouter()
const route = useRoute()

// 响应式数据
const loading = ref(false)
const currentModel = ref<LLMResponse | null>(null)

// 表单相关
const editFormRef = ref<FormInstance>()

const editForm = reactive<UpdateLLMRequest>({
  llm_id: '',
  model: '',
  api_key: '',
  base_url: '',
  provider: '',
  llm_type: ''
})

// 表单验证规则
const formRules: FormRules = {
  model: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  api_key: [
    { required: true, message: '请输入API密钥', trigger: 'blur' }
  ],
  base_url: [
    { required: true, message: '请输入基础URL', trigger: 'blur' }
  ],
  provider: [
    { required: true, message: '请输入提供商', trigger: 'blur' }
  ]
}

// 获取模型详情
const fetchModelDetail = async () => {
  const modelId = route.query.id as string
  if (!modelId) {
    ElMessage.error('缺少模型ID参数')
    router.push('/model')
    return
  }

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
      
      const targetModel = allModels.find(model => model.llm_id === modelId)
      if (targetModel) {
        currentModel.value = targetModel
        // 填充表单
        Object.assign(editForm, {
          llm_id: targetModel.llm_id,
          model: targetModel.model,
          api_key: targetModel.api_key,
          base_url: targetModel.base_url,
          provider: targetModel.provider,
          llm_type: targetModel.llm_type
        })
      } else {
        ElMessage.error('未找到指定的模型')
        router.push('/model')
      }
    } else {
      ElMessage.error(response.data.status_message || '获取模型详情失败')
      router.push('/model')
    }
  } catch (error) {
    ElMessage.error('获取模型详情失败')
    console.error('获取模型详情失败:', error)
    router.push('/model')
  } finally {
    loading.value = false
  }
}

// 返回模型管理页面
const goBack = () => {
  router.push('/model')
}

// 更新模型
const handleUpdate = async () => {
  if (!editFormRef.value) return
  
  try {
    await editFormRef.value.validate()
    const response = await updateLLMAPI(editForm)
    
    if (response.data.status_code === 200) {
      ElMessage.success('更新成功')
      router.push('/model')
    } else {
      ElMessage.error(response.data.status_message || '更新失败')
    }
  } catch (error) {
    ElMessage.error('更新失败')
    console.error('更新模型失败:', error)
  }
}

// 删除模型
const handleDelete = async () => {
  if (!currentModel.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除模型"${currentModel.value.model}"吗？删除后无法恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const response = await deleteLLMAPI({ llm_id: currentModel.value.llm_id })
    
    if (response.data.status_code === 200) {
      router.push('/model')
    } else {
      ElMessage.error(response.data.status_message || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除模型失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 测试模型连接
const testModel = async () => {
  if (!currentModel.value) return
  
  ElMessage.info(`正在测试 ${currentModel.value.model} 连接...`)
  // 这里可以添加实际的测试逻辑
  setTimeout(() => {
    ElMessage.success(`${currentModel.value!.model} 连接测试完成`)
  }, 2000)
}

onMounted(() => {
  fetchModelDetail()
})
</script>

<template>
  <div class="model-editor-page" v-loading="loading">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <div class="breadcrumb">
          <span class="breadcrumb-item clickable" @click="goBack">模型管理</span>
          <span class="breadcrumb-separator">></span>
          <span class="breadcrumb-item active">编辑模型</span>
        </div>
      </div>
      
      <div class="header-title">
        <div class="title-icon">
          <el-icon><Setting /></el-icon>
        </div>
        <h2>编辑模型</h2>
      </div>
    </div>

    <!-- 编辑表单 -->
    <div v-if="currentModel" class="edit-form-section">
      <div class="form-container">
        <div class="form-header">
          <div class="form-icon">
            <el-icon><Cpu /></el-icon>
          </div>
          <div class="form-title">
            <h3>模型配置</h3>
            <p>修改模型的基本信息和连接配置</p>
          </div>
        </div>
        
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
                  placeholder="请输入您的API密钥"
                  maxlength="200"
                  class="form-input"
                />
              </div>
            </div>
          </div>
        </div>

        <div class="form-actions-wrapper">
          <button 
            class="dialog-btn cancel-btn" 
            @click="goBack"
          >
            <span class="btn-icon">❌</span>
            <span class="btn-text">取消</span>
          </button>
          <button 
            class="dialog-btn confirm-btn" 
            :class="{ 'disabled': !editForm.model || !editForm.api_key || !editForm.base_url || !editForm.provider }"
            :disabled="!editForm.model || !editForm.api_key || !editForm.base_url || !editForm.provider"
            @click="handleUpdate"
          >
            <span class="btn-icon">✅</span>
            <span class="btn-text">保存更改</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading" class="empty-state">
      <div class="empty-icon">
        <el-icon><Close /></el-icon>
      </div>
      <h3>未找到模型</h3>
      <p>请检查模型ID是否正确</p>
      <el-button 
        type="primary" 
        :icon="ArrowLeft"
        @click="goBack"
        size="large"
      >
        返回模型管理
      </el-button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.model-editor-page {
  padding: 24px;
  height: 100%;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: 100vh;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    background: white;
    padding: 24px 32px;
    border-radius: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(226, 232, 240, 0.6);
    
          .header-left {
        display: flex;
        align-items: center;
        gap: 20px;
        
        .breadcrumb {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 15px;
          color: #94a3b8;
          
          .breadcrumb-item {
            transition: all 0.3s ease;
            padding: 8px 12px;
            border-radius: 100px;
            cursor: default;
            
            &.clickable {
              cursor: pointer;
              color: #64748b;
              font-weight: 500;
              
              &:hover {
                color: #3b82f6;
                background: rgba(59, 130, 246, 0.1);
                transform: translateY(-1px);
              }
              
              &:active {
                transform: translateY(0);
              }
            }
            
            &.active {
              color: #3b82f6;
              font-weight: 600;
              background: rgba(59, 130, 246, 0.05);
            }
          }
          
          .breadcrumb-separator {
            color: #cbd5e1;
            font-weight: 500;
          }
        }
      }
    
    .header-title {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .title-icon {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
        
        .el-icon {
          font-size: 24px;
          color: white;
        }
      }
      
      h2 {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        background: linear-gradient(135deg, #1e293b 0%, #475569 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
    }
  }
  
  .edit-form-section {
    .form-container {
      background: white;
      border-radius: 20px;
      padding: 24px 32px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
      border: 1px solid rgba(226, 232, 240, 0.6);
      
      .form-header {
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 32px;
        padding-bottom: 24px;
        border-bottom: 2px solid #f1f5f9;
        
        .form-icon {
          width: 48px;
          height: 48px;
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
          
          .el-icon {
            font-size: 28px;
            color: white;
          }
        }
        
                  .form-title {
            h3 {
              margin: 0 0 12px 0;
              font-size: 28px;
              font-weight: 800;
              background: linear-gradient(135deg, #1e293b 0%, #475569 100%);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
              background-clip: text;
              letter-spacing: -0.5px;
            }
            
            p {
              margin: 0;
              font-size: 16px;
              color: #64748b;
              line-height: 1.6;
              font-weight: 500;
            }
          }
      }
      
      .form-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 32px;
        margin-bottom: 24px;
        
        .form-section {
          background: #ffffff;
          border-radius: 20px;
          padding: 24px;
          border: 1px solid #f1f5f9;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.02);
          
          .section-header {
            margin-bottom: 24px;
            padding-bottom: 12px;
            border-bottom: 1px solid #f1f5f9;
            
            h4 {
              margin: 0;
              font-size: 18px;
              color: #1e293b;
              font-weight: 600;
              display: flex;
              align-items: center;
              gap: 8px;
            }
          }
          
          .form-item {
            margin-bottom: 24px;
            
            &:last-child {
              margin-bottom: 0;
            }
            
            .form-label {
              display: flex;
              align-items: center;
              margin-bottom: 10px;
              
              .label-text {
                font-size: 15px;
                font-weight: 600;
                color: #334155;
              }
              
              .required-mark {
                color: #ef4444;
                margin-left: 4px;
                font-weight: bold;
              }
            }
            
            .input-wrapper {
              position: relative;
              
              .form-input {
                width: 100%;
                box-sizing: border-box;
                padding: 14px 20px;
                border: 2px solid #e2e8f0;
                border-radius: 100px;
                font-size: 15px;
                color: #1e293b;
                background: #f8fafc;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                
                &:focus {
                  outline: none;
                  border-color: #3b82f6;
                  background: #ffffff;
                  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
                  transform: translateY(-1px);
                }
                
                &::placeholder {
                  color: #94a3b8;
                  font-weight: 400;
                }
              }
            }
          }
        }
      }
        
      .form-actions-wrapper {
        display: flex;
        justify-content: flex-start;
        align-items: center;
        gap: 16px;
        margin-top: 10px;
        padding-top: 24px;
        border-top: 2px solid #f1f5f9;
        
        .dialog-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 12px 28px;
          border-radius: 100px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          border: none;
          
          .btn-icon {
            font-size: 18px;
          }
          
          &.cancel-btn {
            background: #f1f5f9;
            color: #64748b;
            
            &:hover {
              background: #e2e8f0;
              color: #475569;
              transform: translateY(-2px);
            }
          }
          
          &.confirm-btn {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            
            &:hover:not(.disabled) {
              box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
              transform: translateY(-2px);
            }
            
            &.disabled {
              background: #cbd5e1;
              box-shadow: none;
              cursor: not-allowed;
              opacity: 0.7;
            }
          }
        }
      }
    }
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
    background: white;
    border-radius: 20px;
    padding: 80px 40px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
    
    .empty-icon {
      font-size: 80px;
      color: #cbd5e1;
      margin-bottom: 24px;
    }
    
    h3 {
      margin: 0 0 12px 0;
      font-size: 24px;
      font-weight: 600;
      color: #475569;
    }
    
    p {
      margin: 0 0 32px 0;
      color: #64748b;
      font-size: 16px;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .model-editor-page {
    padding: 16px;
    
         .page-header {
       flex-direction: column;
       gap: 20px;
       padding: 20px;
       
       .header-left {
         justify-content: center;
         
         .breadcrumb {
           font-size: 14px;
           
           .breadcrumb-item {
             padding: 6px 10px;
           }
         }
       }
     }
    
    .edit-form-section .form-container {
      padding: 24px;
      
      .form-header {
        flex-direction: column;
        text-align: center;
        gap: 16px;
      }
      
      .edit-form .form-section .form-row {
        grid-template-columns: 1fr;
        gap: 16px;
      }
      
             .edit-form .form-actions {
         flex-direction: column;
         gap: 16px;
         
         .action-btn {
           width: 100%;
           max-width: 200px;
         }
       }
    }
  }
}
</style> 