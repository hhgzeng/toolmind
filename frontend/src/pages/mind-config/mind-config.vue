<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Connection, Cpu, Operation } from '@element-plus/icons-vue'
import { 
  getVisibleLLMsAPI, 
  getMindConfigAPI,
  updateMindConfigAPI,
  type LLMResponse,
  type MindModelConfig
} from '../../apis/llm'

const models = ref<LLMResponse[]>([])
const loading = ref(false)

const mindConfig = ref<MindModelConfig>({
  conversation_model_id: null,
  tool_call_model_id: null,
  reasoning_model_id: null
})
const savingMind = ref(false)

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
    const configRes = await getMindConfigAPI()
    if (configRes.data.status_code === 200) {
      if (Object.keys(configRes.data.data).length > 0) {
        mindConfig.value = configRes.data.data
      }
    }
  } catch (error) {
    console.error('获取 Mind 配置失败', error)
  }
}

const saveMindConfig = async () => {
  savingMind.value = true
  try {
    const res = await updateMindConfigAPI(mindConfig.value)
    if (res.data.status_code === 200) {
      if (res.data.data && Object.keys(res.data.data).length > 0) {
        mindConfig.value = res.data.data
      }
    }
  } catch (error) {
    ElMessage.error('保存 Mind 配置失败')
  } finally {
    savingMind.value = false
  }
}

const hasModels = computed(() => models.value.length > 0)

onMounted(() => {
  fetchModels()
})
</script>

<template>
  <div class="mind-config-page">
    <div class="page-header">
      <h2>
        <el-icon class="page-icon"><Operation /></el-icon>
        模型配置
      </h2>
    </div>

    <div class="mind-config-section" v-loading="loading || savingMind">
      <div class="section-title">
        <h3>ToolMind 核心模型配置</h3>
        <p>为 ToolMind 的不同功能组件配置专属的 AI 模型</p>
      </div>
      
      <div v-if="hasModels" class="config-grid">
        <div class="config-card">
          <div class="config-icon">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <div class="config-info">
            <h4>对话与任务生成模型</h4>
            <p>负责理解用户意图并规划任务执行路径</p>
          </div>
          <el-select 
            v-model="mindConfig.conversation_model_id" 
            placeholder="请选择会话模型" 
            class="model-select"
            clearable
            no-data-text="无模型"
            @change="saveMindConfig"
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
          <div class="config-icon">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="config-info">
            <h4>工具调用模型</h4>
            <p>负责执行 MCP 协议和外部工具调用</p>
          </div>
          <el-select 
            v-model="mindConfig.tool_call_model_id" 
            placeholder="请选择工具模型" 
            class="model-select"
            clearable
            no-data-text="无模型"
            @change="saveMindConfig"
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
          <div class="config-icon">
            <el-icon><Cpu /></el-icon>
          </div>
          <div class="config-info">
            <h4>结果推理与评估模型</h4>
            <p>对任务执行的最终结果进行自我验证和评估</p>
          </div>
          <el-select 
            v-model="mindConfig.reasoning_model_id" 
            placeholder="请选择评估模型" 
            class="model-select"
            clearable
            no-data-text="无模型"
            @change="saveMindConfig"
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

      <div v-else class="empty-state">
        <div class="empty-icon">
          <span class="empty-emoji">🤖</span>
        </div>
        <h3>还没有可用模型</h3>
        <p>请先在「模型管理」中创建至少一个模型，再回来为 ToolMind 引擎进行配置。</p>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.mind-config-page {
  padding: 30px;
  min-height: calc(100vh - 60px);
  background-color: #ffffff;

  .page-header {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
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

      .page-icon {
        font-size: 30px;
        width: 32px;
        height: 32px;
        color: #409eff;
      }
    }

    .header-subtitle {
      font-size: 14px;
      color: #64748b;
    }
  }
}

.mind-config-section {
  margin-top: 0;
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

  .empty-state {
    text-align: center;
    padding: 60px 30px;

    .empty-icon {
      margin-bottom: 24px;

      .empty-emoji {
        font-size: 48px;
        opacity: 0.8;
      }
    }

    h3 {
      font-size: 20px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 12px;
    }

    p {
      font-size: 14px;
      color: #606266;
      margin: 0 auto;
      max-width: 420px;
    }
  }
}

@media (max-width: 768px) {
  .mind-config-page {
    padding: 20px;
    
    .page-header {
      padding: 20px;
      h2 {
        text-align: center;
        justify-content: center;
      }
      .header-subtitle {
        text-align: center;
      }
    }
  }
}
</style>

