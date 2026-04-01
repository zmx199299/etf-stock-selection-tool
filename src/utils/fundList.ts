import { scoreToDirection, type MarketDirection } from './marketColors'

export type TechnicalValue = {
  value: string
  signal: MarketDirection
}

export type FundListItem = {
  code: string
  name: string
  prevClose: number
  open: number
  close: number
  high: number
  low: number
  volatility: number
  macd: TechnicalValue
  rsi: TechnicalValue
  boll: TechnicalValue
  ma5: TechnicalValue
  ma20: TechnicalValue
  score: number
}

export type FundListRow = FundListItem & {
  changePct: number
  scoreLabel: string
  scoreDirection: MarketDirection
}

export function calculateChangePct(close: number, prevClose: number) {
  if (prevClose === 0) {
    return 0
  }

  return Number((((close - prevClose) / prevClose) * 100).toFixed(2))
}

export function getScoreLabel(score: number) {
  if (score >= 9) {
    return '强烈看多'
  }

  if (score >= 7) {
    return '看多'
  }

  if (score >= 4) {
    return '中性'
  }

  if (score >= 2) {
    return '看空'
  }

  return '强烈看空'
}

export function buildFundRows(funds: FundListItem[]): FundListRow[] {
  return funds.map((fund) => ({
    ...fund,
    changePct: calculateChangePct(fund.close, fund.prevClose),
    scoreLabel: getScoreLabel(fund.score),
    scoreDirection: scoreToDirection(fund.score),
  }))
}

export function filterFundRows(rows: FundListRow[], keyword: string) {
  const normalizedKeyword = keyword.trim().toLowerCase()

  if (!normalizedKeyword) {
    return rows
  }

  return rows.filter((row) => {
    return row.code.toLowerCase().includes(normalizedKeyword)
      || row.name.toLowerCase().includes(normalizedKeyword)
  })
}
