<template>
  <div class="login-container">
    <div class="login-bg">
      <div class="bg-shape shape-1"></div>
      <div class="bg-shape shape-2"></div>
      <div class="bg-shape shape-3"></div>
    </div>
    
    <div class="login-content">
      <div class="login-left">
        <div class="brand">
          <div class="brand-icon">
            <el-icon :size="48"><Monitor /></el-icon>
          </div>
          <h1>服务器硬盘巡检平台</h1>
          <p>Server Disk Inspection Platform</p>
        </div>
        <div class="features">
          <div class="feature-item">
            <el-icon><CircleCheck /></el-icon>
            <span>自动化巡检，实时监控服务器状态</span>
          </div>
          <div class="feature-item">
            <el-icon><CircleCheck /></el-icon>
            <span>智能告警，及时发现磁盘异常</span>
          </div>
          <div class="feature-item">
            <el-icon><CircleCheck /></el-icon>
            <span>可视化报表，数据一目了然</span>
          </div>
        </div>
      </div>
      
      <div class="login-right">
        <div class="login-card">
          <div class="login-header">
            <h2>欢迎回来</h2>
            <p>请登录您的账号以继续</p>
          </div>
          
          <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin" class="login-form">
            <el-form-item prop="username">
              <el-input 
                v-model="form.username" 
                placeholder="请输入用户名" 
                size="large"
                :prefix-icon="User"
                class="custom-input"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input 
                v-model="form.password" 
                type="password" 
                placeholder="请输入密码" 
                size="large"
                :prefix-icon="Lock"
                show-password
                class="custom-input"
              />
            </el-form-item>
            
            <div class="login-options">
              <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            </div>
            
            <el-form-item>
              <el-button 
                type="primary" 
                class="login-btn" 
                :loading="loading" 
                native-type="submit"
              >
                <span v-if="!loading">登 录</span>
                <span v-else>登录中...</span>
              </el-button>
            </el-form-item>
          </el-form>
          
          <div class="login-footer">
            <p>© 2024 服务器硬盘巡检平台</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Monitor, CircleCheck } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const rememberMe = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await userStore.login(form)
    if (res.success) {
      ElMessage.success('登录成功')
      router.push('/dashboard')
    } else {
      ElMessage.error(res.message || '登录失败')
    }
  } catch (e) {
    ElMessage.error('登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  
  .bg-shape {
    position: absolute;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.5;
    animation: float 20s ease-in-out infinite;
  }
  
  .shape-1 {
    width: 600px;
    height: 600px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    top: -200px;
    right: -100px;
    animation-delay: 0s;
  }
  
  .shape-2 {
    width: 400px;
    height: 400px;
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    bottom: -100px;
    left: -100px;
    animation-delay: -5s;
  }
  
  .shape-3 {
    width: 300px;
    height: 300px;
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    top: 50%;
    left: 30%;
    animation-delay: -10s;
  }
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  25% { transform: translate(30px, -30px) rotate(5deg); }
  50% { transform: translate(-20px, 20px) rotate(-5deg); }
  75% { transform: translate(20px, 30px) rotate(3deg); }
}

.login-content {
  display: flex;
  width: 900px;
  min-height: 520px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.login-left {
  flex: 1;
  padding: 48px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  color: #fff;
  
  .brand {
    margin-bottom: 48px;
    
    .brand-icon {
      width: 80px;
      height: 80px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 24px;
      box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
    }
    
    h1 {
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 8px;
      background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    p {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.6);
      letter-spacing: 1px;
    }
  }
  
  .features {
    .feature-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 0;
      color: rgba(255, 255, 255, 0.8);
      font-size: 14px;
      
      .el-icon {
        color: #67C23A;
        font-size: 18px;
      }
    }
  }
}

.login-right {
  width: 400px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 100%;
  padding: 48px;
  
  .login-header {
    text-align: center;
    margin-bottom: 32px;
    
    h2 {
      font-size: 24px;
      font-weight: 600;
      color: #1a1a2e;
      margin-bottom: 8px;
    }
    
    p {
      font-size: 14px;
      color: #909399;
    }
  }
}

.login-form {
  .el-form-item {
    margin-bottom: 24px;
  }
  
  :deep(.custom-input) {
    .el-input__wrapper {
      padding: 4px 16px;
      border-radius: 12px;
      box-shadow: 0 0 0 1px #dcdfe6;
      transition: all 0.3s;
      
      &:hover {
        box-shadow: 0 0 0 1px #c0c4cc;
      }
      
      &.is-focus {
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3);
      }
    }
    
    .el-input__inner {
      height: 44px;
    }
    
    .el-input__prefix {
      color: #909399;
    }
  }
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  
  :deep(.el-checkbox__label) {
    color: #606266;
    font-size: 13px;
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
  }
  
  &:active {
    transform: translateY(0);
  }
}

.login-footer {
  text-align: center;
  margin-top: 32px;
  
  p {
    font-size: 12px;
    color: #c0c4cc;
  }
}

@media (max-width: 900px) {
  .login-content {
    width: 95%;
    flex-direction: column;
    min-height: auto;
  }
  
  .login-left {
    padding: 32px;
    
    .brand {
      margin-bottom: 24px;
      
      h1 {
        font-size: 22px;
      }
    }
    
    .features {
      display: none;
    }
  }
  
  .login-right {
    width: 100%;
  }
  
  .login-card {
    padding: 32px;
  }
}
</style>
