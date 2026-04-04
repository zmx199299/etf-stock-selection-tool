import { flushPromises, mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Analysis from '../Analysis.vue'
import { useColorModeStore } from '../../stores/colorMode'
import { getSharedFundCards } from '../../utils/dashboardSignals'

const sharedCards = getSharedFundCards()
const defaultEntryCards = sharedCards.slice(0, 10)

const routeMock = vi.fn()
const pushMock = vi.fn()
const routeState = reactive({ query: { code: '510300' } as Record<string, string | undefined> })

vi.mock('vue-router', () => ({
  useRoute: () => routeMock(),
  useRouter: () => ({
    push: pushMock,
  }),
}))

describe('Analysis', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    routeState.query = { code: '510300' }
    pushMock.mockReset()
    pushMock.mockImplementation(async (location: { query?: Record<string, string | undefined> }) => {
      routeState.query = { ...(location.query ?? {}) }
    })
    routeMock.mockImplementation(() => routeState)
  })

  it('第三页沿用统一页面壳层与顶部横栏框架', () => {
    const wrapper = mount(Analysis)

    expect(wrapper.get('[data-test="analysis-shell"]').classes()).toEqual(
      expect.arrayContaining(['min-h-full', 'bg-slate-50', 'p-4', 'md:p-6']),
    )
    expect(wrapper.get('[data-test="analysis-topbar"]').classes()).toEqual(
      expect.arrayContaining(['rounded-2xl', 'border', 'border-slate-200', 'bg-white', 'p-4', 'md:p-5']),
    )
    expect(wrapper.get('[data-test="analysis-topbar-right"]').classes()).toEqual(
      expect.arrayContaining(['flex', 'flex-col', 'gap-3', 'md:flex-row', 'md:items-center', 'lg:w-[380px]', 'lg:flex-none']),
    )
  })

  it('带代码进入时按确认顺序展示四段内容', () => {
    const wrapper = mount(Analysis)

    const sectionOrder = wrapper.findAll('[data-test^="analysis-section-"]').map((node) => node.attributes('data-test'))

    expect(sectionOrder).toEqual([
      'analysis-section-summary',
      'analysis-section-strategy',
      'analysis-section-chart',
      'analysis-section-metrics',
    ])
    expect(wrapper.text()).toContain('沪深300ETF')
    expect(wrapper.text()).toContain('震荡偏强')
  })

  it('首屏摘要区与策略建议区采用 40/60 双栏布局并展示关键字段', () => {
    const wrapper = mount(Analysis)

    expect(wrapper.get('[data-test="analysis-hero-grid"]').classes()).toEqual(
      expect.arrayContaining(['grid', 'gap-4', 'lg:grid-cols-[2fr_3fr]']),
    )

    const pageText = wrapper.text()

    expect(pageText).toContain('沪深300ETF')
    expect(pageText).toContain('510300')
    expect(pageText).toContain('市场')
    expect(pageText).toContain('SH')
    expect(pageText).toContain('最新价')
    expect(pageText).toContain('4.123')
    expect(pageText).toContain('涨跌幅')
    expect(pageText).toContain('+0.56%')
    expect(pageText).toContain('参考净值')
    expect(pageText).toContain('4.118')
    expect(pageText).toContain('溢价率')
    expect(pageText).toContain('+0.12%')
    expect(pageText).toContain('风险等级')
    expect(pageText).toContain('中等波动')

    expect(pageText).toContain('买入区间')
    expect(pageText).toContain('4.05 - 4.10')
    expect(pageText).toContain('卖出区间')
    expect(pageText).toContain('4.22 - 4.28')
    expect(pageText).toContain('仓位建议')
    expect(pageText).toContain('建议 4 成以内仓位')
    expect(pageText).toContain('止盈止损')
    expect(pageText).toContain('跌破 3.98 止损')
    expect(pageText).toContain('4.22 分批止盈')
    expect(pageText).toContain('持有周期')
    expect(pageText).toContain('5 - 10 个交易日')
    expect(pageText).toContain('风险提示')
    expect(pageText).toContain('若量能不能持续放大，反弹空间会被压缩。')
  })

  it('图表区默认展示 day 周期，并从活动周期读取摘要与指标', () => {
    const wrapper = mount(Analysis)

    const periodSelect = wrapper.get('[data-test="analysis-period-select"]')

    expect((periodSelect.element as HTMLSelectElement).value).toBe('day')
    expect(wrapper.get('[data-test="analysis-period-summary"]').text()).toContain('日K')
    expect(wrapper.get('[data-test="analysis-chart-mock"]').text()).toContain('K 线')
    expect(wrapper.get('[data-test="analysis-chart-summary"]').text()).toContain('图表')
    expect(wrapper.findAll('[data-test="analysis-chart-candle"]')).toHaveLength(12)
    expect(wrapper.findAll('[data-test^="analysis-chart-volume-bar-"]')).toHaveLength(12)
    expect(wrapper.findAll('[data-test="analysis-metric-card"]')).toHaveLength(4)
    expect(wrapper.get('[data-test="analysis-metric-value-MACD"]').text()).toContain('金叉')
  })

  it('直接点击第三页时顶部显示承接自第一页的基金卡片，而不是固定示例按钮', async () => {
    routeState.query = {}
    const wrapper = mount(Analysis)

    await flushPromises()

    const entryStrip = wrapper.get('[data-test="analysis-entry-strip"]')
    const entryButtons = wrapper.findAll('[data-test^="analysis-entry-card-"]')

    expect(entryStrip.attributes('data-test')).toBe('analysis-entry-strip')
    expect(entryButtons).toHaveLength(10)
    expect(wrapper.find('[data-test="analysis-pick-159915"]').exists()).toBe(false)

    defaultEntryCards.forEach((card) => {
      expect(wrapper.get(`[data-test="analysis-entry-card-${card.code}"]`).text()).toContain(card.name)
    })
  })

  it('无参卡片页通过与首页同源的共享加载器生成入口卡片', async () => {
    routeState.query = {}
    vi.resetModules()
    vi.doMock('../../utils/dashboardSignals', async () => {
      const actual = await vi.importActual<typeof import('../../utils/dashboardSignals')>(
        '../../utils/dashboardSignals',
      )

      const cards = [
        {
          code: '699999',
          name: '联动基金A',
          tPlus: 'T+0',
          currentPrice: 1.111,
          changePct: 1.11,
          buyPrice: null,
          sellPrice: null,
          stopLoss: null,
          latestNav: 1.11,
          navDate: '2026-03-30',
          premiumRate: 0.11,
          expectedProfit: null,
          expectedProfitPct: null,
          maxLoss: null,
          maxLossPct: null,
        },
        ...actual.getSharedFundCards().slice(0, 9),
      ]

      return {
        ...actual,
        loadSharedFundCards: async () => cards,
        getSharedFundCards: () => cards,
        getAnalysisEntryCards: (routeCode?: string | null, sharedCards = cards) => actual.getAnalysisEntryCards(routeCode, sharedCards),
      }
    })

    const { default: SharedAnalysis } = await import('../Analysis.vue')
    const wrapper = mount(SharedAnalysis)

    await flushPromises()

    expect(wrapper.get('[data-test="analysis-entry-card-699999"]').text()).toContain('联动基金A')

    vi.doUnmock('../../utils/dashboardSignals')
  })

  it('无参卡片页首屏不会先显示本地 getter 卡片，再被同源加载结果覆盖', async () => {
    routeState.query = {}
    vi.resetModules()
    vi.doMock('../../utils/dashboardSignals', async () => {
      const actual = await vi.importActual<typeof import('../../utils/dashboardSignals')>(
        '../../utils/dashboardSignals',
      )

      return {
        ...actual,
        getSharedFundCards: () => [
          {
            code: '699998',
            name: '旧入口卡片',
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
            code: '699997',
            name: '新入口卡片',
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
        getAnalysisEntryCards: (routeCode?: string | null, sharedCards = []) => actual.getAnalysisEntryCards(routeCode, sharedCards),
      }
    })

    const { default: AsyncAnalysis } = await import('../Analysis.vue')
    const wrapper = mount(AsyncAnalysis)

    expect(wrapper.text()).not.toContain('旧入口卡片')

    await flushPromises()

    expect(wrapper.text()).toContain('新入口卡片')

    vi.doUnmock('../../utils/dashboardSignals')
  })

  it('路由未带 code 时保留顶部横栏与卡片页，但不显示详情主体', async () => {
    routeState.query = {}
    const wrapper = mount(Analysis)

    await flushPromises()

    expect(wrapper.find('[data-test="analysis-topbar"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="analysis-entry-strip"]').exists()).toBe(true)
    expect(wrapper.findAll('[data-test^="analysis-entry-card-"]')).toHaveLength(10)
    expect(wrapper.get('[data-test="analysis-empty-state"]').text()).toContain('请从顶部卡片或搜索选择基金')
    expect(wrapper.find('[data-test="analysis-section-summary"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="analysis-section-chart"]').exists()).toBe(false)
  })

  it('点击顶部基金卡片后进入纯详情页并重置周期为 day', async () => {
    routeState.query = {}
    const wrapper = mount(Analysis)

    await flushPromises()

    await wrapper.get('[data-test="analysis-entry-card-159915"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      name: 'analysis',
      query: { code: '159915' },
    })
    expect(wrapper.text()).toContain('创业板ETF')
    expect(wrapper.find('[data-test="analysis-empty-state"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="analysis-entry-strip"]').exists()).toBe(false)
    expect((wrapper.get('[data-test="analysis-period-select"]').element as HTMLSelectElement).value).toBe('day')
    expect(wrapper.get('[data-test="analysis-period-summary"]').text()).toContain('日K')
  })

  it('带 code 进入时直接显示纯详情页，不再展示顶部卡片页', () => {
    const wrapper = mount(Analysis)

    expect(wrapper.find('[data-test="analysis-topbar"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="analysis-entry-strip"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="analysis-empty-state"]').exists()).toBe(false)
    expect(wrapper.get('[data-test="analysis-section-summary"]').text()).toContain('沪深300ETF')
  })

  it('点击默认顶部卡片中的共享基金后会进入对应分析态，而不是回到空态', async () => {
    routeState.query = {}
    const wrapper = mount(Analysis)

    await flushPromises()

    await wrapper.get('[data-test="analysis-entry-card-513130"]').trigger('click')

    expect(wrapper.find('[data-test="analysis-empty-state"]').exists()).toBe(false)
    expect(wrapper.get('[data-test="analysis-section-summary"]').text()).toContain('恒生科技ETF')
  })

  it('无基金代码时仍允许页内搜索后切换到分析态', async () => {
    routeState.query = {}
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-search"]').setValue('创业板')
    expect(wrapper.findAll('[data-test="analysis-pick-159915"]')).toHaveLength(1)
    await wrapper.get('[data-test="analysis-pick-159915"]').trigger('click')

    expect(wrapper.text()).toContain('创业板ETF')
    expect(wrapper.find('[data-test="analysis-empty-state"]').exists()).toBe(false)
  })

  it('顶部搜索也能命中共享入口中的轻量分析基金', async () => {
    routeState.query = {}
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-search"]').setValue('513130')

    expect(wrapper.findAll('[data-test="analysis-pick-513130"]')).toHaveLength(1)

    await wrapper.get('[data-test="analysis-pick-513130"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      name: 'analysis',
      query: { code: '513130' },
    })
    expect(wrapper.get('[data-test="analysis-section-summary"]').text()).toContain('恒生科技ETF')
  })

  it('无效基金代码时保持空状态并显示无结果提示', async () => {
    routeState.query = { code: '000000' }
    const wrapper = mount(Analysis)

    expect(wrapper.get('[data-test="analysis-empty-state"]').text()).toContain('请从顶部卡片或搜索选择基金')

    await wrapper.get('[data-test="analysis-search"]').setValue('不存在')

    expect(wrapper.get('[data-test="analysis-empty-hint"]').text()).toContain('未找到匹配基金')
  })

  it('路由代码变化时优先展示新的基金内容', async () => {
    routeState.query = {}
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-search"]').setValue('创业板')
    await wrapper.get('[data-test="analysis-pick-159915"]').trigger('click')
    expect(wrapper.text()).toContain('创业板ETF')

    routeState.query = { code: '510300' }
    await wrapper.vm.$forceUpdate()
    await wrapper.vm.$nextTick()

    expect(wrapper.get('[data-test="analysis-section-summary"]').text()).toContain('沪深300ETF')
    expect(wrapper.get('[data-test="analysis-section-summary"]').text()).not.toContain('创业板ETF')
  })

  it('路由代码被清空后回到无代码引导态', async () => {
    routeState.query = {}
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-search"]').setValue('创业板')
    await wrapper.get('[data-test="analysis-pick-159915"]').trigger('click')
    expect(wrapper.text()).toContain('创业板ETF')

    routeState.query = { code: '510300' }
    await wrapper.vm.$nextTick()
    routeState.query = {}
    await wrapper.vm.$nextTick()

    expect(wrapper.get('[data-test="analysis-empty-state"]').text()).toContain('请从顶部卡片或搜索选择基金')
  })

  it('路由带 code 进入后页内切换基金，再清空路由时仍会回到空态', async () => {
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-search"]').setValue('创业板')
    await wrapper.get('[data-test="analysis-pick-159915"]').trigger('click')
    expect(wrapper.text()).toContain('创业板ETF')

    routeState.query = {}
    await wrapper.vm.$nextTick()

    expect(wrapper.get('[data-test="analysis-empty-state"]').text()).toContain('请从顶部卡片或搜索选择基金')
  })

  it('路由带入共享 getter 额外提供的 code 时，直接进入该基金详情态且不显示卡片页', () => {
    const wrapper = mount(Analysis)

    expect(getSharedFundCards().map((card) => card.code)).toContain('510300')
    expect(wrapper.find('[data-test="analysis-entry-strip"]').exists()).toBe(false)
    expect(wrapper.get('[data-test="analysis-section-summary"]').text()).toContain('沪深300ETF')
  })

  it('分析态下也可通过顶部搜索继续切换基金', async () => {
    const wrapper = mount(Analysis)

    expect(wrapper.get('[data-test="analysis-section-summary"]').text()).toContain('沪深300ETF')

    await wrapper.get('[data-test="analysis-search"]').setValue('创业板')
    await wrapper.get('[data-test="analysis-pick-159915"]').trigger('click')

    expect(wrapper.get('[data-test="analysis-section-summary"]').text()).toContain('创业板ETF')
    expect(wrapper.get('[data-test="analysis-section-summary"]').text()).not.toContain('沪深300ETF')
  })

  it('切换基金后图表周期会重置为默认 day', async () => {
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-period-select"]').setValue('week')
    expect((wrapper.get('[data-test="analysis-period-select"]').element as HTMLSelectElement).value).toBe('week')

    await wrapper.get('[data-test="analysis-search"]').setValue('创业板')
    await wrapper.get('[data-test="analysis-pick-159915"]').trigger('click')

    expect((wrapper.get('[data-test="analysis-period-select"]').element as HTMLSelectElement).value).toBe('day')
    expect(wrapper.get('[data-test="analysis-period-summary"]').text()).toContain('日K')
  })

  it('路由 code 变化后图表周期会重置为默认 day', async () => {
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-period-select"]').setValue('week')
    expect((wrapper.get('[data-test="analysis-period-select"]').element as HTMLSelectElement).value).toBe('week')

    routeState.query = { code: '159915' }
    await wrapper.vm.$nextTick()

    expect((wrapper.get('[data-test="analysis-period-select"]').element as HTMLSelectElement).value).toBe('day')
    expect(wrapper.get('[data-test="analysis-period-summary"]').text()).toContain('日K')
  })

  it('日K展示价格轴和时间轴，切到分时后显示分时线与均价线', async () => {
    const wrapper = mount(Analysis)

    expect(wrapper.findAll('[data-test="analysis-price-axis-label"]')).toHaveLength(4)
    expect(wrapper.findAll('[data-test="analysis-time-axis-label"]')).toHaveLength(5)
    expect(wrapper.findAll('[data-test="analysis-chart-candle"]')).toHaveLength(12)

    await wrapper.get('[data-test="analysis-period-select"]').setValue('intraday')

    expect(wrapper.find('[data-test="analysis-intraday-line"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="analysis-intraday-avg-line"]').exists()).toBe(true)
    expect(wrapper.findAll('[data-test="analysis-chart-candle"]')).toHaveLength(0)
    expect(wrapper.findAll('[data-test="analysis-price-axis-label"]')).toHaveLength(4)
    expect(wrapper.findAll('[data-test="analysis-time-axis-label"]')).toHaveLength(5)
    expect(wrapper.get('[data-test="analysis-chart-mock"]').text()).toContain('分时')
    expect(wrapper.get('[data-test="analysis-chart-mock"]').text()).not.toContain('分时 / K 线')
  })

  it('周期下拉文案与确认范围保持一致', () => {
    const wrapper = mount(Analysis)

    const optionTexts = wrapper.findAll('[data-test="analysis-period-select"] option').map((node) => node.text())

    expect(optionTexts).toEqual(['分时', '日K', '5分', '60分', '120分', '周K', '月K', '季K', '年K'])
  })

  it('切到周K后价格轴和时间轴跟随周K周期数据变化', async () => {
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-period-select"]').setValue('week')

    const priceLabels = wrapper.findAll('[data-test="analysis-price-axis-label"]').map((node) => node.text())
    const timeLabels = wrapper.findAll('[data-test="analysis-time-axis-label"]').map((node) => node.text())

    expect(wrapper.get('[data-test="analysis-period-summary"]').text()).toContain('周K')
    expect(priceLabels).toEqual(['3.80', '3.95', '4.10', '4.25'])
    expect(timeLabels).toEqual(['第1周', '第2周', '第3周', '第4周', '第5周'])
  })

  it('切到周K后图旁解读与技术指标卡随当前周期联动', async () => {
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-period-select"]').setValue('week')

    expect(wrapper.get('[data-test="analysis-period-summary"]').text()).toContain('周K')
    expect(wrapper.get('[data-test="analysis-chart-summary"]').text()).toBe('用于确认中期波段的支撑与压力区。')
    expect(wrapper.get('[data-test="analysis-chart-headline"]').text()).toBe('周线尝试站稳箱体上沿')
    expect(wrapper.text()).not.toContain('价格仍在近期整理平台上沿附近震荡')
    expect(wrapper.findAll('[data-test="analysis-metric-card"]')).toHaveLength(4)
    expect(wrapper.get('[data-test="analysis-metric-label-0"]').text()).toBe('周线趋势')
    expect(wrapper.get('[data-test="analysis-metric-value-0"]').text()).toBe('偏强')
    expect(wrapper.get('[data-test="analysis-metric-label-1"]').text()).toBe('占位指标 1')
    expect(wrapper.get('[data-test="analysis-metric-value-1"]').text()).toBe('--')
    expect(wrapper.get('[data-test="analysis-metric-summary-1"]').text()).toBe('当前周期 mock 指标待补充')
  })

  it('非分时 K 周期也展示各自的 K 线实体，不再是空主图', async () => {
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-period-select"]').setValue('m5')

    expect(wrapper.findAll('[data-test="analysis-chart-candle"]')).toHaveLength(12)

    await wrapper.get('[data-test="analysis-period-select"]').setValue('week')

    expect(wrapper.findAll('[data-test="analysis-chart-candle"]')).toHaveLength(12)
  })

  it('长周期 K 线高度会被限制在图表容器内，不会出现实体高过影线的异常形态', async () => {
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-period-select"]').setValue('year')

    const candleLine = wrapper.get('[data-test="analysis-chart-candle-0-line"]').attributes('style') ?? ''
    const candleBody = wrapper.get('[data-test="analysis-chart-candle-0-body"]').attributes('style') ?? ''
    const lineHeight = Number(candleLine.match(/height:\s*(\d+)px/)?.[1] ?? 0)
    const bodyHeight = Number(candleBody.match(/height:\s*(\d+)px/)?.[1] ?? 0)

    expect(lineHeight).toBeLessThanOrEqual(128)
    expect(bodyHeight).toBeLessThanOrEqual(lineHeight)
  })

  it('K 线 hover 时显示日期和 OHLC 浮层，移出后隐藏', async () => {
    const wrapper = mount(Analysis)

    const hitArea = wrapper.get('[data-test="analysis-chart-hit-area"]').element as HTMLDivElement
    vi.spyOn(hitArea, 'getBoundingClientRect').mockReturnValue({
      x: 40,
      y: 50,
      width: 320,
      height: 160,
      top: 50,
      right: 360,
      bottom: 210,
      left: 40,
      toJSON: () => ({}),
    })

    await wrapper.get('[data-test="analysis-chart-candle-hitbox-0"]').trigger('mouseenter', { clientX: 120, clientY: 96 })

    const tooltip = wrapper.get('[data-test="analysis-chart-tooltip"]')

    expect(tooltip.text()).toContain('日期：04-08')
    expect(tooltip.text()).toContain('开盘：4.010')
    expect(tooltip.text()).toContain('收盘：4.080')
    expect(tooltip.text()).toContain('最高：4.100')
    expect(tooltip.text()).toContain('最低：3.990')
    expect(tooltip.attributes('style')).toContain('left: 92px;')
    expect(tooltip.attributes('style')).toContain('top: 58px;')

    await wrapper.get('[data-test="analysis-chart-hit-area"]').trigger('mouseleave')

    expect(wrapper.find('[data-test="analysis-chart-tooltip"]').exists()).toBe(false)
  })

  it('分时 hover 时显示时间、价格和均价浮层', async () => {
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-period-select"]').setValue('intraday')
    const hitArea = wrapper.get('[data-test="analysis-chart-hit-area"]').element as HTMLDivElement
    vi.spyOn(hitArea, 'getBoundingClientRect').mockReturnValue({
      x: 20,
      y: 30,
      width: 280,
      height: 160,
      top: 30,
      right: 300,
      bottom: 190,
      left: 20,
      toJSON: () => ({}),
    })
    await wrapper.get('[data-test="analysis-intraday-hitbox-0"]').trigger('mouseenter', { clientX: 88, clientY: 72 })

    const tooltip = wrapper.get('[data-test="analysis-chart-tooltip"]')

    expect(tooltip.text()).toContain('时间：09:30')
    expect(tooltip.text()).toContain('价格：4.070')
    expect(tooltip.text()).toContain('均价：4.060')
    expect(tooltip.attributes('style')).toContain('left: 80px;')
    expect(tooltip.attributes('style')).toContain('top: 54px;')
  })

  it('切换基金时会立即清空当前 hover 浮层', async () => {
    routeState.query = {}
    const wrapper = mount(Analysis)

    await flushPromises()

    await wrapper.get('[data-test="analysis-entry-card-513130"]').trigger('click')

    const hitArea = wrapper.get('[data-test="analysis-chart-hit-area"]').element as HTMLDivElement
    vi.spyOn(hitArea, 'getBoundingClientRect').mockReturnValue({
      x: 40,
      y: 50,
      width: 320,
      height: 160,
      top: 50,
      right: 360,
      bottom: 210,
      left: 40,
      toJSON: () => ({}),
    })

    await wrapper.get('[data-test="analysis-chart-candle-hitbox-0"]').trigger('mouseenter', { clientX: 120, clientY: 96 })

    expect(wrapper.find('[data-test="analysis-chart-tooltip"]').exists()).toBe(true)

    await wrapper.get('[data-test="analysis-search"]').setValue('513500')
    await wrapper.get('[data-test="analysis-pick-513500"]').trigger('click')

    expect(wrapper.find('[data-test="analysis-chart-tooltip"]').exists()).toBe(false)
  })

  it('切到季K时不会因为重复时间轴文案触发 Vue 重复 key 警告', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-period-select"]').setValue('quarter')

    const loggedMessages = [...warnSpy.mock.calls, ...errorSpy.mock.calls].flat().join(' ')

    expect(loggedMessages).not.toContain('Duplicate keys found')

    warnSpy.mockRestore()
    errorSpy.mockRestore()
  })

  it('K 线与多空指标颜色跟随全局红绿配色方案切换', async () => {
    const wrapper = mount(Analysis)
    const colorModeStore = useColorModeStore()

    expect(wrapper.get('[data-test="analysis-chart-candle-0-body"]').classes()).toContain('bg-red-500')
    expect(wrapper.get('[data-test="analysis-chart-candle-1-body"]').classes()).toContain('bg-green-500')
    expect(wrapper.get('[data-test="analysis-metric-value-MACD"]').classes()).toContain('text-red-500')
    expect(wrapper.get('[data-test="analysis-metric-dot-0"]').classes()).toContain('bg-red-500')
    expect(wrapper.get('[data-test="analysis-metric-value-RSI"]').classes()).toContain('text-gray-500')

    await wrapper.get('[data-test="analysis-mode-intl"]').trigger('click')
    await wrapper.vm.$nextTick()

    expect(colorModeStore.mode).toBe('intl')
    expect(wrapper.get('[data-test="analysis-chart-candle-0-body"]').classes()).toContain('bg-green-500')
    expect(wrapper.get('[data-test="analysis-chart-candle-1-body"]').classes()).toContain('bg-red-500')
    expect(wrapper.get('[data-test="analysis-metric-value-MACD"]').classes()).toContain('text-green-600')
    expect(wrapper.get('[data-test="analysis-metric-dot-0"]').classes()).toContain('bg-green-500')
    expect(wrapper.get('[data-test="analysis-metric-value-RSI"]').classes()).toContain('text-gray-500')
  })

  it('切到周K后指标卡和成交量柱也继续服从全局红绿配色', async () => {
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-period-select"]').setValue('week')

    expect(wrapper.get('[data-test="analysis-metric-label-0"]').text()).toBe('周线趋势')
    expect(wrapper.get('[data-test="analysis-metric-value-0"]').classes()).toContain('text-red-500')
    expect(wrapper.get('[data-test="analysis-metric-dot-0"]').classes()).toContain('bg-red-500')
    expect(wrapper.get('[data-test="analysis-metric-label-1"]').text()).toBe('占位指标 1')
    expect(wrapper.get('[data-test="analysis-metric-value-1"]').classes()).toContain('text-gray-500')
    expect(wrapper.get('[data-test="analysis-chart-volume-bar-0"]').classes()).toContain('bg-red-500')

    await wrapper.get('[data-test="analysis-mode-intl"]').trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.get('[data-test="analysis-metric-value-0"]').classes()).toContain('text-green-600')
    expect(wrapper.get('[data-test="analysis-metric-dot-0"]').classes()).toContain('bg-green-500')
    expect(wrapper.get('[data-test="analysis-metric-value-1"]').classes()).toContain('text-gray-500')
    expect(wrapper.get('[data-test="analysis-chart-volume-bar-0"]').classes()).toContain('bg-green-500')
  })

  it('分时主线颜色也跟随全局红绿配色切换', async () => {
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-period-select"]').setValue('intraday')

    expect(wrapper.get('[data-test="analysis-intraday-line"]').attributes('stroke')).toBe('#ef4444')
    expect(wrapper.get('[data-test="analysis-intraday-avg-line"]').attributes('stroke')).toBe('#22c55e')

    await wrapper.get('[data-test="analysis-mode-intl"]').trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.get('[data-test="analysis-intraday-line"]').attributes('stroke')).toBe('#16a34a')
    expect(wrapper.get('[data-test="analysis-intraday-avg-line"]').attributes('stroke')).toBe('#ef4444')
  })
})
