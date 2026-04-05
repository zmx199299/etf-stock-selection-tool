import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useColorModeStore } from './stores/colorMode'
import { ensureStartupSync } from './utils/startupSync'
import './style.css'

export async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)
  useColorModeStore(pinia).hydrate()
  app.use(router)

  await ensureStartupSync()

  app.mount('#app')
}

if (!import.meta.env.TEST) {
  void bootstrap()
}
