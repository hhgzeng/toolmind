<script setup lang="ts">
import { Setting, Sunny, Moon } from '@element-plus/icons-vue'
import { theme as useTheme } from '../../apis/theme'

const { theme, setTheme } = useTheme()
</script>

<template>
  <div class="general-settings-page">
    <div class="page-header">
      <h2>
        <el-icon class="page-icon">
          <Setting />
        </el-icon>
        通用设置
      </h2>
    </div>

    <div class="settings-section">
      <div class="section-title">
        <h3>主题</h3>
      </div>

      <div class="theme-control">
        <div class="theme-grid">
          <div
            class="theme-card"
            :class="{ active: theme === 'light' }"
            @click="setTheme('light')"
          >
            <div class="theme-icon light">
              <el-icon><Sunny /></el-icon>
            </div>
            <div class="theme-info">
              <h4>浅色</h4>
            </div>
          </div>

          <div
            class="theme-card"
            :class="{ active: theme === 'dark' }"
            @click="setTheme('dark')"
          >
            <div class="theme-icon dark">
              <el-icon><Moon /></el-icon>
            </div>
            <div class="theme-info">
              <h4>深色</h4>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.general-settings-page {
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

.settings-section {
  margin-top: 0;
  background: #ffffff;
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

  .theme-control {
    .theme-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 20px;
    }

    .theme-card {
      background: #f8f9fa;
      border-radius: 24px;
      padding: 20px;
      border: 1px solid #ebeef5;
      display: flex;
      align-items: center;
      gap: 16px;
      cursor: pointer;
      transition: all 0.25s ease;

      &:hover {
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.06);
        transform: translateY(-2px);
        border-color: #c6e2ff;
      }

      &.active {
        border-color: #409eff;
        box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.35);
        background: linear-gradient(135deg, #eef5ff, #ffffff);
      }

      .theme-icon {
        width: 48px;
        height: 48px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;

        &.light {
          background: rgba(251, 191, 36, 0.12);

          .el-icon {
            color: #f59e0b;
          }
        }

        &.dark {
          background: rgba(59, 130, 246, 0.12);

          .el-icon {
            color: #3b82f6;
          }
        }

        .el-icon {
          font-size: 24px;
        }
      }

      .theme-info {
        h4 {
          margin: 0 0 4px 0;
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }

        p {
          margin: 0;
          font-size: 13px;
          color: #606266;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .general-settings-page {
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

/* 深色模式 */
.theme-dark {
  .general-settings-page {
    background-color: #020617;

    .page-header {
      background: linear-gradient(to right, #020617, #0b1120);
      box-shadow: 0 8px 30px rgba(15, 23, 42, 0.9);

      .header-subtitle {
        color: #9ca3af;
      }
    }
  }

  .settings-section {
    background: #020617;
    border-color: #1f2937;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);

    .section-title {
      h3 {
        color: #e5e7eb;
      }

      p {
        color: #9ca3af;
      }
    }

    .theme-control {
      .theme-card {
        background: #020617;
        border-color: #1f2937;

        &:hover {
          border-color: #2563eb;
          box-shadow: 0 10px 30px rgba(37, 99, 235, 0.45);
        }

        &.active {
          background: radial-gradient(circle at top left, #1f2937, #020617);
          border-color: #2563eb;
          box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.7);
        }

        .theme-info {
          h4 {
            color: #e5e7eb;
          }

          p {
            color: #9ca3af;
          }
        }
      }
    }
  }
}
</style>

