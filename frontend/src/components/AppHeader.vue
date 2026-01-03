<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const props = defineProps({
  mode: { type: String, default: 'full' }, // 'simple' | 'full'
  user: { type: Object, default: null }
})

const emit = defineEmits(['logout', 'open-settings', 'open-backup'])

const router = useRouter()
const route = useRoute()
const menuOpen = ref(false)
const menuRef = ref(null)

const toggleMenu = () => {
  menuOpen.value = !menuOpen.value
}

const closeMenu = (e) => {
  if (menuRef.value && !menuRef.value.contains(e.target)) {
    menuOpen.value = false
  }
}

const handleLogout = () => {
  menuOpen.value = false
  emit('logout')
}

const handleSettings = () => {
  menuOpen.value = false
  emit('open-settings')
}

const handleBackup = () => {
  menuOpen.value = false
  emit('open-backup')
}

onMounted(() => document.addEventListener('click', closeMenu))
onUnmounted(() => document.removeEventListener('click', closeMenu))
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <!-- Brand -->
      <div class="brand">
        <div class="brand-icon">🦑</div>
        <span class="brand-text">S3<span class="hl">Assistant</span></span>
      </div>

      <!-- Nav (full mode only) -->
      <nav v-if="mode === 'full'" class="nav-links">
        <a @click="router.push('/schedule')" class="nav-link" :class="{ active: route.path === '/schedule' }">日程</a>
        <a @click="router.push('/battles')" class="nav-link" :class="{ active: route.path.startsWith('/battles') }">对战</a>
        <a @click="router.push('/coop')" class="nav-link" :class="{ active: route.path.startsWith('/coop') }">打工</a>
      </nav>

      <!-- Right -->
      <div class="right-section">
        <!-- User (full mode) -->
        <div v-if="mode === 'full' && user" class="user-info">
          <div class="avatar">{{ (user.user_nickname || '?')[0] }}</div>
          <span class="name">{{ user.user_nickname || '未知' }}</span>
        </div>

        <!-- Hamburger -->
        <div class="menu-container" ref="menuRef">
          <button class="menu-btn" @click.stop="toggleMenu" aria-label="菜单">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
              <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
            </svg>
          </button>

          <Transition name="fade">
            <div v-if="menuOpen" class="ink-dropdown">
              <a class="ink-item" @click="handleSettings">
                <div class="ink-icon">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.488.488 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
                </div>
                <span>代理配置</span>
              </a>
              <a class="ink-item" @click="handleBackup">
                <div class="ink-icon">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19 12v7H5v-7H3v7c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-7h-2zm-6 .67l2.59-2.58L17 11.5l-5 5-5-5 1.41-1.41L11 12.67V3h2v9.67z"/></svg>
                </div>
                <span>数据备份</span>
              </a>
              <div class="ink-divider"></div>
              <a class="ink-item logout" @click="handleLogout">
                <div class="ink-icon">
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M10.09 15.59L11.5 17l5-5-5-5-1.41 1.41L12.67 11H3v2h9.67l-2.58 2.59zM19 3H5c-1.11 0-2 .9-2 2v4h2V5h14v14H5v-4H3v4c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/></svg>
                </div>
                <span>退出登录</span>
              </a>
            </div>
          </Transition>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0,0,0,0.05);
  height: 56px;
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  user-select: none;
}
.brand-icon { font-size: 22px; }
.brand-text { font-weight: 800; font-size: 17px; color: #2d2d2d; }
.hl { color: #E60012; }

.nav-links {
  display: flex;
  gap: 4px;
  background: #f0f0f0;
  padding: 4px;
  border-radius: 24px;
}
.nav-link {
  padding: 6px 18px;
  border-radius: 18px;
  color: #666;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.nav-link:hover { color: #E60012; background: rgba(255,255,255,0.6); }
.nav-link.active { background: #fff; color: #E60012; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }

.right-section { display: flex; align-items: center; gap: 14px; }

.user-info { display: flex; align-items: center; gap: 8px; }
.avatar {
  width: 30px; height: 30px; border-radius: 50%;
  background: linear-gradient(135deg, #E60012, #ff5252);
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 13px;
}
.name { font-weight: 600; font-size: 13px; color: #333; }

.menu-container { position: relative; }
.menu-btn {
  background: none; border: none; cursor: pointer;
  color: #333; padding: 6px; border-radius: 8px;
  display: flex; transition: background 0.15s;
}
.menu-btn:hover { background: #f0f0f0; }
.menu-btn:focus-visible { outline: 2px solid #603BFF; outline-offset: 2px; background: #f0f0f0; }

.ink-dropdown {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
  min-width: 160px;
  padding: 6px;
  border: 1px solid #eee;
  transform-origin: top right;
}

.ink-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 10px;
  color: #333;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 1, 0.5, 1);
  text-decoration: none;
}
.ink-item:hover { background: #f5f5f5; color: #603BFF; }
.ink-item.logout:hover { background: #fff5f5; color: #E60012; }
.ink-item:focus-visible { outline: 2px solid #603BFF; outline-offset: -2px; }

.ink-icon { display: flex; align-items: center; justify-content: center; color: inherit; }
.ink-divider { height: 1px; background: #eee; margin: 4px 10px; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.15s, transform 0.15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
