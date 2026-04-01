import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Dashboard from '../Dashboard.vue'
import { useColorModeStore } from '../../stores/colorMode'

const pushMock = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}))

describe('Dashboard', () => {
  beforeEach(() => {
    localStorage.clear()
    pushMock.mockReset()
    setActivePinia(createPinia())
  })

  it('挂载后默认使用 cn 配色，并在切换到 intl 后同步更新涨跌类名', async () => {
    const wrapper = mount(Dashboard)
    const colorModeStore = useColorModeStore()

    await flushPromises()

    expect(wrapper.get('[data-test="dashboard-change-513130"]').classes()).toContain('text-red-500')

    colorModeStore.setMode('intl')
    await flushPromises()

    expect(wrapper.get('[data-test="dashboard-change-513130"]').classes()).toContain('text-green-600')
  })
})
