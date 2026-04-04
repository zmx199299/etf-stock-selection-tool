# 第三页技术分析页面 Mock 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `Analysis.vue` 从占位页实现为已确认的第三页 Mock 页面，完成基础信息摘要、策略建议、图表 Mock 与技术指标结论四段结构，并保持与第二页统一的页面壳层。

**Architecture:** 首版只做前端 Mock，实现重点是页面结构与阅读顺序，而不是图表数据真实性。通过新增纯 TypeScript Mock 数据模块承载第三页示例内容，`Analysis.vue` 负责根据路由 `code` 与页内搜索状态切换展示“带代码分析态”和“无代码引导态”，同时沿用现有顶部横栏与全局配色规则。

**Tech Stack:** Vue 3 / TypeScript / Vue Router / Pinia / Tailwind CSS v4 / Vitest / @vue/test-utils / jsdom

**Design Doc:** `docs/superpowers/specs/2026-04-03-analysis-page-design.md`

---

## 前置说明

- 本轮只实现第三页 Mock 页面，不接 ECharts、不接真实后端接口、不扩展 Rust / Python。
- 继续遵循固定三段框架：左侧导航栏不改、顶部横栏统一、中间内容展示区为实现重点。
- 只提交与第三页 Mock 页面相关的代码和文档，避免把无关工作区文件带入提交。

## 文件边界

- Create: `src/utils/analysisMock.ts` - 第三页示例基金数据、摘要信息、策略建议、图表说明与指标结论的纯 TypeScript Mock 数据源与查找函数。
- Create: `src/utils/__tests__/analysisMock.spec.ts` - 覆盖按代码查找、默认数据与无结果分支。
- Modify: `src/views/Analysis.vue` - 将占位页改造为第三页研究报告主线型 Mock 页面。
- Create: `src/views/__tests__/Analysis.spec.ts` - 覆盖第三页页面壳层、带代码展示、无代码引导、页内搜索切换与四段布局顺序。
- Modify: `src/router/index.ts` - 保持 `analysis` 路由不变，本轮通常无需改动；仅在测试中确认 query 使用方式。
- Modify: `docs/development/human/2026-04-03-daily-log.md` - 记录第三页实现计划开始与后续实现结果。
- Modify: `docs/development/ai/current_state.md` - 更新第三页计划执行状态。

---

### Task 1: 建立第三页 Mock 数据边界

**Files:**
- Create: `src/utils/analysisMock.ts`
- Test: `src/utils/__tests__/analysisMock.spec.ts`

- [ ] **Step 1: 先写失败的 Mock 数据测试**

创建 `src/utils/__tests__/analysisMock.spec.ts`：

```ts
import { describe, expect, it } from 'vitest'

import { getAnalysisMockByCode, getDefaultAnalysisMock, searchAnalysisCandidates } from '../analysisMock'

describe('analysisMock', () => {
  it('按基金代码返回对应分析 Mock 数据', () => {
    const result = getAnalysisMockByCode('510300')

    expect(result?.code).toBe('510300')
    expect(result?.name).toBe('沪深300ETF')
    expect(result?.strategy.conclusion).toContain('震荡偏强')
  })

  it('默认示例基金使用第一条 Mock 数据', () => {
    expect(getDefaultAnalysisMock().code).toBe('510300')
  })

  it('搜索候选支持代码和名称关键字匹配', () => {
    const byCode = searchAnalysisCandidates('159915')
    const byName = searchAnalysisCandidates('创业板')

    expect(byCode).toHaveLength(1)
    expect(byCode[0].code).toBe('159915')
    expect(byName[0].name).toContain('创业板')
  })
})
```

- [ ] **Step 2: 运行测试确认当前失败**

Run: `npm run test -- --run src/utils/__tests__/analysisMock.spec.ts`

Expected: FAIL，报错 `Cannot find module '../analysisMock'` 或缺少导出函数。

- [ ] **Step 3: 写最小 Mock 数据实现**

创建 `src/utils/analysisMock.ts`：

```ts
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
  chartHeadline: string
  chartSummary: string
  metrics: AnalysisMetric[]
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
      stopLoss: '跌破 3.98 止损',
      holdingPeriod: '5 - 10 个交易日',
      riskNote: '若量能不能持续放大，反弹空间会被压缩。',
    },
    chartHeadline: '价格仍在近期整理平台上沿附近震荡',
    chartSummary: '主图区域首版只展示高保真 Mock，用于确认图表尺寸、层级和阅读动线。',
    metrics: [
      { label: 'MACD', value: '金叉', summary: '短线动能转强', tone: 'bullish' },
      { label: 'RSI', value: '52', summary: '仍在中性偏强区域', tone: 'neutral' },
      { label: 'BOLL', value: '中轨上方', summary: '价格重回中轨之上', tone: 'bullish' },
      { label: '均线', value: 'MA5 上穿 MA20', summary: '短期趋势改善', tone: 'bullish' },
    ],
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
      stopLoss: '跌破 2.12 止损',
      holdingPeriod: '3 - 5 个交易日',
      riskNote: '创业板波动较大，若指数回撤需快速收缩仓位。',
    },
    chartHeadline: '短线放量反弹，但仍处高波动节奏',
    chartSummary: '图表区重点观察近期低点抬升与量能配合。',
    metrics: [
      { label: 'MACD', value: '红柱放大', summary: '上行动能增强', tone: 'bullish' },
      { label: 'RSI', value: '68', summary: '接近短线过热', tone: 'bearish' },
      { label: 'BOLL', value: '靠近上轨', summary: '价格逼近上沿压力', tone: 'neutral' },
      { label: '均线', value: '短期多头', summary: '短期趋势维持向上', tone: 'bullish' },
    ],
  },
]

export function getAnalysisMockByCode(code: string) {
  return ANALYSIS_MOCKS.find((item) => item.code === code)
}

export function getDefaultAnalysisMock() {
  return ANALYSIS_MOCKS[0]
}

export function searchAnalysisCandidates(keyword: string) {
  const normalized = keyword.trim().toLowerCase()

  if (!normalized) {
    return ANALYSIS_MOCKS
  }

  return ANALYSIS_MOCKS.filter((item) => {
    return item.code.toLowerCase().includes(normalized) || item.name.toLowerCase().includes(normalized)
  })
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test -- --run src/utils/__tests__/analysisMock.spec.ts`

Expected: PASS，3 个测试通过。

- [ ] **Step 5: 提交**

```bash
git add src/utils/analysisMock.ts src/utils/__tests__/analysisMock.spec.ts
git commit -m "feat: add analysis mock data model"
```

---

### Task 2: 先用测试钉住第三页固定框架与展示顺序

**Files:**
- Modify: `src/views/Analysis.vue`
- Test: `src/views/__tests__/Analysis.spec.ts`

- [ ] **Step 1: 先写失败的第三页页面结构测试**

创建 `src/views/__tests__/Analysis.spec.ts`：

```ts
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Analysis from '../Analysis.vue'

const routeMock = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => routeMock(),
}))

describe('Analysis', () => {
  beforeEach(() => {
    routeMock.mockReturnValue({ query: { code: '510300' } })
  })

  it('第三页沿用统一页面壳层与顶部横栏框架', () => {
    const wrapper = mount(Analysis)

    expect(wrapper.get('[data-test="analysis-shell"]').classes()).toEqual(
      expect.arrayContaining(['min-h-full', 'bg-slate-50', 'p-4', 'md:p-6']),
    )
    expect(wrapper.get('[data-test="analysis-topbar-right"]').classes()).toEqual(
      expect.arrayContaining(['flex', 'flex-col', 'gap-3', 'md:flex-row', 'md:items-center', 'lg:w-[380px]', 'lg:flex-none']),
    )
  })

  it('带代码进入时按确认顺序展示四段内容', () => {
    const wrapper = mount(Analysis)

    const sectionOrder = wrapper.findAll('[data-test^="analysis-section-"]').map((node) => node.attributes('data-test'))

    expect(sectionOrder).toEqual([
      'analysis-section-summary',
      'analysis-section-strategy',
      'analysis-section-chart',
      'analysis-section-metrics',
    ])
    expect(wrapper.text()).toContain('沪深300ETF')
    expect(wrapper.text()).toContain('震荡偏强')
  })
})
```

- [ ] **Step 2: 运行测试确认当前失败**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: FAIL，报错找不到 `analysis-shell` 或内容顺序结构。

- [ ] **Step 3: 写最小页面骨架实现**

把 `src/views/Analysis.vue` 改为：

```vue
<template>
  <section data-test="analysis-shell" class="min-h-full bg-slate-50 p-4 md:p-6">
    <div class="flex w-full flex-col gap-4">
      <header data-test="analysis-topbar" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div class="space-y-1">
            <h1 class="text-2xl font-semibold tracking-tight text-slate-900">技术分析</h1>
            <p class="text-sm text-slate-500">{{ headerDescription }}</p>
          </div>

          <div data-test="analysis-topbar-right" class="flex flex-col gap-3 md:flex-row md:items-center lg:w-[380px] lg:flex-none">
            <div class="inline-flex rounded-xl bg-slate-100 p-1">
              <button class="rounded-lg bg-white px-3 py-2 text-sm font-medium text-slate-900 shadow-sm">当前基金</button>
            </div>
            <input
              data-test="analysis-search"
              v-model="keyword"
              type="text"
              placeholder="搜索基金代码/名称"
              class="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-slate-300 focus:ring-2 focus:ring-slate-200 md:w-64"
            />
          </div>
        </div>
      </header>

      <div data-test="analysis-section-summary" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        {{ activeAnalysis?.name }}
      </div>
      <div data-test="analysis-section-strategy" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        {{ activeAnalysis?.strategy.conclusion }}
      </div>
      <div data-test="analysis-section-chart" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        {{ activeAnalysis?.chartHeadline }}
      </div>
      <div data-test="analysis-section-metrics" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        {{ activeAnalysis?.metrics[0].label }}
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

import { getAnalysisMockByCode } from '../utils/analysisMock'

const route = useRoute()
const keyword = ref('')

const activeCode = computed(() => String(route.query.code ?? '510300'))
const activeAnalysis = computed(() => getAnalysisMockByCode(activeCode.value))
const headerDescription = computed(() => `${activeAnalysis.value?.name ?? '未选择基金'} ${activeAnalysis.value?.code ?? ''}`.trim())
</script>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: PASS，2 个测试通过。

- [ ] **Step 5: 提交**

```bash
git add src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts
git commit -m "feat: scaffold analysis mock layout"
```

---

### Task 3: 完成首屏摘要区与策略建议区的 40 / 60 布局

**Files:**
- Modify: `src/views/Analysis.vue`
- Test: `src/views/__tests__/Analysis.spec.ts`

- [ ] **Step 1: 先写失败的首屏比例与字段测试**

在 `src/views/__tests__/Analysis.spec.ts` 追加：

```ts
it('首屏采用摘要 40% / 策略 60% 的双栏布局，并展示主次策略字段', () => {
  const wrapper = mount(Analysis)

  expect(wrapper.get('[data-test="analysis-hero-grid"]').classes()).toEqual(
    expect.arrayContaining(['grid', 'gap-4', 'xl:grid-cols-[2fr_3fr]']),
  )
  expect(wrapper.text()).toContain('买入区间')
  expect(wrapper.text()).toContain('仓位建议')
  expect(wrapper.text()).toContain('止盈止损')
  expect(wrapper.text()).toContain('持有周期')
  expect(wrapper.text()).toContain('风险提示')
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: FAIL，缺少 `analysis-hero-grid` 或缺少字段文案。

- [ ] **Step 3: 写最小实现**

把首屏四段中的前两段改为一组双栏布局：

```vue
<div data-test="analysis-hero-grid" class="grid gap-4 xl:grid-cols-[2fr_3fr]">
  <section data-test="analysis-section-summary" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="grid gap-3 sm:grid-cols-2">
      <div class="rounded-xl bg-slate-50 p-4">
        <div class="text-xs uppercase tracking-[0.08em] text-slate-400">基金</div>
        <div class="mt-2 text-base font-semibold text-slate-900">{{ activeAnalysis?.name }}</div>
        <div class="text-sm text-slate-500">{{ activeAnalysis?.code }} · {{ activeAnalysis?.market }}</div>
      </div>
      <div class="rounded-xl bg-slate-50 p-4">
        <div class="text-xs uppercase tracking-[0.08em] text-slate-400">现价</div>
        <div class="mt-2 text-base font-semibold text-slate-900">{{ activeAnalysis?.price }}</div>
      </div>
      <div class="rounded-xl bg-slate-50 p-4">
        <div class="text-xs uppercase tracking-[0.08em] text-slate-400">涨跌幅</div>
        <div class="mt-2 text-base font-semibold text-slate-900">{{ activeAnalysis?.change }}</div>
      </div>
      <div class="rounded-xl bg-slate-50 p-4">
        <div class="text-xs uppercase tracking-[0.08em] text-slate-400">IOPV / 溢价</div>
        <div class="mt-2 text-base font-semibold text-slate-900">{{ activeAnalysis?.iopv }} / {{ activeAnalysis?.premium }}</div>
      </div>
    </div>
  </section>

  <section data-test="analysis-section-strategy" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="space-y-4">
      <div class="rounded-2xl bg-slate-900 p-5 text-white">
        <div class="text-xs uppercase tracking-[0.08em] text-slate-300">操作结论</div>
        <div class="mt-3 text-2xl font-semibold tracking-tight">{{ activeAnalysis?.strategy.conclusion }}</div>
      </div>
      <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <div class="rounded-xl bg-slate-50 p-4"><div class="text-xs text-slate-400">买入区间</div><div class="mt-2 text-sm font-medium text-slate-900">{{ activeAnalysis?.strategy.buyZone }}</div></div>
        <div class="rounded-xl bg-slate-50 p-4"><div class="text-xs text-slate-400">卖出区间</div><div class="mt-2 text-sm font-medium text-slate-900">{{ activeAnalysis?.strategy.sellZone }}</div></div>
        <div class="rounded-xl bg-slate-50 p-4"><div class="text-xs text-slate-400">仓位建议</div><div class="mt-2 text-sm font-medium text-slate-900">{{ activeAnalysis?.strategy.position }}</div></div>
        <div class="rounded-xl bg-slate-50 p-4"><div class="text-xs text-slate-400">止盈止损</div><div class="mt-2 text-sm font-medium text-slate-900">{{ activeAnalysis?.strategy.stopLoss }}</div></div>
        <div class="rounded-xl bg-slate-50 p-4"><div class="text-xs text-slate-400">持有周期</div><div class="mt-2 text-sm font-medium text-slate-900">{{ activeAnalysis?.strategy.holdingPeriod }}</div></div>
        <div class="rounded-xl bg-slate-50 p-4"><div class="text-xs text-slate-400">风险提示</div><div class="mt-2 text-sm font-medium text-slate-900">{{ activeAnalysis?.strategy.riskNote }}</div></div>
      </div>
    </div>
  </section>
</div>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: PASS，新增首屏测试通过。

- [ ] **Step 5: 提交**

```bash
git add src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts
git commit -m "feat: add analysis summary and strategy hero"
```

---

### Task 4: 完成图表 Mock 区与技术指标结论区

**Files:**
- Modify: `src/views/Analysis.vue`
- Test: `src/views/__tests__/Analysis.spec.ts`

- [ ] **Step 1: 先写失败的图表与指标区测试**

在 `src/views/__tests__/Analysis.spec.ts` 追加：

```ts
it('图表区展示高保真 Mock 主图，指标区展示四张结论卡', () => {
  const wrapper = mount(Analysis)

  expect(wrapper.get('[data-test="analysis-chart-mock"]').text()).toContain('K 线')
  expect(wrapper.get('[data-test="analysis-chart-summary"]').text()).toContain('图表')
  expect(wrapper.findAll('[data-test="analysis-metric-card"]')).toHaveLength(4)
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: FAIL，缺少图表 Mock 和指标卡节点。

- [ ] **Step 3: 写最小实现**

把后两段补成如下结构：

```vue
<section data-test="analysis-section-chart" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
  <div class="space-y-4">
    <div>
      <h2 class="text-lg font-semibold text-slate-900">图表研判</h2>
      <p data-test="analysis-chart-summary" class="mt-1 text-sm text-slate-500">{{ activeAnalysis?.chartSummary }}</p>
    </div>
    <div class="grid gap-4 xl:grid-cols-[2fr_1fr]">
      <div data-test="analysis-chart-mock" class="rounded-2xl border border-slate-200 bg-slate-50 p-6">
        <div class="text-sm font-medium text-slate-700">K 线 / 趋势 / 成交量 Mock 图</div>
        <div class="mt-4 h-72 rounded-xl bg-white"></div>
      </div>
      <div class="rounded-2xl bg-slate-50 p-5 text-sm text-slate-600">
        <div class="text-xs uppercase tracking-[0.08em] text-slate-400">图旁解读</div>
        <div class="mt-3 text-base font-medium text-slate-900">{{ activeAnalysis?.chartHeadline }}</div>
      </div>
    </div>
  </div>
</section>

<section data-test="analysis-section-metrics" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
  <div class="space-y-4">
    <div>
      <h2 class="text-lg font-semibold text-slate-900">技术指标结论</h2>
      <p class="mt-1 text-sm text-slate-500">使用克制的信息卡对关键指标做总结，不抢主视线。</p>
    </div>
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <article
        v-for="metric in activeAnalysis?.metrics"
        :key="metric.label"
        data-test="analysis-metric-card"
        class="rounded-2xl bg-slate-50 p-5"
      >
        <div class="text-xs uppercase tracking-[0.08em] text-slate-400">{{ metric.label }}</div>
        <div class="mt-3 text-lg font-semibold text-slate-900">{{ metric.value }}</div>
        <div class="mt-2 text-sm text-slate-600">{{ metric.summary }}</div>
      </article>
    </div>
  </div>
</section>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: PASS，图表与指标区测试通过。

- [ ] **Step 5: 提交**

```bash
git add src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts
git commit -m "feat: add analysis chart and metric sections"
```

---

### Task 5: 实现无代码引导态与页内搜索切换

**Files:**
- Modify: `src/views/Analysis.vue`
- Test: `src/views/__tests__/Analysis.spec.ts`

- [ ] **Step 1: 先写失败的入口状态测试**

在 `src/views/__tests__/Analysis.spec.ts` 追加：

```ts
it('无基金代码时显示引导卡，并允许页内搜索后切换到分析态', async () => {
  routeMock.mockReturnValue({ query: {} })
  const wrapper = mount(Analysis)

  expect(wrapper.get('[data-test="analysis-empty-state"]').text()).toContain('请选择基金')

  await wrapper.get('[data-test="analysis-search"]').setValue('创业板')
  await wrapper.get('[data-test="analysis-pick-159915"]').trigger('click')

  expect(wrapper.text()).toContain('创业板ETF')
  expect(wrapper.find('[data-test="analysis-empty-state"]').exists()).toBe(false)
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: FAIL，缺少空状态或搜索切换行为。

- [ ] **Step 3: 写最小实现**

在 `src/views/Analysis.vue` 中加入本地选中代码与候选列表：

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

import { getAnalysisMockByCode, searchAnalysisCandidates } from '../utils/analysisMock'

const route = useRoute()
const keyword = ref('')
const selectedCode = ref<string | null>(null)

const routeCode = computed(() => {
  const raw = route.query.code
  return typeof raw === 'string' && raw ? raw : null
})

const activeCode = computed(() => selectedCode.value ?? routeCode.value)
const activeAnalysis = computed(() => (activeCode.value ? getAnalysisMockByCode(activeCode.value) : null))
const candidates = computed(() => searchAnalysisCandidates(keyword.value))
const headerDescription = computed(() => {
  if (activeAnalysis.value) {
    return `${activeAnalysis.value.name} · ${activeAnalysis.value.code}`
  }

  return '先搜索或选择基金，再查看技术分析内容'
})

function selectCode(code: string) {
  selectedCode.value = code
}
</script>
```

并在模板中补空状态：

```vue
<div v-if="!activeAnalysis" data-test="analysis-empty-state" class="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-sm">
  <h2 class="text-xl font-semibold text-slate-900">请选择基金</h2>
  <p class="mt-2 text-sm text-slate-500">第三页支持从列表页带代码进入，也支持在页内搜索后查看示例分析。</p>
  <div class="mt-6 grid gap-3 md:grid-cols-2">
    <button
      v-for="candidate in candidates"
      :key="candidate.code"
      :data-test="`analysis-pick-${candidate.code}`"
      type="button"
      class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-left transition hover:border-slate-300 hover:bg-white"
      @click="selectCode(candidate.code)"
    >
      <div class="font-medium text-slate-900">{{ candidate.name }}</div>
      <div class="text-sm text-slate-500">{{ candidate.code }}</div>
    </button>
  </div>
</div>

<template v-else>
  <div data-test="analysis-hero-grid" class="grid gap-4 xl:grid-cols-[2fr_3fr]">
    <section data-test="analysis-section-summary" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="grid gap-3 sm:grid-cols-2">
        <div class="rounded-xl bg-slate-50 p-4">
          <div class="text-xs uppercase tracking-[0.08em] text-slate-400">基金</div>
          <div class="mt-2 text-base font-semibold text-slate-900">{{ activeAnalysis.name }}</div>
          <div class="text-sm text-slate-500">{{ activeAnalysis.code }} · {{ activeAnalysis.market }}</div>
        </div>
        <div class="rounded-xl bg-slate-50 p-4">
          <div class="text-xs uppercase tracking-[0.08em] text-slate-400">现价</div>
          <div class="mt-2 text-base font-semibold text-slate-900">{{ activeAnalysis.price }}</div>
        </div>
        <div class="rounded-xl bg-slate-50 p-4">
          <div class="text-xs uppercase tracking-[0.08em] text-slate-400">涨跌幅</div>
          <div class="mt-2 text-base font-semibold text-slate-900">{{ activeAnalysis.change }}</div>
        </div>
        <div class="rounded-xl bg-slate-50 p-4">
          <div class="text-xs uppercase tracking-[0.08em] text-slate-400">IOPV / 溢价</div>
          <div class="mt-2 text-base font-semibold text-slate-900">{{ activeAnalysis.iopv }} / {{ activeAnalysis.premium }}</div>
        </div>
      </div>
    </section>

    <section data-test="analysis-section-strategy" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="space-y-4">
        <div class="rounded-2xl bg-slate-900 p-5 text-white">
          <div class="text-xs uppercase tracking-[0.08em] text-slate-300">操作结论</div>
          <div class="mt-3 text-2xl font-semibold tracking-tight">{{ activeAnalysis.strategy.conclusion }}</div>
        </div>
        <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <div class="rounded-xl bg-slate-50 p-4"><div class="text-xs text-slate-400">买入区间</div><div class="mt-2 text-sm font-medium text-slate-900">{{ activeAnalysis.strategy.buyZone }}</div></div>
          <div class="rounded-xl bg-slate-50 p-4"><div class="text-xs text-slate-400">卖出区间</div><div class="mt-2 text-sm font-medium text-slate-900">{{ activeAnalysis.strategy.sellZone }}</div></div>
          <div class="rounded-xl bg-slate-50 p-4"><div class="text-xs text-slate-400">仓位建议</div><div class="mt-2 text-sm font-medium text-slate-900">{{ activeAnalysis.strategy.position }}</div></div>
          <div class="rounded-xl bg-slate-50 p-4"><div class="text-xs text-slate-400">止盈止损</div><div class="mt-2 text-sm font-medium text-slate-900">{{ activeAnalysis.strategy.stopLoss }}</div></div>
          <div class="rounded-xl bg-slate-50 p-4"><div class="text-xs text-slate-400">持有周期</div><div class="mt-2 text-sm font-medium text-slate-900">{{ activeAnalysis.strategy.holdingPeriod }}</div></div>
          <div class="rounded-xl bg-slate-50 p-4"><div class="text-xs text-slate-400">风险提示</div><div class="mt-2 text-sm font-medium text-slate-900">{{ activeAnalysis.strategy.riskNote }}</div></div>
        </div>
      </div>
    </section>
  </div>

  <section data-test="analysis-section-chart" class="mt-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="space-y-4">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">图表研判</h2>
        <p data-test="analysis-chart-summary" class="mt-1 text-sm text-slate-500">{{ activeAnalysis.chartSummary }}</p>
      </div>
      <div class="grid gap-4 xl:grid-cols-[2fr_1fr]">
        <div data-test="analysis-chart-mock" class="rounded-2xl border border-slate-200 bg-slate-50 p-6">
          <div class="text-sm font-medium text-slate-700">K 线 / 趋势 / 成交量 Mock 图</div>
          <div class="mt-4 h-72 rounded-xl bg-white"></div>
        </div>
        <div class="rounded-2xl bg-slate-50 p-5 text-sm text-slate-600">
          <div class="text-xs uppercase tracking-[0.08em] text-slate-400">图旁解读</div>
          <div class="mt-3 text-base font-medium text-slate-900">{{ activeAnalysis.chartHeadline }}</div>
        </div>
      </div>
    </div>
  </section>

  <section data-test="analysis-section-metrics" class="mt-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="space-y-4">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">技术指标结论</h2>
        <p class="mt-1 text-sm text-slate-500">使用克制的信息卡对关键指标做总结，不抢主视线。</p>
      </div>
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <article
          v-for="metric in activeAnalysis.metrics"
          :key="metric.label"
          data-test="analysis-metric-card"
          class="rounded-2xl bg-slate-50 p-5"
        >
          <div class="text-xs uppercase tracking-[0.08em] text-slate-400">{{ metric.label }}</div>
          <div class="mt-3 text-lg font-semibold text-slate-900">{{ metric.value }}</div>
          <div class="mt-2 text-sm text-slate-600">{{ metric.summary }}</div>
        </article>
      </div>
    </div>
  </section>
</template>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: PASS，入口状态测试通过。

- [ ] **Step 5: 运行相关回归并提交**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts src/views/__tests__/FundList.spec.ts src/views/__tests__/Dashboard.spec.ts src/utils/__tests__/analysisMock.spec.ts`

Expected: PASS，第三页与现有首页、第二页测试全部通过。

```bash
git add src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts src/utils/analysisMock.ts src/utils/__tests__/analysisMock.spec.ts
git commit -m "feat: add analysis mock interactions"
```

---

### Task 6: 完成文档收口与构建验证

**Files:**
- Modify: `docs/development/human/2026-04-03-daily-log.md`
- Modify: `docs/development/ai/current_state.md`

- [ ] **Step 1: 更新人类日志中的实现结果**

在 `docs/development/human/2026-04-03-daily-log.md` 追加：

```md
## Mock 实现结果

- 第三页 `Analysis.vue` 已从占位页改为研究报告主线型 Mock 页面。
- 已实现带基金代码直达与页内搜索选择两种入口状态。
- 已完成摘要区、策略建议区、图表 Mock 区与技术指标结论区四段结构。
```

- [ ] **Step 2: 更新 AI 状态中的执行进度**

在 `docs/development/ai/current_state.md` 更新：

```md
- 第三页 `Analysis.vue` 首版 Mock 页面已实现，当前为结构确认阶段。
- 第三页支持带基金代码直达与页内搜索切换，图表仍为高保真 Mock。
```

- [ ] **Step 3: 运行最终验证**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts src/views/__tests__/FundList.spec.ts src/views/__tests__/Dashboard.spec.ts src/utils/__tests__/analysisMock.spec.ts`

Expected: PASS，所有相关测试通过。

Run: `npm run build`

Expected: PASS，前端构建通过。

- [ ] **Step 4: 提交**

```bash
git add docs/development/human/2026-04-03-daily-log.md docs/development/ai/current_state.md
git commit -m "docs: record analysis mock progress"
```

---

## 自检

- 规格覆盖检查：已覆盖固定页面壳层、四段顺序、40/60 首屏布局、策略主次、双入口状态和图表 Mock 边界。
- 占位词检查：未使用任何占位式语句；每个任务都有明确代码和命令。
- 一致性检查：计划中的 `analysis-shell`、`analysis-hero-grid`、`analysis-empty-state`、`analysis-chart-mock` 等命名在所有任务中保持一致。
