import { ref } from 'vue'
import { defineStore } from 'pinia'

export type ColorMode = 'cn' | 'intl'

export const COLOR_MODE_STORAGE_KEY = 'market-color-mode'

const DEFAULT_COLOR_MODE: ColorMode = 'cn'

function isColorMode(value: string | null): value is ColorMode {
  return value === 'cn' || value === 'intl'
}

export const useColorModeStore = defineStore('colorMode', () => {
  const mode = ref<ColorMode>(DEFAULT_COLOR_MODE)
  const hydrated = ref(false)

  function hydrate() {
    const storedMode = localStorage.getItem(COLOR_MODE_STORAGE_KEY)
    mode.value = isColorMode(storedMode) ? storedMode : DEFAULT_COLOR_MODE
    hydrated.value = true
  }

  function setMode(nextMode: ColorMode) {
    mode.value = nextMode
    localStorage.setItem(COLOR_MODE_STORAGE_KEY, nextMode)
  }

  function toggleMode() {
    setMode(mode.value === 'cn' ? 'intl' : 'cn')
  }

  return {
    mode,
    hydrated,
    hydrate,
    setMode,
    toggleMode,
  }
})
