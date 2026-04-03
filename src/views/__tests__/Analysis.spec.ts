import { mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Analysis from '../Analysis.vue'
import { useColorModeStore } from '../../stores/colorMode'

const routeMock = vi.fn()
const routeState = reactive({ query: { code: '510300' } as Record<string, string | undefined> })

vi.mock('vue-router', () => ({
  useRoute: () => routeMock(),
}))

describe('Analysis', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    routeState.query = { code: '510300' }
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

  it('无基金代码时显示引导卡，并允许页内搜索后切换到分析态', async () => {
    routeState.query = {}
    const wrapper = mount(Analysis)

    expect(wrapper.get('[data-test="analysis-empty-state"]').text()).toContain('请选择基金')

    await wrapper.get('[data-test="analysis-search"]').setValue('创业板')
    expect(wrapper.findAll('[data-test="analysis-pick-159915"]')).toHaveLength(1)
    await wrapper.get('[data-test="analysis-pick-159915"]').trigger('click')

    expect(wrapper.text()).toContain('创业板ETF')
    expect(wrapper.find('[data-test="analysis-empty-state"]').exists()).toBe(false)
  })

  it('无效基金代码时保持空状态并显示无结果提示', async () => {
    routeState.query = { code: '000000' }
    const wrapper = mount(Analysis)

    expect(wrapper.get('[data-test="analysis-empty-state"]').text()).toContain('请选择基金')

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

    expect(wrapper.text()).toContain('沪深300ETF')
    expect(wrapper.text()).not.toContain('创业板ETF')
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

    expect(wrapper.get('[data-test="analysis-empty-state"]').text()).toContain('请选择基金')
  })

  it('路由带 code 进入后页内切换基金，再清空路由时仍会回到空态', async () => {
    const wrapper = mount(Analysis)

    await wrapper.get('[data-test="analysis-search"]').setValue('创业板')
    await wrapper.get('[data-test="analysis-pick-159915"]').trigger('click')
    expect(wrapper.text()).toContain('创业板ETF')

    routeState.query = {}
    await wrapper.vm.$nextTick()

    expect(wrapper.get('[data-test="analysis-empty-state"]').text()).toContain('请选择基金')
  })

  it('分析态下也可通过顶部搜索继续切换基金', async () => {
    const wrapper = mount(Analysis)

    expect(wrapper.text()).toContain('沪深300ETF')

    await wrapper.get('[data-test="analysis-search"]').setValue('创业板')
    await wrapper.get('[data-test="analysis-pick-159915"]').trigger('click')

    expect(wrapper.text()).toContain('创业板ETF')
    expect(wrapper.text()).not.toContain('沪深300ETF')
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
