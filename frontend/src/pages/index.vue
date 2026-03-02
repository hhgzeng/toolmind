<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { useRouter } from "vue-router"
import { useRoute } from "vue-router"
import { Setting } from "@element-plus/icons-vue"

const route = useRoute()
const router = useRouter()

const current = ref(route.meta.current)

const goCurrent = (item: string) => {
  const routes: Record<string, string> = {
    "workspace": "/workspace",
    "model": "/model",
    "mind-config": "/mind-config",
    "web-search": "/web-search",
    "mcp-server": "/mcp-server",
    "dashboard": "/dashboard",
    "general-settings": "/general-settings"
  }
  
  router.push(routes[item] || "/")
}

watch(
  route,
  (val) => {
    current.value = route.meta.current
  },
  {
    immediate: true
  }
)
</script>

<template>
  <div class="ai-body">
    <div class="ai-main">
      <div class="sidebar">
        <!-- 导航菜单 -->
        <div class="sidebar-nav">
          <el-menu
            active-text-color="#1a1a1a"
            background-color="transparent"
            class="el-menu-vertical-demo"
            :default-active="current"
            text-color="#333"
          >
            <el-menu-item index="workspace" @click="goCurrent('workspace')">
              <template #title>
                <el-icon><Back /></el-icon>
                <span>返回</span>
              </template>
            </el-menu-item>
            <el-menu-item index="general-settings" @click="goCurrent('general-settings')">
              <template #title>
                <el-icon><Setting /></el-icon>
                <span>通用设置</span>
              </template>
            </el-menu-item>
            <el-menu-item index="mind-config" @click="goCurrent('mind-config')">
              <template #title>
                <el-icon><Operation /></el-icon>
                <span>模型配置</span>
              </template>
            </el-menu-item>
            <el-menu-item index="web-search" @click="goCurrent('web-search')">
              <template #title>
                <el-icon><Search /></el-icon>
                <span>联网搜索</span>
              </template>
            </el-menu-item>
            <el-menu-item index="model" @click="goCurrent('model')">
              <template #title>
                <el-icon><Cpu /></el-icon>
                <span>模型管理</span>
              </template>
            </el-menu-item>
            <el-menu-item index="mcp-server" @click="goCurrent('mcp-server')">
              <template #title>
                <el-icon><Connection /></el-icon>
                <span>MCP 服务器</span>
              </template>
            </el-menu-item>
            <el-menu-item index="dashboard" @click="goCurrent('dashboard')">
              <template #title>
                <el-icon><DataAnalysis /></el-icon>
                <span>数据看板</span>
              </template>
            </el-menu-item>
          </el-menu>
        </div>
      </div>
      <div class="content">
        <router-view></router-view>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.ai-body {
  @import url('https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&family=Zhi+Mang+Xing&family=Ma+Shan+Zheng&display=swap');
  overflow: hidden;
  
  .ai-main {
    display: flex;
    height: 100vh;
    background-color: #ffffff;
    
    .sidebar {
      height: calc(100% - 32px);
      margin: 16px;
      width: 260px;
      min-width: 260px;
      background: #ffffff;
      display: flex;
      flex-direction: column;
      border: 1px solid #ebebeb;
      border-radius: 24px;
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);

      .sidebar-nav {
        flex: 1;
        padding: 8px 0;
      }
    }

    .content {
      flex: 1;
      overflow-y: auto;
      background-color: #ffffff;
      border-radius: 0;
      margin-left: 0;
      box-shadow: none;
    }
  }
}

// 菜单样式优化
:deep(.el-menu-vertical-demo) {
  border-right: none;
  background: transparent;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif;
  
  .el-menu-item {
    border-radius: 20px;
    margin: 4px 10px;
    padding: 0 16px;
    height: 52px;
    line-height: 52px;
    font-size: 15px;
    font-weight: 500;
    letter-spacing: 0.3px;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
    color: #333;
    
    &:hover {
      background: rgba(0, 0, 0, 0.04);
      color: #1a1a1a;
    }
    
    &.is-active {
      background: #f0f0f4;
      color: #1a1a1a;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02), inset 0 1px 1px rgba(0, 0, 0, 0.04);
      border: none;
      
      .el-icon {
        color: #1a1a1a;
      }
      
      span {
        font-weight: 600;
        color: #1a1a1a !important;
      }
    }
    
    .el-icon {
      margin-right: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      font-size: 20px;
      transition: all 0.2s ease;
    }
    
    span {
      position: relative;
      z-index: 1;
      transition: all 0.2s ease;
      font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif;
    }
  }
}

/* 深色模式 */
.theme-dark {
  .ai-body {
    .ai-main {
      background-color: #020617;

      .sidebar {
        background: #020617;
        border-color: #1f2937;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7);
      }

      .content {
        background-color: #020617;
      }
    }
  }

  ::deep(.el-menu-vertical-demo) {
    .el-menu-item {
      color: #e5e7eb;

      &:hover {
        background: rgba(148, 163, 184, 0.2);
        color: #f9fafb;
      }

      &.is-active {
        background: rgba(37, 99, 235, 0.18);
        color: #f9fafb;
        box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.6);

        span {
          color: #ffffff !important;
        }
      }
    }
  }
}
</style>
