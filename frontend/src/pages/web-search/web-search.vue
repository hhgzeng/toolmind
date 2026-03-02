<script setup lang="ts">
import { ref, onMounted } from "vue"
import { ElMessage } from "element-plus"
import { Connection } from "@element-plus/icons-vue"
import { getWebSearchAPI, updateWebSearchAPI, type WebSearchSettings } from "../../apis/web-search"

const loading = ref(false)
const saving = ref(false)

const websearch = ref<WebSearchSettings>({
  api_key: ""
})

const fetchConfig = async () => {
  loading.value = true
  try {
    const res = await getWebSearchAPI()
    if (res.data.status_code === 200 && res.data.data) {
      websearch.value.api_key = res.data.data.api_key || ""
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
      // ElMessage.success("已保存联网搜索配置")
      websearch.value.api_key = res.data.data.api_key || ""
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
        <el-icon class="page-icon"><Search /></el-icon>
        联网搜索
      </h2>
    </div>

    <div class="web-search-config-section" v-loading="loading || saving">
      <div class="section-title">
        <h3>Tavily API Key</h3>
        <p>请填入 Tavily API Key，以支持联网搜索功能。</p>
      </div>

      <el-form label-position="top" class="config-form">
        <el-form-item>
          <el-input
            v-model="websearch.api_key"
            type="password"
            show-password
            placeholder="请输入 Tavily API Key，例如 tvly-xxxxxx"
            autocomplete="off"
            @change="saveConfig"
          />
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

  .config-form {
    .el-form-item {
      margin-bottom: 16px;
    }

    :deep(.el-input__wrapper) {
      border-radius: 999px !important;
      padding-left: 18px;
      padding-right: 18px;
    }
  }
}

@media (max-width: 768px) {
  .tavily-config-page {
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

