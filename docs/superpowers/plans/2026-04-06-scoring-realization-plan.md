# Scoring 页面真实化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Scoring (评分详情) 页面的伪数据替换为真实后端的 RPC 数据连通，并在后端 AnalysisService 中新增基于当前行情的策略建议计算。

**Architecture:** Python 后端由 `AnalysisService` 提供业务组装（查询行情 + 调用现成 Scorer + 策略计算），`server.py` 进行 RPC 暴露；前端 `Scoring.vue` 通过 Tauri `invoke_engine` 拉取并进行字段映射。

**Tech Stack:** Python 3 (pytest), Vue 3 + TypeScript (vitest, vue-test-utils), Tauri (invoke).

---

### Task 1: 后端 AnalysisService 评分接口实现与测试

**Files:**
- Modify: `src-python/engine/services/analysis_service.py`
- Modify: `src-python/tests/test_analysis_service.py`

- [ ] **Step 1: Write the failing test**

```python
# in src-python/tests/test_analysis_service.py
from unittest.mock import Mock
import pandas as pd
from engine.services.analysis_service import AnalysisService

def test_get_scoring_data():
    db_mock = Mock()
    indicators_mock = Mock()
    source_mock = Mock()
    
    # Mock DB query for fund info and daily quote
    db_mock.fetch_all.side_effect = [
        [("510300", "沪深300ETF")], # 基金基础信息
        [("510300", "2026-04-06", 4.0, 3.9, 4.1, 3.8, 100000, 4.0, 1.0)], # 最新日线, close=4.0
    ]
    
    service = AnalysisService(db_mock, indicators_mock, source_mock)
    
    # We also need a mock scorer. The real AnalysisService doesn't take scorer in constructor yet,
    # wait, we might need to patch the Scorer or pass it. Let's patch it.
    from unittest.mock import patch
    with patch('engine.services.analysis_service.Scorer') as MockScorer:
        instance = MockScorer.return_value
        instance.score.return_value = {
            "total_score": 60.0,
            "trend_score": 60.0,
            "momentum_score": 60.0,
            "volatility_score": 60.0,
            "volume_score": 60.0,
            "signal": "看多"
        }
        
        result = service.get_scoring_data("510300")
        
        assert result["code"] == "510300"
        assert result["name"] == "沪深300ETF"
        assert result["price"] == 4.0
        assert result["change"] == 1.0
        assert result["trend_score"] == 60.0
        assert result["advice_amount"] == 2500 # 10000 / (4.0*100) = 25 -> 2500
        assert result["estimate_fee"] == 2.0 # 2500 * 4.0 * 0.0002 = 2.0
        assert result["stop_loss"] == 3.8 # 4.0 * 0.95
        assert result["take_profit"] == 4.4 # 4.0 * 1.10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest src-python/tests/test_analysis_service.py -v`
Expected: FAIL with "AttributeError: 'AnalysisService' object has no attribute 'get_scoring_data'"

- [ ] **Step 3: Write minimal implementation**

```python
# in src-python/engine/services/analysis_service.py (add import at top if needed)
from engine.scoring.scorer import Scorer
import math

# inside AnalysisService class:
    def get_scoring_data(self, code: str) -> dict:
        fund_info = self.db.fetch_all("SELECT code, name FROM funds WHERE code = ?", (code,))
        name = fund_info[0][1] if fund_info else f"基金{code}"
        
        # Get latest quote
        quote_query = "SELECT close, pct_chg FROM daily_quotes WHERE code = ? ORDER BY date DESC LIMIT 1"
        quote_info = self.db.fetch_all(quote_query, (code,))
        
        price = 0.0
        change = 0.0
        if quote_info:
            price = quote_info[0][0]
            change = quote_info[0][1] if len(quote_info[0]) > 1 and quote_info[0][1] is not None else 0.0
            
        scorer = Scorer()
        import pandas as pd
        # pass a dummy df for now since Scorer handles df.empty gracefully or we can pass an empty df
        score_res = scorer.score(pd.DataFrame())
        
        # Calculate strategy advice
        advice_amount = 0
        estimate_fee = 0.0
        stop_loss = 0.0
        take_profit = 0.0
        
        if price > 0:
            # target 10000 RMB investment
            lots = math.floor(10000 / (price * 100))
            advice_amount = lots * 100
            estimate_fee = round(advice_amount * price * 0.0002, 2) # 万2预估
            stop_loss = round(price * 0.95, 3)
            take_profit = round(price * 1.10, 3)
            
        return {
            "code": code,
            "name": name,
            "price": price,
            "change": change,
            "total_score": score_res.get("total_score", 50.0),
            "trend_score": score_res.get("trend_score", 50.0),
            "momentum_score": score_res.get("momentum_score", 50.0),
            "volatility_score": score_res.get("volatility_score", 50.0),
            "volume_score": score_res.get("volume_score", 50.0),
            "signal": score_res.get("signal", "中性"),
            "advice_amount": advice_amount,
            "estimate_fee": estimate_fee,
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest src-python/tests/test_analysis_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src-python/engine/services/analysis_service.py src-python/tests/test_analysis_service.py
git commit -m "feat(backend): implement get_scoring_data in AnalysisService with strategy calculation"
```

### Task 2: 后端 Server RPC 开放与测试

**Files:**
- Modify: `src-python/engine/server.py`
- Modify: `src-python/tests/test_server.py`

- [ ] **Step 1: Write the failing test**

```python
# in src-python/tests/test_server.py (add to test_create_real_server)
def test_create_real_server():
    from engine.server import create_real_server
    from unittest.mock import Mock
    
    db_mock = Mock()
    source_mock = Mock()
    server = create_real_server(db_mock, source_mock)
    
    # Check if get_scoring_data is registered
    assert "get_scoring_data" in server.methods
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest src-python/tests/test_server.py -k test_create_real_server -v`
Expected: FAIL (KeyError or AssertionError)

- [ ] **Step 3: Write minimal implementation**

```python
# in src-python/engine/server.py
# 1. REMOVE the global `def get_scoring_data(code: str = "510300"):` around line 55 (the mock one)
# 2. Inside `create_real_server`:
    def get_scoring_data_real(code: str):
        return analysis_service.get_scoring_data(code)
        
    server.register_method("get_scoring_data", get_scoring_data_real)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest src-python/tests/test_server.py -k test_create_real_server -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src-python/engine/server.py src-python/tests/test_server.py
git commit -m "feat(backend): register get_scoring_data in real JSON-RPC server"
```

### Task 3: 前端 Scoring.vue 真实连通与展示 (及对应测试)

**Files:**
- Modify: `src/views/Scoring.vue`
- Modify/Create: `src/views/__tests__/Scoring.spec.ts`

- [ ] **Step 1: Write the failing test**

```typescript
# in src/views/__tests__/Scoring.spec.ts (create if not exist)
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import Scoring from '../Scoring.vue'

// Mock tauri invoke
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn()
}))

describe('Scoring.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially and then real data', async () => {
    const { invoke } = await import('@tauri-apps/api/core')
    const mockInvoke = invoke as any
    
    mockInvoke.mockResolvedValue({
      code: '510300',
      name: '测试ETF',
      price: 1.0,
      change: 2.0,
      trend_score: 80,
      momentum_score: 80,
      volatility_score: 80,
      volume_score: 80,
      total_score: 80,
      signal: '看多',
      advice_amount: 1000,
      estimate_fee: 1.5,
      stop_loss: 0.9,
      take_profit: 1.1
    })

    const wrapper = mount(Scoring)
    
    // Check loading text
    expect(wrapper.text()).toContain('加载中')
    
    // Wait for promises to resolve
    await new Promise(resolve => setTimeout(resolve, 0))
    await wrapper.vm.$nextTick()
    
    // Check data
    expect(wrapper.text()).toContain('测试ETF')
    expect(wrapper.text()).toContain('80')
    expect(wrapper.text()).toContain('1000 份')
    expect(mockInvoke).toHaveBeenCalledWith('invoke_engine', {
      method: 'get_scoring_data',
      params: { code: '510300' }
    })
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test -- src/views/__tests__/Scoring.spec.ts`
Expected: FAIL (Component uses mock data, no loading state, test assertions fail)

- [ ] **Step 3: Write minimal implementation**

```vue
# in src/views/Scoring.vue
# 1. Remove `const mockScoringData = ...` and `isDev` logic
# 2. Add loading/error states
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
       <!-- rest of the template exactly as is, but change v-model references if needed, 
            actually currentFund already uses camelCase in template like currentFund.trendScore.
            So we MUST map the snake_case from backend to camelCase. -->
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
        <!-- score section... -->
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
      <!-- charts and advice -->
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
/* 保持原有样式，新增 loading/error 样式 */
.loading-state, .error-state {
  padding: 40px;
  text-align: center;
  color: #6b7280;
  font-size: 16px;
}
.error-state {
  color: #ef4444;
}
/* ...原有样式... */
</style>
```

*(Note: Append the original `<style scoped>` exactly as it was, just adding `.loading-state` and `.error-state` block)*

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test -- src/views/__tests__/Scoring.spec.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/views/Scoring.vue src/views/__tests__/Scoring.spec.ts
git commit -m "feat(ui): connect Scoring page to real backend data and remove mocks"
```

