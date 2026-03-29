import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Screening from '../views/Screening.vue'
import Scoring from '../views/Scoring.vue'
import Config from '../views/Config.vue'
import Scheduler from '../views/Scheduler.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: Dashboard },
    { path: '/screening', name: 'screening', component: Screening },
    { path: '/scoring', name: 'scoring', component: Scoring },
    { path: '/config', name: 'config', component: Config },
    { path: '/scheduler', name: 'scheduler', component: Scheduler },
  ],
})

export default router