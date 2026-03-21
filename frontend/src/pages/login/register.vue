<script setup lang="ts">
import { Lock, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { RegisterForm } from '../../api/auth'
import { registerAPI } from '../../api/auth'

const router = useRouter()

const registerForm = reactive<RegisterForm>({
  user_name: '',
  user_password: ''
})

const confirmPassword = ref('')
const loading = ref(false)

const validateForm = () => {
  if (!registerForm.user_name) {
    ElMessage.warning('请输入用户名')
    return false
  }

  if (registerForm.user_name.length > 20) {
    ElMessage.warning('用户名长度不应该超过20个字符')
    return false
  }

  if (!registerForm.user_password) {
    ElMessage.warning('请输入密码')
    return false
  }

  if (registerForm.user_password.length < 6) {
    ElMessage.warning('密码长度至少6个字符')
    return false
  }

  if (registerForm.user_password !== confirmPassword.value) {
    ElMessage.warning('两次输入的密码不一致')
    return false
  }

  return true
}

const handleRegister = async () => {
  if (!validateForm()) {
    return
  }

  try {
    loading.value = true
    const response = await registerAPI(registerForm)

    if (response.data.status_code === 200) {
      ElMessage.success('注册成功，请登录')
      // 跳转到登录页面
      router.push('/login')
    } else {
      ElMessage.error(response.data.status_message || '注册失败')
    }
  } catch (error: any) {
    console.error('注册错误:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('注册失败，请检查网络连接')
    }
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="register-container">
    <!-- 左侧 3D 图形 -->
    <div class="side-section left-section">
      <div class="graphic-container">
        <div class="cube-3d">
          <div class="cube-face front"></div>
          <div class="cube-face back"></div>
          <div class="cube-face right"></div>
          <div class="cube-face left"></div>
          <div class="cube-face top"></div>
          <div class="cube-face bottom"></div>
        </div>
        <div class="cylinder-3d"></div>
        <div class="sphere-3d"></div>
      </div>
    </div>

    <!-- 中间注册表单区域 -->
    <div class="center-section">
      <div class="register-form-container">
        <!-- Logo和标题 -->
        <div class="header">
          <div class="logo">
            <div class="logo-inner">
              <img class="logo-icon" src="../../assets/toolmind.png" alt="ToolMind" />
              <span class="logo-title">ToolMind</span>
            </div>
          </div>
        </div>

        <!-- 注册表单 -->
        <div class="register-form">
          <el-input v-model="registerForm.user_name" placeholder="请输入用户名（最多20个字符）" size="large" class="register-input"
            :prefix-icon="User" @keyup.enter="handleRegister" />

          <el-input v-model="registerForm.user_password" type="password" placeholder="请输入密码（至少6个字符）" size="large"
            class="register-input" :prefix-icon="Lock" show-password @keyup.enter="handleRegister" />

          <el-input v-model="confirmPassword" type="password" placeholder="请再次输入密码" size="large" class="register-input"
            :prefix-icon="Lock" show-password @keyup.enter="handleRegister" />

          <div class="form-actions">
            <div class="login-link">
              <span>已有账号？</span>
              <a href="#" @click="goToLogin">登录</a>
            </div>
          </div>

          <el-button type="primary" size="large" class="register-button" :loading="loading" @click="handleRegister">
            注册
          </el-button>
        </div>
      </div>
    </div>

    <!-- 右侧 3D 图形（镜像展示） -->
    <div class="side-section right-section">
      <div class="graphic-container graphic-right">
        <div class="cube-3d">
          <div class="cube-face front"></div>
          <div class="cube-face back"></div>
          <div class="cube-face right"></div>
          <div class="cube-face left"></div>
          <div class="cube-face top"></div>
          <div class="cube-face bottom"></div>
        </div>
        <div class="cylinder-3d"></div>
        <div class="sphere-3d"></div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.register-container {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.side-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: #ffffff;

  .graphic-container {
    position: relative;
    width: 400px;
    height: 400px;

    .cube-3d {
      position: absolute;
      width: 120px;
      height: 120px;
      top: 50px;
      left: 100px;
      transform-style: preserve-3d;
      animation: rotateCube 10s infinite linear;

      .cube-face {
        position: absolute;
        width: 120px;
        height: 120px;
        background: linear-gradient(45deg, #4f81ff, #3b66db);
        border: 1px solid rgba(255, 255, 255, 0.2);

        &.front {
          transform: rotateY(0deg) translateZ(60px);
        }

        &.back {
          transform: rotateY(180deg) translateZ(60px);
        }

        &.right {
          transform: rotateY(90deg) translateZ(60px);
        }

        &.left {
          transform: rotateY(-90deg) translateZ(60px);
        }

        &.top {
          transform: rotateX(90deg) translateZ(60px);
        }

        &.bottom {
          transform: rotateX(-90deg) translateZ(60px);
        }
      }
    }

    .cylinder-3d {
      position: absolute;
      width: 80px;
      height: 160px;
      top: 200px;
      left: 50px;
      background: linear-gradient(180deg, #6b9eff, #4f81ff);
      border-radius: 40px;
      animation: floatUp 6s ease-in-out infinite;
    }

    .sphere-3d {
      position: absolute;
      width: 60px;
      height: 60px;
      top: 120px;
      right: 80px;
      background: radial-gradient(circle at 30% 30%, #8bb6ff, #4f81ff);
      border-radius: 50%;
      animation: floatDown 8s ease-in-out infinite;
    }
  }

  .graphic-right {
    transform: scaleX(-1);
  }
}

.center-section {
  width: 450px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;

  .register-form-container {
    width: 320px;
    padding: 40px 0;

    .header {
      text-align: center;
      margin-bottom: 40px;

      .logo {
        margin-bottom: 16px;

        .logo-inner {
          display: inline-flex;
          align-items: center;
          gap: 10px;
        }

        .logo-icon {
          width: 36px;
          height: 36px;
          object-fit: contain;
        }

        .logo-title {
          font-size: 26px;
          font-weight: 700;
          letter-spacing: 1px;
          font-family: 'SF Pro Display', 'Helvetica Neue', 'Arial', sans-serif;
          color: #4D6BFE;
        }
      }
    }

    .register-form {
      .register-input {
        margin-bottom: 16px;

        :deep(.el-input__wrapper) {
          background: #f8f9fc;
          border: 1px solid #e1e5e9;
          border-radius: 999px;
          padding: 8px 18px;
          box-shadow: none;

          &:hover {
            border-color: #4f81ff;
          }

          &.is-focus {
            border-color: #4f81ff;
            box-shadow: 0 0 0 3px rgba(79, 129, 255, 0.1);
          }
        }

        :deep(.el-input__prefix) {
          font-size: 18px;
          color: #8a94a6;
          margin-right: 6px;
        }

        :deep(.el-input__inner) {
          color: #2c3e50;
          font-size: 15px;
          font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;
          font-weight: 400;

          &::placeholder {
            color: #a0a0a0;
            font-size: 14px;
          }
        }
      }

      .form-actions {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 24px;

        .login-link {
          font-size: 15px;
          color: #666;
          font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;

          a {
            color: #4f81ff;
            text-decoration: none;
            margin-left: 6px;
            font-weight: 500;
            transition: all 0.2s ease;

            &:hover {
              text-decoration: underline;
              color: #3b66db;
            }
          }
        }
      }

      .register-button {
        width: 100%;
        height: 52px;
        background: linear-gradient(45deg, #4f81ff, #3b66db);
        border: none;
        border-radius: 999px;
        font-size: 18px;
        font-weight: 600;
        font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;
        letter-spacing: 1px;
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-1px);
          box-shadow: 0 8px 25px rgba(79, 129, 255, 0.3);
        }

        &:active {
          transform: translateY(0);
        }
      }
    }


  }
}

@keyframes rotateCube {
  0% {
    transform: rotateX(0deg) rotateY(0deg);
  }

  100% {
    transform: rotateX(360deg) rotateY(360deg);
  }
}

@keyframes floatUp {

  0%,
  100% {
    transform: translateY(0px);
  }

  50% {
    transform: translateY(-15px);
  }
}

@keyframes floatDown {

  0%,
  100% {
    transform: translateY(0px);
  }

  50% {
    transform: translateY(10px);
  }
}

/* 深色模式 */
.theme-dark {
  .register-container {
    background: #18181b;
  }

  .side-section {
    background: #18181b;

    .graphic-container {
      .cube-3d {
        .cube-face {
          background: linear-gradient(45deg, #4d6bfe, #1d4ed8);
          border-color: rgba(255, 255, 255, 0.1);
        }
      }

      .cylinder-3d {
        background: linear-gradient(180deg, #4338ca, #1d4ed8);
      }

      .sphere-3d {
        background: radial-gradient(circle at 30% 30%, #60a5fa, #1d4ed8);
      }
    }
  }

  .center-section {
    background: #18181b;

    .register-form-container {
      .header {
        .logo {
          .logo-title {
            color: #4D6BFE;
          }
        }
      }

      .register-form {
        .register-input {
          :deep(.el-input__wrapper) {
            background: #18181b;
            border-color: #27272a;

            &:hover {
              border-color: #4d6bfe;
            }

            &.is-focus {
              border-color: #4d6bfe;
              box-shadow: 0 0 0 1px rgba(77, 107, 254, 0.65);
            }
          }

          :deep(.el-input__prefix) {
            color: #a1a1aa;
          }

          :deep(.el-input__inner) {
            color: #e5e7eb;

            &::placeholder {
              color: #6b7280;
            }
          }
        }

        .form-actions {
          .login-link {
            color: #a1a1aa;

            a {
              color: #93c5fd;

              &:hover {
                color: #bfdbfe;
              }
            }
          }
        }

        .register-button {
          background: linear-gradient(45deg, #4d6bfe, #2563eb);

          &:hover {
            box-shadow: 0 10px 28px rgba(37, 99, 235, 0.6);
          }
        }
      }


    }
  }
}
</style>