import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { COLOR_MODE_STORAGE_KEY, useColorModeStore } from '../colorMode'

describe('colorMode store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('hydrate() 从 localStorage 读取 intl', () => {
    localStorage.setItem(COLOR_MODE_STORAGE_KEY, 'intl')
    const store = useColorModeStore()

    store.hydrate()

    expect(store.mode).toBe('intl')
    expect(store.hydrated).toBe(true)
  })

  it('setMode("intl") 会持久化到 localStorage', () => {
    const store = useColorModeStore()

    store.setMode('intl')

    expect(store.mode).toBe('intl')
    expect(localStorage.getItem(COLOR_MODE_STORAGE_KEY)).toBe('intl')
  })

  it('无效存储值会回退到 cn', () => {
    localStorage.setItem(COLOR_MODE_STORAGE_KEY, 'invalid')
    const store = useColorModeStore()

    store.hydrate()

    expect(store.mode).toBe('cn')
    expect(store.hydrated).toBe(true)
  })
})
