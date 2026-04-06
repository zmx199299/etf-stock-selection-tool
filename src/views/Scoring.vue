<template>
  <div class="scoring">
    <div class="header">
      <h1>技术评分</h1>
      <div class="search-bar">
        <input v-model="searchCode" type="text" class="search-input" placeholder="输入基金代码..." @keyup.enter="handleSearch" />
        <button class="btn-primary" @click="handleSearch">分析</button>
      </div>
    </div>

    <div v-if="isLoading" class="loading-state">
      <p>加载中...</p>
    </div>
    
    <div v-else-if="errorMsg" class="error-state">
      <p>{{ errorMsg }}</p>
    </div>

    <div class="content" v-else-if="currentFund">
      <div class="fund-info">
        <div class="fund-header">
          <h2>{{ currentFund.code }} - {{ currentFund.name }}</h2>
          <span class="price">{{ currentFund.price }}</span>
        </div>
        <div class="fund-meta">
          <span class="change" :class="currentFund.change > 0 ? 'up' : 'down'">
            {{ currentFund.change > 0 ? '+' : '' }}{{ currentFund.change }}%
          </span>
        </div>
      </div>
      
      <div class="score-card">
        <div class="score-display">
          <div class="score-circle">
            <span class="score-value">{{ currentFund.totalScore || totalScore }}</span>
          </div>
          <div class="score-label">综合评分</div>
          <div class="signal" :class="signalClass">{{ currentFund.signal }}</div>
        </div>

        <div class="score-breakdown">
          <div class="score-item">
            <span class="item-label">趋势得分</span>
            <div class="item-bar"><div class="bar-fill" :style="{ width: currentFund.trendScore + '%' }"></div></div>
            <span class="item-value">{{ currentFund.trendScore }}</span>
          </div>
          <div class="score-item">
            <span class="item-label">动量得分</span>
            <div class="item-bar"><div class="bar-fill" :style="{ width: currentFund.momentumScore + '%' }"></div></div>
            <span class="item-value">{{ currentFund.momentumScore }}</span>
          </div>
          <div class="score-item">
            <span class="item-label">波动得分</span>
            <div class="item-bar"><div class="bar-fill" :style="{ width: currentFund.volatilityScore + '%' }"></div></div>
            <span class="item-value">{{ currentFund.volatilityScore }}</span>
          </div>
          <div class="score-item">
            <span class="item-label">量能得分</span>
            <div class="item-bar"><div class="bar-fill" :style="{ width: currentFund.volumeScore + '%' }"></div></div>
            <span class="item-value">{{ currentFund.volumeScore }}</span>
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header"><h3>K线图表</h3></div>
        <div class="chart-placeholder"><span>📈 ECharts 图表区域 (待接入真实数据)</span></div>
      </div>

      <div class="advice-card">
        <div class="advice-header"><h3>交易建议</h3></div>
        <div class="advice-content">
          <div class="advice-item"><span class="label">建议买入量</span><span class="value">{{ currentFund.adviceAmount }} 份</span></div>
          <div class="advice-item"><span class="label">预估费用</span><span class="value">¥{{ currentFund.estimateFee }}</span></div>
          <div class="advice-item"><span class="label">止损价</span><span class="value">¥{{ currentFund.stopLoss }}</span></div>
          <div class="advice-item"><span class="label">止盈价</span><span class="value">¥{{ currentFund.takeProfit }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const currentFund = ref<any>(null)
const isLoading = ref(true)
const errorMsg = ref('')
const searchCode = ref('510300')

const fetchScoringData = async (code: string) => {
  isLoading.value = true
  errorMsg.value = ''
  currentFund.value = null
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const res: any = await invoke('invoke_engine', {
      method: 'get_scoring_data',
      params: { code }
    })
    
    if (res && res.code) {
      // Map snake_case to camelCase for the template
      currentFund.value = {
        code: res.code,
        name: res.name,
        price: res.price,
        change: res.change,
        signal: res.signal,
        totalScore: res.total_score,
        trendScore: res.trend_score,
        momentumScore: res.momentum_score,
        volatilityScore: res.volatility_score,
        volumeScore: res.volume_score,
        adviceAmount: res.advice_amount,
        estimateFee: res.estimate_fee,
        stopLoss: res.stop_loss,
        takeProfit: res.take_profit
      }
    } else {
      errorMsg.value = '未找到该基金的评分数据'
    }
  } catch (error: any) {
    console.error('获取评分数据失败:', error)
    errorMsg.value = `请求失败: ${error.message || String(error)}`
  } finally {
    isLoading.value = false
  }
}

const handleSearch = () => {
  if (searchCode.value.trim()) {
    fetchScoringData(searchCode.value.trim())
  }
}

onMounted(() => {
  fetchScoringData(searchCode.value)
})

const totalScore = computed(() => {
  if (!currentFund.value) return 0
  const f = currentFund.value
  return Math.round((f.trendScore * 0.4 + f.momentumScore * 0.3 + f.volatilityScore * 0.1 + f.volumeScore * 0.2))
})

const signalClass = computed(() => {
  if (!currentFund.value || !currentFund.value.signal) return ''
  const s = currentFund.value.signal
  return s.replace(/[\u4e00-\u9fa5]/g, '').toLowerCase()
})
</script>

<style scoped>
.loading-state, .error-state {
  padding: 40px;
  text-align: center;
  color: #6b7280;
  font-size: 16px;
}
.error-state {
  color: #ef4444;
}

.scoring {
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

.search-bar {
  display: flex;
  gap: 12px;
}

.search-input {
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  width: 280px;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.fund-info {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.fund-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.fund-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.fund-header .price {
  font-size: 28px;
  font-weight: 700;
  color: #2563eb;
}

.fund-meta .change {
  font-size: 16px;
  font-weight: 600;
}

.fund-meta .change.up {
  color: #22c55e;
}

.fund-meta .change.down {
  color: #ef4444;
}

.score-card {
  background: white;
  padding: 24px;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 32px;
}

.score-display {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.score-circle {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  border: 12px solid #22c55e;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.score-value {
  font-size: 48px;
  font-weight: 800;
  color: #1f2937;
}

.score-label {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
}

.signal {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
}

.信号 {
  background: #dcfce7;
  color: #166534;
}

.score-breakdown {
  display: flex;
  flex-direction: column;
  gap: 20px;
  justify-content: center;
}

.score-item {
  display: grid;
  grid-template-columns: 80px 1fr 40px;
  gap: 16px;
  align-items: center;
}

.score-item .item-label {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.score-item .item-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.score-item .item-bar .bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #2563eb, #22c55e);
  border-radius: 4px;
}

.score-item .item-value {
  font-size: 14px;
  font-weight: 700;
  color: #1f2937;
}

.card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.card-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.chart-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 16px;
}

.advice-card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.advice-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #f0fdf4;
}

.advice-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #166534;
}

.advice-content {
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.advice-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.advice-item .label {
  font-size: 14px;
  color: #6b7280;
}

.advice-item .value {
  font-size: 14px;
  font-weight: 700;
  color: #1f2937;
}
</style>