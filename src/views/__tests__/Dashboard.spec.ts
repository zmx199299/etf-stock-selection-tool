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

  it('挂载后默认使用 cn 配色，并在切换到 intl 后同步更新首页关键语义颜色', async () => {
    const wrapper = mount(Dashboard)
    const colorModeStore = useColorModeStore()

    await flushPromises()

    expect(wrapper.get('[data-test="dashboard-change-513130"]').classes()).toContain('text-red-500')
    expect(wrapper.get('[data-test="dashboard-premium-513130"]').classes()).toContain('text-red-500')
    expect(wrapper.get('[data-test="dashboard-risk-bullish-513130"]').classes()).toContain('bg-red-500')
    expect(wrapper.get('[data-test="dashboard-risk-bearish-513130"]').classes()).toContain('bg-green-500')

    colorModeStore.setMode('intl')
    await flushPromises()

    expect(wrapper.get('[data-test="dashboard-change-513130"]').classes()).toContain('text-green-600')
    expect(wrapper.get('[data-test="dashboard-premium-513130"]').classes()).toContain('text-green-600')
    expect(wrapper.get('[data-test="dashboard-risk-bullish-513130"]').classes()).toContain('bg-green-500')
    expect(wrapper.get('[data-test="dashboard-risk-bearish-513130"]').classes()).toContain('bg-red-500')
  })

  it('页面挂载不会重置已有共享配色状态', async () => {
    const colorModeStore = useColorModeStore()
    colorModeStore.setMode('intl')
    localStorage.removeItem('market-color-mode')

    const wrapper = mount(Dashboard)

    await flushPromises()

    expect(wrapper.get('[data-test="dashboard-change-513130"]').classes()).toContain('text-green-600')
  })

  it('首页采用与第二页一致的页面壳层，并且不展示止损点字段', async () => {
    const wrapper = mount(Dashboard)

    await flushPromises()

    expect(wrapper.get('[data-test="dashboard-shell"]').classes()).toEqual(
      expect.arrayContaining(['min-h-full', 'bg-slate-50', 'p-4', 'md:p-6']),
    )
    expect(wrapper.get('[data-test="dashboard-topbar"]').classes()).toEqual(
      expect.arrayContaining(['rounded-2xl', 'border-slate-200', 'bg-white', 'p-4', 'md:p-5']),
    )
    expect(wrapper.text()).not.toContain('止损点')
  })

  it('首页顶部栏采用固定框架，右侧控制区与第二页基线一致', async () => {
    const wrapper = mount(Dashboard)

    await flushPromises()

    expect(wrapper.get('[data-test="dashboard-topbar-flex"]').classes()).toEqual(
      expect.arrayContaining(['flex', 'flex-col', 'gap-4', 'lg:flex-row', 'lg:items-center', 'lg:justify-between']),
    )
    expect(wrapper.get('[data-test="dashboard-topbar-left"]').classes()).toEqual(
      expect.arrayContaining(['space-y-1']),
    )
    expect(wrapper.get('[data-test="dashboard-topbar-right"]').classes()).toEqual(
      expect.arrayContaining(['flex', 'flex-col', 'gap-3', 'md:flex-row', 'md:items-center', 'lg:w-[380px]', 'lg:flex-none']),
    )
    expect(wrapper.get('[data-test="dashboard-tab-group"]').classes()).toEqual(
      expect.arrayContaining(['inline-flex', 'rounded-xl', 'bg-slate-100', 'p-1']),
    )
    expect(wrapper.get('[data-test="dashboard-control-slot"]').classes()).toEqual(
      expect.arrayContaining(['hidden', 'h-[42px]', 'md:block', 'lg:flex-1']),
    )
  })

  it('首页卡片区采用均布网格，避免瀑布流左对齐', async () => {
    const wrapper = mount(Dashboard)

    await flushPromises()

    expect(wrapper.get('[data-test="dashboard-card-grid"]').classes()).toEqual(
      expect.arrayContaining(['grid', 'gap-6', 'md:grid-cols-2', 'lg:grid-cols-3', 'xl:grid-cols-4', '2xl:grid-cols-6']),
    )
    expect(wrapper.get('[data-test="dashboard-card-grid"]').classes()).not.toEqual(
      expect.arrayContaining(['columns-1', 'md:columns-2', 'lg:columns-3']),
    )
  })
})
