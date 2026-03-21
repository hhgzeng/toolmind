<script setup lang="ts">
import { Moon, Setting, Sunny } from '@element-plus/icons-vue';
import { theme as useTheme } from '../../api/theme';

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
          <div class="theme-card" :class="{ active: theme === 'light' }" @click="setTheme('light')">
            <div class="theme-icon light">
              <el-icon>
                <Sunny />
              </el-icon>
            </div>
            <div class="theme-info">
              <h4>浅色</h4>
            </div>
          </div>

          <div class="theme-card" :class="{ active: theme === 'dark' }" @click="setTheme('dark')">
            <div class="theme-icon dark">
              <el-icon>
                <Moon />
              </el-icon>
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
      color: #303133;

      .page-icon {
        font-size: 30px;
        width: 32px;
        height: 32px;
        color: #303133;
      }
    }

  }
}

.settings-section {
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
    }
  }
}

/* 深色模式 */
.theme-dark {
  .general-settings-page {
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
    }
  }

  .settings-section {
    background: #242426;
    border-color: #2c2c2e;
    box-shadow: none;

    .section-title {
      h3 {
        color: #f5f5f7;
      }
    }

    .theme-control {
      .theme-card {
        background: #2c2c2e;
        border-color: #3a3a3c;

        &:hover {
          background: rgba(255, 255, 255, 0.06);
          border-color: rgba(255, 255, 255, 0.18);
          box-shadow: none;
        }

        &.active {
          background: #3a3a3c;
          border-color: #4d6bfe;
          box-shadow: none;
        }

        .theme-icon {
          &.light {
            background: rgba(251, 191, 36, 0.1);

            .el-icon {
              color: #f59e0b;
            }
          }

          &.dark {
            background: rgba(77, 107, 254, 0.12);

            .el-icon {
              color: #4d6bfe;
            }
          }
        }

        .theme-info {
          h4 {
            color: #f5f5f7;
          }
        }
      }
    }
  }
}
</style>
