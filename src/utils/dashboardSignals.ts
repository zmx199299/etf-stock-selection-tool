export interface DashboardSignal {
  code: string
  name: string
  t_plus: string
  current_price: number
  change_pct: number
  buy_price: number | null
  sell_price: number | null
  stop_loss: number | null
  latest_nav: number | null
  nav_date: string | null
  premium_rate: number | null
  expected_profit: number | null
  expected_profit_pct: number | null
  max_loss: number | null
  max_loss_pct: number | null
}

export interface SharedFundCard {
  code: string
  name: string
  tPlus: string
  currentPrice: number
  changePct: number
  buyPrice: number | null
  sellPrice: number | null
  stopLoss: number | null
  latestNav: number | null
  navDate: string | null
  premiumRate: number | null
  expectedProfit: number | null
  expectedProfitPct: number | null
  maxLoss: number | null
  maxLossPct: number | null
}

const dashboardSignalsMock: DashboardSignal[] = [
  { name: '恒生科技ETF', code: '513130', change_pct: 1.85, latest_nav: 0.456, nav_date: '2026-03-30', premium_rate: 0.12, t_plus: 'T+0', current_price: 0.456, buy_price: null, sell_price: null, stop_loss: null, expected_profit: null, expected_profit_pct: null, max_loss: null, max_loss_pct: null },
  { name: '标普500ETF', code: '513500', change_pct: 0.88, latest_nav: 1.234, nav_date: '2026-03-30', premium_rate: 1.45, t_plus: 'T+0', current_price: 1.234, buy_price: null, sell_price: null, stop_loss: null, expected_profit: null, expected_profit_pct: null, max_loss: null, max_loss_pct: null },
  { name: '创业板ETF', code: '159915', change_pct: -1.45, latest_nav: 2.11, nav_date: '2026-03-30', premium_rate: -0.22, t_plus: 'T+1', current_price: 2.11, buy_price: null, sell_price: null, stop_loss: null, expected_profit: null, expected_profit_pct: null, max_loss: null, max_loss_pct: null },
  { name: '纳指100ETF', code: '159941', change_pct: 2.11, latest_nav: 0.889, nav_date: '2026-03-30', premium_rate: 2.1, t_plus: 'T+0', current_price: 0.889, buy_price: null, sell_price: null, stop_loss: null, expected_profit: null, expected_profit_pct: null, max_loss: null, max_loss_pct: null },
  { name: '红利低波ETF', code: '512890', change_pct: 0.23, latest_nav: 1.005, nav_date: '2026-03-30', premium_rate: 0.01, t_plus: 'T+1', current_price: 1.005, buy_price: null, sell_price: null, stop_loss: null, expected_profit: null, expected_profit_pct: null, max_loss: null, max_loss_pct: null },
  { name: '芯片ETF', code: '159995', change_pct: -2.56, latest_nav: 0.998, nav_date: '2026-03-30', premium_rate: -0.45, t_plus: 'T+1', current_price: 0.998, buy_price: null, sell_price: null, stop_loss: null, expected_profit: null, expected_profit_pct: null, max_loss: null, max_loss_pct: null },
  { name: '券商ETF', code: '512000', change_pct: 4.12, latest_nav: 0.852, nav_date: '2026-03-30', premium_rate: 0.88, t_plus: 'T+1', current_price: 0.852, buy_price: null, sell_price: null, stop_loss: null, expected_profit: null, expected_profit_pct: null, max_loss: null, max_loss_pct: null },
  { name: '医疗ETF', code: '512170', change_pct: -0.75, latest_nav: 0.334, nav_date: '2026-03-30', premium_rate: 0.05, t_plus: 'T+1', current_price: 0.334, buy_price: null, sell_price: null, stop_loss: null, expected_profit: null, expected_profit_pct: null, max_loss: null, max_loss_pct: null },
  { name: '中概互联网', code: '513050', change_pct: 3.44, latest_nav: 0.912, nav_date: '2026-03-30', premium_rate: 0.67, t_plus: 'T+0', current_price: 0.912, buy_price: 0.842, sell_price: 0.91, stop_loss: 0.81, expected_profit: 89.6, expected_profit_pct: 8.2, max_loss: 225.8, max_loss_pct: 3.5 },
  { name: '游戏ETF', code: '159869', change_pct: -3.11, latest_nav: 1.022, nav_date: '2026-03-30', premium_rate: -1.05, t_plus: 'T+1', current_price: 1.022, buy_price: null, sell_price: null, stop_loss: null, expected_profit: null, expected_profit_pct: null, max_loss: null, max_loss_pct: null },
  { name: '沪深300ETF', code: '510300', change_pct: 0.56, latest_nav: 4.118, nav_date: '2026-03-30', premium_rate: 0.12, t_plus: 'T+1', current_price: 4.123, buy_price: null, sell_price: null, stop_loss: null, expected_profit: null, expected_profit_pct: null, max_loss: null, max_loss_pct: null },
]

function cloneDashboardSignal(signal: DashboardSignal): DashboardSignal {
  return { ...signal }
}

export function toSharedFundCard(signal: DashboardSignal): SharedFundCard {
  return {
    code: signal.code,
    name: signal.name,
    tPlus: signal.t_plus,
    currentPrice: signal.current_price,
    changePct: signal.change_pct,
    buyPrice: signal.buy_price,
    sellPrice: signal.sell_price,
    stopLoss: signal.stop_loss,
    latestNav: signal.latest_nav,
    navDate: signal.nav_date,
    premiumRate: signal.premium_rate,
    expectedProfit: signal.expected_profit,
    expectedProfitPct: signal.expected_profit_pct,
    maxLoss: signal.max_loss,
    maxLossPct: signal.max_loss_pct,
  }
}

export function toSharedFundCards(signals: DashboardSignal[]): SharedFundCard[] {
  return signals.map((signal) => toSharedFundCard(signal))
}

export function getDashboardSignalsMock(): DashboardSignal[] {
  return dashboardSignalsMock.map(cloneDashboardSignal)
}

export function getSharedFundCards(): SharedFundCard[] {
  return toSharedFundCards(getDashboardSignalsMock())
}

export async function loadSharedFundCards(): Promise<SharedFundCard[]> {
  if (import.meta.env.DEV || import.meta.env.MODE === 'test') {
    return getSharedFundCards()
  }

  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const result = await invoke<DashboardSignal[]>('invoke_engine', {
      method: 'get_dashboard_signals',
      params: {},
    })

    return Array.isArray(result) ? toSharedFundCards(result) : getSharedFundCards()
  } catch {
    return getSharedFundCards()
  }
}

export function getAnalysisEntryCards(routeCode?: string | null, sharedCards: SharedFundCard[] = getSharedFundCards(), count: number = 10): SharedFundCard[] {
  const defaultCards = sharedCards.slice(0, count)

  if (!routeCode) {
    return defaultCards
  }

  return []
}

export type DashboardSignalCard = SharedFundCard

export const toDashboardSignalCard = toSharedFundCard
export const toDashboardSignalCards = toSharedFundCards
export const getDashboardSignalCards = getSharedFundCards
