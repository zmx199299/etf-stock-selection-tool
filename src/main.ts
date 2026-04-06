import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useColorModeStore } from './stores/colorMode'
import { ensureStartupSync } from './utils/startupSync'
import './style.css'
import 'echarts'
import ECharts from 'vue-echarts'

export async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)
  useColorModeStore(pinia).hydrate()
  app.use(router)
  app.component('v-chart', ECharts)

  await ensureStartupSync()

  app.mount('#app')
}

if (!import.meta.env.TEST) {
  void bootstrap()
}
