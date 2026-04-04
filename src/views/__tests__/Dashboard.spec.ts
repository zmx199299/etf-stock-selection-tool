import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Dashboard from '../Dashboard.vue'
import { useColorModeStore } from '../../stores/colorMode'
import { getSharedFundCards } from '../../utils/dashboardSignals'

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

  it('首页仍渲染共享基金卡片数据中的已知代码和名称', async () => {
    const wrapper = mount(Dashboard)
    const [firstSignal] = getSharedFundCards()

    await flushPromises()

    expect(wrapper.text()).toContain(firstSignal.name)
    expect(wrapper.text()).toContain(`${firstSignal.code}.SH`)
  })

  it('首页仍只展示默认 10 张卡片，不把额外详情入口基金带到首页', async () => {
    const wrapper = mount(Dashboard)

    await flushPromises()

    expect(wrapper.findAll('.fund-card')).toHaveLength(10)
    expect(wrapper.text()).not.toContain('沪深300ETF')
  })

  it('首页通过共享加载器读取基金卡片数据', async () => {
    vi.resetModules()
    vi.doMock('../../utils/dashboardSignals', async () => {
      const actual = await vi.importActual<typeof import('../../utils/dashboardSignals')>(
        '../../utils/dashboardSignals',
      )

        return {
          ...actual,
          loadSharedFundCards: async () => [
            {
              code: '599999',
              name: '哨兵基金',
              tPlus: 'T+0',
              currentPrice: 1.234,
              changePct: 0.66,
              buyPrice: null,
              sellPrice: null,
              stopLoss: null,
              latestNav: 1.233,
              navDate: '2026-03-30',
              premiumRate: 0.11,
              expectedProfit: null,
              expectedProfitPct: null,
              maxLoss: null,
              maxLossPct: null,
            },
          ],
          toSharedFundCards: () => [
            {
              code: '599999',
              name: '哨兵基金',
            tPlus: 'T+0',
            currentPrice: 1.234,
            changePct: 0.66,
            buyPrice: null,
            sellPrice: null,
            stopLoss: null,
            latestNav: 1.233,
            navDate: '2026-03-30',
            premiumRate: 0.11,
            expectedProfit: null,
            expectedProfitPct: null,
            maxLoss: null,
            maxLossPct: null,
          },
        ],
        getSharedFundCards: () => [
          {
            code: '599999',
            name: '哨兵基金',
            tPlus: 'T+0',
            currentPrice: 1.234,
            changePct: 0.66,
            buyPrice: null,
            sellPrice: null,
            stopLoss: null,
            latestNav: 1.233,
            navDate: '2026-03-30',
            premiumRate: 0.11,
            expectedProfit: null,
            expectedProfitPct: null,
            maxLoss: null,
            maxLossPct: null,
          },
        ],
      }
    })

    const { default: SharedDashboard } = await import('../Dashboard.vue')
    const wrapper = mount(SharedDashboard)

    await flushPromises()

    expect(wrapper.text()).toContain('哨兵基金')
    expect(wrapper.text()).toContain('599999.SH')

    vi.doUnmock('../../utils/dashboardSignals')
  })

  it('首页首屏不会先回退到本地 getter，再被异步加载结果覆盖', async () => {
    vi.resetModules()
    vi.doMock('../../utils/dashboardSignals', async () => {
      const actual = await vi.importActual<typeof import('../../utils/dashboardSignals')>(
        '../../utils/dashboardSignals',
      )

      return {
        ...actual,
        getSharedFundCards: () => [
          {
            code: '500001',
            name: '同步旧卡片',
            tPlus: 'T+0',
            currentPrice: 1,
            changePct: 0,
            buyPrice: null,
            sellPrice: null,
            stopLoss: null,
            latestNav: 1,
            navDate: '2026-03-30',
            premiumRate: 0,
            expectedProfit: null,
            expectedProfitPct: null,
            maxLoss: null,
            maxLossPct: null,
          },
        ],
        loadSharedFundCards: async () => [
          {
            code: '500002',
            name: '异步新卡片',
            tPlus: 'T+0',
            currentPrice: 1,
            changePct: 0,
            buyPrice: null,
            sellPrice: null,
            stopLoss: null,
            latestNav: 1,
            navDate: '2026-03-30',
            premiumRate: 0,
            expectedProfit: null,
            expectedProfitPct: null,
            maxLoss: null,
            maxLossPct: null,
          },
        ],
      }
    })

    const { default: AsyncDashboard } = await import('../Dashboard.vue')
    const wrapper = mount(AsyncDashboard)

    expect(wrapper.text()).not.toContain('同步旧卡片')

    await flushPromises()

    expect(wrapper.text()).toContain('异步新卡片')

    vi.doUnmock('../../utils/dashboardSignals')
  })

  it('首页面对缺失卡片字段时仍使用安全文案渲染', async () => {
    vi.resetModules()
    vi.doMock('../../utils/dashboardSignals', async () => {
      const actual = await vi.importActual<typeof import('../../utils/dashboardSignals')>(
        '../../utils/dashboardSignals',
      )

      return {
        ...actual,
        loadSharedFundCards: async () => [
          {
            code: '511111',
            name: '缺失值基金',
            tPlus: 'T+1',
            currentPrice: 1.2,
            changePct: 0,
            buyPrice: null,
            sellPrice: null,
            stopLoss: null,
            latestNav: null,
            navDate: null,
            premiumRate: null,
            expectedProfit: null,
            expectedProfitPct: null,
            maxLoss: null,
            maxLossPct: null,
          },
        ],
        toSharedFundCards: () => [
          {
            code: '511111',
            name: '缺失值基金',
            tPlus: 'T+1',
            currentPrice: 1.2,
            changePct: 0,
            buyPrice: null,
            sellPrice: null,
            stopLoss: null,
            latestNav: null,
            navDate: null,
            premiumRate: null,
            expectedProfit: null,
            expectedProfitPct: null,
            maxLoss: null,
            maxLossPct: null,
          },
        ],
        getSharedFundCards: () => [
          {
            code: '511111',
            name: '缺失值基金',
            tPlus: 'T+1',
            currentPrice: 1.2,
            changePct: 0,
            buyPrice: null,
            sellPrice: null,
            stopLoss: null,
            latestNav: null,
            navDate: null,
            premiumRate: null,
            expectedProfit: null,
            expectedProfitPct: null,
            maxLoss: null,
            maxLossPct: null,
          },
        ],
      }
    })

    const { default: SafeDashboard } = await import('../Dashboard.vue')
    const wrapper = mount(SafeDashboard)

    await flushPromises()

    expect(wrapper.text()).toContain('缺失值基金')
    expect(wrapper.text()).toContain('加载中')

    vi.doUnmock('../../utils/dashboardSignals')
  })
})
