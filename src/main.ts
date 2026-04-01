import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useColorModeStore } from './stores/colorMode'
import './style.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
useColorModeStore(pinia).hydrate()
app.use(router)
app.mount('#app')
