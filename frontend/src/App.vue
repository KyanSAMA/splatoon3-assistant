<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authService } from './api/auth'
import { splatoonService } from './api/splatoon'
import { onSessionExpired } from './api/session'
import { setGlobalSyncing } from './api/syncState'
import AppHeader from './components/AppHeader.vue'
import SyncProgress from './components/SyncProgress.vue'

const router = useRouter()
const route = useRoute()

// 视图状态：select（用户选择）、login（登录流程）、home（业务页面）
const view = ref('loading')
let unsubscribeSession = null
const currentUser = ref(null)
const users = ref([])
const isLoading = ref(false)
const errorMsg = ref('')

// 数据同步状态
const isSyncing = ref(false)
const syncStep = ref(0)
const syncMessage = ref('')

// 连接状态
const connectivityWarning = ref('')
const showSettings = ref(false)
const proxyConfig = ref({ address: '', enabled: false })
const isSavingSettings = ref(false)
const isLoadingSettings = ref(false)
const settingsMsg = ref({ text: '', type: '' })

// 备份状态
const showBackup = ref(false)
const isExporting = ref(false)
const isImporting = ref(false)
const backupMsg = ref({ text: '', type: '' })
const importResult = ref(null)

// 登录流程状态
const STEP = { IDLE: 0, SHOW_LINK: 1, INPUT_CALLBACK: 2 }
const loginStep = ref(STEP.IDLE)
const loginUrl = ref('')
const loginState = ref('')
const callbackInput = ref('')

// 检查连通性
const checkConnectivity = async () => {
  try {
    const res = await fetch('/api/config/check-connectivity')
    const data = await res.json()
    if (!data.reachable) {
      connectivityWarning.value = data.message
    } else {
      connectivityWarning.value = ''
    }
  } catch (e) {
    connectivityWarning.value = '无法连接后端服务'
  }
}

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

    // 显示同步进度
    isSyncing.value = true
    setGlobalSyncing(true)
    syncStep.value = 0
    syncMessage.value = '准备同步...'
    try {
      await splatoonService.refreshAllDataWithProgress((step, msg) => {
        syncStep.value = step
        syncMessage.value = msg
      })
    } catch (e) {
      console.error('数据同步失败:', e)
    } finally {
      setTimeout(() => {
        isSyncing.value = false
        setGlobalSyncing(false)
      }, 800)
    }
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

// 打开设置
const openSettings = async () => {
  showSettings.value = true
  settingsMsg.value = { text: '', type: '' }
  isLoadingSettings.value = true
  try {
    const res = await fetch('/api/config')
    if (!res.ok) throw new Error('load-failed')
    const data = await res.json()
    proxyConfig.value = {
      address: data['proxy.address'] || '',
      enabled: data['proxy.enabled'] === true || data['proxy.enabled'] === 'true'
    }
  } catch (e) {
    settingsMsg.value = { text: '读取配置失败，请稍后重试', type: 'error' }
  } finally {
    isLoadingSettings.value = false
  }
}

const closeSettings = () => {
  showSettings.value = false
}

// 点击外部关闭：需要按下和释放都在 overlay 上
const overlayMouseDownTarget = ref(null)
const onOverlayMouseDown = (e) => {
  overlayMouseDownTarget.value = e.target
}
const onOverlayMouseUp = (e) => {
  // 只有按下和释放都在 overlay 本身时才关闭
  if (overlayMouseDownTarget.value === e.currentTarget && e.target === e.currentTarget) {
    closeSettings()
  }
  overlayMouseDownTarget.value = null
}

const saveProxySettings = async () => {
  const trimmedAddress = proxyConfig.value.address.trim()
  proxyConfig.value.address = trimmedAddress

  // 验证：启用时必须填写有效地址
  if (proxyConfig.value.enabled && !trimmedAddress) {
    settingsMsg.value = { text: '启用时需填写代理地址', type: 'error' }
    return
  }

  // 格式验证 host:port（端口必填）
  if (trimmedAddress && !/^[\w.-]+:\d{1,5}$/.test(trimmedAddress)) {
    settingsMsg.value = { text: '格式无效，请输入 主机:端口', type: 'error' }
    return
  }

  isSavingSettings.value = true
  settingsMsg.value = { text: '', type: '' }
  try {
    // 顺序调用避免部分成功
    const addressRes = await fetch('/api/config/proxy.address', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value: trimmedAddress })
    })
    if (!addressRes.ok) throw new Error('update-address-failed')

    const enabledRes = await fetch('/api/config/proxy.enabled', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value: proxyConfig.value.enabled })
    })
    if (!enabledRes.ok) throw new Error('update-enabled-failed')

    // 保存成功，短暂显示后关闭弹窗
    settingsMsg.value = { text: '配置已保存', type: 'success' }
    setTimeout(() => {
      showSettings.value = false
      checkConnectivity()
    }, 800)
  } catch (e) {
    settingsMsg.value = { text: '保存失败，请检查网络', type: 'error' }
  } finally {
    isSavingSettings.value = false
  }
}

// 备份弹窗
const openBackup = () => {
  showBackup.value = true
  backupMsg.value = { text: '', type: '' }
  importResult.value = null
}

const closeBackup = () => {
  showBackup.value = false
}

const backupOverlayMouseDownTarget = ref(null)
const onBackupOverlayMouseDown = (e) => {
  backupOverlayMouseDownTarget.value = e.target
}
const onBackupOverlayMouseUp = (e) => {
  if (backupOverlayMouseDownTarget.value === e.currentTarget && e.target === e.currentTarget) {
    closeBackup()
  }
  backupOverlayMouseDownTarget.value = null
}

const exportData = async () => {
  isExporting.value = true
  backupMsg.value = { text: '', type: '' }
  try {
    const res = await fetch('/api/data/export')
    if (!res.ok) throw new Error('export-failed')
    const data = await res.json()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `splatoon3_backup_${data.user?.user_nickname || 'unknown'}_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    backupMsg.value = { text: '导出成功', type: 'success' }
  } catch (e) {
    backupMsg.value = { text: '导出失败，请稍后重试', type: 'error' }
  } finally {
    isExporting.value = false
  }
}

const importData = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return

  isImporting.value = true
  backupMsg.value = { text: '', type: '' }
  importResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch('/api/data/import', {
      method: 'POST',
      body: formData
    })
    const result = await res.json()
    if (!res.ok) {
      throw new Error(result.detail || 'import-failed')
    }
    importResult.value = result
    if (result.success) {
      backupMsg.value = { text: '导入成功', type: 'success' }
    } else {
      backupMsg.value = { text: result.errors?.join(', ') || '导入失败', type: 'error' }
    }
  } catch (e) {
    backupMsg.value = { text: e.message || '导入失败', type: 'error' }
  } finally {
    isImporting.value = false
    e.target.value = ''
  }
}

// 监听视图变化，进入登录页时检查连通性
watch(view, (val) => {
  if (val === 'login' || val === 'select') {
    checkConnectivity()
  }
})

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

    <!-- Header (登录/选择页使用简化模式) -->
    <AppHeader
      v-if="view !== 'loading'"
      :mode="view === 'home' ? 'full' : 'simple'"
      :user="currentUser"
      @logout="logout"
      @open-settings="openSettings"
      @open-backup="openBackup"
    />

    <!-- Loading -->
    <div v-if="view === 'loading'" class="loading-view">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- 用户选择页面 -->
    <div v-else-if="view === 'select'" class="card">
      <!-- 连通性警告 -->
      <div v-if="connectivityWarning" class="warning-banner">
        ⚠️ {{ connectivityWarning }}
      </div>

      <div class="header">
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
      <!-- 连通性警告 -->
      <div v-if="connectivityWarning" class="warning-banner">
        ⚠️ {{ connectivityWarning }}
      </div>

      <div class="header">
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

    <!-- 业务主页 -->
    <div v-else-if="view === 'home'" class="home-view">
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <keep-alive :include="['BattleListView', 'CoopListView']">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </main>

      <div v-if="errorMsg" class="error-toast">{{ errorMsg }}</div>
    </div>

    <!-- 设置弹窗 -->
    <Teleport to="body">
      <div v-if="showSettings" class="settings-overlay" @mousedown="onOverlayMouseDown" @mouseup="onOverlayMouseUp">
        <div class="settings-modal">
          <div class="settings-header">
            <h3>代理配置</h3>
            <button class="close-btn" @click="closeSettings" aria-label="关闭设置">✕</button>
          </div>
          <div class="settings-body">
            <div class="form-group">
              <label class="form-label">代理地址</label>
              <input
                v-model="proxyConfig.address"
                type="text"
                class="ink-input"
                placeholder="127.0.0.1:7890"
              />
            </div>
            <div class="form-group row">
              <label class="form-label">是否启用代理</label>
              <label class="toggle-switch">
                <input type="checkbox" v-model="proxyConfig.enabled">
                <span class="slider"></span>
              </label>
            </div>
            <div class="settings-footer">
              <div v-if="settingsMsg.text" :class="['msg', settingsMsg.type]">{{ settingsMsg.text }}</div>
              <button class="btn-save" @click="saveProxySettings" :disabled="isSavingSettings || isLoadingSettings">
                {{ isSavingSettings ? '保存中...' : (isLoadingSettings ? '加载中...' : '保存配置') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 备份弹窗 -->
    <Teleport to="body">
      <div v-if="showBackup" class="settings-overlay" @mousedown="onBackupOverlayMouseDown" @mouseup="onBackupOverlayMouseUp">
        <div class="settings-modal backup-modal">
          <div class="settings-header">
            <h3>数据备份</h3>
            <button class="close-btn" @click="closeBackup" aria-label="关闭">✕</button>
          </div>
          <div class="settings-body">
            <div class="backup-section">
              <div class="backup-title">导出数据</div>
              <p class="backup-desc">将所有对战、打工记录导出为 JSON 文件</p>
              <button class="btn-backup" @click="exportData" :disabled="isExporting">
                {{ isExporting ? '导出中...' : '导出数据' }}
              </button>
            </div>

            <div class="backup-divider"></div>

            <div class="backup-section">
              <div class="backup-title">导入数据</div>
              <p class="backup-desc">从备份文件恢复数据，已存在的记录会跳过</p>
              <label class="btn-backup btn-import" :class="{ disabled: isImporting }">
                {{ isImporting ? '导入中...' : '选择文件' }}
                <input type="file" accept=".json" @change="importData" :disabled="isImporting" hidden>
              </label>
            </div>

            <div v-if="importResult" class="import-result">
              <div class="result-row"><span>对战</span><span>导入 {{ importResult.battles_imported }}，跳过 {{ importResult.battles_skipped }}</span></div>
              <div class="result-row"><span>打工</span><span>导入 {{ importResult.coops_imported }}，跳过 {{ importResult.coops_skipped }}</span></div>
              <div class="result-row"><span>地图记录</span><span>导入 {{ importResult.stage_records_imported }}，跳过 {{ importResult.stage_records_skipped }}</span></div>
              <div class="result-row"><span>武器记录</span><span>导入 {{ importResult.weapon_records_imported }}，跳过 {{ importResult.weapon_records_skipped }}</span></div>
            </div>

            <div v-if="backupMsg.text" :class="['msg', backupMsg.type]" style="margin-top: 16px;">{{ backupMsg.text }}</div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 数据同步进度 -->
    <SyncProgress v-model="isSyncing" :step="syncStep" :message="syncMessage" />
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
  margin: 80px auto 40px;
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

/* Warning Banner */
.warning-banner {
  background: #fff3cd;
  color: #856404;
  padding: 12px 16px;
  border-radius: 10px;
  margin-bottom: 20px;
  font-size: 13px;
  border: 1px solid #ffeeba;
  text-align: left;
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

/* Home View */
.home-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding-top: 56px;
}

.main-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 10;
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

/* Settings Modal */
.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.settings-modal {
  background: #fff;
  border-radius: 16px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.settings-header h3 {
  font-size: 16px;
  font-weight: 700;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  color: #999;
  cursor: pointer;
  padding: 4px;
}

.close-btn:hover {
  color: #E60012;
}
.close-btn:focus-visible {
  outline: 2px solid #603BFF;
  outline-offset: 2px;
}

.settings-body {
  padding: 24px;
}

.form-group { margin-bottom: 20px; }
.form-group.row { display: flex; justify-content: space-between; align-items: center; }

.form-label { display: block; font-weight: 700; font-size: 14px; color: #333; margin-bottom: 8px; }
.form-group.row .form-label { margin-bottom: 0; }

.ink-input {
  width: 100%;
  padding: 12px 16px;
  background: #f8f9fa;
  border: 2px solid #eee;
  border-radius: 12px;
  font-family: inherit;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}
.ink-input:focus { outline: none; border-color: #603BFF; background: #fff; }

/* Toggle Switch */
.toggle-switch { position: relative; display: inline-block; width: 50px; height: 26px; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute; cursor: pointer; inset: 0;
  background-color: #ccc; border-radius: 34px; transition: .3s;
}
.slider:before {
  position: absolute; content: ""; height: 20px; width: 20px;
  left: 3px; bottom: 3px; background-color: white; border-radius: 50%; transition: .3s;
}
input:checked + .slider { background-color: #603BFF; }
input:checked + .slider:before { transform: translateX(24px); }
.toggle-switch input:focus-visible + .slider {
  outline: 2px solid #603BFF;
  outline-offset: 2px;
}

.settings-footer { display: flex; align-items: center; justify-content: flex-end; gap: 12px; margin-top: 24px; }

.btn-save {
  background: #603BFF;
  color: #fff;
  padding: 10px 24px;
  border-radius: 20px;
  border: none;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-save:hover { background: #5029ff; transform: translateY(-1px); }
.btn-save:disabled { opacity: 0.7; cursor: default; transform: none; }
.btn-save:focus-visible { outline: 2px solid #EAFF3D; outline-offset: 2px; }

.msg { font-size: 13px; font-weight: 600; }
.msg.success { color: #2eb82e; }
.msg.error { color: #E60012; }

/* Backup Modal */
.backup-section { margin-bottom: 8px; }
.backup-title { font-weight: 700; font-size: 15px; color: #333; margin-bottom: 6px; }
.backup-desc { font-size: 13px; color: #888; margin-bottom: 12px; }
.backup-divider { height: 1px; background: #eee; margin: 20px 0; }

.btn-backup {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #603BFF;
  color: #fff;
  padding: 10px 20px;
  border-radius: 20px;
  border: none;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-backup:hover { background: #5029ff; transform: translateY(-1px); }
.btn-backup:disabled, .btn-backup.disabled { opacity: 0.7; cursor: default; transform: none; }
.btn-import { background: #E60012; }
.btn-import:hover { background: #cc0010; }

.import-result {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 14px 16px;
  margin-top: 16px;
}
.result-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #555;
  padding: 4px 0;
}
.result-row span:first-child { font-weight: 600; color: #333; }
</style>
