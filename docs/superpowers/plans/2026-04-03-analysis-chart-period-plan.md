# 第三页技术分析图表周期切换实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为第三页 `Analysis.vue` 增加周期下拉框、价格轴、时间轴、分时图 / K 线双形态，以及图旁解读和指标区随周期联动，并保持与全局红绿配色方案一致。

**Architecture:** 保持第三页现有页面壳层、摘要区和策略区不变，只扩展图表区与指标区。通过把 `analysisMock` 从“单组图表描述”升级为“按周期组织”的 Mock 数据结构，让 `Analysis.vue` 根据当前选中周期切换主图形态、价格轴、时间轴、图旁解读和指标卡，同时复用现有 `colorMode` store 与 `marketColors` 工具统一控制涨跌/多空语义颜色。

**Tech Stack:** Vue 3 / TypeScript / Vue Router / Pinia / Tailwind CSS v4 / Vitest / @vue/test-utils / jsdom

**Design Doc:** `docs/superpowers/specs/2026-04-03-analysis-chart-period-design.md`

---

## 前置说明

- 本轮只改第三页图表区和指标区，不重做首页与第二页。
- 继续只做 Mock，不引入 ECharts，不接真实行情接口。
- 必须延续全局红绿配色规则，不能在第三页引入新的本地配色逻辑。

## 文件边界

- Modify: `src/utils/analysisMock.ts` - 将第三页图表与指标数据升级为按周期组织，新增价格轴、时间轴、主图数据和周期解读。
- Modify: `src/utils/__tests__/analysisMock.spec.ts` - 覆盖周期数据查找、周期集合完整性和返回值隔离。
- Modify: `src/views/Analysis.vue` - 增加周期下拉框、分时图 / K 线切换、价格轴、时间轴和周期联动显示。
- Modify: `src/views/__tests__/Analysis.spec.ts` - 覆盖周期下拉、分时 / K 线切换、价格轴时间轴渲染和颜色联动。
- Modify: `docs/development/human/2026-04-03-daily-log.md` - 追加第三页图表区周期化改造结果。
- Modify: `docs/development/ai/current_state.md` - 更新第三页进入“周期化图表 Mock”阶段的状态。

---

### Task 1: 把第三页 Mock 数据扩成按周期组织

**Files:**
- Modify: `src/utils/analysisMock.ts`
- Test: `src/utils/__tests__/analysisMock.spec.ts`

- [ ] **Step 1: 先写失败的周期数据测试**

在 `src/utils/__tests__/analysisMock.spec.ts` 追加：

```ts
it('每只基金都包含完整的九种图表周期数据', () => {
  const result = getAnalysisMockByCode('510300')

  expect(result?.periods.intraday.label).toBe('分时')
  expect(result?.periods.day.label).toBe('日K')
  expect(result?.periods.m5.label).toBe('5分')
  expect(result?.periods.m60.label).toBe('60分')
  expect(result?.periods.m120.label).toBe('120分')
  expect(result?.periods.week.label).toBe('周K')
  expect(result?.periods.month.label).toBe('月K')
  expect(result?.periods.quarter.label).toBe('季K')
  expect(result?.periods.year.label).toBe('年K')
})

it('分时周期提供分时线所需的价格轴与时间轴数据', () => {
  const result = getAnalysisMockByCode('510300')

  expect(result?.periods.intraday.priceAxis).toHaveLength(5)
  expect(result?.periods.intraday.timeAxis).toContain('09:30')
  expect(result?.periods.intraday.linePoints.length).toBeGreaterThan(4)
})

it('K线周期提供蜡烛图与成交量所需数据', () => {
  const result = getAnalysisMockByCode('510300')

  expect(result?.periods.day.candles).toHaveLength(12)
  expect(result?.periods.day.volumes).toHaveLength(12)
  expect(result?.periods.day.metrics).toHaveLength(4)
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test -- --run src/utils/__tests__/analysisMock.spec.ts`

Expected: FAIL，提示 `periods`、`priceAxis`、`timeAxis` 或 `candles` 等字段不存在。

- [ ] **Step 3: 写最小数据结构实现**

在 `src/utils/analysisMock.ts` 中：

```ts
export type AnalysisChartCandle = {
  open: number
  close: number
  high: number
  low: number
  direction: 'bullish' | 'bearish'
}

export type AnalysisMetric = {
  label: string
  value: string
  summary: string
  tone: 'bullish' | 'neutral' | 'bearish'
}

export type AnalysisPeriodMock = {
  key: 'intraday' | 'day' | 'm5' | 'm60' | 'm120' | 'week' | 'month' | 'quarter' | 'year'
  label: string
  summary: string
  chartHeadline: string
  chartSummary: string
  priceAxis: string[]
  timeAxis: string[]
  linePoints: number[]
  avgLinePoints: number[]
  candles: AnalysisChartCandle[]
  volumes: number[]
  metrics: AnalysisMetric[]
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
  periods: Record<AnalysisPeriodMock['key'], AnalysisPeriodMock>
}
```

并把 `510300` / `159915` 的原 `chartHeadline`、`chartSummary`、`metrics` 下沉为 `periods` 下的数据，保证九个周期都存在。

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test -- --run src/utils/__tests__/analysisMock.spec.ts`

Expected: PASS，原有测试和新增周期测试全部通过。

- [ ] **Step 5: 提交**

```bash
git add src/utils/analysisMock.ts src/utils/__tests__/analysisMock.spec.ts
git commit -m "feat: add period-based analysis chart mock data"
```

---

### Task 2: 为第三页图表区加周期下拉框并默认显示日K

**Files:**
- Modify: `src/views/Analysis.vue`
- Test: `src/views/__tests__/Analysis.spec.ts`

- [ ] **Step 1: 先写失败的周期选择测试**

在 `src/views/__tests__/Analysis.spec.ts` 追加：

```ts
it('图表区提供周期下拉框并默认显示日K内容', () => {
  const wrapper = mount(Analysis)

  expect((wrapper.get('[data-test="analysis-period-select"]').element as HTMLSelectElement).value).toBe('day')
  expect(wrapper.get('[data-test="analysis-period-summary"]').text()).toContain('日K')
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: FAIL，缺少 `analysis-period-select` 或 `analysis-period-summary`。

- [ ] **Step 3: 写最小实现**

在 `src/views/Analysis.vue` 的 `<script setup>` 中增加：

```ts
type AnalysisPeriodKey = 'intraday' | 'day' | 'm5' | 'm60' | 'm120' | 'week' | 'month' | 'quarter' | 'year'

const selectedPeriod = ref<AnalysisPeriodKey>('day')

const periodOptions: Array<{ value: AnalysisPeriodKey; label: string }> = [
  { value: 'intraday', label: '分时' },
  { value: 'day', label: '日K' },
  { value: 'm5', label: '5分' },
  { value: 'm60', label: '60分' },
  { value: 'm120', label: '120分' },
  { value: 'week', label: '周K' },
  { value: 'month', label: '月K' },
  { value: 'quarter', label: '季K' },
  { value: 'year', label: '年K' },
]

const activePeriod = computed(() => activeAnalysis.value?.periods[selectedPeriod.value] ?? null)
```

并把图表卡头部调整为：

```vue
<div class="flex items-start justify-between gap-4">
  <div>
    <h2 class="text-lg font-semibold text-slate-900">图表研判</h2>
    <p data-test="analysis-period-summary" class="mt-1 text-sm text-slate-500">
      当前周期：{{ activePeriod?.label }}，{{ activePeriod?.summary }}
    </p>
  </div>

  <select
    data-test="analysis-period-select"
    v-model="selectedPeriod"
    class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none focus:border-slate-300 focus:ring-2 focus:ring-slate-200"
  >
    <option v-for="option in periodOptions" :key="option.value" :value="option.value">
      {{ option.label }}
    </option>
  </select>
</div>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: PASS，周期选择测试通过。

- [ ] **Step 5: 提交**

```bash
git add src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts
git commit -m "feat: add analysis period selector"
```

---

### Task 3: 图表区增加价格轴、时间轴与分时/K线双形态

**Files:**
- Modify: `src/views/Analysis.vue`
- Test: `src/views/__tests__/Analysis.spec.ts`

- [ ] **Step 1: 先写失败的图表形态测试**

在 `src/views/__tests__/Analysis.spec.ts` 追加：

```ts
it('日K默认展示价格轴、时间轴和十二根K线', () => {
  const wrapper = mount(Analysis)

  expect(wrapper.findAll('[data-test="analysis-price-axis-label"]')).toHaveLength(5)
  expect(wrapper.findAll('[data-test="analysis-time-axis-label"]')).toHaveLength(5)
  expect(wrapper.findAll('[data-test="analysis-chart-candle"]')).toHaveLength(12)
})

it('切换到分时后改为分时线与均价线，不再显示K线实体', async () => {
  const wrapper = mount(Analysis)

  await wrapper.get('[data-test="analysis-period-select"]').setValue('intraday')

  expect(wrapper.find('[data-test="analysis-intraday-line"]').exists()).toBe(true)
  expect(wrapper.find('[data-test="analysis-intraday-avg-line"]').exists()).toBe(true)
  expect(wrapper.findAll('[data-test="analysis-chart-candle"]')).toHaveLength(0)
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: FAIL，缺少价格轴、时间轴或分时线节点。

- [ ] **Step 3: 写最小实现**

把图表主区域改为：

```vue
<div class="grid gap-4 xl:grid-cols-[2fr_1fr]">
  <div data-test="analysis-chart-mock" class="rounded-2xl border border-slate-200 bg-slate-50 p-6">
    <div class="grid grid-cols-[56px_1fr] gap-3">
      <div class="flex h-64 flex-col justify-between text-xs text-slate-400">
        <span v-for="label in activePeriod?.priceAxis" :key="label" data-test="analysis-price-axis-label">{{ label }}</span>
      </div>
      <div>
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <div v-if="selectedPeriod === 'intraday'" class="space-y-4">
            <div data-test="analysis-intraday-line" class="h-40 rounded-lg bg-slate-50"></div>
            <div data-test="analysis-intraday-avg-line" class="h-1 rounded-full bg-slate-300"></div>
          </div>
          <div v-else class="flex h-40 items-end gap-2 rounded-lg bg-[linear-gradient(180deg,#f8fafc_0%,#ffffff_100%)] px-2 pb-3">
            <div
              v-for="(candle, index) in activePeriod?.candles"
              :key="`candle-${index}`"
              data-test="analysis-chart-candle"
              class="relative flex w-full items-end justify-center"
            >
              <div class="absolute bottom-2 w-px bg-slate-300" :style="{ height: `${Math.max(candle.high - candle.low, 18)}px` }"></div>
              <div
                :data-test="`analysis-chart-candle-${index}-body`"
                class="w-3 rounded-sm"
                :class="getMetricPalette(candle.direction).barClass"
                :style="{ height: `${Math.max(Math.abs(candle.close - candle.open) * 120, 18)}px` }"
              ></div>
            </div>
          </div>

          <div class="mt-4 flex h-16 items-end gap-2 px-2">
            <div
              v-for="(volume, index) in activePeriod?.volumes"
              :key="`volume-${index}`"
              data-test="analysis-chart-volume-bar"
              class="w-full rounded-t"
              :class="getVolumeBarClass(index)"
              :style="{ height: `${volume}%` }"
            ></div>
          </div>
        </div>

        <div class="mt-3 flex justify-between px-2 text-xs text-slate-400">
          <span v-for="label in activePeriod?.timeAxis" :key="label" data-test="analysis-time-axis-label">{{ label }}</span>
        </div>
      </div>
    </div>
  </div>

  <div class="rounded-2xl bg-slate-50 p-5 text-sm text-slate-600">
    <div class="text-xs uppercase tracking-[0.08em] text-slate-400">图旁解读</div>
    <div class="mt-3 text-base font-medium text-slate-900">{{ activePeriod?.chartHeadline }}</div>
    <p class="mt-3 leading-6">{{ activePeriod?.chartSummary }}</p>
  </div>
</div>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: PASS，图表形态测试通过。

- [ ] **Step 5: 提交**

```bash
git add src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts
git commit -m "feat: add period-aware analysis chart mock"
```

---

### Task 4: 让图旁解读和四张指标卡随周期联动

**Files:**
- Modify: `src/views/Analysis.vue`
- Test: `src/views/__tests__/Analysis.spec.ts`

- [ ] **Step 1: 先写失败的周期联动测试**

在 `src/views/__tests__/Analysis.spec.ts` 追加：

```ts
it('切换周期后图旁解读和指标卡一起更新', async () => {
  const wrapper = mount(Analysis)

  expect(wrapper.get('[data-test="analysis-metric-value-MACD"]').text()).toContain('金叉')

  await wrapper.get('[data-test="analysis-period-select"]').setValue('week')

  expect(wrapper.get('[data-test="analysis-period-summary"]').text()).toContain('周K')
  expect(wrapper.get('[data-test="analysis-metric-value-MACD"]').text()).not.toContain('金叉')
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: FAIL，指标区仍使用固定数据，不随周期变化。

- [ ] **Step 3: 写最小实现**

把指标区循环改成基于 `activePeriod?.metrics`：

```vue
<article
  v-for="metric in activePeriod?.metrics"
  :key="metric.label"
  data-test="analysis-metric-card"
  class="rounded-2xl bg-slate-50 p-5"
>
  <div class="flex items-center justify-between">
    <div class="text-xs uppercase tracking-[0.08em] text-slate-400">{{ metric.label }}</div>
    <span
      :data-test="`analysis-metric-dot-${metric.label}`"
      class="h-2.5 w-2.5 rounded-full"
      :class="getMetricPalette(metric.tone).dotClass"
    ></span>
  </div>
  <div
    :data-test="`analysis-metric-value-${metric.label}`"
    class="mt-3 text-lg font-semibold"
    :class="getMetricPalette(metric.tone).valueClass"
  >
    {{ metric.value }}
  </div>
  <div class="mt-2 text-sm text-slate-600">{{ metric.summary }}</div>
</article>
```

同时把图旁解读绑定到 `activePeriod`。

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: PASS，周期联动测试通过。

- [ ] **Step 5: 提交**

```bash
git add src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts
git commit -m "feat: sync analysis insights with selected period"
```

---

### Task 5: 保持第三页图表与指标颜色服从全局红绿配色

**Files:**
- Modify: `src/views/Analysis.vue`
- Test: `src/views/__tests__/Analysis.spec.ts`

- [ ] **Step 1: 先写失败的配色联动测试**

在 `src/views/__tests__/Analysis.spec.ts` 保留并补强如下测试：

```ts
it('K线与多空指标颜色跟随全局红绿配色方案切换', async () => {
  const wrapper = mount(Analysis)
  const colorModeStore = useColorModeStore()

  expect(wrapper.get('[data-test="analysis-chart-candle-0-body"]').classes()).toContain('bg-red-500')
  expect(wrapper.get('[data-test="analysis-chart-candle-1-body"]').classes()).toContain('bg-green-500')
  expect(wrapper.get('[data-test="analysis-metric-value-MACD"]').classes()).toContain('text-red-500')
  expect(wrapper.get('[data-test="analysis-metric-dot-MACD"]').classes()).toContain('bg-red-500')

  await wrapper.get('[data-test="analysis-mode-intl"]').trigger('click')
  await wrapper.vm.$nextTick()

  expect(colorModeStore.mode).toBe('intl')
  expect(wrapper.get('[data-test="analysis-chart-candle-0-body"]').classes()).toContain('bg-green-500')
  expect(wrapper.get('[data-test="analysis-chart-candle-1-body"]').classes()).toContain('bg-red-500')
  expect(wrapper.get('[data-test="analysis-metric-value-MACD"]').classes()).toContain('text-green-600')
  expect(wrapper.get('[data-test="analysis-metric-dot-MACD"]').classes()).toContain('bg-green-500')
})
```

- [ ] **Step 2: 运行测试确认失败（若当前实现未覆盖新图形态）**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: FAIL，若新增分时图或成交量没有统一走全局配色工具，测试会失败。

- [ ] **Step 3: 写最小实现**

在 `src/views/Analysis.vue` 中确保所有涨跌/多空颜色都统一通过 `getDirectionPalette(colorMode.mode, direction)` 计算，包括：

```ts
const changePalette = computed(() => {
  const value = Number(activeAnalysis.value?.change.replace('%', '') ?? '0')
  return getDirectionPalette(colorMode.mode, numericToDirection(value))
})

const premiumPalette = computed(() => {
  const value = Number(activeAnalysis.value?.premium.replace('%', '') ?? '0')
  return getDirectionPalette(colorMode.mode, numericToDirection(value))
})

function getMetricPalette(direction: MarketDirection) {
  return getDirectionPalette(colorMode.mode, direction)
}

function getVolumeBarClass(index: number) {
  if (selectedPeriod.value === 'intraday') {
    const previous = activePeriod.value?.linePoints[index - 1] ?? activePeriod.value?.linePoints[index] ?? 0
    const current = activePeriod.value?.linePoints[index] ?? previous
    return getDirectionPalette(colorMode.mode, numericToDirection(current - previous)).barClass
  }

  return getDirectionPalette(colorMode.mode, activePeriod.value?.candles[index]?.direction ?? 'neutral').barClass
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: PASS，颜色联动测试通过。

- [ ] **Step 5: 提交**

```bash
git add src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts
git commit -m "feat: sync analysis chart colors with global mode"
```

---

### Task 6: 更新文档并做最终验证

**Files:**
- Modify: `docs/development/human/2026-04-03-daily-log.md`
- Modify: `docs/development/ai/current_state.md`

- [ ] **Step 1: 更新当日日志**

在 `docs/development/human/2026-04-03-daily-log.md` 追加：

```md
## 图表区周期化改造

- 第三页图表区已支持单下拉框周期切换，范围包括分时、日K、5分、60分、120分、周K、月K、季K、年K。
- 分时图与 K 线图已区分为两种不同 Mock 形态，并补齐价格轴与时间轴。
- 图旁解读、指标卡、多空颜色现已随当前周期和全局红绿配色联动。
```

- [ ] **Step 2: 更新 AI 状态**

在 `docs/development/ai/current_state.md` 追加或替换为：

```md
- 第三页图表区已进入“周期化高保真 Mock”阶段，支持分时与多种 K 线周期切换。
- 第三页图表、图旁解读、技术指标和全局红绿配色已经联动。
```

- [ ] **Step 3: 运行最终测试**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts src/views/__tests__/FundList.spec.ts src/views/__tests__/Dashboard.spec.ts src/utils/__tests__/analysisMock.spec.ts`

Expected: PASS，第三页与现有相关页面测试全部通过。

Run: `npm run build`

Expected: PASS，前端构建通过。

- [ ] **Step 4: 提交**

```bash
git add docs/development/human/2026-04-03-daily-log.md docs/development/ai/current_state.md
git commit -m "docs: record analysis chart period upgrade"
```

---

## 自检

- 规格覆盖检查：已覆盖周期下拉、分时/日K双形态、价格轴、时间轴、图旁解读联动、指标卡联动和全局红绿配色联动。
- 占位词检查：无 TBD / TODO / later 等占位语句；每个任务都包含明确文件、测试和命令。
- 一致性检查：周期 key、测试选择器、图表节点和配色函数命名在各任务中保持一致。
