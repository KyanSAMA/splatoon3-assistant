<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const menuItems = [
  { id: 'schedule', title: '日程表', icon: '📅', route: '/schedule', color: '#603BFF' },
  { id: 'battles', title: '对战记录', icon: '⚔️', route: '/battles', color: '#EAFF3D', disabled: true },
  { id: 'coop', title: '打工', icon: '🐟', route: '/coop', color: '#F75B28', disabled: true },
]

const navigate = (item) => {
  if (!item.disabled) {
    router.push(item.route)
  }
}
</script>

<template>
  <main class="home-container">
    <h2 class="section-title">功能菜单</h2>
    <div class="menu-grid">
      <div
        v-for="item in menuItems"
        :key="item.id"
        class="menu-card"
        :class="{ disabled: item.disabled }"
        :style="{ '--hover-color': item.color }"
        @click="navigate(item)"
      >
        <div class="icon">{{ item.icon }}</div>
        <div class="title">{{ item.title }}</div>
        <div v-if="item.disabled" class="coming-soon">即将推出</div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.home-container {
  padding: 24px;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}

.section-title {
  margin-bottom: 24px;
  color: #333;
  font-size: 18px;
  font-weight: 700;
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 20px;
}

.menu-card {
  background: #fff;
  border-radius: 16px;
  padding: 28px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
  position: relative;
}

.menu-card:hover:not(.disabled) {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-bottom: 4px solid var(--hover-color);
}

.menu-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.icon {
  font-size: 40px;
}

.title {
  font-weight: 700;
  color: #333;
  font-size: 15px;
}

.coming-soon {
  position: absolute;
  top: 10px;
  right: 10px;
  background: #f0f0f0;
  color: #888;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
