<template>
  <div class="config">
    <div class="header">
      <h1>交易配置</h1>
      <button class="btn-primary" @click="handleSave">保存配置</button>
    </div>

    <div class="content">
      <div class="card">
        <div class="card-header">
          <h3>交易账户设置</h3>
        </div>
        <div class="form-group">
          <label>总预算 (元)</label>
          <input type="number" v-model.number="config.budget" class="input" />
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3>手续费设置 (分品种)</h3>
        </div>
        
        <!-- ETF Fee Config -->
        <div class="fee-section">
          <h4 class="fee-title">ETF 基金</h4>
          <div class="form-grid">
            <div class="form-group">
              <label>佣金费率 (万分比)</label>
              <input type="number" v-model.number="config.fees.etf.commissionRate" class="input" step="0.1" />
            </div>
            <div class="form-group">
              <label>最低佣金 (元)</label>
              <input type="number" v-model.number="config.fees.etf.minCommission" class="input" step="0.1" />
            </div>
            <div class="form-group">
              <label>印花税 (千分比)</label>
              <input type="number" v-model.number="config.fees.etf.stampDuty" class="input" step="0.1" disabled title="ETF通常免印花税" />
            </div>
          </div>
        </div>

        <!-- LOF Fee Config -->
        <div class="fee-section">
          <h4 class="fee-title">LOF 基金</h4>
          <div class="form-grid">
            <div class="form-group">
              <label>佣金费率 (万分比)</label>
              <input type="number" v-model.number="config.fees.lof.commissionRate" class="input" step="0.1" />
            </div>
            <div class="form-group">
              <label>最低佣金 (元)</label>
              <input type="number" v-model.number="config.fees.lof.minCommission" class="input" step="0.1" />
            </div>
            <div class="form-group">
              <label>印花税 (千分比)</label>
              <input type="number" v-model.number="config.fees.lof.stampDuty" class="input" step="0.1" disabled title="LOF通常免印花税" />
            </div>
          </div>
        </div>

        <!-- Stock Fee Config -->
        <div class="fee-section border-none">
          <h4 class="fee-title">股票 (A股)</h4>
          <div class="form-grid">
            <div class="form-group">
              <label>佣金费率 (万分比)</label>
              <input type="number" v-model.number="config.fees.stock.commissionRate" class="input" step="0.1" />
            </div>
            <div class="form-group">
              <label>最低佣金 (元)</label>
              <input type="number" v-model.number="config.fees.stock.minCommission" class="input" step="0.1" />
            </div>
            <div class="form-group">
              <label>印花税 (千分比)</label>
              <input type="number" v-model.number="config.fees.stock.stampDuty" class="input" step="0.1" disabled title="股票印花税由国家规定（当前单边0.5‰）" />
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3>分析阈值设置</h3>
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label>买入评分阈值</label>
            <input type="number" v-model.number="config.scoreThreshold" class="input" />
          </div>
          <div class="form-group">
            <label>目标止盈 (%)</label>
            <input type="number" v-model.number="config.targetProfit" class="input" step="0.1" />
          </div>
          <div class="form-group">
            <label>止损 (%)</label>
            <input type="number" v-model.number="config.stopLoss" class="input" step="0.1" />
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3>成本测算预览 (以 {{ previewType.toUpperCase() }} 为例)</h3>
          <select v-model="previewType" class="preview-select">
            <option value="etf">ETF</option>
            <option value="lof">LOF</option>
            <option value="stock">股票</option>
          </select>
        </div>
        <div class="preview">
          <div class="preview-item">
            <span class="label">交易金额</span>
            <span class="value">¥{{ previewAmount.toLocaleString() }}</span>
          </div>
          <div class="preview-item">
            <span class="label">佣金</span>
            <span class="value">¥{{ previewCommission.toFixed(2) }}</span>
          </div>
          <div class="preview-item">
            <span class="label">印花税 (卖出)</span>
            <span class="value">¥{{ previewStampDuty.toFixed(2) }}</span>
          </div>
          <div class="preview-divider"></div>
          <div class="preview-item total">
            <span class="label">预估总成本</span>
            <span class="value">¥{{ previewTotal.toFixed(2) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

type AssetType = 'etf' | 'lof' | 'stock';

const config = ref({
  budget: 100000,
  fees: {
    etf: { commissionRate: 1.5, minCommission: 0, stampDuty: 0 },
    lof: { commissionRate: 1.5, minCommission: 5, stampDuty: 0 },
    stock: { commissionRate: 1.5, minCommission: 5, stampDuty: 1.0 }
  },
  scoreThreshold: 60,
  targetProfit: 5.0,
  stopLoss: 3.0,
})

const previewType = ref<AssetType>('etf')

const previewAmount = computed(() => config.value.budget)

const previewCommission = computed(() => {
  const selectedFee = config.value.fees[previewType.value]
  const rate = selectedFee.commissionRate / 10000
  const fee = previewAmount.value * rate
  return selectedFee.minCommission > 0 ? Math.max(fee, selectedFee.minCommission) : fee
})

const previewStampDuty = computed(() => {
  const selectedFee = config.value.fees[previewType.value]
  return previewAmount.value * (selectedFee.stampDuty / 1000)
})

const previewTotal = computed(() => previewCommission.value + previewStampDuty.value)

const fetchTaxRates = async () => {
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const res: any = await invoke('invoke_engine', {
      method: 'fetch_legal_tax_rates',
      params: {}
    })
    if (res && res.stock) {
      config.value.fees.etf.stampDuty = res.etf.stamp_duty
      config.value.fees.lof.stampDuty = res.lof.stamp_duty
      config.value.fees.stock.stampDuty = res.stock.stamp_duty
    }
  } catch (error) {
    console.error('获取法定税率失败:', error)
  }
}

onMounted(() => {
  fetchTaxRates();
})

const handleSave = () => {
  alert('配置已保存！')
}
</script>

<style scoped>
.config {
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

.card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.preview-select {
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 13px;
}

.fee-section {
  padding: 0;
  border-bottom: 1px dashed #e5e7eb;
}

.fee-section.border-none {
  border-bottom: none;
}

.fee-title {
  padding: 16px 20px 0;
  font-size: 14px;
  font-weight: 600;
  color: #4b5563;
}

.form-group {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.input {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.input:disabled {
  background-color: #f3f4f6;
  color: #9ca3af;
  cursor: not-allowed;
}

.preview {
  padding: 20px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  font-size: 14px;
}

.preview-item .label {
  color: #6b7280;
}

.preview-item .value {
  font-weight: 600;
  color: #1f2937;
}

.preview-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 10px 0;
}

.preview-item.total {
  font-size: 16px;
  padding-top: 10px;
}

.preview-item.total .label,
.preview-item.total .value {
  font-weight: 700;
}

.preview-item.total .value {
  color: #2563eb;
}
</style>
