<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from './api/auth'
import { onSessionExpired } from './api/session'

const router = useRouter()

// 视图状态：select（用户选择）、login（登录流程）、home（业务页面）
const view = ref('loading')
let unsubscribeSession = null
const currentUser = ref(null)
const users = ref([])
const isLoading = ref(false)
const errorMsg = ref('')

// 登录流程状态
const STEP = { IDLE: 0, SHOW_LINK: 1, INPUT_CALLBACK: 2 }
const loginStep = ref(STEP.IDLE)
const loginUrl = ref('')
const loginState = ref('')
const callbackInput = ref('')

const loadUsers = async () => {
  try {
    const [cur, all] = await Promise.all([
      authService.getCurrentUser(),
      authService.getUsers()
    ])
    currentUser.value = cur
    users.value = all || []

    if (cur) {
      view.value = 'home'
    } else if (all && all.length > 0) {
      view.value = 'select'
    } else {
      view.value = 'login'
    }
  } catch (e) {
    console.error('Load error:', e)
    view.value = 'login'
  }
}

// 用户选择
const selectUser = async (userId) => {
  try {
    isLoading.value = true
    errorMsg.value = ''
    await authService.switchUser(userId)
    await loadUsers()
  } catch (e) {
    errorMsg.value = '选择用户失败'
  } finally {
    isLoading.value = false
  }
}

const goToLogin = () => {
  loginStep.value = STEP.IDLE
  view.value = 'login'
}

const goToSelect = () => {
  resetLogin()
  view.value = 'select'
}

// 登录流程
const startLogin = async () => {
  try {
    errorMsg.value = ''
    isLoading.value = true
    const data = await authService.getLoginUrl()
    loginUrl.value = data.login_url
    loginState.value = data.state
    loginStep.value = STEP.SHOW_LINK
  } catch (e) {
    errorMsg.value = '获取登录链接失败'
  } finally {
    isLoading.value = false
  }
}

const openLoginUrl = () => {
  window.open(loginUrl.value, '_blank', 'noopener,noreferrer')
  loginStep.value = STEP.INPUT_CALLBACK
}

const submitCallback = async () => {
  if (!callbackInput.value.trim()) {
    errorMsg.value = '请粘贴回调链接'
    return
  }
  try {
    errorMsg.value = ''
    isLoading.value = true
    await authService.handleCallback(callbackInput.value.trim(), loginState.value)
    resetLogin()
    await loadUsers()
  } catch (e) {
    errorMsg.value = e.message || '登录失败'
  } finally {
    isLoading.value = false
  }
}

const resetLogin = () => {
  loginStep.value = STEP.IDLE
  loginUrl.value = ''
  loginState.value = ''
  callbackInput.value = ''
  errorMsg.value = ''
}

// 登出
const logout = async () => {
  try {
    isLoading.value = true
    await authService.logout()
    currentUser.value = null
    await loadUsers()
  } catch (e) {
    errorMsg.value = '登出失败'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadUsers()
  // 监听 session 过期事件，跳转登录
  unsubscribeSession = onSessionExpired(() => {
    currentUser.value = null
    errorMsg.value = 'Session 已过期，请重新登录'
    view.value = 'login'
  })
})

onUnmounted(() => {
  if (unsubscribeSession) unsubscribeSession()
})
</script>

<template>
  <div class="app-wrapper">
    <div class="splatter splatter-1"></div>
    <div class="splatter splatter-2"></div>

    <!-- Loading -->
    <div v-if="view === 'loading'" class="loading-view">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- 用户选择页面 -->
    <div v-else-if="view === 'select'" class="card">
      <div class="header">
        <h1>Splatoon3 Assistant</h1>
        <p class="subtitle">选择账号</p>
      </div>

      <div class="user-list">
        <div
          v-for="u in users"
          :key="u.id"
          class="user-card"
          @click="selectUser(u.id)"
        >
          <div class="avatar">{{ (u.user_nickname || '?')[0] }}</div>
          <span class="user-name">{{ u.user_nickname || '未知用户' }}</span>
        </div>
      </div>

      <button @click="goToLogin" class="btn btn-secondary">
        + 添加其他账号
      </button>

      <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
    </div>

    <!-- 登录流程页面 -->
    <div v-else-if="view === 'login'" class="card">
      <div class="header">
        <h1>Splatoon3 Assistant</h1>
        <p class="subtitle">账号登录</p>
      </div>

      <div class="login-flow">
        <!-- Step 0: 开始 -->
        <div v-if="loginStep === STEP.IDLE">
          <button @click="startLogin" class="btn btn-primary" :disabled="isLoading">
            {{ isLoading ? '获取中...' : '获取登录链接' }}
          </button>
        </div>

        <!-- Step 1: 显示链接 -->
        <div v-else-if="loginStep === STEP.SHOW_LINK" class="step-content">
          <p class="step-hint">请点击下方按钮打开登录页面</p>
          <button @click="openLoginUrl" class="btn btn-primary">
            打开登录页面
          </button>
          <button @click="resetLogin" class="btn btn-text">取消</button>
        </div>

        <!-- Step 2: 输入回调 -->
        <div v-else-if="loginStep === STEP.INPUT_CALLBACK" class="step-content">
          <p class="step-hint">
            登录完成后，右键"选择此人"，选择"复制链接地址"，粘贴到下方输入框
          </p>
          <input
            v-model="callbackInput"
            type="text"
            class="callback-input"
            placeholder="npf71b963c1b7b6d119://auth..."
            @keyup.enter="submitCallback"
          />
          <button @click="submitCallback" class="btn btn-primary" :disabled="isLoading">
            {{ isLoading ? '验证中...' : '完成登录' }}
          </button>
          <button @click="resetLogin" class="btn btn-text">取消</button>
        </div>
      </div>

      <button v-if="users.length > 0 && loginStep === STEP.IDLE" @click="goToSelect" class="btn btn-text">
        ← 返回账号列表
      </button>

      <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
    </div>

    <!-- 业务主页（空页面） -->
    <div v-else-if="view === 'home'" class="home-view">
      <header class="top-bar">
        <nav class="nav-links">
          <a @click="router.push('/')" class="nav-link">首页</a>
          <a @click="router.push('/schedule')" class="nav-link">日程</a>
          <a @click="router.push('/battles')" class="nav-link">对战</a>
        </nav>
        <div class="user-section">
          <div class="user-info">
            <div class="avatar small">{{ (currentUser?.user_nickname || '?')[0] }}</div>
            <span class="user-name">{{ currentUser?.user_nickname || '未知用户' }}</span>
          </div>
          <button @click="logout" class="btn btn-logout" :disabled="isLoading">
            登出
          </button>
        </div>
      </header>

      <main class="main-content">
        <router-view></router-view>
      </main>

      <div v-if="errorMsg" class="error-toast">{{ errorMsg }}</div>
    </div>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background-color: #f0f0f0;
  font-family: 'M PLUS Rounded 1c', -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
}

.app-wrapper {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.splatter {
  position: fixed;
  z-index: 0;
  opacity: 0.12;
  pointer-events: none;
}

.splatter-1 {
  width: 500px;
  height: 500px;
  top: -100px;
  left: -100px;
  background: #603BFF;
  border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%;
  transform: rotate(15deg);
}

.splatter-2 {
  width: 400px;
  height: 400px;
  bottom: -50px;
  right: -50px;
  background: #EAFF3D;
  border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
}

/* Loading */
.loading-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f0f0f0;
  border-top-color: #E60012;
  border-radius: 50%;
  margin-bottom: 15px;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Card */
.card {
  position: relative;
  z-index: 10;
  background: #fff;
  width: 90%;
  max-width: 400px;
  margin: 80px auto;
  border-radius: 24px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.1);
  padding: 40px 30px;
  text-align: center;
}

.header {
  margin-bottom: 30px;
}

.header h1 {
  font-weight: 800;
  color: #2d2d2d;
  font-size: 1.5rem;
  margin-bottom: 8px;
}

.subtitle {
  color: #888;
  font-size: 14px;
}

/* User List */
.user-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px 20px;
  background: #f8f9fa;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.user-card:hover {
  background: #f0f1f2;
  transform: translateX(4px);
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #E60012, #ff4d4d);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 18px;
  flex-shrink: 0;
}

.avatar.small {
  width: 36px;
  height: 36px;
  font-size: 14px;
}

.user-name {
  font-weight: 600;
  color: #2d2d2d;
  font-size: 15px;
}

/* Login Flow */
.login-flow {
  margin-bottom: 20px;
}

.step-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-hint {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  line-height: 1.6;
}

.callback-input {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s;
}

.callback-input:focus {
  outline: none;
  border-color: #E60012;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  font-family: inherit;
  font-weight: 700;
  transition: all 0.15s;
}

.btn:active {
  transform: scale(0.97);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #E60012;
  color: #fff;
  padding: 14px 28px;
  border-radius: 50px;
  font-size: 15px;
  width: 100%;
  box-shadow: 0 4px 15px rgba(230, 0, 18, 0.25);
}

.btn-primary:hover:not(:disabled) {
  box-shadow: 0 6px 20px rgba(230, 0, 18, 0.35);
}

.btn-secondary {
  background: #f0f0f0;
  color: #666;
  padding: 14px 28px;
  border-radius: 50px;
  font-size: 14px;
  width: 100%;
}

.btn-secondary:hover {
  background: #e5e5e5;
  color: #333;
}

.btn-text {
  background: transparent;
  color: #888;
  padding: 10px;
  font-size: 14px;
}

.btn-text:hover {
  color: #E60012;
}

.btn-logout {
  background: transparent;
  color: #E60012;
  padding: 8px 16px;
  font-size: 14px;
  border: 1px solid #E60012;
  border-radius: 20px;
}

.btn-logout:hover {
  background: #E60012;
  color: #fff;
}

/* Home View */
.home-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.top-bar {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: #fff;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.nav-links {
  display: flex;
  gap: 8px;
}

.nav-link {
  padding: 8px 16px;
  border-radius: 20px;
  color: #666;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-link:hover {
  background: #f0f0f0;
  color: #333;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 10;
}

.empty-state {
  text-align: center;
  color: #666;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h2 {
  font-size: 1.5rem;
  color: #2d2d2d;
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
}

/* Error */
.error-msg {
  color: #E60012;
  margin-top: 15px;
  font-size: 14px;
  background: #fff5f5;
  padding: 10px 15px;
  border-radius: 8px;
}

.error-toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #E60012;
  color: #fff;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  z-index: 100;
}
</style>
