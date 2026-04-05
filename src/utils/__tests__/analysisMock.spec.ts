import { describe, expect, it } from 'vitest'

import {
  ANALYSIS_PERIOD_KEYS,
  type AnalysisMock,
  type AnalysisPeriodKey,
  getAnalysisMockByCode,
  getDefaultAnalysisMock,
  searchAnalysisCandidates,
} from '../analysisMock'
import { getSharedFundCards } from '../dashboardSignals'

const KLINE_PERIOD_KEYS: AnalysisPeriodKey[] = ['day', 'm5', 'm60', 'm120', 'week', 'month', 'quarter', 'year']

describe('analysisMock', () => {
  it('按基金代码返回对应分析 Mock 数据', () => {
    const result = getAnalysisMockByCode('510300')

    expect(result?.code).toBe('510300')
    expect(result?.name).toBe('沪深300ETF')
    expect(result?.strategy.conclusion).toContain('震荡偏强')
    expect(result).not.toHaveProperty('chartHeadline')
    expect(result).not.toHaveProperty('chartSummary')
    expect(result).not.toHaveProperty('metrics')
  })

  it('每只基金都包含完整的 9 个分析周期', () => {
    const results = searchAnalysisCandidates('')

    expect(results).toHaveLength(13)

    results.forEach((item: AnalysisMock) => {
      expect(Object.keys(item.periods)).toEqual(ANALYSIS_PERIOD_KEYS)

      ANALYSIS_PERIOD_KEYS.forEach((periodKey: AnalysisPeriodKey) => {
        expect(item.periods[periodKey]).toMatchObject({
          key: periodKey,
          label: expect.any(String),
          summary: expect.any(String),
          chartHeadline: expect.any(String),
          chartSummary: expect.any(String),
          priceAxis: expect.any(Array),
          timeAxis: expect.any(Array),
          linePoints: expect.any(Array),
          avgLinePoints: expect.any(Array),
          candles: expect.any(Array),
          volumes: expect.any(Array),
          metrics: expect.any(Array),
        })
      })
    })
  })

  it('分时周期提供价格轴、时间轴与分时线数据', () => {
    const result = getAnalysisMockByCode('510300')

    expect(result?.periods.intraday.priceAxis).toEqual(['4.06', '4.09', '4.12', '4.15'])
    expect(result?.periods.intraday.timeAxis).toEqual(['09:30', '10:30', '11:30', '14:00', '15:00'])
    expect(result?.periods.intraday.linePoints).toEqual([4.07, 4.1, 4.09, 4.12, 4.13])
  })

  it('日线周期提供 K 线、成交量与指标摘要', () => {
    const result = getAnalysisMockByCode('510300')

    expect(result?.periods.day.candles).toEqual([
      [4.01, 4.1, 3.99, 4.08],
      [4.08, 4.11, 4.03, 4.06],
      [4.06, 4.13, 4.05, 4.12],
      [4.12, 4.14, 4.08, 4.11],
      [4.11, 4.15, 4.1, 4.13],
    ])
    expect(result?.periods.day.volumes).toEqual([860000, 790000, 920000, 880000, 950000])
    expect(result?.periods.day.metrics).toEqual([
      { label: 'MACD', value: '金叉', summary: '短线动能转强', tone: 'bullish' },
      { label: 'RSI', value: '52', summary: '仍在中性偏强区域', tone: 'neutral' },
      { label: 'BOLL', value: '中轨上方', summary: '价格重回中轨之上', tone: 'bullish' },
      { label: '均线', value: 'MA5 上穿 MA20', summary: '短期趋势改善', tone: 'bullish' },
    ])
  })

  it('所有非分时 K 周期都提供最小 K 线数据，供主图重复铺满展示', () => {
    const results = searchAnalysisCandidates('')

    results.forEach((item: AnalysisMock) => {
      expect(item.periods.intraday.candles).toEqual([])

      KLINE_PERIOD_KEYS.forEach((periodKey) => {
        expect(item.periods[periodKey].candles).toHaveLength(5)
        item.periods[periodKey].candles.forEach((candle: number[]) => {
          expect(candle).toHaveLength(4)
        })
      })
    })
  })

  it('默认示例基金使用第一条 Mock 数据', () => {
    expect(getDefaultAnalysisMock().code).toBe('510300')
  })

  it('搜索候选支持代码和名称关键字匹配', () => {
    const byCode = searchAnalysisCandidates('159915')
    const byName = searchAnalysisCandidates('创业板')
    const sharedEntryCode = searchAnalysisCandidates('513130')

    expect(byCode).toHaveLength(1)
    expect(byCode[0].code).toBe('159915')
    expect(byName[0].name).toContain('创业板')
    expect(sharedEntryCode).toHaveLength(1)
    expect(sharedEntryCode[0].code).toBe('513130')
  })

  it('搜索候选会忽略前后空格与大小写差异', () => {
    const result = searchAnalysisCandidates('  etf  ')

    expect(result.length).toBeGreaterThanOrEqual(10)
  })

  it('返回的 Mock 数据不会污染源数据', () => {
    const first = getAnalysisMockByCode('510300')

    if (!first) {
      throw new Error('expected mock data for 510300')
    }

    first.strategy.conclusion = '已被篡改'
    first.periods.intraday.priceAxis[0] = '9.99'
    first.periods.intraday.timeAxis[0] = '00:00'
    first.periods.intraday.linePoints[0] = 999
    first.periods.intraday.avgLinePoints[0] = 888
    first.periods.day.volumes[0] = 1
    first.periods.day.candles[0][0] = 0
    first.periods.day.metrics[0].label = 'tampered'

    const second = getAnalysisMockByCode('510300')

    expect(second?.strategy.conclusion).toContain('震荡偏强')
    expect(second?.periods.intraday.priceAxis[0]).toBe('4.06')
    expect(second?.periods.intraday.timeAxis[0]).toBe('09:30')
    expect(second?.periods.intraday.linePoints[0]).toBe(4.07)
    expect(second?.periods.intraday.avgLinePoints[0]).toBe(4.06)
    expect(second?.periods.day.volumes[0]).toBe(860000)
    expect(second?.periods.day.candles[0][0]).toBe(4.01)
    expect(second?.periods.day.metrics[0].label).toBe('MACD')
  })

  it('默认基金返回值彼此隔离', () => {
    const first = getDefaultAnalysisMock()
    const second = getDefaultAnalysisMock()

    first.periods.day.priceAxis[0] = '0.00'
    first.periods.day.candles[0][1] = 0

    expect(second.periods.day.priceAxis[0]).toBe('3.96')
    expect(second.periods.day.candles[0][1]).toBe(4.1)
  })

  it('搜索结果返回值彼此隔离', () => {
    const first = searchAnalysisCandidates('510300')[0]
    const second = searchAnalysisCandidates('510300')[0]

    first.periods.day.timeAxis[0] = 'fake'
    first.periods.day.avgLinePoints[0] = 0
    first.periods.day.volumes[1] = 0

    expect(second.periods.day.timeAxis[0]).toBe('04-08')
    expect(second.periods.day.avgLinePoints[0]).toBe(4.03)
    expect(second.periods.day.volumes[1]).toBe(790000)
  })

  it('第三页默认顶部入口卡片都能命中对应分析 mock', () => {
    const entryCodes = getSharedFundCards()
      .slice(0, 10)
      .map((card) => card.code)

    entryCodes.forEach((code) => {
      expect(getAnalysisMockByCode(code)?.code).toBe(code)
    })
  })

  it('第二页详情入口里的基金都能命中对应分析 mock', () => {
    ;['510300', '159915', '510500', '588000'].forEach((code) => {
      expect(getAnalysisMockByCode(code)?.code).toBe(code)
    })
  })
})
