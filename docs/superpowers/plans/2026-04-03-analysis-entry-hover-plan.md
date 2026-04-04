# Analysis Entry Hover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让第三页在无参时承接第一页同源基金卡片作为入口页、在带参时直接进入纯详情页，并为 K 线与分时图补齐跟随鼠标的 hover 浮层。

**Architecture:** 把第一页基金卡片数据抽成首页与第三页共用的共享数据加载入口，无参时第三页复用这批数据生成卡片入口页，带参时切换为纯详情页。`Analysis.vue` 保持现有主体结构不变，只在入口态显示自动换行卡片区，并在图表区增加轻量 hover 状态、命中索引和浮层渲染逻辑。

**Tech Stack:** Vue 3 `script setup`、Pinia、Vue Test Utils、Vitest、Tailwind 实用类

---

## 文件边界

- Create: `src/utils/dashboardSignals.ts`
  责任：抽出第一页和第三页共用的基金卡片 Mock 数据与基础类型。
- Modify: `src/views/Dashboard.vue`
  责任：改为消费共享卡片数据，避免第三页维护独立入口数据。
- Modify: `src/views/Analysis.vue`
  责任：新增顶部卡片入口、直接进入第三页时的空态规则、K 线/分时 hover 浮层交互。
- Modify: `src/views/__tests__/Analysis.spec.ts`
  责任：补入口卡片、空态、点击切换、K 线 hover、分时 hover 的回归测试。
- Optional Create: `src/utils/chartHover.ts`
  责任：如果 `Analysis.vue` 过于膨胀，可抽取 hover 命中和浮层定位的轻量纯函数。
- Modify: `docs/development/human/2026-04-03-daily-log.md`
  责任：追加本轮功能完成记录。
- Modify: `docs/development/ai/current_state.md`
  责任：更新第三页状态摘要。

## 任务拆分

### Task 1: 抽取第一页共享基金卡片数据

**Files:**
- Create: `src/utils/dashboardSignals.ts`
- Modify: `src/views/Dashboard.vue`
- Test: `src/views/__tests__/Dashboard.spec.ts`

- [ ] **Step 1: 写共享数据重构前的保护测试**

在 `src/views/__tests__/Dashboard.spec.ts` 里增加一个最小断言，先要求首页仍能渲染已知基金卡片，例如：

```ts
it('首页仍使用共享基金卡片数据渲染已知代码', () => {
  const wrapper = mount(Dashboard)

  expect(wrapper.text()).toContain('513130')
  expect(wrapper.text()).toContain('恒生科技ETF')
})
```

- [ ] **Step 2: 运行测试确认当前首页行为被保护住**

Run: `npm run test -- --run src/views/__tests__/Dashboard.spec.ts`

Expected: PASS，新增断言成为后续抽取共享数据时的保护网

- [ ] **Step 3: 创建共享数据文件**

在 `src/utils/dashboardSignals.ts` 中放入从 `Dashboard.vue` 抽出的类型和 mock 数据，例如：

```ts
export interface DashboardSignal {
  code: string
  name: string
  t_plus: string
  current_price: number
  change_pct: number
  buy_price: number
  sell_price: number
  stop_loss: number
  latest_nav: number
  nav_date: string
  premium_rate: number
  expected_profit: number
  expected_profit_pct: number
  max_loss: number
  max_loss_pct: number
}

export const DASHBOARD_SIGNAL_MOCKS: DashboardSignal[] = [
  { name: '恒生科技ETF', code: '513130', change_pct: 1.85, latest_nav: 0.456, nav_date: '2026-03-30', premium_rate: 0.12, t_plus: 'T+0', current_price: 0.456, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
  { name: '标普500ETF', code: '513500', change_pct: 0.88, latest_nav: 1.234, nav_date: '2026-03-30', premium_rate: 1.45, t_plus: 'T+0', current_price: 1.234, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
  { name: '创业板ETF', code: '159915', change_pct: -1.45, latest_nav: 2.110, nav_date: '2026-03-30', premium_rate: -0.22, t_plus: 'T+1', current_price: 2.110, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
  { name: '纳指100ETF', code: '159941', change_pct: 2.11, latest_nav: 0.889, nav_date: '2026-03-30', premium_rate: 2.10, t_plus: 'T+0', current_price: 0.889, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
  { name: '红利低波ETF', code: '512890', change_pct: 0.23, latest_nav: 1.005, nav_date: '2026-03-30', premium_rate: 0.01, t_plus: 'T+1', current_price: 1.005, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
  { name: '芯片ETF', code: '159995', change_pct: -2.56, latest_nav: 0.998, nav_date: '2026-03-30', premium_rate: -0.45, t_plus: 'T+1', current_price: 0.998, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
  { name: '券商ETF', code: '512000', change_pct: 4.12, latest_nav: 0.852, nav_date: '2026-03-30', premium_rate: 0.88, t_plus: 'T+1', current_price: 0.852, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
  { name: '医疗ETF', code: '512170', change_pct: -0.75, latest_nav: 0.334, nav_date: '2026-03-30', premium_rate: 0.05, t_plus: 'T+1', current_price: 0.334, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
  { name: '中概互联网', code: '513050', change_pct: 3.44, latest_nav: 0.912, nav_date: '2026-03-30', premium_rate: 0.67, t_plus: 'T+0', current_price: 0.912, buy_price: 0.842, sell_price: 0.910, stop_loss: 0.810, expected_profit: 89.60, expected_profit_pct: 8.2, max_loss: 225.80, max_loss_pct: 3.5 },
  { name: '游戏ETF', code: '159869', change_pct: -3.11, latest_nav: 1.022, nav_date: '2026-03-30', premium_rate: -1.05, t_plus: 'T+1', current_price: 1.022, buy_price: 0, sell_price: 0, stop_loss: 0, expected_profit: 0, expected_profit_pct: 0, max_loss: 0, max_loss_pct: 0 },
]
```

- [ ] **Step 4: 修改首页消费共享数据**

在 `src/views/Dashboard.vue` 中删除本地 `interface DashboardSignal` 与 `mockSignals`，改为：

```ts
import { DASHBOARD_SIGNAL_MOCKS, type DashboardSignal } from '../utils/dashboardSignals'

// ...

if (isDev) {
  signals.value = DASHBOARD_SIGNAL_MOCKS
}

// fallback 时也使用 DASHBOARD_SIGNAL_MOCKS
```

- [ ] **Step 5: 运行首页测试确认通过**

Run: `npm run test -- --run src/views/__tests__/Dashboard.spec.ts`

Expected: PASS

- [ ] **Step 6: 提交本任务**

```bash
git add src/utils/dashboardSignals.ts src/views/Dashboard.vue src/views/__tests__/Dashboard.spec.ts
git commit -m "refactor: share dashboard signal mocks"
```

### Task 2: 用顶部卡片替换第三页固定示例入口

**Files:**
- Modify: `src/views/Analysis.vue`
- Modify: `src/views/__tests__/Analysis.spec.ts`
- Use: `src/utils/dashboardSignals.ts`

- [ ] **Step 1: 先写第三页入口行为失败测试**

在 `src/views/__tests__/Analysis.spec.ts` 新增 3 组测试：

```ts
it('直接点击第三页时顶部显示承接自第一页的基金卡片，而不是固定示例按钮', () => {
  routeState.query = {}
  const wrapper = mount(Analysis)

  expect(wrapper.findAll('[data-test^="analysis-entry-card-"]')).toHaveLength(10)
  expect(wrapper.text()).toContain('恒生科技ETF')
  expect(wrapper.text()).toContain('标普500ETF')
  expect(wrapper.text()).not.toContain('第三页支持从列表页带代码进入，也支持在页内搜索后查看示例分析。')
})

it('直接点击第三页且未点卡片前，下方主体保持空态', () => {
  routeState.query = {}
  const wrapper = mount(Analysis)

  expect(wrapper.get('[data-test="analysis-empty-state"]').text()).toContain('请选择基金')
})

it('点击顶部基金卡片后切换到对应分析内容并重置周期为 day', async () => {
  routeState.query = {}
  const wrapper = mount(Analysis)

  await wrapper.get('[data-test="analysis-entry-card-159915"]').trigger('click')

  expect(wrapper.text()).toContain('创业板ETF')
  expect((wrapper.get('[data-test="analysis-period-select"]').element as HTMLSelectElement).value).toBe('day')
})

it('路由带入 code 时直接进入详情态，不再展示顶部卡片页', () => {
  routeState.query = { code: '510300' }
  const wrapper = mount(Analysis)

  expect(wrapper.find('[data-test="analysis-entry-strip"]').exists()).toBe(false)
  expect(wrapper.get('[data-test="analysis-section-summary"]').text()).toContain('沪深300ETF')
})
```

- [ ] **Step 2: 运行第三页测试确认红灯**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: FAIL，失败点应集中在第三页还没有顶部卡片入口和新的空态规则

- [ ] **Step 3: 在第三页接入共享卡片数据并生成入口区**

在 `src/views/Analysis.vue` 中：

1. 引入共享数据：

```ts
import { DASHBOARD_SIGNAL_MOCKS } from '../utils/dashboardSignals'
```

2. 新增一个顶部卡片集合计算属性，规则如下：
- 仅在无 `code` 的入口页展示
- 默认取首页同源卡片数据的前 10 条
- 带 `code` 时不再展示顶部卡片页

3. 在顶部横栏后新增自动换行卡片区，例如：

```vue
<section data-test="analysis-entry-strip" class="grid gap-6 md:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-5">
  <button
    v-for="item in entryCards"
    :key="item.code"
    :data-test="`analysis-entry-card-${item.code}`"
    class="fund-card bg-white rounded-[32px] p-6 border border-gray-100 shadow-sm text-left relative h-full"
    @click="selectCode(item.code)"
  >
```

说明：卡片样式尽量复用首页现有层级和密度，不新增多余说明块。

- [ ] **Step 4: 调整第三页空态与默认选中规则**

在 `Analysis.vue` 中把空态规则改成：

```ts
const activeCode = computed(() => routeCode.value)
const showEntryStrip = computed(() => !routeCode.value)
const showEmptyState = computed(() => !activeAnalysis.value)
```

要求：
- 路由未带 `code` 且用户未点卡片时，主体为空态
- 但顶部卡片入口仍然显示
- 路由带 `code` 或用户点卡片后，主体进入分析态，顶部卡片区隐藏

- [ ] **Step 5: 运行第三页测试确认入口改造转绿**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: 与入口区相关的新测试通过；旧测试若依赖固定示例按钮，则改成“顶部卡片 + 主体空态”的新规格断言

- [ ] **Step 6: 提交本任务**

```bash
git add src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts src/utils/dashboardSignals.ts src/views/Dashboard.vue
git commit -m "feat: add analysis entry cards"
```

### Task 3: 为 K 线补跟随鼠标的 hover 浮层

**Files:**
- Modify: `src/views/Analysis.vue`
- Modify: `src/views/__tests__/Analysis.spec.ts`
- Optional Create: `src/utils/chartHover.ts`

- [ ] **Step 1: 先写 K 线 hover 失败测试**

在 `src/views/__tests__/Analysis.spec.ts` 中新增：

```ts
it('K 线 hover 时显示日期和 OHLC 浮层，移出后隐藏', async () => {
  const wrapper = mount(Analysis)

  await wrapper.get('[data-test="analysis-chart-candle-hitbox-0"]').trigger('mouseenter', { clientX: 120, clientY: 96 })

  const tooltip = wrapper.get('[data-test="analysis-chart-tooltip"]')

  expect(tooltip.text()).toContain('日期：04-08')
  expect(tooltip.text()).toContain('开盘：4.010')
  expect(tooltip.text()).toContain('收盘：4.080')
  expect(tooltip.text()).toContain('最高：4.100')
  expect(tooltip.text()).toContain('最低：3.990')
  expect(tooltip.attributes('style')).toContain('left:')
  expect(tooltip.attributes('style')).toContain('top:')

  await wrapper.get('[data-test="analysis-chart-hit-area"]').trigger('mouseleave')

  expect(wrapper.find('[data-test="analysis-chart-tooltip"]').exists()).toBe(false)
})
```

- [ ] **Step 2: 运行第三页测试确认红灯**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: FAIL，失败原因是当前还没有 tooltip、命中交互区和鼠标跟随定位状态

- [ ] **Step 3: 在第三页实现 K 线 hover 状态**

在 `Analysis.vue` 中新增最小状态：

```ts
const hoveredCandleIndex = ref<number | null>(null)
const tooltipPosition = ref({ x: 12, y: 12 })
```

并基于当前周期原始 `candles` 与 `timeAxis` 组装 tooltip 数据：

```ts
const hoveredCandleDetail = computed(() => {
  if (hoveredCandleIndex.value === null || isIntradayChart.value || !activePeriod.value) {
    return null
  }

  const baseCandles = activePeriod.value.candles
  const actualIndex = hoveredCandleIndex.value % baseCandles.length
  const [open, close, low, high] = baseCandles[actualIndex]

  return {
    label: activePeriod.value.timeAxis[actualIndex] ?? '--',
    open,
    close,
    low,
    high,
  }
})
```

补一个统一的浮层定位函数，用鼠标位置驱动 tooltip 跟随，并做基础边界约束：

```ts
function updateTooltipPosition(event: MouseEvent) {
  const host = event.currentTarget instanceof HTMLElement ? event.currentTarget : null

  if (!host) {
    return
  }

  const rect = host.getBoundingClientRect()
  const rawX = event.clientX - rect.left + 12
  const rawY = event.clientY - rect.top - 12

  tooltipPosition.value = {
    x: Math.max(12, Math.min(rawX, Math.max(rect.width - 180, 12))),
    y: Math.max(12, Math.min(rawY, Math.max(rect.height - 120, 12))),
  }
}
```

然后给每根 K 线增加透明 hitbox：

```vue
<button
  :data-test="`analysis-chart-candle-hitbox-${index}`"
  class="absolute inset-0"
  @mouseenter="(event) => { hoveredCandleIndex = index; updateTooltipPosition(event) }"
  @mousemove="updateTooltipPosition"
  @focus="hoveredCandleIndex = index"
/>
```

并在图表容器里渲染 tooltip：

```vue
<div
  v-if="hoveredCandleDetail"
  data-test="analysis-chart-tooltip"
  class="absolute z-20 rounded-xl border border-slate-200 bg-white/95 px-3 py-2 text-xs text-slate-700 shadow-lg"
  :style="{ left: `${tooltipPosition.x}px`, top: `${tooltipPosition.y}px` }"
>
  <div>日期：{{ hoveredCandleDetail.label }}</div>
  <div>开盘：{{ hoveredCandleDetail.open.toFixed(3) }}</div>
  <div>收盘：{{ hoveredCandleDetail.close.toFixed(3) }}</div>
  <div>最高：{{ hoveredCandleDetail.high.toFixed(3) }}</div>
  <div>最低：{{ hoveredCandleDetail.low.toFixed(3) }}</div>
</div>
```

- [ ] **Step 4: 给图表容器补统一移出隐藏逻辑**

在图表主交互层外包一层容器：

```vue
<div data-test="analysis-chart-hit-area" @mouseleave="clearHover()">
```

并实现：

```ts
function clearHover() {
  hoveredCandleIndex.value = null
  hoveredIntradayIndex.value = null
}
```

- [ ] **Step 5: 运行第三页测试确认 K 线 hover 通过**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: PASS

- [ ] **Step 6: 提交本任务**

```bash
git add src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts
git commit -m "feat: add analysis candle hover tooltip"
```

### Task 4: 为分时图补跟随鼠标的 hover 浮层

**Files:**
- Modify: `src/views/Analysis.vue`
- Modify: `src/views/__tests__/Analysis.spec.ts`

- [ ] **Step 1: 先写分时 hover 失败测试**

在 `src/views/__tests__/Analysis.spec.ts` 中新增：

```ts
it('分时 hover 时显示时间、价格和均价浮层', async () => {
  const wrapper = mount(Analysis)

  await wrapper.get('[data-test="analysis-period-select"]').setValue('intraday')
  await wrapper.get('[data-test="analysis-intraday-hitbox-0"]').trigger('mouseenter', { clientX: 88, clientY: 72 })

  const tooltip = wrapper.get('[data-test="analysis-chart-tooltip"]')

  expect(tooltip.text()).toContain('时间：09:30')
  expect(tooltip.text()).toContain('价格：4.070')
  expect(tooltip.text()).toContain('均价：4.060')
})
```

- [ ] **Step 2: 运行第三页测试确认红灯**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: FAIL，失败原因是分时没有 hover 命中层和浮层内容

- [ ] **Step 3: 在第三页实现分时 hover 状态**

在 `Analysis.vue` 中新增：

```ts
const hoveredIntradayIndex = ref<number | null>(null)
```

补一个分时 tooltip 计算属性：

```ts
const hoveredIntradayDetail = computed(() => {
  if (hoveredIntradayIndex.value === null || !isIntradayChart.value || !activePeriod.value) {
    return null
  }

  const index = hoveredIntradayIndex.value
  return {
    label: activePeriod.value.timeAxis[index] ?? '--',
    price: activePeriod.value.linePoints[index] ?? 0,
    avg: activePeriod.value.avgLinePoints[index] ?? 0,
  }
})
```

在分时图上按点位数量铺透明 hitbox，例如：

```vue
<div class="absolute inset-0 grid" :style="{ gridTemplateColumns: `repeat(${activePeriod?.linePoints.length ?? 0}, minmax(0, 1fr))` }">
  <button
    v-for="(_, index) in activePeriod?.linePoints ?? []"
    :key="`intraday-hitbox-${index}`"
    :data-test="`analysis-intraday-hitbox-${index}`"
    class="h-full w-full"
    @mouseenter="(event) => { hoveredIntradayIndex = index; updateTooltipPosition(event) }"
    @mousemove="updateTooltipPosition"
  />
</div>
```

并复用 `analysis-chart-tooltip`，在分时场景下切换为：

```vue
<template v-if="hoveredIntradayDetail">
  <div>时间：{{ hoveredIntradayDetail.label }}</div>
  <div>价格：{{ hoveredIntradayDetail.price.toFixed(3) }}</div>
  <div>均价：{{ hoveredIntradayDetail.avg.toFixed(3) }}</div>
</template>
```

- [ ] **Step 4: 运行第三页测试确认分时 hover 通过**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: PASS

- [ ] **Step 5: 提交本任务**

```bash
git add src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts
git commit -m "feat: add analysis intraday hover tooltip"
```

### Task 5: 全量回归、文档同步与收尾

**Files:**
- Modify: `docs/development/human/2026-04-03-daily-log.md`
- Modify: `docs/development/ai/current_state.md`

- [ ] **Step 1: 追加开发日志**

在 `docs/development/human/2026-04-03-daily-log.md` 中补充：
- 第三页顶部入口改为承接第一页共享卡片数据
- 卡片自动换行且密度贴近第一页
- K 线/分时 hover 浮层完成

- [ ] **Step 2: 更新 AI 状态摘要**

在 `docs/development/ai/current_state.md` 中补充：
- 第三页不再维护独立示例基金入口
- 第三页顶部卡片与第一页共享数据源
- K 线与分时 hover 浮层已完成或进入最新状态

- [ ] **Step 3: 运行相关前端回归测试**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts src/views/__tests__/Dashboard.spec.ts src/views/__tests__/FundList.spec.ts src/utils/__tests__/analysisMock.spec.ts`

Expected: PASS

- [ ] **Step 4: 运行前端构建验证**

Run: `npm run build`

Expected: PASS

- [ ] **Step 5: 提交收尾改动**

```bash
git add docs/development/human/2026-04-03-daily-log.md docs/development/ai/current_state.md src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts src/views/Dashboard.vue src/utils/dashboardSignals.ts
git commit -m "feat: polish analysis entry and hover"
```
