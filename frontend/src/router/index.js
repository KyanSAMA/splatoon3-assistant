import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ScheduleView from '../views/ScheduleView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/schedule', name: 'schedule', component: ScheduleView },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
