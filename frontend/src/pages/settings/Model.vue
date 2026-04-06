<script setup lang="ts">
import { Cpu, Delete, Edit, Plus, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import {
  createLLMAPI,
  deleteLLMAPI,
  listLLMsAPI,
  updateLLMAPI,
  type CreateLLMRequest,
  type LLMResponse,
  type UpdateLLMRequest
} from '../../api/llm'

// 响应式数据
const models = ref<LLMResponse[]>([])
const loading = ref(false)
const searchKeyword = ref('')

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
  provider: ''
})

// 编辑相关
const editDialogVisible = ref(false)
const editLoading = ref(false)
const editForm = ref<UpdateLLMRequest>({
  llm_id: '',
  model: '',
  api_key: '',
  base_url: '',
  provider: ''
})

// 获取模型列表
const fetchModels = async () => {
  loading.value = true
  try {
    const response = await listLLMsAPI()

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
    provider: ''
  })
}

// 测试模型连接
const testLLMConnection = async (baseUrl: string, apiKey: string, model: string) => {
  try {
    const url = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl
    const testUrl = `${url}/chat/completions`
    
    // 设置 10s 超时
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 10000)
    
    const response = await fetch(testUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: model,
        messages: [{ role: 'user', content: 'hello' }],
        max_tokens: 1
      }),
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    return response.ok
  } catch (error) {
    return false
  }
}

// 创建模型
const handleCreate = async () => {
  // 检查必填字段
  if (!createForm.value.model || !createForm.value.api_key || !createForm.value.base_url || !createForm.value.provider) {
    ElMessage.error('请填写所有必填字段')
    return
  }

  // 检查模型是否已存在
  const isExist = models.value.some(m => 
    m.model === createForm.value.model && 
    m.base_url === createForm.value.base_url
  )
  if (isExist) {
    ElMessage.warning('模型已存在')
    return
  }

  createLoading.value = true
  try {
    // 连接检测
    const isValid = await testLLMConnection(createForm.value.base_url, createForm.value.api_key, createForm.value.model)
    if (!isValid) {
      ElMessage.error('模型添加失败，请检查模型添加信息')
      createLoading.value = false
      return
    }

    const response = await createLLMAPI(createForm.value)

    if (response.data.status_code === 200) {
      createDialogVisible.value = false
      fetchModels()
      ElMessage.success('模型添加成功')
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
    provider: model.provider || ''
  })
}

// 编辑模型
const handleEdit = async () => {
  if (!editForm.value.model || !editForm.value.base_url || !editForm.value.provider) {
    ElMessage.error('请填写所有必填字段')
    return
  }

  // 检查模型是否已存在（排除自身）
  const isExist = models.value.some(m => 
    m.llm_id !== editForm.value.llm_id &&
    m.model === editForm.value.model && 
    m.base_url === editForm.value.base_url
  )
  if (isExist) {
    ElMessage.warning('模型已存在')
    return
  }

  editLoading.value = true
  try {
    // 获取原有的 API 密钥（如果表单中不填，那么使用原来的用来测试）
    const originalModel = models.value.find(m => m.llm_id === editForm.value.llm_id)
    const testApiKey = editForm.value.api_key || (originalModel ? originalModel.api_key : '')

    // 连接检测
    const isValid = await testLLMConnection(editForm.value.base_url, testApiKey, editForm.value.model)
    if (!isValid) {
      ElMessage.error('模型修改失败，请检查模型修改信息')
      editLoading.value = false
      return
    }

    const response = await updateLLMAPI(editForm.value)

    if (response.data.status_code === 200) {
      editDialogVisible.value = false
      fetchModels()
      ElMessage.success('模型修改成功')
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
        <el-icon class="model-icon">
          <Cpu />
        </el-icon>
        模型管理
      </h2>
      <div class="header-actions">
        <div class="search-box">
          <el-input v-model="searchKeyword" placeholder="搜索模型名称或提供商..." :prefix-icon="Search" clearable
            @clear="clearSearch" style="width: 300px" />
        </div>

        <div class="action-buttons">
          <el-button type="primary" :icon="Plus" @click="openCreateDialog" class="add-btn">
            添加模型
          </el-button>
        </div>
      </div>
    </div>

    <!-- 模型列表 -->
    <div class="model-list" v-loading="loading">
      <!-- 模型列表 (静态视图) -->
      <div class="static-model-list" v-if="filteredModels.length > 0">
        <div class="list-header">
          <div class="header-col col-model">模型</div>
          <div class="header-col col-url">基础 URL</div>
          <div class="header-col col-actions">操作</div>
        </div>
        <div class="list-body">
          <div v-for="row in filteredModels" :key="row.llm_id" class="list-row">
            <!-- 模型信息列 -->
            <div class="cell col-model">
              <div class="model-info-cell">
                <div class="model-avatar">
                  <span v-if="row.provider === 'OpenAI'" class="provider-icon">O</span>
                  <span v-else-if="row.provider === 'Anthropic'" class="provider-icon">A</span>
                  <span v-else-if="row.provider === 'Google'" class="provider-icon">G</span>
                  <span v-else class="provider-icon">{{ row.provider ? row.provider[0] : 'M' }}</span>
                </div>
                <div class="model-title">
                  <div class="model-name">{{ row.model }}</div>
                  <div class="model-provider">{{ row.provider }}</div>
                </div>
              </div>
            </div>

            <!-- 基础 URL 列 -->
            <div class="cell col-url">
              <div class="url-value">{{ truncateUrl(row.base_url, 38) }}</div>
            </div>

            <!-- 操作列 -->
            <div class="cell col-actions">
              <div class="action-buttons-cell">
                <el-button size="small" type="primary" @click.stop="openEditDialog(row)" title="编辑模型"
                  class="action-btn edit-btn">
                  <el-icon>
                    <Edit />
                  </el-icon>
                  <span>编辑</span>
                </el-button>
                <el-button size="small" type="danger" @click.stop="deleteModel(row)" title="删除模型"
                  class="action-btn delete-btn">
                  <el-icon>
                    <Delete />
                  </el-icon>
                  <span>删除</span>
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!loading" class="empty-state">
        <div class="empty-icon">
          <span class="empty-emoji">🤖</span>
        </div>
        <h3>暂无模型</h3>
        <p>点击添加按钮创建您的第一个 AI 模型吧</p>
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
                  <input v-model="createForm.model" type="text" placeholder="例如：gpt-4, claude-3.5-sonnet" maxlength="50"
                    class="form-input" />
                </div>
              </div>

              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">提供商</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input v-model="createForm.provider" type="text" placeholder="例如：OpenAI, Anthropic, 阿里云"
                    maxlength="50" class="form-input" />
                </div>
              </div>

              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">基础URL</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input v-model="createForm.base_url" type="text" placeholder="例如：https://api.openai.com/v1"
                    maxlength="200" class="form-input" />
                </div>
              </div>

              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">API密钥</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input v-model="createForm.api_key" type="password" placeholder="请输入您的API密钥" maxlength="200"
                    class="form-input" />
                </div>
              </div>
            </div>

            <!-- 对话框底部 -->
            <div class="dialog-footer">
              <button class="dialog-btn cancel-btn" @click.stop="createDialogVisible = false">取消</button>
              <button class="dialog-btn confirm-btn"
                :class="{ 'disabled': !createForm.model || !createForm.api_key || !createForm.base_url || !createForm.provider }"
                :disabled="!createForm.model || !createForm.api_key || !createForm.base_url || !createForm.provider || createLoading"
                @click.stop="handleCreate">{{ createLoading ? '创建中...' : '创建' }}</button>
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
                  <input v-model="editForm.model" type="text" placeholder="例如：gpt-4, claude-3.5-sonnet" maxlength="50"
                    class="form-input" />
                </div>
              </div>

              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">提供商</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input v-model="editForm.provider" type="text" placeholder="例如：OpenAI, Anthropic, 阿里云" maxlength="50"
                    class="form-input" />
                </div>
              </div>

              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">基础URL</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input v-model="editForm.base_url" type="text" placeholder="例如：https://api.openai.com/v1"
                    maxlength="200" class="form-input" />
                </div>
              </div>

              <div class="form-item">
                <label class="form-label">
                  <span class="label-text">API密钥</span>
                  <span class="required-mark">*</span>
                </label>
                <div class="input-wrapper">
                  <input v-model="editForm.api_key" type="password" placeholder="请输入您的API密钥(留空则不修改)" maxlength="200"
                    class="form-input" />
                </div>
              </div>
            </div>

            <!-- 对话框底部 -->
            <div class="dialog-footer">
              <button class="dialog-btn cancel-btn" @click.stop="editDialogVisible = false">取消</button>
              <button class="dialog-btn confirm-btn"
                :class="{ 'disabled': !editForm.model || !editForm.base_url || !editForm.provider }"
                :disabled="!editForm.model || !editForm.base_url || !editForm.provider || editLoading"
                @click.stop="handleEdit">{{ editLoading ? '保存中...' : '保存' }}</button>
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
              <button class="confirm-dialog-btn confirm-cancel-btn" @click="cancelDelete"
                :disabled="deleteLoading">取消</button>
              <button class="confirm-dialog-btn confirm-delete-btn" @click="confirmDelete" :disabled="deleteLoading">{{
                deleteLoading ? '删除中...' : '删除' }}</button>
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
      color: #303133;

      .model-icon {
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

    .static-model-list {
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

      .col-model {
        width: 35%;
      }

      .col-url {
        flex: 1;
      }

      .col-actions {
        width: 200px;
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
          background: linear-gradient(135deg, #409eff 0%, #3a7be2 100%);
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
        word-break: break-all;

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


    }
  }
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

  }
}

/* 深色模式 */
.theme-dark {
  .model-page {
    background-color: #1c1c1e;

    .page-header {
      background: #242426;
      box-shadow: none;

      h2 {
        color: #f5f5f7;

        .model-icon {
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

    .model-list {
      .static-model-list {
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
          }
        }

        .model-info-cell {
          .model-title {
            .model-name {
              color: #f5f5f7;
            }

            .model-provider {
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

      :deep(.el-loading-mask) {
        background-color: rgba(0, 0, 0, 0.6);

        .el-loading-spinner .el-loading-text {
          color: #e5e5ea;
        }
      }
    }
  }

  /* 创建/编辑模型对话框深色模式 */
  .dialog-overlay {
    background-color: rgba(0, 0, 0, 0.6);

    .dialog-container {
      background: #1c1c1e;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
    }

    .dialog-body {
      background: #1c1c1e;
    }

    .form-label {
      color: #e5e5ea;
    }

    .label-text {
      color: #e5e5ea;
    }

    .input-wrapper {
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
    }

    .dialog-footer {
      border-top: none;

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

  /* 删除确认对话框深色模式 */
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

      .confirm-dialog-footer {
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

.form-input:focus {
  outline: none;
  border-color: #409eff;
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

        &:hover {
          background: #f5f5f5;
        }
      }

      &.confirm-delete-btn {
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