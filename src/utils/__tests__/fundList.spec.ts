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
    macd: { value: '金叉', signal: 'bullish' },
    rsi: { value: '52', signal: 'bullish' },
    boll: { value: '中轨', signal: 'bullish' },
    ma5: { value: '上穿', signal: 'bullish' },
    ma20: { value: '粘合', signal: 'bullish' },
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
    macd: { value: '绿柱', signal: 'bearish' },
    rsi: { value: '25', signal: 'bearish' },
    boll: { value: '上轨', signal: 'bearish' },
    ma5: { value: '空头', signal: 'bearish' },
    ma20: { value: '向下', signal: 'bearish' },
    score: 1,
  },
]

describe('fundList', () => {
  it('calculateChangePct() 返回保留两位的小数', () => {
    expect(calculateChangePct(4.123, 4.1)).toBe(0.56)
    expect(calculateChangePct(4.123, 0)).toBe(0)
  })

  it('getScoreLabel() 返回评分标签并覆盖阈值', () => {
    expect(getScoreLabel(9)).toBe('强烈看多')
    expect(getScoreLabel(7)).toBe('看多')
    expect(getScoreLabel(4)).toBe('中性')
    expect(getScoreLabel(2)).toBe('看空')
    expect(getScoreLabel(5)).toBe('中性')
    expect(getScoreLabel(1)).toBe('强烈看空')
  })

  it('buildFundRows() 构建衍生字段并覆盖阈值方向', () => {
    const rows = buildFundRows([
      ...sampleFunds,
      { ...sampleFunds[0], code: '159915', name: '创业板ETF', score: 7 },
      { ...sampleFunds[0], code: '512100', name: '中证1000ETF', score: 4 },
      { ...sampleFunds[1], code: '512480', name: '半导体ETF', score: 2 },
    ])

    expect(rows[0]?.changePct).toBe(0.56)
    expect(rows[0]?.scoreLabel).toBe('强烈看多')
    expect(rows[1]?.scoreDirection).toBe('bearish')
    expect(rows[2]?.scoreLabel).toBe('看多')
    expect(rows[2]?.scoreDirection).toBe('bullish')
    expect(rows[3]?.scoreLabel).toBe('中性')
    expect(rows[3]?.scoreDirection).toBe('neutral')
    expect(rows[4]?.scoreLabel).toBe('看空')
    expect(rows[4]?.scoreDirection).toBe('bearish')
  })

  it('filterFundRows() 按代码和名称过滤', () => {
    const rows = buildFundRows(sampleFunds)

    expect(filterFundRows(rows, '510300')).toHaveLength(1)
    expect(filterFundRows(rows, ' 科创 ')).toHaveLength(1)
    expect(filterFundRows(rows, '')).toHaveLength(2)
    expect(filterFundRows(rows, '不存在')).toHaveLength(0)
  })
})
