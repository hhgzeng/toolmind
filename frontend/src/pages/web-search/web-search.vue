<script setup lang="ts">
import { Search } from "@element-plus/icons-vue"
import { ElMessage } from "element-plus"
import { onMounted, ref } from "vue"
import { getWebSearchAPI, updateWebSearchAPI, type WebSearchSettings } from "../../api/web-search"

const loading = ref(false)
const saving = ref(false)

const websearch = ref<WebSearchSettings>({
  api_key: "",
  enabled: false
})

const fetchConfig = async () => {
  loading.value = true
  try {
    const res = await getWebSearchAPI()
    if (res.data.status_code === 200 && res.data.data) {
      websearch.value.api_key = res.data.data.api_key || ""
      websearch.value.enabled = res.data.data.enabled ?? true
    } else {
      ElMessage.error(res.data.status_message || "获取联网搜索配置失败")
    }
  } catch (error) {
    ElMessage.error("获取联网搜索配置失败")
  } finally {
    loading.value = false
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    const res = await updateWebSearchAPI(websearch.value)
    if (res.data.status_code === 200) {
      websearch.value.api_key = res.data.data.api_key || ""
      websearch.value.enabled = res.data.data.enabled ?? true
    } else {
      ElMessage.error(res.data.status_message || "保存联网搜索配置失败")
    }
  } catch (error) {
    ElMessage.error("保存联网搜索配置失败")
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchConfig()
})
</script>

<template>
  <div class="web-search-config-page">
    <div class="page-header">
      <h2>
        <el-icon class="page-icon">
          <Search />
        </el-icon>
        联网搜索
      </h2>
    </div>

    <div class="web-search-config-section">
      <div class="section-title">
        <div class="section-title-main">
          <div>
            <h3>Tavily API Key</h3>
            <p>请填入 Tavily API Key，以支持联网搜索功能。</p>
          </div>
          <div class="switch-wrapper" style="min-height: 32px;">
            <el-switch v-if="!loading" v-model="websearch.enabled" active-text="开启" inactive-text="关闭"
              @change="saveConfig" />
          </div>
        </div>
      </div>

      <el-form label-position="top" class="config-form">
        <el-form-item>
          <div v-if="loading" class="skeleton-input"></div>
          <el-input v-else v-model="websearch.api_key" type="password" show-password
            placeholder="请输入 Tavily API Key，例如 tvly-xxxxxx" autocomplete="off" @change="saveConfig">
          </el-input>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.web-search-config-page {
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
      color: #303133;

      .page-icon {
        font-size: 30px;
        width: 32px;
        height: 32px;
        color: #303133;
      }
    }

    .header-subtitle {
      font-size: 14px;
      color: #64748b;
    }
  }
}

.web-search-config-section {
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

    .section-title-main {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }

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

    .switch-wrapper {
      display: flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
    }
  }

  .config-form {
    .el-form-item {
      margin-bottom: 16px;
    }

    .skeleton-input {
      width: 100%;
      height: 36px;
      border-radius: 999px;
      box-shadow: 0 0 0 1px #dcdfe6 inset;
      animation: skeleton-pulse 1.5s ease-in-out infinite;
    }

    :deep(.el-input__wrapper) {
      border-radius: 999px !important;
      padding-left: 18px;
      padding-right: 18px;
      box-shadow: 0 0 0 1px #dcdfe6 inset !important;
      transition: all .3s cubic-bezier(0.4, 0, 0.2, 1);
      background: #ffffff;
      min-height: 36px !important;
      height: 36px !important;
    }

    :deep(.el-input__inner) {
      color: #475569;
      font-size: 14px;
      line-height: 1.2;
    }

    :deep(.el-input__wrapper.is-hovering),
    :deep(.el-input__wrapper:hover) {
      box-shadow: 0 0 0 1px #a8abb2 inset !important;
    }

    :deep(.el-input__wrapper.is-focus),
    :deep(.el-input__wrapper.is-focused) {
      box-shadow: 0 0 0 1.5px #409eff inset !important;
    }
  }
}

@media (max-width: 768px) {
  .web-search-config-page {
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

@keyframes skeleton-pulse {
  0% {
    background-color: #ffffff;
    box-shadow: 0 0 0 1px #dcdfe6 inset;
  }

  50% {
    background-color: #f1f5f9;
    box-shadow: 0 0 0 1px #dcdfe6 inset;
  }

  100% {
    background-color: #ffffff;
    box-shadow: 0 0 0 1px #dcdfe6 inset;
  }
}

@keyframes skeleton-pulse-dark {
  0% {
    background-color: #2c2c2e;
    box-shadow: 0 0 0 1px #3a3a3c inset;
  }

  50% {
    background-color: #363638;
    box-shadow: 0 0 0 1px #3a3a3c inset;
  }

  100% {
    background-color: #2c2c2e;
    box-shadow: 0 0 0 1px #3a3a3c inset;
  }
}

/* 深色模式 */
.theme-dark {
  .web-search-config-page {
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

      .header-subtitle {
        color: rgba(255, 255, 255, 0.55);
      }
    }
  }

  .web-search-config-section {
    background: #242426;
    border-color: #2c2c2e;
    box-shadow: none;

    .section-title {
      h3 {
        color: #f5f5f7;
      }

      p {
        color: rgba(255, 255, 255, 0.55);
      }

      .switch-wrapper {
        :deep(.el-switch__label:not(.is-active)) {
          color: rgba(255, 255, 255, 0.55);
        }
      }
    }

    .config-form {
      .skeleton-input {
        animation: skeleton-pulse-dark 1.5s ease-in-out infinite;
      }

      :deep(.el-input__wrapper) {
        background-color: #2c2c2e;
        border-color: #3a3a3c;
        box-shadow: 0 0 0 1px #3a3a3c inset !important;
        transition: all .3s cubic-bezier(0.4, 0, 0.2, 1);
      }

      :deep(.el-input__inner) {
        color: #e5e7eb;
      }

      :deep(.el-input__suffix-inner .el-icon) {
        color: #9ca3af;
      }

      :deep(.el-input__wrapper.is-hovering),
      :deep(.el-input__wrapper:hover) {
        box-shadow: 0 0 0 1px #4b5563 inset !important;
      }

      :deep(.el-input__wrapper.is-focus),
      :deep(.el-input__wrapper.is-focused) {
        box-shadow: 0 0 0 1.5px #3b82f6 inset !important;
      }
    }
  }
}
</style>
