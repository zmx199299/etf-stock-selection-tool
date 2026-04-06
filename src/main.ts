import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useColorModeStore } from './stores/colorMode'
import { ensureStartupSync, setStartupSyncError } from './utils/startupSync'
import { invoke } from '@tauri-apps/api/core'
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

  try {
    await invoke('start_engine')
  } catch (e) {
    console.error('Failed to start engine:', e)
    const msg = e instanceof Error ? e.message : String(e)
    setStartupSyncError(`引擎启动失败: ${msg}`)
  }

  await ensureStartupSync()

  app.mount('#app')
}

if (!import.meta.env.TEST) {
  void bootstrap()
}
