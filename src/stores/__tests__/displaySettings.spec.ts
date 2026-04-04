import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { CARD_COUNT_STORAGE_KEY, useDisplaySettingsStore } from '../displaySettings'

describe('displaySettings store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('默认 cardCount 为 10', () => {
    const store = useDisplaySettingsStore()

    expect(store.cardCount).toBe(10)
  })

  it('setCardCount() 更新内存值并持久化到 localStorage', () => {
    const store = useDisplaySettingsStore()

    store.setCardCount(6)

    expect(store.cardCount).toBe(6)
    expect(localStorage.getItem(CARD_COUNT_STORAGE_KEY)).toBe('6')
  })

  it('hydrate() 从 localStorage 读取已保存的值', () => {
    localStorage.setItem(CARD_COUNT_STORAGE_KEY, '8')
    const store = useDisplaySettingsStore()

    store.hydrate()

    expect(store.cardCount).toBe(8)
    expect(store.hydrated).toBe(true)
  })

  it('hydrate() 遇到无效值时回退到默认值 10', () => {
    localStorage.setItem(CARD_COUNT_STORAGE_KEY, '999')
    const store = useDisplaySettingsStore()

    store.hydrate()

    expect(store.cardCount).toBe(10)
    expect(store.hydrated).toBe(true)
  })

  it('hydrate() 遇到非数字字符串时回退到默认值 10', () => {
    localStorage.setItem(CARD_COUNT_STORAGE_KEY, 'abc')
    const store = useDisplaySettingsStore()

    store.hydrate()

    expect(store.cardCount).toBe(10)
    expect(store.hydrated).toBe(true)
  })

  it('重复 hydrate() 不会再次覆盖当前内存态', () => {
    localStorage.setItem(CARD_COUNT_STORAGE_KEY, '8')
    const store = useDisplaySettingsStore()

    store.hydrate()
    store.setCardCount(12)
    localStorage.setItem(CARD_COUNT_STORAGE_KEY, '6')

    store.hydrate()

    expect(store.cardCount).toBe(12)
  })
})
