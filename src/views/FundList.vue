<template>
  <div class="fund-list">
    <div class="header">
      <h1>全量场内基金</h1>
      <div class="controls">
        <div class="color-inversion">
          <label class="switch">
            <input type="checkbox" v-model="invertColors" />
            <span class="slider"></span>
          </label>
          <span>看多为红色/看空为绿色</span>
        </div>
        <input type="text" class="search-input" placeholder="搜索基金代码/名称..." />
      </div>
    </div>

    <div class="content">
      <div class="card">
        <div class="table-container">
          <table class="fund-table">
            <thead>
              <tr>
                <th>基金代码</th>
                <th>基金名称</th>
                <th>昨日收盘</th>
                <th>开盘</th>
                <th>收盘</th>
                <th>最高</th>
                <th>最低</th>
                <th>
                  波动率
                  <span class="tooltip-icon" :title="volatilityTooltip">?</span>
                </th>
                <th class="tech-column">MACD</th>
                <th class="tech-column">RSI</th>
                <th class="tech-column">BOLL</th>
                <th class="tech-column">MA5</th>
                <th class="tech-column">MA20</th>
                <th>推荐打分</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="fund in funds" :key="fund.code">
                <td class="code">{{ fund.code }}</td>
                <td class="name">{{ fund.name }}</td>
                <td class="num">{{ fund.prevClose }}</td>
                <td class="num">{{ fund.open }}</td>
                <td class="num">{{ fund.close }}</td>
                <td class="num">{{ fund.high }}</td>
                <td class="num">{{ fund.low }}</td>
                <td class="num">{{ (fund.volatility * 100).toFixed(2) }}%</td>
                <!-- 技术指标列 -->
                <td class="tech-indicator" :class="getTechClass(fund.macd.signal)">
                  {{ fund.macd.value }}
                </td>
                <td class="tech-indicator" :class="getTechClass(fund.rsi.signal)">
                  {{ fund.rsi.value }}
                </td>
                <td class="tech-indicator" :class="getTechClass(fund.boll.signal)">
                  {{ fund.boll.value }}
                </td>
                <td class="tech-indicator" :class="getTechClass(fund.ma5.signal)">
                  {{ fund.ma5.value }}
                </td>
                <td class="tech-indicator" :class="getTechClass(fund.ma20.signal)">
                  {{ fund.ma20.value }}
                </td>
                <!-- 推荐打分 -->
                <td class="score-cell">
                  <div class="score-circle" :class="getScoreClass(fund.score)">
                    {{ fund.score }}
                  </div>
                  <span class="score-label">{{ getScoreLabel(fund.score) }}</span>
                </td>
                <td>
                  <button class="btn-text">详情</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const isDev = import.meta.env.DEV

// 波动率悬浮提示
const volatilityTooltip = '今日波动率 = (最高 - 最低) / 最低'

const funds = ref<any[]>([])
const invertColors = ref(false)

// Mock 数据，用于开发环境或后端不可用时兜底
const mockFunds = [
  {
    code: '510300', name: '沪深300ETF', prevClose: 4.100, open: 4.105, close: 4.123,
    high: 4.150, low: 4.080, volatility: (4.150 - 4.080) / 4.080,
    macd: { signal: 'bullish', value: '金叉' }, rsi: { signal: 'neutral', value: '52' },
    boll: { signal: 'bullish', value: '中轨' }, ma5: { signal: 'bullish', value: '上穿' },
    ma20: { signal: 'neutral', value: '粘合' }, score: 9
  },
  {
    code: '159915', name: '创业板ETF', prevClose: 2.240, open: 2.245, close: 2.256,
    high: 2.280, low: 2.230, volatility: (2.280 - 2.230) / 2.230,
    macd: { signal: 'bullish', value: '红柱' }, rsi: { signal: 'bullish', value: '68' },
    boll: { signal: 'bullish', value: '下轨' }, ma5: { signal: 'bullish', value: '多头' },
    ma20: { signal: 'bullish', value: '向上' }, score: 10
  },
  {
    code: '510500', name: '中证500ETF', prevClose: 6.800, open: 6.790, close: 6.789,
    high: 6.820, low: 6.750, volatility: (6.820 - 6.750) / 6.750,
    macd: { signal: 'bearish', value: '死叉' }, rsi: { signal: 'neutral', value: '48' },
    boll: { signal: 'neutral', value: '中轨' }, ma5: { signal: 'bearish', value: '下穿' },
    ma20: { signal: 'neutral', value: '粘合' }, score: 3
  },
  {
    code: '588000', name: '科创50ETF', prevClose: 1.050, open: 1.045, close: 1.030,
    high: 1.060, low: 1.020, volatility: (1.060 - 1.020) / 1.020,
    macd: { signal: 'bearish', value: '绿柱' }, rsi: { signal: 'bearish', value: '25' },
    boll: { signal: 'bearish', value: '上轨' }, ma5: { signal: 'bearish', value: '空头' },
    ma20: { signal: 'bearish', value: '向下' }, score: 1
  }
]

const fetchFunds = async () => {
  // 开发环境直接使用 mock 数据，无需 Tauri 后端
  if (isDev) {
    funds.value = mockFunds
    return
  }

  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const res: any = await invoke('invoke_engine', {
      method: 'get_fund_list',
      params: {}
    });
    if (res && Array.isArray(res)) {
      funds.value = res;
    }
  } catch (error) {
    console.error('Failed to fetch fund list:', error);
    // 后端不可用时使用 mock 数据兜底
    funds.value = mockFunds
  }
}

onMounted(() => {
  fetchFunds();
})

const getTechClass = (signal: string) => {
  if (signal === 'bullish') return invertColors.value ? 'bearish' : 'bullish'
  if (signal === 'bearish') return invertColors.value ? 'bullish' : 'bearish'
  return 'neutral'
}

// 决定分数颜色类
const getScoreClass = (score: number) => {
  if (score >= 9) return 'strong-buy'
  if (score >= 7) return 'buy'
  if (score >= 4) return 'neutral'
  if (score >= 2) return 'sell'
  return 'strong-sell'
}

const getScoreLabel = (score: number) => {
  if (score >= 9) return '强烈看多'
  if (score >= 7) return '看多'
  if (score >= 4) return '中性'
  if (score >= 2) return '看空'
  return '强烈看空'
}
</script>

<style scoped>
.fund-list {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.controls {
  display: flex;
  gap: 20px;
  align-items: center;
}

.color-inversion {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 14px;
  color: #374151;
}

/* Switch styles */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.3s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #2563eb;
}

input:checked + .slider:before {
  transform: translateX(20px);
}

.search-input {
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  width: 240px;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.table-container {
  padding: 0 20px 20px;
  overflow-x: auto;
}

.fund-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1400px;
}

.fund-table thead th {
  text-align: left;
  padding: 14px 12px;
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  border-bottom: 2px solid #e5e7eb;
  position: sticky;
  top: 0;
  background: white;
  z-index: 10;
}

.tooltip-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #e5e7eb;
  color: #6b7280;
  font-size: 12px;
  font-weight: 700;
  margin-left: 6px;
  cursor: help;
}

.fund-table tbody td {
  padding: 14px 12px;
  font-size: 14px;
  color: #374151;
  border-bottom: 1px solid #f3f4f6;
}

.fund-table tbody tr:hover {
  background: #f9fafb;
}

.code {
  font-family: monospace;
  font-weight: 700;
  color: #2563eb;
}

.name {
  font-weight: 500;
}

.num {
  font-family: monospace;
  text-align: right;
}

.tech-column {
  text-align: center;
}

.tech-indicator {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 700;
  text-align: center;
  display: inline-block;
  min-width: 60px;
}

.tech-indicator.bullish {
  background: #fee2e2;
  color: #991b1b;
}

.tech-indicator.bearish {
  background: #dcfce7;
  color: #166534;
}

.tech-indicator.neutral {
  background: #fef3c7;
  color: #92400e;
}

.score-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.score-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 15px;
  color: white;
}

.score-circle.strong-buy {
  background: #16a34a;
}

.score-circle.buy {
  background: #22c55e;
}

.score-circle.neutral {
  background: #f59e0b;
}

.score-circle.sell {
  background: #f97316;
}

.score-circle.strong-sell {
  background: #dc2626;
}

.score-label {
  font-size: 11px;
  color: #6b7280;
  text-align: center;
}

.btn-text {
  background: none;
  border: none;
  color: #2563eb;
  font-size: 13px;
  cursor: pointer;
}
</style>
