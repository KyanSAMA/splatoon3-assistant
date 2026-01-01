import { createRouter, createWebHashHistory } from 'vue-router'
import ScheduleView from '../views/ScheduleView.vue'
import BattleListView from '../views/BattleListView.vue'
import BattleDetailView from '../views/BattleDetailView.vue'

const routes = [
  { path: '/', redirect: '/schedule' },
  { path: '/schedule', name: 'schedule', component: ScheduleView },
  { path: '/battles', name: 'battles', component: BattleListView },
  { path: '/battles/:id', name: 'battle-detail', component: BattleDetailView },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
