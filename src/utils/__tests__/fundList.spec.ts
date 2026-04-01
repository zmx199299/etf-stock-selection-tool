import { describe, expect, it } from 'vitest'

import {
  buildFundRows,
  calculateChangePct,
  filterFundRows,
  getScoreLabel,
  type FundListItem,
} from '../fundList'

const sampleFunds: FundListItem[] = [
  {
    code: '510300',
    name: '沪深300ETF',
    prevClose: 4.1,
    open: 4.11,
    close: 4.123,
    high: 4.15,
    low: 4.08,
    volatility: 1.71,
    macd: { value: 0.12, signal: 'bullish' },
    rsi: { value: 63.5, signal: 'bullish' },
    boll: { value: 4.13, signal: 'bullish' },
    ma5: { value: 4.09, signal: 'bullish' },
    ma20: { value: 4.02, signal: 'bullish' },
    score: 9,
  },
  {
    code: '588000',
    name: '科创50ETF',
    prevClose: 1,
    open: 0.99,
    close: 0.97,
    high: 1.01,
    low: 0.96,
    volatility: 5,
    macd: { value: -0.08, signal: 'bearish' },
    rsi: { value: 39.2, signal: 'bearish' },
    boll: { value: 0.98, signal: 'bearish' },
    ma5: { value: 0.99, signal: 'bearish' },
    ma20: { value: 1.02, signal: 'bearish' },
    score: 1,
  },
]

describe('fundList', () => {
  it('calculateChangePct() 返回保留两位的小数', () => {
    expect(calculateChangePct(4.123, 4.1)).toBe(0.56)
  })

  it('getScoreLabel() 返回评分标签', () => {
    expect(getScoreLabel(9)).toBe('强烈看多')
    expect(getScoreLabel(5)).toBe('中性')
    expect(getScoreLabel(1)).toBe('强烈看空')
  })

  it('buildFundRows() 构建衍生字段', () => {
    const rows = buildFundRows(sampleFunds)

    expect(rows[0]?.changePct).toBe(0.56)
    expect(rows[0]?.scoreLabel).toBe('强烈看多')
    expect(rows[1]?.scoreDirection).toBe('bearish')
  })

  it('filterFundRows() 按代码和名称过滤', () => {
    const rows = buildFundRows(sampleFunds)

    expect(filterFundRows(rows, '510300')).toHaveLength(1)
    expect(filterFundRows(rows, ' 科创 ')).toHaveLength(1)
    expect(filterFundRows(rows, '')).toHaveLength(2)
  })
})
