import { describe, expect, it } from 'vitest'

import * as dashboardSignals from '../dashboardSignals'

const {
  getDashboardSignalsMock,
  getAnalysisEntryCards,
  getSharedFundCards,
  loadSharedFundCards,
  toSharedFundCard,
  toSharedFundCards,
} = dashboardSignals

describe('dashboardSignals', () => {
  it('将原始 snake_case 信号转换为 camelCase 卡片模型', () => {
    const rawSignal = {
      code: '513130',
      name: '恒生科技ETF',
      t_plus: 'T+0',
      current_price: 0.456,
      change_pct: 1.85,
      buy_price: null,
      sell_price: null,
      stop_loss: null,
      latest_nav: 0.456,
      nav_date: '2026-03-30',
      premium_rate: 0.12,
      expected_profit: null,
      expected_profit_pct: null,
      max_loss: null,
      max_loss_pct: null,
    }

    expect(toSharedFundCard(rawSignal)).toEqual({
      code: '513130',
      name: '恒生科技ETF',
      tPlus: 'T+0',
      currentPrice: 0.456,
      changePct: 1.85,
      buyPrice: null,
      sellPrice: null,
      stopLoss: null,
      latestNav: 0.456,
      navDate: '2026-03-30',
      premiumRate: 0.12,
      expectedProfit: null,
      expectedProfitPct: null,
      maxLoss: null,
      maxLossPct: null,
    })
  })

  it('批量转换时为每条信号生成卡片模型', () => {
    const rawSignals = [
      {
        code: '513130',
        name: '恒生科技ETF',
        t_plus: 'T+0',
        current_price: 0.456,
        change_pct: 1.85,
        buy_price: null,
        sell_price: null,
        stop_loss: null,
        latest_nav: 0.456,
        nav_date: '2026-03-30',
        premium_rate: 0.12,
        expected_profit: null,
        expected_profit_pct: null,
        max_loss: null,
        max_loss_pct: null,
      },
    ]

    expect(toSharedFundCards(rawSignals)).toEqual([
      expect.objectContaining({
        code: '513130',
        name: '恒生科技ETF',
        tPlus: 'T+0',
      }),
    ])
  })

  it('mock getter 返回隔离副本', () => {
    const first = getDashboardSignalsMock()
    const second = getDashboardSignalsMock()

    first[0].name = '被污染的数据'

    expect(second[0].name).toBe('恒生科技ETF')
  })

  it('共享卡片 getter 返回转换后的 camelCase 数据且结果隔离', () => {
    const first = getSharedFundCards()
    const second = getSharedFundCards()

    expect(first[0]).toEqual(
      expect.objectContaining({
        code: '513130',
        name: '恒生科技ETF',
        tPlus: 'T+0',
        currentPrice: 0.456,
        latestNav: 0.456,
        navDate: '2026-03-30',
        premiumRate: 0.12,
      }),
    )

    first[0].name = '被污染的卡片'

    expect(second[0].name).toBe('恒生科技ETF')
  })

  it('共享卡片 getter 包含默认 10 条之外的详情页入口基金卡片', () => {
    const cards = getSharedFundCards()
    const cardCodes = cards.map((card) => card.code)

    expect(cards).toHaveLength(11)
    expect(cardCodes.slice(0, 10)).not.toContain('510300')
    expect(cardCodes).toContain('510300')
  })

  it('提供统一的分析页顶部入口卡片选取函数', () => {
    expect(typeof (dashboardSignals as { getAnalysisEntryCards?: unknown }).getAnalysisEntryCards).toBe('function')
  })

  it('分析页入口 getter 在无 route code 时返回默认前 10 条卡片', () => {
    const entryCodes = getAnalysisEntryCards().map((card) => card.code)

    expect(entryCodes).toEqual(getSharedFundCards().slice(0, 10).map((card) => card.code))
  })

  it('分析页入口 getter 在带 route code 时返回空卡片集合，由详情页单独承接', () => {
    const entryCodes = getAnalysisEntryCards('510300').map((card) => card.code)

    expect(entryCodes).toEqual([])
  })

  it('提供与首页同源的共享卡片加载器', async () => {
    await expect(loadSharedFundCards()).resolves.toEqual(getSharedFundCards())
  })
})
