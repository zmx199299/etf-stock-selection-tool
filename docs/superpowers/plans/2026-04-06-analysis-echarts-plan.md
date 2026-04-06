# Analysis 页面图表真实化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用真实的 ECharts 取代前端 Mock 图表，打通 Analysis 后端真实查询，实现前后端数据联动。

**Architecture:** 前端移除 mockAnalysis 引用，引入 vue-echarts 和 ECharts。编写 chartAdapter 将后端的数据转化为 Option，由 Analysis.vue 通过 `<v-chart>` 渲染真实的分时图和K线图。

**Tech Stack:** Vue 3 + TypeScript, Tauri, ECharts, vue-echarts, vitest.

---

### Task 1: 依赖安装与组件挂载测试

**Files:**
- Modify: `package.json`
- Modify: `src/main.ts`
- Create: `src/utils/chartAdapter.ts`
- Modify: `src/views/__tests__/Analysis.spec.ts`

- [ ] **Step 1: Install Dependencies**
```bash
npm install echarts vue-echarts
```

- [ ] **Step 2: Write failing test for adapter**
```typescript
// in src/utils/__tests__/chartAdapter.spec.ts
import { describe, it, expect } from 'vitest'
import { buildIntradayOption, buildKLineOption } from '../chartAdapter'

describe('chartAdapter', () => {
  it('buildIntradayOption builds correct option', () => {
    const periodData = { timeAxis: ['09:30', '09:31'], linePoints: [1.0, 1.1], avgLinePoints: [1.0, 1.05], volumes: [100, 200] }
    const option = buildIntradayOption(periodData as any, 'cn')
    expect(option.series).toHaveLength(3) // price, avg, volume
    expect(option.xAxis[0].data).toEqual(['09:30', '09:31'])
  })
})
```

- [ ] **Step 3: Run test to verify failure**
Run: `npm run test -- src/utils/__tests__/chartAdapter.spec.ts`
Expected: FAIL (module not found)

- [ ] **Step 4: Implement minimal adapter and global mount**
```typescript
// in src/utils/chartAdapter.ts
export function buildIntradayOption(periodData: any, colorMode: 'cn' | 'intl'): any {
  if (!periodData || !periodData.timeAxis) return {}
  const lineCol = colorMode === 'cn' ? '#ef4444' : '#16a34a'
  const avgCol = colorMode === 'cn' ? '#22c55e' : '#ef4444'
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: [{ left: '10%', right: '5%', top: '5%', height: '60%' }, { left: '10%', right: '5%', top: '75%', height: '20%' }],
    xAxis: [
      { type: 'category', data: periodData.timeAxis, gridIndex: 0, boundaryGap: false },
      { type: 'category', data: periodData.timeAxis, gridIndex: 1, boundaryGap: false, show: false }
    ],
    yAxis: [{ type: 'value', scale: true, gridIndex: 0 }, { type: 'value', gridIndex: 1 }],
    series: [
      { name: '价格', type: 'line', data: periodData.linePoints, xAxisIndex: 0, yAxisIndex: 0, lineStyle: { color: lineCol }, showSymbol: false },
      { name: '均价', type: 'line', data: periodData.avgLinePoints, xAxisIndex: 0, yAxisIndex: 0, lineStyle: { color: avgCol, type: 'dashed' }, showSymbol: false },
      { name: '成交量', type: 'bar', data: periodData.volumes, xAxisIndex: 1, yAxisIndex: 1 }
    ]
  }
}

export function buildKLineOption(periodData: any, colorMode: 'cn' | 'intl'): any {
  if (!periodData || !periodData.timeAxis) return {}
  const upColor = colorMode === 'cn' ? '#ef4444' : '#22c55e'
  const downColor = colorMode === 'cn' ? '#22c55e' : '#ef4444'
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: [{ left: '10%', right: '5%', top: '5%', height: '60%' }, { left: '10%', right: '5%', top: '75%', height: '20%' }],
    xAxis: [
      { type: 'category', data: periodData.timeAxis, gridIndex: 0 },
      { type: 'category', data: periodData.timeAxis, gridIndex: 1, show: false }
    ],
    yAxis: [{ type: 'value', scale: true, gridIndex: 0 }, { type: 'value', gridIndex: 1 }],
    series: [
      { name: 'K线', type: 'candlestick', data: periodData.candles, itemStyle: { color: upColor, color0: downColor, borderColor: upColor, borderColor0: downColor }, xAxisIndex: 0, yAxisIndex: 0 },
      { name: '成交量', type: 'bar', data: periodData.volumes, xAxisIndex: 1, yAxisIndex: 1 }
    ]
  }
}
```
```typescript
// in src/main.ts
// Add ECharts registration
import 'echarts'
import ECharts from 'vue-echarts'

export async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)
  useColorModeStore(pinia).hydrate()
  app.use(router)
  app.component('v-chart', ECharts) // <--- ADD THIS

  await ensureStartupSync()

  app.mount('#app')
}
```

- [ ] **Step 5: Run tests and commit**
Run: `npm run test -- src/utils/__tests__/chartAdapter.spec.ts`
Expected: PASS
```bash
git add package.json package-lock.json src/main.ts src/utils/chartAdapter.ts src/utils/__tests__/chartAdapter.spec.ts
git commit -m "feat(ui): add echarts and chartAdapter for Analysis"
```

### Task 2: 替换 Analysis.vue 数据流逻辑

**Files:**
- Modify: `src/views/Analysis.vue`
- Modify: `src/views/__tests__/Analysis.spec.ts`

- [ ] **Step 1: Write the failing test**
```typescript
// in src/views/__tests__/Analysis.spec.ts
// Replace the top mock of vue-router and tauri
// Change existing test 'fetches real data when code is selected'
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import Analysis from '../Analysis.vue'

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn()
}))

describe('Analysis.vue real data', () => {
  it('calls invoke_engine to fetch analysis data', async () => {
    const { invoke } = await import('@tauri-apps/api/core')
    const mockInvoke = invoke as any
    mockInvoke.mockResolvedValue({
      code: '510300',
      name: '测试ETF',
      price: '4.00',
      change: '1.0%',
      market: 'SH',
      iopv: '4.00',
      premium: '0.0%',
      riskLevel: '低风险',
      strategy: { conclusion: '观望' },
      periods: {
        day: { label: '日K', summary: 'test', chartSummary: 'test', metrics: [] }
      }
    })

    const wrapper = mount(Analysis, { global: { mocks: { $route: { query: { code: '510300' } } } } })
    await new Promise(r => setTimeout(r, 0))
    expect(mockInvoke).toHaveBeenCalledWith('invoke_engine', { method: 'get_analysis_data', params: { code: '510300' } })
    expect(wrapper.text()).toContain('测试ETF')
  })
})
```

- [ ] **Step 2: Run test to verify failure**
Run: `npm run test -- src/views/__tests__/Analysis.spec.ts`
Expected: FAIL (Component uses `analysisMock`)

- [ ] **Step 3: Write implementation**
```vue
// in src/views/Analysis.vue
// 1. Remove import of `getAnalysisMockByCode`, `searchAnalysisCandidates`
// 2. Add import for `invoke` from `@tauri-apps/api/core`
// 3. Define `activeAnalysis` as `ref<any>(null)`
// 4. Implement `fetchAnalysisData` and call in watch(routeCode)
// 5. Update template to use `v-chart` instead of the huge SVG section

<script setup lang="ts">
// ... imports
import { invoke } from '@tauri-apps/api/core'
import { buildIntradayOption, buildKLineOption } from '../utils/chartAdapter'

const activeAnalysis = ref<any>(null)
const candidates = ref<any[]>([])

// replace old mock logic:
const fetchAnalysisData = async (code: string) => {
  activeAnalysis.value = null
  try {
    const res = await invoke('invoke_engine', {
      method: 'get_analysis_data',
      params: { code }
    })
    if (res) activeAnalysis.value = res
  } catch (err) {
    console.error(err)
  }
}

watch(routeCode, (code) => {
  activePeriodKey.value = 'day'
  if (code) {
    keyword.value = ''
    fetchAnalysisData(code)
  } else {
    activeAnalysis.value = null
  }
}, { immediate: true })

watch(keyword, async (kw) => {
  if (!kw.trim()) {
    candidates.value = []
    return
  }
  try {
    candidates.value = await invoke('invoke_engine', { method: 'search_funds', params: { keyword: kw } })
  } catch (e) {
    candidates.value = []
  }
})

const chartOption = computed(() => {
  if (!activePeriod.value) return {}
  if (isIntradayChart.value) return buildIntradayOption(activePeriod.value, colorMode.mode)
  return buildKLineOption(activePeriod.value, colorMode.mode)
})
</script>

<template>
<!-- IN THE CHART MOCK AREA, replace everything inside `<div class="mt-4 rounded-xl...` with: -->
<div class="mt-4 rounded-xl border border-slate-200 bg-white p-4 h-[400px]">
  <v-chart class="h-full w-full" :option="chartOption" autoresize />
</div>
<!-- NOTE: You can remove the old complex SVG and Hitbox elements from the template completely -->
</template>
```

- [ ] **Step 4: Run tests**
Run: `npm run test -- src/views/__tests__/Analysis.spec.ts`
*(Note: You will likely need to fix or remove older tests in `Analysis.spec.ts` that specifically asserted on SVG inner HTML like `hitbox` elements since they are now gone. Update the test file so it passes.)*

- [ ] **Step 5: Commit**
```bash
git add src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts
git commit -m "feat(ui): replace Analysis mock with real invoke_engine and ECharts v-chart"
```
