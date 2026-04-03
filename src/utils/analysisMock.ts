export type AnalysisStrategy = {
  conclusion: string
  buyZone: string
  sellZone: string
  position: string
  stopLoss: string
  holdingPeriod: string
  riskNote: string
}

export type AnalysisMetric = {
  label: string
  value: string
  summary: string
  tone: 'bullish' | 'neutral' | 'bearish'
}

export const ANALYSIS_PERIOD_KEYS = [
  'intraday',
  'day',
  'm5',
  'm60',
  'm120',
  'week',
  'month',
  'quarter',
  'year',
] as const

export type AnalysisPeriodKey = (typeof ANALYSIS_PERIOD_KEYS)[number]

export type AnalysisPeriod = {
  key: AnalysisPeriodKey
  label: string
  summary: string
  chartHeadline: string
  chartSummary: string
  priceAxis: string[]
  timeAxis: string[]
  linePoints: number[]
  avgLinePoints: number[]
  candles: number[][]
  volumes: number[]
  metrics: AnalysisMetric[]
}

export type AnalysisPeriods = Record<AnalysisPeriodKey, AnalysisPeriod>

export type AnalysisMock = {
  code: string
  name: string
  market: string
  price: string
  change: string
  iopv: string
  premium: string
  riskLevel: string
  strategy: AnalysisStrategy
  periods: AnalysisPeriods
}

type AnalysisPeriodDraft = Omit<AnalysisPeriod, 'key'>

const ANALYSIS_PERIOD_LABELS: Record<AnalysisPeriodKey, string> = {
  intraday: '分时',
  day: '日线',
  m5: '5 分钟',
  m60: '60 分钟',
  m120: '120 分钟',
  week: '周线',
  month: '月线',
  quarter: '季线',
  year: '年线',
}

function cloneMetrics(metrics: AnalysisMetric[]) {
  return metrics.map((metric) => ({ ...metric }))
}

function clonePeriod(period: AnalysisPeriod): AnalysisPeriod {
  return {
    ...period,
    priceAxis: [...period.priceAxis],
    timeAxis: [...period.timeAxis],
    linePoints: [...period.linePoints],
    avgLinePoints: [...period.avgLinePoints],
    candles: period.candles.map((candle) => [...candle]),
    volumes: [...period.volumes],
    metrics: cloneMetrics(period.metrics),
  }
}

function createPeriods(base: Record<AnalysisPeriodKey, Omit<AnalysisPeriodDraft, 'label'>>) {
  return Object.fromEntries(
    ANALYSIS_PERIOD_KEYS.map((key) => {
      const period = base[key]

      return [
        key,
        clonePeriod({
          key,
          label: ANALYSIS_PERIOD_LABELS[key],
          ...period,
        }),
      ]
    }),
  ) as AnalysisPeriods
}

const ANALYSIS_MOCKS: AnalysisMock[] = [
  {
    code: '510300',
    name: '沪深300ETF',
    market: 'SH',
    price: '4.123',
    change: '+0.56%',
    iopv: '4.118',
    premium: '+0.12%',
    riskLevel: '中等波动',
    strategy: {
      conclusion: '震荡偏强，适合分批关注',
      buyZone: '4.05 - 4.10',
      sellZone: '4.22 - 4.28',
      position: '建议 4 成以内仓位',
      stopLoss: '4.22 分批止盈，跌破 3.98 止损',
      holdingPeriod: '5 - 10 个交易日',
      riskNote: '若量能不能持续放大，反弹空间会被压缩。',
    },
    periods: createPeriods({
      intraday: {
        summary: '盘中价格围绕均价线震荡上移，适合确认分时承接。',
        chartHeadline: '分时价格在均价线上方缓步抬升',
        chartSummary: '用于确认盘中节奏、价格轴刻度和分时折线样式。',
        priceAxis: ['4.06', '4.09', '4.12', '4.15'],
        timeAxis: ['09:30', '10:30', '11:30', '14:00', '15:00'],
        linePoints: [4.07, 4.1, 4.09, 4.12, 4.13],
        avgLinePoints: [4.06, 4.08, 4.09, 4.1, 4.11],
        candles: [],
        volumes: [180000, 220000, 150000, 260000, 190000],
        metrics: [
          { label: '分时斜率', value: '上行', summary: '午后抬升更明显', tone: 'bullish' },
          { label: '均价偏离', value: '+0.02', summary: '价格略强于均价', tone: 'neutral' },
        ],
      },
      day: {
        summary: '价格仍在近期整理平台上沿附近震荡，日线趋势偏强。',
        chartHeadline: '价格仍在近期整理平台上沿附近震荡',
        chartSummary: '主图区域首版只展示高保真 Mock，用于确认图表尺寸、层级和阅读动线。',
        priceAxis: ['3.96', '4.02', '4.08', '4.14'],
        timeAxis: ['04-08', '04-09', '04-10', '04-11', '04-12'],
        linePoints: [4.01, 4.06, 4.08, 4.11, 4.13],
        avgLinePoints: [4.03, 4.04, 4.05, 4.07, 4.08],
        candles: [
          [4.01, 4.08, 3.99, 4.1],
          [4.08, 4.06, 4.03, 4.11],
          [4.06, 4.12, 4.05, 4.13],
          [4.12, 4.11, 4.08, 4.14],
          [4.11, 4.13, 4.1, 4.15],
        ],
        volumes: [860000, 790000, 920000, 880000, 950000],
        metrics: [
          { label: 'MACD', value: '金叉', summary: '短线动能转强', tone: 'bullish' },
          { label: 'RSI', value: '52', summary: '仍在中性偏强区域', tone: 'neutral' },
          { label: 'BOLL', value: '中轨上方', summary: '价格重回中轨之上', tone: 'bullish' },
          { label: '均线', value: 'MA5 上穿 MA20', summary: '短期趋势改善', tone: 'bullish' },
        ],
      },
      m5: {
        summary: '5 分钟级别延续窄幅整理，观察回踩承接。',
        chartHeadline: '5 分钟节奏偏强但上冲斜率有限',
        chartSummary: '适合预览短线分笔走势与均线跟随效果。',
        priceAxis: ['4.06', '4.08', '4.10', '4.12'],
        timeAxis: ['13:35', '13:50', '14:05', '14:20', '14:35'],
        linePoints: [4.07, 4.08, 4.09, 4.1, 4.11],
        avgLinePoints: [4.07, 4.07, 4.08, 4.09, 4.09],
        candles: [
          [4.07, 4.08, 4.06, 4.09],
          [4.08, 4.07, 4.06, 4.09],
          [4.07, 4.09, 4.07, 4.1],
          [4.09, 4.1, 4.08, 4.11],
          [4.1, 4.11, 4.09, 4.12],
        ],
        volumes: [52000, 47000, 61000, 58000, 64000],
        metrics: [{ label: '短均线', value: '多头', summary: '5 分钟均线仍向上', tone: 'bullish' }],
      },
      m60: {
        summary: '60 分钟图维持抬升通道，回踩仍有承接。',
        chartHeadline: '60 分钟通道上沿附近震荡',
        chartSummary: '观察小时级别趋势是否继续扩张。',
        priceAxis: ['3.98', '4.04', '4.10', '4.16'],
        timeAxis: ['周一', '周二', '周三', '周四', '周五'],
        linePoints: [4.0, 4.04, 4.08, 4.1, 4.13],
        avgLinePoints: [4.01, 4.03, 4.05, 4.07, 4.09],
        candles: [
          [4.0, 4.04, 3.99, 4.05],
          [4.04, 4.03, 4.01, 4.06],
          [4.03, 4.08, 4.02, 4.09],
          [4.08, 4.1, 4.06, 4.12],
          [4.1, 4.13, 4.08, 4.14],
        ],
        volumes: [320000, 340000, 360000, 330000, 390000],
        metrics: [{ label: '小时趋势', value: '上行', summary: '通道结构未破坏', tone: 'bullish' }],
      },
      m120: {
        summary: '120 分钟级别显示平台突破后回踩确认。',
        chartHeadline: '120 分钟回踩平台后重新走强',
        chartSummary: '观察中短线趋势确认与支撑位置。',
        priceAxis: ['3.95', '4.02', '4.09', '4.16'],
        timeAxis: ['上周四', '上周五', '本周一', '本周二', '本周三'],
        linePoints: [3.99, 4.03, 4.06, 4.1, 4.12],
        avgLinePoints: [4.0, 4.01, 4.03, 4.05, 4.07],
        candles: [
          [3.99, 4.03, 3.97, 4.04],
          [4.03, 4.02, 4.0, 4.05],
          [4.02, 4.06, 4.01, 4.07],
          [4.06, 4.1, 4.04, 4.11],
          [4.1, 4.12, 4.08, 4.13],
        ],
        volumes: [410000, 430000, 420000, 450000, 470000],
        metrics: [{ label: '中继形态', value: '成立', summary: '平台突破后缩量整理', tone: 'bullish' }],
      },
      week: {
        summary: '周线处于箱体上沿，等待中期趋势进一步确认。',
        chartHeadline: '周线尝试站稳箱体上沿',
        chartSummary: '用于确认中期波段的支撑与压力区。',
        priceAxis: ['3.80', '3.95', '4.10', '4.25'],
        timeAxis: ['第1周', '第2周', '第3周', '第4周', '第5周'],
        linePoints: [3.88, 3.94, 4.01, 4.08, 4.13],
        avgLinePoints: [3.9, 3.93, 3.97, 4.01, 4.05],
        candles: [
          [3.88, 3.94, 3.84, 3.96],
          [3.94, 3.99, 3.9, 4.01],
          [3.99, 4.03, 3.96, 4.06],
          [4.03, 4.08, 4.0, 4.1],
          [4.08, 4.13, 4.05, 4.16],
        ],
        volumes: [4200000, 4500000, 4700000, 4600000, 4900000],
        metrics: [{ label: '周线趋势', value: '偏强', summary: '重心持续上移', tone: 'bullish' }],
      },
      month: {
        summary: '月线仍在恢复阶段，长线趋势改善但需量能确认。',
        chartHeadline: '月线修复延续，斜率温和',
        chartSummary: '用于观察长周期估值修复空间。',
        priceAxis: ['3.60', '3.80', '4.00', '4.20'],
        timeAxis: ['11月', '12月', '1月', '2月', '3月'],
        linePoints: [3.72, 3.81, 3.93, 4.02, 4.13],
        avgLinePoints: [3.74, 3.79, 3.85, 3.92, 3.99],
        candles: [
          [3.72, 3.8, 3.68, 3.82],
          [3.8, 3.84, 3.76, 3.87],
          [3.84, 3.92, 3.81, 3.95],
          [3.92, 4.01, 3.89, 4.04],
          [4.01, 4.13, 3.98, 4.16],
        ],
        volumes: [16000000, 17200000, 16800000, 17500000, 18200000],
        metrics: [{ label: '月线均线', value: '修复', summary: '长周期趋势逐步转正', tone: 'neutral' }],
      },
      quarter: {
        summary: '季线维持低位回升，波段修复格局延续。',
        chartHeadline: '季线自低位缓慢抬升',
        chartSummary: '适合确认资产配置级别的趋势拐点。',
        priceAxis: ['3.20', '3.50', '3.80', '4.10'],
        timeAxis: ['Q1', 'Q2', 'Q3', 'Q4', 'Q1'],
        linePoints: [3.32, 3.48, 3.67, 3.91, 4.13],
        avgLinePoints: [3.35, 3.46, 3.6, 3.77, 3.93],
        candles: [
          [3.32, 3.46, 3.25, 3.5],
          [3.46, 3.61, 3.4, 3.65],
          [3.61, 3.76, 3.55, 3.8],
          [3.76, 3.94, 3.7, 3.99],
          [3.94, 4.13, 3.88, 4.18],
        ],
        volumes: [42000000, 45000000, 47000000, 49000000, 51000000],
        metrics: [{ label: '季线结构', value: '修复中', summary: '长期底部逐渐抬高', tone: 'neutral' }],
      },
      year: {
        summary: '年线仍在长期区间中部，适合用作大级别趋势参考。',
        chartHeadline: '年线回到长期中枢附近',
        chartSummary: '用于确认更长周期的风险收益比。',
        priceAxis: ['2.80', '3.20', '3.60', '4.00'],
        timeAxis: ['2021', '2022', '2023', '2024', '2025'],
        linePoints: [2.96, 3.12, 3.41, 3.78, 4.13],
        avgLinePoints: [3.0, 3.09, 3.22, 3.45, 3.68],
        candles: [
          [2.96, 3.11, 2.88, 3.16],
          [3.11, 3.28, 3.02, 3.34],
          [3.28, 3.52, 3.2, 3.58],
          [3.52, 3.82, 3.45, 3.88],
          [3.82, 4.13, 3.74, 4.2],
        ],
        volumes: [120000000, 126000000, 131000000, 138000000, 145000000],
        metrics: [{ label: '年线定位', value: '中枢', summary: '长期趋势改善但未脱离震荡', tone: 'neutral' }],
      },
    }),
  },
  {
    code: '159915',
    name: '创业板ETF',
    market: 'SZ',
    price: '2.256',
    change: '+0.71%',
    iopv: '2.248',
    premium: '+0.18%',
    riskLevel: '高波动',
    strategy: {
      conclusion: '弹性较强，但追高风险偏大',
      buyZone: '2.18 - 2.22',
      sellZone: '2.32 - 2.38',
      position: '建议 3 成试探仓位',
      stopLoss: '2.32 分批止盈，跌破 2.12 止损',
      holdingPeriod: '3 - 5 个交易日',
      riskNote: '创业板波动较大，若指数回撤需快速收缩仓位。',
    },
    periods: createPeriods({
      intraday: {
        summary: '分时反弹斜率更陡，但振幅明显大于宽基 ETF。',
        chartHeadline: '分时快速拉升后高位震荡',
        chartSummary: '用于观察高弹性品种盘中波动与均价偏离。',
        priceAxis: ['2.18', '2.21', '2.24', '2.27'],
        timeAxis: ['09:30', '10:30', '11:30', '14:00', '15:00'],
        linePoints: [2.19, 2.23, 2.22, 2.26, 2.25],
        avgLinePoints: [2.18, 2.2, 2.21, 2.22, 2.23],
        candles: [],
        volumes: [260000, 310000, 280000, 350000, 330000],
        metrics: [{ label: '分时强度', value: '偏强', summary: '高位承接仍在', tone: 'bullish' }],
      },
      day: {
        summary: '短线放量反弹，但仍处高波动节奏。',
        chartHeadline: '短线放量反弹，但仍处高波动节奏',
        chartSummary: '图表区重点观察近期低点抬升与量能配合。',
        priceAxis: ['2.08', '2.14', '2.20', '2.26'],
        timeAxis: ['04-08', '04-09', '04-10', '04-11', '04-12'],
        linePoints: [2.12, 2.16, 2.19, 2.23, 2.25],
        avgLinePoints: [2.14, 2.15, 2.16, 2.18, 2.2],
        candles: [
          [2.1, 2.15, 2.08, 2.16],
          [2.15, 2.14, 2.11, 2.17],
          [2.14, 2.2, 2.13, 2.21],
          [2.2, 2.23, 2.18, 2.25],
          [2.23, 2.25, 2.21, 2.27],
        ],
        volumes: [1320000, 1210000, 1480000, 1530000, 1610000],
        metrics: [
          { label: 'MACD', value: '红柱放大', summary: '上行动能增强', tone: 'bullish' },
          { label: 'RSI', value: '68', summary: '接近短线过热', tone: 'bearish' },
          { label: 'BOLL', value: '靠近上轨', summary: '价格逼近上沿压力', tone: 'neutral' },
          { label: '均线', value: '短期多头', summary: '短期趋势维持向上', tone: 'bullish' },
        ],
      },
      m5: {
        summary: '5 分钟拉升后震荡，追价需控制节奏。',
        chartHeadline: '5 分钟冲高后横盘整理',
        chartSummary: '用于判断短线追高风险。',
        priceAxis: ['2.19', '2.21', '2.23', '2.25'],
        timeAxis: ['13:35', '13:50', '14:05', '14:20', '14:35'],
        linePoints: [2.2, 2.21, 2.23, 2.22, 2.24],
        avgLinePoints: [2.19, 2.2, 2.21, 2.21, 2.22],
        candles: [
          [2.2, 2.21, 2.19, 2.22],
          [2.21, 2.2, 2.19, 2.22],
          [2.2, 2.23, 2.2, 2.24],
          [2.23, 2.22, 2.21, 2.24],
          [2.22, 2.24, 2.21, 2.25],
        ],
        volumes: [88000, 94000, 103000, 97000, 110000],
        metrics: [{ label: '波动率', value: '偏高', summary: '分时回撤较大', tone: 'bearish' }],
      },
      m60: {
        summary: '60 分钟级别反弹流畅，但上方压力仍近。',
        chartHeadline: '60 分钟反弹延续，靠近前高',
        chartSummary: '观察小时级别是否突破前高。',
        priceAxis: ['2.05', '2.11', '2.17', '2.23'],
        timeAxis: ['周一', '周二', '周三', '周四', '周五'],
        linePoints: [2.08, 2.12, 2.16, 2.21, 2.25],
        avgLinePoints: [2.09, 2.11, 2.14, 2.17, 2.2],
        candles: [
          [2.08, 2.12, 2.06, 2.13],
          [2.12, 2.11, 2.09, 2.14],
          [2.11, 2.16, 2.1, 2.17],
          [2.16, 2.21, 2.14, 2.22],
          [2.21, 2.25, 2.19, 2.26],
        ],
        volumes: [520000, 560000, 610000, 640000, 690000],
        metrics: [{ label: '小时动能', value: '增强', summary: '反弹惯性仍在', tone: 'bullish' }],
      },
      m120: {
        summary: '120 分钟级别已接近前高区，追价性价比下降。',
        chartHeadline: '120 分钟触及前高压力区',
        chartSummary: '用于判断中短线压力位置。',
        priceAxis: ['2.02', '2.09', '2.16', '2.23'],
        timeAxis: ['上周四', '上周五', '本周一', '本周二', '本周三'],
        linePoints: [2.05, 2.1, 2.14, 2.2, 2.24],
        avgLinePoints: [2.06, 2.08, 2.11, 2.15, 2.18],
        candles: [
          [2.05, 2.1, 2.03, 2.11],
          [2.1, 2.13, 2.08, 2.14],
          [2.13, 2.17, 2.11, 2.18],
          [2.17, 2.21, 2.15, 2.22],
          [2.21, 2.24, 2.18, 2.25],
        ],
        volumes: [730000, 780000, 820000, 860000, 910000],
        metrics: [{ label: '压力位', value: '临近', summary: '前高附近需放量突破', tone: 'neutral' }],
      },
      week: {
        summary: '周线弹性较强，但仍处震荡区间内部。',
        chartHeadline: '周线自区间下沿快速反弹',
        chartSummary: '观察波段反弹是否演变为趋势反转。',
        priceAxis: ['1.90', '2.00', '2.10', '2.20'],
        timeAxis: ['第1周', '第2周', '第3周', '第4周', '第5周'],
        linePoints: [1.96, 2.01, 2.08, 2.17, 2.25],
        avgLinePoints: [1.98, 2.0, 2.04, 2.1, 2.15],
        candles: [
          [1.96, 2.01, 1.93, 2.03],
          [2.01, 2.05, 1.99, 2.07],
          [2.05, 2.11, 2.03, 2.13],
          [2.11, 2.18, 2.08, 2.2],
          [2.18, 2.25, 2.15, 2.27],
        ],
        volumes: [7100000, 7600000, 8200000, 8400000, 8900000],
        metrics: [{ label: '周线弹性', value: '较高', summary: '波动与收益并存', tone: 'neutral' }],
      },
      month: {
        summary: '月线仍在修复下降趋势，弹性强于宽基。',
        chartHeadline: '月线反弹斜率更陡',
        chartSummary: '适合观察成长风格的修复力度。',
        priceAxis: ['1.70', '1.85', '2.00', '2.15'],
        timeAxis: ['11月', '12月', '1月', '2月', '3月'],
        linePoints: [1.78, 1.86, 1.97, 2.11, 2.25],
        avgLinePoints: [1.8, 1.84, 1.9, 1.99, 2.08],
        candles: [
          [1.78, 1.85, 1.75, 1.87],
          [1.85, 1.92, 1.82, 1.95],
          [1.92, 2.0, 1.89, 2.03],
          [2.0, 2.11, 1.97, 2.14],
          [2.11, 2.25, 2.07, 2.28],
        ],
        volumes: [26000000, 27300000, 28100000, 29400000, 30100000],
        metrics: [{ label: '月线修复', value: '继续', summary: '趋势扭转仍需时间', tone: 'neutral' }],
      },
      quarter: {
        summary: '季线仍在大区间底部修复，波动显著。',
        chartHeadline: '季线从低位恢复但未脱离震荡',
        chartSummary: '用于评估高成长板块长期修复节奏。',
        priceAxis: ['1.40', '1.60', '1.80', '2.00'],
        timeAxis: ['Q1', 'Q2', 'Q3', 'Q4', 'Q1'],
        linePoints: [1.49, 1.58, 1.71, 1.96, 2.25],
        avgLinePoints: [1.52, 1.57, 1.64, 1.77, 1.96],
        candles: [
          [1.49, 1.58, 1.44, 1.61],
          [1.58, 1.69, 1.53, 1.72],
          [1.69, 1.83, 1.64, 1.87],
          [1.83, 2.01, 1.78, 2.05],
          [2.01, 2.25, 1.95, 2.3],
        ],
        volumes: [68000000, 71000000, 76000000, 82000000, 87000000],
        metrics: [{ label: '季线风险', value: '较高', summary: '长期波动仍偏大', tone: 'bearish' }],
      },
      year: {
        summary: '年线仍低于历史高位较多，适合只做大方向参考。',
        chartHeadline: '年线远离历史高位，修复仍在路上',
        chartSummary: '用于评估长期赔率与风格波动。',
        priceAxis: ['1.00', '1.30', '1.60', '1.90'],
        timeAxis: ['2021', '2022', '2023', '2024', '2025'],
        linePoints: [1.12, 1.24, 1.43, 1.82, 2.25],
        avgLinePoints: [1.18, 1.23, 1.33, 1.53, 1.77],
        candles: [
          [1.12, 1.25, 1.05, 1.29],
          [1.25, 1.42, 1.18, 1.46],
          [1.42, 1.65, 1.34, 1.7],
          [1.65, 1.93, 1.57, 1.98],
          [1.93, 2.25, 1.84, 2.31],
        ],
        volumes: [210000000, 225000000, 238000000, 251000000, 269000000],
        metrics: [{ label: '长期估值', value: '修复中', summary: '高弹性也意味着高回撤', tone: 'neutral' }],
      },
    }),
  },
]

function cloneAnalysisMock(mock: AnalysisMock) {
  return {
    ...mock,
    strategy: { ...mock.strategy },
    periods: Object.fromEntries(ANALYSIS_PERIOD_KEYS.map((key) => [key, clonePeriod(mock.periods[key])])) as AnalysisPeriods,
  }
}

export function getAnalysisMockByCode(code: string) {
  const match = ANALYSIS_MOCKS.find((item) => item.code === code)
  return match ? cloneAnalysisMock(match) : undefined
}

export function getDefaultAnalysisMock() {
  return cloneAnalysisMock(ANALYSIS_MOCKS[0])
}

export function searchAnalysisCandidates(keyword: string) {
  const normalized = keyword.trim().toLowerCase()

  if (!normalized) {
    return ANALYSIS_MOCKS.map(cloneAnalysisMock)
  }

  return ANALYSIS_MOCKS.filter((item) => {
    return item.code.toLowerCase().includes(normalized) || item.name.toLowerCase().includes(normalized)
  }).map(cloneAnalysisMock)
}
