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

  it('重复 hydrate() 不会再次覆盖当前内存态', () => {
    localStorage.setItem(COLOR_MODE_STORAGE_KEY, 'intl')
    const store = useColorModeStore()

    store.hydrate()
    store.setMode('cn')
    localStorage.setItem(COLOR_MODE_STORAGE_KEY, 'intl')

    store.hydrate()

    expect(store.mode).toBe('cn')
    expect(store.hydrated).toBe(true)
  })

  it('toggleMode() 会切换模式并持久化', () => {
    const store = useColorModeStore()

    store.toggleMode()
    expect(store.mode).toBe('intl')
    expect(localStorage.getItem(COLOR_MODE_STORAGE_KEY)).toBe('intl')

    store.toggleMode()
    expect(store.mode).toBe('cn')
    expect(localStorage.getItem(COLOR_MODE_STORAGE_KEY)).toBe('cn')
  })
})
