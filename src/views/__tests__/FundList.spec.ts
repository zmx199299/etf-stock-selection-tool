import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import FundList from '../FundList.vue'
import { COLOR_MODE_STORAGE_KEY, useColorModeStore } from '../../stores/colorMode'

const pushMock = vi.fn()
const openMock = vi.fn()

function createDeferred() {
  let resolve!: () => void
  const promise = new Promise<void>((resolver) => {
    resolve = resolver
  })

  return { promise, resolve }
}

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}))

const { sampleFunds } = vi.hoisted(() => ({
  sampleFunds: [
    {
      code: '510300',
      name: '沪深300ETF',
      prevClose: 4.1,
      open: 4.11,
      close: 4.123,
      high: 4.15,
      low: 4.08,
      volatility: 0.0172,
      macd: { value: '金叉', signal: 'bullish' },
      rsi: { value: '52', signal: 'bullish' },
      boll: { value: '中轨', signal: 'bullish' },
      ma5: { value: '上穿', signal: 'bullish' },
      ma20: { value: '粘合', signal: 'bullish' },
      score: 9,
    },
    {
      code: '159915',
      name: '创业板ETF',
      prevClose: 1,
      open: 0.99,
      close: 0.97,
      high: 1.01,
      low: 0.96,
      volatility: 5,
      macd: { value: '绿柱', signal: 'bearish' },
      rsi: { value: '25', signal: 'bearish' },
      boll: { value: '上轨', signal: 'bearish' },
      ma5: { value: '空头', signal: 'bearish' },
      ma20: { value: '向下', signal: 'bearish' },
      score: 1,
    },
    {
      code: '512100',
      name: '中证1000ETF',
      prevClose: 1,
      open: 1,
      close: 1,
      high: 1,
      low: 1,
      volatility: 1,
      macd: { value: '金叉', signal: 'bullish' },
      rsi: { value: '52', signal: 'bullish' },
      boll: { value: '中轨', signal: 'bullish' },
      ma5: { value: '上穿', signal: 'bullish' },
      ma20: { value: '粘合', signal: 'bullish' },
      score: 7,
    },
    {
      code: '512480',
      name: '半导体ETF',
      prevClose: 1,
      open: 1,
      close: 1,
      high: 1,
      low: 1,
      volatility: 1,
      macd: { value: '绿柱', signal: 'bearish' },
      rsi: { value: '25', signal: 'bearish' },
      boll: { value: '上轨', signal: 'bearish' },
      ma5: { value: '空头', signal: 'bearish' },
      ma20: { value: '向下', signal: 'bearish' },
      score: 2,
    },
  ]
}))

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn().mockResolvedValue(sampleFunds),
}))

describe('FundList', () => {
  beforeEach(() => {
    localStorage.clear()
    pushMock.mockReset()
    openMock.mockReset()
    vi.unstubAllEnvs()
    setActivePinia(createPinia())
    vi.stubGlobal('open', openMock)
  })

  afterEach(() => {
    vi.doUnmock('../../utils/startupSync')
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('搜索创业板后只显示匹配基金', async () => {
    const wrapper = mount(FundList)
    await flushPromises()

    const searchInput = wrapper.get('[data-test="fund-search"]')
    await searchInput.setValue('创业板')

    expect(wrapper.text()).toContain('创业板ETF')
    expect(wrapper.text()).not.toContain('沪深300ETF')
  })

  it('大屏容器不会被固定最大宽度限制', async () => {
    const wrapper = mount(FundList)
    await flushPromises()
    const shell = wrapper.get('section > div')

    expect(shell.classes()).not.toContain('max-w-7xl')
    expect(shell.classes()).toContain('w-full')
  })

  it('顶部文案使用全量监测口径', async () => {
    const wrapper = mount(FundList)
    await flushPromises()

    expect(wrapper.text()).toContain('全量场内基金（不含货币/债券基金）')
    expect(wrapper.text()).toContain('共监测4支')
    expect(wrapper.text()).not.toContain('场内基金宽表')
    expect(wrapper.text()).not.toContain('支持代码和名称搜索')
  })

  it('第二页顶部栏采用固定框架，右侧控制区宽度固定为统一基线', async () => {
    const wrapper = mount(FundList)
    await flushPromises()

    expect(wrapper.get('[data-test="fund-shell"]').classes()).toEqual(
      expect.arrayContaining(['min-h-full', 'bg-slate-50', 'p-4', 'md:p-6']),
    )
    expect(wrapper.get('[data-test="fund-topbar"]').classes()).toEqual(
      expect.arrayContaining(['rounded-2xl', 'border', 'border-slate-200', 'bg-white', 'p-4', 'md:p-5']),
    )
    expect(wrapper.get('[data-test="fund-topbar-flex"]').classes()).toEqual(
      expect.arrayContaining(['flex', 'flex-col', 'gap-4', 'lg:flex-row', 'lg:items-center', 'lg:justify-between']),
    )
    expect(wrapper.get('[data-test="fund-topbar-left"]').classes()).toEqual(
      expect.arrayContaining(['space-y-1']),
    )
    expect(wrapper.get('[data-test="fund-topbar-right"]').classes()).toEqual(
      expect.arrayContaining(['flex', 'flex-col', 'gap-3', 'md:flex-row', 'md:items-center', 'lg:w-[380px]', 'lg:flex-none']),
    )
    expect(wrapper.get('[data-test="fund-tab-group"]').classes()).toEqual(
      expect.arrayContaining(['inline-flex', 'rounded-xl', 'bg-slate-100', 'p-1']),
    )
  })

  it('切换到 intl 模式会同步更新 store 和 localStorage', async () => {
    const wrapper = mount(FundList)
    await flushPromises()
    const colorModeStore = useColorModeStore()

    await wrapper.get('[data-test="mode-intl"]').trigger('click')

    expect(colorModeStore.mode).toBe('intl')
    expect(localStorage.getItem(COLOR_MODE_STORAGE_KEY)).toBe('intl')
  })

  it('波动率按后端比率数据转换为百分比显示，并随共享颜色模式切换上涨语义类名', async () => {
    const wrapper = mount(FundList)
    await flushPromises()
    const changeCell = wrapper.get('[data-test="change-510300"]')

    expect(wrapper.text()).toContain('1.72%')
    expect(changeCell.classes()).toContain('text-red-500')

    await wrapper.get('[data-test="mode-intl"]').trigger('click')

    expect(wrapper.get('[data-test="change-510300"]').classes()).toContain('text-green-600')
  })

  it('点击代码名称区域会打开雪球详情页', async () => {
    const wrapper = mount(FundList)
    await flushPromises()

    await wrapper.get('[data-test="xueqiu-510300"]').trigger('click')

    expect(openMock).toHaveBeenCalledWith('https://xueqiu.com/S/SH510300', '_blank', 'noopener,noreferrer')
  })

  it('点击详情分析会跳转到 analysis 路由', async () => {
    const wrapper = mount(FundList)
    await flushPromises()

    await wrapper.get('[data-test="detail-510300"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      name: 'analysis',
      query: { code: '510300' },
    })
  })

  it('详情分析跳转会携带 code 查询参数，供第三页直接进入详情态', async () => {
    const wrapper = mount(FundList)
    await flushPromises()

    await wrapper.get('[data-test="detail-159915"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      name: 'analysis',
      query: { code: '159915' },
    })
  })

  it('搜索无结果时显示空状态文案', async () => {
    const wrapper = mount(FundList)
    await flushPromises()

    await wrapper.get('[data-test="fund-search"]').setValue('不存在的关键词')

    expect(wrapper.get('[data-test="fund-empty"]').text()).toContain('没有匹配的基金')
  })

  it('第二页挂载时先完成启动同步，再读取基金列表', async () => {
    vi.resetModules()
    vi.stubEnv('MODE', 'production')
    vi.stubEnv('DEV', false)

    const startupSync = createDeferred()
    const ensureStartupSync = vi.fn().mockImplementation(() => startupSync.promise)
    const invoke = vi.fn().mockResolvedValue([])

    vi.doMock('../../utils/startupSync', () => ({
      ensureStartupSync,
      getStartupSyncState: () => ({ status: 'success', message: '' }),
    }))

    vi.doMock('@tauri-apps/api/core', () => ({ invoke }))

    const { default: SyncFundList } = await import('../FundList.vue')
    mount(SyncFundList)

    await flushPromises()

    expect(ensureStartupSync).toHaveBeenCalledTimes(1)
    expect(invoke).not.toHaveBeenCalled()

    startupSync.resolve()
    await flushPromises()

    expect(invoke).toHaveBeenCalledWith('invoke_engine', {
      method: 'get_fund_list',
      params: {},
    })
  })

  it('启动同步未完成前第二页不会显示没有匹配的基金空状态', async () => {
    vi.resetModules()
    vi.stubEnv('MODE', 'production')
    vi.stubEnv('DEV', false)

    const startupSync = createDeferred()
    const ensureStartupSync = vi.fn().mockImplementation(() => startupSync.promise)
    const invoke = vi.fn().mockResolvedValue([])

    vi.doMock('../../utils/startupSync', () => ({
      ensureStartupSync,
      getStartupSyncState: () => ({ status: 'idle' }),
    }))

    vi.doMock('@tauri-apps/api/core', () => ({ invoke }))

    const { default: PendingFundList } = await import('../FundList.vue')
    const wrapper = mount(PendingFundList)

    await Promise.resolve()

    expect(ensureStartupSync).toHaveBeenCalledTimes(1)
    expect(invoke).not.toHaveBeenCalled()
    expect(wrapper.text()).not.toContain('没有匹配的基金')

    startupSync.resolve()
    await flushPromises()

    expect(wrapper.get('[data-test="fund-empty"]').text()).toContain('没有匹配的基金')
  })

  it('启动同步失败时第二页仍显示失败提示和基金列表', async () => {
    vi.resetModules()
    vi.stubEnv('MODE', 'production')
    vi.stubEnv('DEV', false)

    const invoke = vi.fn().mockResolvedValue([
      {
        code: '512100',
        name: '失败后基金',
        prevClose: 1,
        open: 1,
        close: 1.01,
        high: 1.02,
        low: 0.99,
        volatility: 0.03,
        macd: { signal: 'bullish', value: '金叉' },
        rsi: { signal: 'neutral', value: '50' },
        boll: { signal: 'neutral', value: '中轨' },
        ma5: { signal: 'bullish', value: '上穿' },
        ma20: { signal: 'neutral', value: '粘合' },
        score: 7,
      },
    ])

    vi.doMock('../../utils/startupSync', () => ({
      ensureStartupSync: vi.fn().mockResolvedValue(undefined),
      getStartupSyncState: () => ({ status: 'error', message: '引擎连接失败，当前显示本地旧数据' }),
    }))

    vi.doMock('@tauri-apps/api/core', () => ({ invoke }))

    const { default: ErrorFundList } = await import('../FundList.vue')
    const wrapper = mount(ErrorFundList)

    await flushPromises()

    expect(wrapper.get('[data-test="startup-sync-alert"]').text()).toContain('引擎连接失败')
    expect(wrapper.get('[data-test="startup-sync-alert"]').text()).toContain('本地旧数据')
    expect(wrapper.text()).toContain('失败后基金')
  })
})
