import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import Dashboard from '../views/Dashboard.vue'
import FundList from '../views/FundList.vue'
import Analysis from '../views/Analysis.vue'
import Settings from '../views/Settings.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        { path: '', name: 'dashboard', component: Dashboard },
        { path: 'funds', name: 'funds', component: FundList },
        { path: 'analysis', name: 'analysis', component: Analysis },
        { path: 'settings', name: 'settings', component: Settings },
      ],
    },
  ],
})

export default router