# FundList 宽表格与全局配色 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `FundList.vue` 重构为已确认的宽表格页面，并让 `FundList.vue` 与 `Dashboard.vue` 共享可持久化的全局 `红多 / 绿多` 配色状态。

**Architecture:** 先补齐前端最小 Vitest 基线，再把方向性色彩映射和基金列表衍生计算抽成可测试的纯 TypeScript 单元；`FundList.vue` 与 `Dashboard.vue` 只负责取数、绑定 Pinia store 和渲染。全局配色状态由 Pinia store 持有并落到 `localStorage`，页面统一通过语义映射函数拿颜色类，彻底移除页面内私有的 `invertColors` 判断。

**Tech Stack:** Vue 3 / TypeScript / Pinia / Vue Router / Tailwind CSS v4 / Vitest / @vue/test-utils / jsdom

**Design Doc:** `docs/superpowers/specs/2026-03-31-fund-list-page-design.md`

---

## 前置说明

- 本轮只涉及前端 UI 与前端状态管理，不改 Rust / Python 接口与数据结构，因此不需要执行跨栈冷备份协议。
- 当前仓库已经存在未提交文档改动；执行每个 commit 时只 `git add` 当前任务列出的文件，避免把无关文件带入提交。
- 自动化验证范围以本轮改动相关的前端测试和 `npm run build` 为主；Python 与 Rust 本轮不需要重跑。

## 文件边界

- Modify: `package.json` - 新增前端测试脚本与测试依赖声明。
- Modify: `package-lock.json` - 锁定新增前端测试依赖。
- Modify: `vite.config.ts` - 配置 Vitest 的 `jsdom` 测试环境。
- Modify: `src/main.ts` - 在应用挂载前初始化 Pinia 并执行全局配色状态 `hydrate()`。
- Create: `src/test/setup.ts` - 统一清理 `localStorage` 与 DOM。
- Create: `src/test/smoke.spec.ts` - 保留一个前端测试基线烟雾测试。
- Create: `src/stores/colorMode.ts` - 全局 `红多 / 绿多` 配色 store 与持久化逻辑。
- Create: `src/stores/__tests__/colorMode.spec.ts` - store 单元测试。
- Create: `src/utils/marketColors.ts` - 方向性色彩语义映射与分值方向判定。
- Create: `src/utils/__tests__/marketColors.spec.ts` - 映射工具单元测试。
- Create: `src/utils/fundList.ts` - 第二页列表衍生数据、搜索过滤、标签映射。
- Create: `src/utils/__tests__/fundList.spec.ts` - 列表衍生逻辑单元测试。
- Modify: `src/views/FundList.vue` - 重写为确认后的宽表格页面，接入全局配色与搜索过滤。
- Create: `src/views/__tests__/FundList.spec.ts` - 第二页关键交互组件测试。
- Modify: `src/views/Dashboard.vue` - 将方向色文本与风险条改为走共享映射。
- Create: `src/views/__tests__/Dashboard.spec.ts` - 首页共享配色响应测试。
- Create: `docs/development/human/2026-04-01-daily-log.md` - 记录当日实现结果。
- Modify: `docs/development/ai/current_state.md` - 更新 AI 上下文状态与下一步。

---

### Task 1: 建立前端测试基线

**Files:**
- Create: `src/test/smoke.spec.ts`
- Create: `src/test/setup.ts`
- Modify: `package.json`
- Modify: `package-lock.json`
- Modify: `vite.config.ts`

- [ ] **Step 1: 先写一个失败的烟雾测试**

创建 `src/test/smoke.spec.ts`：

```ts
import { describe, expect, it } from 'vitest'

describe('frontend test harness', () => {
  it('provides jsdom browser globals', () => {
    localStorage.setItem('ping', 'pong')
    expect(localStorage.getItem('ping')).toBe('pong')
  })
})
```

- [ ] **Step 2: 运行测试，确认当前基线确实失败**

Run: `npm run test -- --run src/test/smoke.spec.ts`

Expected: FAIL，报错类似 `Missing script: "test"`，说明前端测试基线尚未建立。

- [ ] **Step 3: 补齐 Vitest 运行环境的最小实现**

先安装依赖：

```bash
npm install -D vitest @vue/test-utils jsdom
```

更新 `package.json`：

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "test": "vitest",
    "preview": "vite preview",
    "tauri": "tauri"
  }
}
```

更新 `vite.config.ts`：

```ts
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  clearScreen: false,
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
  server: {
    port: 1420,
    strictPort: true,
    watch: {
      ignored: ['**/src-tauri/**'],
    },
  },
})
```

创建 `src/test/setup.ts`：

```ts
import { afterEach } from 'vitest'

afterEach(() => {
  localStorage.clear()
  document.body.innerHTML = ''
})
```

- [ ] **Step 4: 重新运行烟雾测试，确认基线可用**

Run: `npm run test -- --run src/test/smoke.spec.ts`

Expected: PASS，输出 `1 passed`。

- [ ] **Step 5: 提交测试基线**

```bash
git add package.json package-lock.json vite.config.ts src/test/setup.ts src/test/smoke.spec.ts
git commit -m "test: add frontend vitest baseline"
```

---

### Task 2: 实现全局配色 store 与方向映射

**Files:**
- Create: `src/stores/colorMode.ts`
- Create: `src/stores/__tests__/colorMode.spec.ts`
- Create: `src/utils/marketColors.ts`
- Create: `src/utils/__tests__/marketColors.spec.ts`
- Modify: `src/main.ts`

- [ ] **Step 1: 先写 store 与映射工具的失败测试**

创建 `src/stores/__tests__/colorMode.spec.ts`：

```ts
import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { COLOR_MODE_STORAGE_KEY, useColorModeStore } from '../colorMode'

describe('useColorModeStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('hydrates saved mode from localStorage', () => {
    localStorage.setItem(COLOR_MODE_STORAGE_KEY, 'intl')
    const store = useColorModeStore()

    store.hydrate()

    expect(store.mode).toBe('intl')
    expect(store.hydrated).toBe(true)
  })

  it('persists mode changes', () => {
    const store = useColorModeStore()

    store.setMode('intl')

    expect(store.mode).toBe('intl')
    expect(localStorage.getItem(COLOR_MODE_STORAGE_KEY)).toBe('intl')
  })

  it('ignores invalid stored values', () => {
    localStorage.setItem(COLOR_MODE_STORAGE_KEY, 'wrong')
    const store = useColorModeStore()

    store.hydrate()

    expect(store.mode).toBe('cn')
  })
})
```

创建 `src/utils/__tests__/marketColors.spec.ts`：

```ts
import { describe, expect, it } from 'vitest'
import { getDirectionPalette, numericToDirection, scoreToDirection } from '../marketColors'

describe('marketColors', () => {
  it('maps bullish colors for cn mode to red', () => {
    expect(getDirectionPalette('cn', 'bullish').valueClass).toBe('text-red-500')
  })

  it('maps bullish colors for intl mode to green', () => {
    expect(getDirectionPalette('intl', 'bullish').valueClass).toBe('text-green-600')
  })

  it('maps numeric values to market direction', () => {
    expect(numericToDirection(1.2)).toBe('bullish')
    expect(numericToDirection(0)).toBe('neutral')
    expect(numericToDirection(-1.2)).toBe('bearish')
  })

  it('maps score buckets to market direction', () => {
    expect(scoreToDirection(9)).toBe('bullish')
    expect(scoreToDirection(5)).toBe('neutral')
    expect(scoreToDirection(2)).toBe('bearish')
  })
})
```

- [ ] **Step 2: 运行测试，确认因为缺少实现而失败**

Run: `npm run test -- --run src/stores/__tests__/colorMode.spec.ts src/utils/__tests__/marketColors.spec.ts`

Expected: FAIL，报错类似 `Failed to resolve import '../colorMode'` 和 `Failed to resolve import '../marketColors'`。

- [ ] **Step 3: 写最小实现让 store 与映射测试通过**

创建 `src/stores/colorMode.ts`：

```ts
import { ref } from 'vue'
import { defineStore } from 'pinia'

export type ColorMode = 'cn' | 'intl'
export const COLOR_MODE_STORAGE_KEY = 'market-color-mode'

export const useColorModeStore = defineStore('colorMode', () => {
  const mode = ref<ColorMode>('cn')
  const hydrated = ref(false)

  function hydrate() {
    if (hydrated.value) {
      return
    }

    if (typeof window === 'undefined') {
      hydrated.value = true
      return
    }

    const saved = window.localStorage.getItem(COLOR_MODE_STORAGE_KEY)
    if (saved === 'cn' || saved === 'intl') {
      mode.value = saved
    }

    hydrated.value = true
  }

  function setMode(value: ColorMode) {
    mode.value = value
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(COLOR_MODE_STORAGE_KEY, value)
    }
  }

  function toggleMode() {
    setMode(mode.value === 'cn' ? 'intl' : 'cn')
  }

  return { mode, hydrated, hydrate, setMode, toggleMode }
})
```

创建 `src/utils/marketColors.ts`：

```ts
import type { ColorMode } from '../stores/colorMode'

export type MarketDirection = 'bullish' | 'bearish' | 'neutral'

interface DirectionPalette {
  valueClass: string
  softTextClass: string
  dotClass: string
  barClass: string
}

const palettes: Record<ColorMode, Record<MarketDirection, DirectionPalette>> = {
  cn: {
    bullish: {
      valueClass: 'text-red-500',
      softTextClass: 'text-red-400',
      dotClass: 'bg-red-500',
      barClass: 'bg-red-400',
    },
    bearish: {
      valueClass: 'text-green-600',
      softTextClass: 'text-green-500',
      dotClass: 'bg-green-500',
      barClass: 'bg-green-400',
    },
    neutral: {
      valueClass: 'text-amber-500',
      softTextClass: 'text-gray-400',
      dotClass: 'bg-amber-400',
      barClass: 'bg-gray-300',
    },
  },
  intl: {
    bullish: {
      valueClass: 'text-green-600',
      softTextClass: 'text-green-500',
      dotClass: 'bg-green-500',
      barClass: 'bg-green-400',
    },
    bearish: {
      valueClass: 'text-red-500',
      softTextClass: 'text-red-400',
      dotClass: 'bg-red-500',
      barClass: 'bg-red-400',
    },
    neutral: {
      valueClass: 'text-amber-500',
      softTextClass: 'text-gray-400',
      dotClass: 'bg-amber-400',
      barClass: 'bg-gray-300',
    },
  },
}

export function getDirectionPalette(mode: ColorMode, direction: MarketDirection): DirectionPalette {
  return palettes[mode][direction]
}

export function numericToDirection(value: number): MarketDirection {
  if (value > 0) {
    return 'bullish'
  }
  if (value < 0) {
    return 'bearish'
  }
  return 'neutral'
}

export function scoreToDirection(score: number): MarketDirection {
  if (score >= 7) {
    return 'bullish'
  }
  if (score <= 3) {
    return 'bearish'
  }
  return 'neutral'
}
```

更新 `src/main.ts`：

```ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import { useColorModeStore } from './stores/colorMode'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
useColorModeStore(pinia).hydrate()
app.use(router)
app.mount('#app')
```

- [ ] **Step 4: 运行测试，确认 store 与映射工具全部通过**

Run: `npm run test -- --run src/stores/__tests__/colorMode.spec.ts src/utils/__tests__/marketColors.spec.ts`

Expected: PASS，输出 `7 passed`。

- [ ] **Step 5: 提交全局配色基础能力**

```bash
git add src/main.ts src/stores/colorMode.ts src/stores/__tests__/colorMode.spec.ts src/utils/marketColors.ts src/utils/__tests__/marketColors.spec.ts
git commit -m "feat: add global market color mode"
```

---

### Task 3: 抽出 FundList 衍生数据与过滤逻辑

**Files:**
- Create: `src/utils/fundList.ts`
- Create: `src/utils/__tests__/fundList.spec.ts`

- [ ] **Step 1: 先写衍生数据工具的失败测试**

创建 `src/utils/__tests__/fundList.spec.ts`：

```ts
import { describe, expect, it } from 'vitest'
import { buildFundRows, calculateChangePct, filterFundRows, getScoreLabel, type FundListItem } from '../fundList'

const sampleFunds: FundListItem[] = [
  {
    code: '510300',
    name: '沪深300ETF',
    prevClose: 4.1,
    open: 4.105,
    close: 4.123,
    high: 4.15,
    low: 4.08,
    volatility: 0.017,
    macd: { signal: 'bullish', value: '金叉' },
    rsi: { signal: 'neutral', value: '52' },
    boll: { signal: 'bullish', value: '中轨' },
    ma5: { signal: 'bullish', value: '上穿' },
    ma20: { signal: 'neutral', value: '粘合' },
    score: 9,
  },
  {
    code: '588000',
    name: '科创50ETF',
    prevClose: 1.05,
    open: 1.045,
    close: 1.03,
    high: 1.06,
    low: 1.02,
    volatility: 0.039,
    macd: { signal: 'bearish', value: '绿柱' },
    rsi: { signal: 'bearish', value: '25' },
    boll: { signal: 'bearish', value: '上轨' },
    ma5: { signal: 'bearish', value: '空头' },
    ma20: { signal: 'bearish', value: '向下' },
    score: 1,
  },
]

describe('fundList helpers', () => {
  it('calculates change percent from close and prevClose', () => {
    expect(calculateChangePct(4.123, 4.1)).toBe(0.56)
  })

  it('maps score buckets to readable labels', () => {
    expect(getScoreLabel(9)).toBe('强烈看多')
    expect(getScoreLabel(5)).toBe('中性')
    expect(getScoreLabel(1)).toBe('强烈看空')
  })

  it('builds derived rows with change percent and score label', () => {
    const rows = buildFundRows(sampleFunds)

    expect(rows[0].changePct).toBe(0.56)
    expect(rows[0].scoreLabel).toBe('强烈看多')
    expect(rows[1].scoreDirection).toBe('bearish')
  })

  it('filters by code or name using trimmed keyword', () => {
    const rows = buildFundRows(sampleFunds)

    expect(filterFundRows(rows, '510300')).toHaveLength(1)
    expect(filterFundRows(rows, ' 科创 ')).toHaveLength(1)
    expect(filterFundRows(rows, '')).toHaveLength(2)
  })
})
```

- [ ] **Step 2: 运行测试，确认因为缺少工具文件而失败**

Run: `npm run test -- --run src/utils/__tests__/fundList.spec.ts`

Expected: FAIL，报错类似 `Failed to resolve import '../fundList'`。

- [ ] **Step 3: 写最小实现让衍生数据逻辑通过**

创建 `src/utils/fundList.ts`：

```ts
import { scoreToDirection, type MarketDirection } from './marketColors'

export interface TechnicalValue {
  signal: MarketDirection
  value: string
}

export interface FundListItem {
  code: string
  name: string
  prevClose: number
  open: number
  close: number
  high: number
  low: number
  volatility: number
  macd: TechnicalValue
  rsi: TechnicalValue
  boll: TechnicalValue
  ma5: TechnicalValue
  ma20: TechnicalValue
  score: number
}

export interface FundListRow extends FundListItem {
  changePct: number
  scoreLabel: string
  scoreDirection: MarketDirection
}

export function calculateChangePct(close: number, prevClose: number): number {
  if (prevClose === 0) {
    return 0
  }

  return Number((((close - prevClose) / prevClose) * 100).toFixed(2))
}

export function getScoreLabel(score: number): string {
  if (score >= 9) {
    return '强烈看多'
  }
  if (score >= 7) {
    return '看多'
  }
  if (score >= 4) {
    return '中性'
  }
  if (score >= 2) {
    return '看空'
  }
  return '强烈看空'
}

export function buildFundRows(funds: FundListItem[]): FundListRow[] {
  return funds.map((fund) => ({
    ...fund,
    changePct: calculateChangePct(fund.close, fund.prevClose),
    scoreLabel: getScoreLabel(fund.score),
    scoreDirection: scoreToDirection(fund.score),
  }))
}

export function filterFundRows(rows: FundListRow[], keyword: string): FundListRow[] {
  const normalizedKeyword = keyword.trim().toLowerCase()
  if (!normalizedKeyword) {
    return rows
  }

  return rows.filter((row) => {
    return row.code.includes(normalizedKeyword) || row.name.toLowerCase().includes(normalizedKeyword)
  })
}
```

- [ ] **Step 4: 运行测试，确认 FundList 衍生逻辑通过**

Run: `npm run test -- --run src/utils/__tests__/fundList.spec.ts`

Expected: PASS，输出 `4 passed`。

- [ ] **Step 5: 提交列表数据工具**

```bash
git add src/utils/fundList.ts src/utils/__tests__/fundList.spec.ts
git commit -m "feat: add fund list row helpers"
```

---

### Task 4: 按确认稿重写 FundList 宽表格页面

**Files:**
- Modify: `src/views/FundList.vue`
- Create: `src/views/__tests__/FundList.spec.ts`

- [ ] **Step 1: 先写页面交互失败测试**

创建 `src/views/__tests__/FundList.spec.ts`：

```ts
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import FundList from '../FundList.vue'
import { useColorModeStore } from '../../stores/colorMode'

const pushMock = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}))

describe('FundList.vue', () => {
  beforeEach(() => {
    localStorage.clear()
    pushMock.mockReset()
  })

  it('filters rows by code or name', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(FundList, {
      global: {
        plugins: [pinia],
      },
    })

    await flushPromises()
    await wrapper.get('[data-test="fund-search"]').setValue('创业板')

    expect(wrapper.text()).toContain('创业板ETF')
    expect(wrapper.text()).not.toContain('沪深300ETF')
  })

  it('updates the shared color mode from the header toggle', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(FundList, {
      global: {
        plugins: [pinia],
      },
    })
    const store = useColorModeStore()

    await flushPromises()
    await wrapper.get('[data-test="mode-intl"]').trigger('click')

    expect(store.mode).toBe('intl')
    expect(localStorage.getItem('market-color-mode')).toBe('intl')
  })

  it('routes detail button to analysis page', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(FundList, {
      global: {
        plugins: [pinia],
      },
    })

    await flushPromises()
    await wrapper.get('[data-test="detail-510300"]').trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      name: 'analysis',
      query: { code: '510300' },
    })
  })

  it('shows an empty state when no rows match the keyword', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(FundList, {
      global: {
        plugins: [pinia],
      },
    })

    await flushPromises()
    await wrapper.get('[data-test="fund-search"]').setValue('不存在的基金')

    expect(wrapper.get('[data-test="fund-empty"]').text()).toContain('没有匹配的基金')
  })
})
```

- [ ] **Step 2: 运行测试，确认当前旧页面无法满足新交互**

Run: `npm run test -- --run src/views/__tests__/FundList.spec.ts`

Expected: FAIL，至少会报 `Unable to get [data-test="fund-search"]` 或 `Unable to get [data-test="mode-intl"]`。

- [ ] **Step 3: 按确认稿实现新的宽表格页面**

将 `src/views/FundList.vue` 重写为下面结构。保留现有 4 条 mock 数据，但补上 `FundListItem[]` 类型，并删除本地 `invertColors` 复选框状态：

```vue
<template>
  <section class="px-4 pb-8 md:px-8 md:pb-10">
    <header class="sticky top-0 md:top-6 z-30 mt-4 md:mt-6 mb-6 rounded-[24px] border border-gray-100 bg-white/90 p-6 shadow-sm backdrop-blur-md">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-[10px] font-bold uppercase tracking-[0.28em] text-gray-400">Fund Flow</p>
          <h1 class="mt-2 text-2xl font-black tracking-tight text-gray-900">全量场内基金</h1>
          <p class="mt-1 text-sm text-gray-400">共 {{ rows.length }} 只，当前显示 {{ filteredRows.length }} 只，支持代码 / 名称即时过滤。</p>
        </div>

        <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div class="inline-flex rounded-xl bg-gray-100 p-1">
            <button
              data-test="mode-cn"
              type="button"
              class="rounded-lg px-4 py-2 text-xs font-bold transition-all"
              :class="colorMode.mode === 'cn' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
              @click="colorMode.setMode('cn')"
            >
              红多
            </button>
            <button
              data-test="mode-intl"
              type="button"
              class="rounded-lg px-4 py-2 text-xs font-bold transition-all"
              :class="colorMode.mode === 'intl' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
              @click="colorMode.setMode('intl')"
            >
              绿多
            </button>
          </div>

          <input
            data-test="fund-search"
            v-model.trim="keyword"
            type="text"
            placeholder="搜索代码 / 名称"
            class="w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-700 outline-none transition focus:border-blue-300 sm:w-72"
          />
        </div>
      </div>
    </header>

    <div class="overflow-hidden rounded-[28px] border border-gray-100 bg-white shadow-sm">
      <div class="overflow-x-auto">
        <table class="min-w-[1480px] w-full border-collapse">
          <thead class="sticky top-0 z-10 bg-white">
            <tr class="border-b border-gray-100 text-[11px] font-bold uppercase tracking-[0.18em] text-gray-400">
              <th class="px-6 py-4 text-left">代码/名称</th>
              <th class="px-4 py-4 text-right">昨收</th>
              <th class="px-4 py-4 text-right">开盘</th>
              <th class="px-4 py-4 text-right">现价</th>
              <th class="px-4 py-4 text-right">最高</th>
              <th class="px-4 py-4 text-right">最低</th>
              <th class="px-4 py-4 text-right">波动</th>
              <th class="px-4 py-4 text-right">涨跌幅</th>
              <th class="px-4 py-4 text-center">MACD</th>
              <th class="px-4 py-4 text-center">RSI</th>
              <th class="px-4 py-4 text-center">BOLL</th>
              <th class="px-4 py-4 text-center">MA5</th>
              <th class="px-4 py-4 text-center">MA20</th>
              <th class="px-4 py-4 text-center">多空</th>
              <th class="px-6 py-4 text-center">操作</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="row in filteredRows"
              :key="row.code"
              class="border-b border-gray-50 text-sm text-gray-600 transition-colors hover:bg-gray-50/80"
            >
              <td class="px-6 py-4">
                <div class="font-semibold text-gray-900">{{ row.name }}</div>
                <div class="mt-1 font-mono text-[11px] text-gray-400">{{ row.code }}</div>
              </td>

              <td class="px-4 py-4 text-right font-mono">{{ row.prevClose.toFixed(3) }}</td>
              <td class="px-4 py-4 text-right font-mono">{{ row.open.toFixed(3) }}</td>
              <td class="px-4 py-4 text-right font-mono font-semibold text-gray-900">{{ row.close.toFixed(3) }}</td>
              <td class="px-4 py-4 text-right font-mono" :class="paletteFor(numericToDirection(row.high - row.prevClose)).softTextClass">{{ row.high.toFixed(3) }}</td>
              <td class="px-4 py-4 text-right font-mono" :class="paletteFor(numericToDirection(row.low - row.prevClose)).softTextClass">{{ row.low.toFixed(3) }}</td>
              <td class="px-4 py-4 text-right font-mono text-gray-500">{{ (row.volatility * 100).toFixed(2) }}%</td>
              <td class="px-4 py-4 text-right font-mono text-base font-black" :class="paletteFor(numericToDirection(row.changePct)).valueClass">
                {{ row.changePct > 0 ? '+' : '' }}{{ row.changePct.toFixed(2) }}%
              </td>

              <td class="px-4 py-4 text-center text-xs font-semibold" :class="paletteFor(row.macd.signal).softTextClass">{{ row.macd.value }}</td>
              <td class="px-4 py-4 text-center text-xs font-semibold" :class="paletteFor(row.rsi.signal).softTextClass">{{ row.rsi.value }}</td>
              <td class="px-4 py-4 text-center text-xs font-semibold" :class="paletteFor(row.boll.signal).softTextClass">{{ row.boll.value }}</td>
              <td class="px-4 py-4 text-center text-xs font-semibold" :class="paletteFor(row.ma5.signal).softTextClass">{{ row.ma5.value }}</td>
              <td class="px-4 py-4 text-center text-xs font-semibold" :class="paletteFor(row.ma20.signal).softTextClass">{{ row.ma20.value }}</td>

              <td class="px-4 py-4 text-center">
                <div class="flex items-center justify-center gap-2">
                  <span class="h-2.5 w-2.5 rounded-full" :class="paletteFor(row.scoreDirection).dotClass"></span>
                  <span class="font-semibold" :class="paletteFor(row.scoreDirection).valueClass">{{ row.score }}</span>
                </div>
                <div class="mt-1 text-[11px] font-semibold" :class="paletteFor(row.scoreDirection).softTextClass">{{ row.scoreLabel }}</div>
              </td>

              <td class="px-6 py-4 text-center">
                <button
                  :data-test="`detail-${row.code}`"
                  type="button"
                  class="rounded-full bg-blue-600 px-4 py-2 text-xs font-bold text-white transition hover:bg-blue-500"
                  @click="goToAnalysis(row.code)"
                >
                  详情分析
                </button>
              </td>
            </tr>

            <tr v-if="filteredRows.length === 0">
              <td data-test="fund-empty" colspan="15" class="px-6 py-12 text-center text-sm text-gray-400">
                没有匹配的基金，请调整搜索关键词。
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useColorModeStore } from '../stores/colorMode'
import { buildFundRows, filterFundRows, type FundListItem } from '../utils/fundList'
import { getDirectionPalette, numericToDirection, type MarketDirection } from '../utils/marketColors'

const router = useRouter()
const colorMode = useColorModeStore()
const useMockData = import.meta.env.DEV || import.meta.env.MODE === 'test'

const funds = ref<FundListItem[]>([])
const keyword = ref('')

const mockFunds: FundListItem[] = [
  {
    code: '510300',
    name: '沪深300ETF',
    prevClose: 4.1,
    open: 4.105,
    close: 4.123,
    high: 4.15,
    low: 4.08,
    volatility: (4.15 - 4.08) / 4.08,
    macd: { signal: 'bullish', value: '金叉' },
    rsi: { signal: 'neutral', value: '52' },
    boll: { signal: 'bullish', value: '中轨' },
    ma5: { signal: 'bullish', value: '上穿' },
    ma20: { signal: 'neutral', value: '粘合' },
    score: 9,
  },
  {
    code: '159915',
    name: '创业板ETF',
    prevClose: 2.24,
    open: 2.245,
    close: 2.256,
    high: 2.28,
    low: 2.23,
    volatility: (2.28 - 2.23) / 2.23,
    macd: { signal: 'bullish', value: '红柱' },
    rsi: { signal: 'bullish', value: '68' },
    boll: { signal: 'bullish', value: '下轨' },
    ma5: { signal: 'bullish', value: '多头' },
    ma20: { signal: 'bullish', value: '向上' },
    score: 10,
  },
  {
    code: '510500',
    name: '中证500ETF',
    prevClose: 6.8,
    open: 6.79,
    close: 6.789,
    high: 6.82,
    low: 6.75,
    volatility: (6.82 - 6.75) / 6.75,
    macd: { signal: 'bearish', value: '死叉' },
    rsi: { signal: 'neutral', value: '48' },
    boll: { signal: 'neutral', value: '中轨' },
    ma5: { signal: 'bearish', value: '下穿' },
    ma20: { signal: 'neutral', value: '粘合' },
    score: 3,
  },
  {
    code: '588000',
    name: '科创50ETF',
    prevClose: 1.05,
    open: 1.045,
    close: 1.03,
    high: 1.06,
    low: 1.02,
    volatility: (1.06 - 1.02) / 1.02,
    macd: { signal: 'bearish', value: '绿柱' },
    rsi: { signal: 'bearish', value: '25' },
    boll: { signal: 'bearish', value: '上轨' },
    ma5: { signal: 'bearish', value: '空头' },
    ma20: { signal: 'bearish', value: '向下' },
    score: 1,
  },
]

const rows = computed(() => buildFundRows(funds.value))
const filteredRows = computed(() => filterFundRows(rows.value, keyword.value))

function paletteFor(direction: MarketDirection) {
  return getDirectionPalette(colorMode.mode, direction)
}

function goToAnalysis(code: string) {
  router.push({ name: 'analysis', query: { code } })
}

async function fetchFunds() {
  if (useMockData) {
    funds.value = mockFunds
    return
  }

  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const result = await invoke('invoke_engine', {
      method: 'get_fund_list',
      params: {},
    })
    funds.value = result as FundListItem[]
  } catch (error) {
    console.error('获取基金列表失败:', error)
    funds.value = mockFunds
  }
}

onMounted(fetchFunds)
</script>
```

- [ ] **Step 4: 运行页面测试，确认第二页关键交互通过**

Run: `npm run test -- --run src/views/__tests__/FundList.spec.ts`

Expected: PASS，输出 `4 passed`。

- [ ] **Step 5: 提交第二页宽表格重构**

```bash
git add src/views/FundList.vue src/views/__tests__/FundList.spec.ts
git commit -m "feat: rebuild fund list wide table"
```

---

### Task 5: 让 Dashboard 响应共享配色

**Files:**
- Modify: `src/views/Dashboard.vue`
- Create: `src/views/__tests__/Dashboard.spec.ts`

- [ ] **Step 1: 先写首页共享配色响应的失败测试**

创建 `src/views/__tests__/Dashboard.spec.ts`：

```ts
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import Dashboard from '../Dashboard.vue'
import { useColorModeStore } from '../../stores/colorMode'

const pushMock = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}))

describe('Dashboard.vue', () => {
  beforeEach(() => {
    localStorage.clear()
    pushMock.mockReset()
  })

  it('re-renders positive change text when color mode changes', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useColorModeStore()
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [pinia],
      },
    })

    await flushPromises()
    expect(wrapper.get('[data-test="dashboard-change-513130"]').classes()).toContain('text-red-500')

    store.setMode('intl')
    await nextTick()

    expect(wrapper.get('[data-test="dashboard-change-513130"]').classes()).toContain('text-green-600')
  })
})
```

- [ ] **Step 2: 运行测试，确认当前首页仍然写死红绿类名**

Run: `npm run test -- --run src/views/__tests__/Dashboard.spec.ts`

Expected: FAIL，第二个断言失败，因为当前 `Dashboard.vue` 仍然硬编码 `text-red-500` / `text-green-500`。

- [ ] **Step 3: 把首页的方向色全部接入共享映射**

更新 `src/views/Dashboard.vue` 的导入和状态初始化：

```ts
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useColorModeStore } from '../stores/colorMode'
import { getDirectionPalette, numericToDirection } from '../utils/marketColors'

const router = useRouter()
const colorMode = useColorModeStore()
const useMockData = import.meta.env.DEV || import.meta.env.MODE === 'test'
```

新增方向色 helper：

```ts
function paletteFor(value: number) {
  return getDirectionPalette(colorMode.mode, numericToDirection(value))
}

function barClass(direction: 'bullish' | 'bearish') {
  return getDirectionPalette(colorMode.mode, direction).barClass
}
```

将 `fetchSignals()` 的开发模式判断替换为：

```ts
async function fetchSignals() {
  if (useMockData) {
    signals.value = mockSignals
    return
  }

  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const result = await invoke('invoke_engine', { method: 'get_dashboard_signals', params: {} })
    signals.value = result as DashboardSignal[]
  } catch (e) {
    console.error('获取信号失败:', e)
    signals.value = mockSignals
  }
}
```

把模板中的方向色绑定替换为共享映射：

```vue
<span
  :data-test="`dashboard-change-${signal.code}`"
  :class="paletteFor(signal.change_pct).valueClass"
  class="text-3xl font-black leading-none tabular-nums"
>
  {{ signal.change_pct >= 0 ? '+' : '' }}{{ signal.change_pct.toFixed(2) }}%
</span>

<span
  :class="paletteFor(signal.premium_rate).softTextClass"
  class="text-[10px] opacity-80 font-bold uppercase tracking-tighter"
>
  实时溢价
</span>

<span
  :class="paletteFor(signal.premium_rate).valueClass"
  class="text-[13px] font-mono font-bold leading-tight"
>
  {{ signal.premium_rate > 0 ? '+' : '' }}{{ signal.premium_rate.toFixed(2) }}%
</span>

<div class="h-1.5 w-full bg-gray-100 rounded-full flex overflow-hidden">
  <div :class="barClass('bearish')" :style="{ width: riskWidth(signal) + '%' }"></div>
  <div :class="barClass('bullish')" class="flex-1 ml-0.5"></div>
</div>
```

其余布局、mock 数据和 Tab 结构保持现状不动。

- [ ] **Step 4: 运行首页测试，确认切换全局模式后颜色会联动**

Run: `npm run test -- --run src/views/__tests__/Dashboard.spec.ts src/views/__tests__/FundList.spec.ts`

Expected: PASS，输出 `5 passed`。

- [ ] **Step 5: 提交首页联动改造**

```bash
git add src/views/Dashboard.vue src/views/__tests__/Dashboard.spec.ts
git commit -m "feat: wire dashboard into shared color mode"
```

---

### Task 6: 全量验证并同步开发文档

**Files:**
- Create: `docs/development/human/2026-04-01-daily-log.md`
- Modify: `docs/development/ai/current_state.md`

- [ ] **Step 1: 运行本轮前端测试全集**

Run: `npm run test -- --run`

Expected: PASS，输出所有前端测试通过。

- [ ] **Step 2: 运行前端构建验证**

Run: `npm run build`

Expected: PASS，输出 `vue-tsc --noEmit && vite build` 成功完成。

- [ ] **Step 3: 启动开发预览做人眼验收**

Run: `npm run dev`

Expected: Vite 输出本地地址（通常是 `http://localhost:1420/`）。

人工检查：

```text
1. 访问 /funds，确认页面为宽表格，不是卡片流。
2. 确认顶部右侧存在 红多 / 绿多 切换器 与 搜索框。
3. 切换 红多 / 绿多 后，/funds 的 涨跌幅、技术指标、多空圆点 立即切换颜色语义。
4. 返回 /，确认 Dashboard 中涨跌幅、实时溢价、风险条同步响应同一设置。
5. 缩窄窗口，确认顶部控制栏折行，表格保持横向滚动而不是塌成卡片。
```

- [ ] **Step 4: 更新人类开发日志**

创建 `docs/development/human/2026-04-01-daily-log.md`：

```md
# 2026-04-01 开发日志

## 今日开发内容

1. **前端测试基线补齐**：
   - 引入 `Vitest + @vue/test-utils + jsdom`。
   - 建立前端 smoke test 与页面/工具测试运行链路。

2. **全局方向色状态落地**：
   - 新增 Pinia 全局 `红多 / 绿多` 配色 store。
   - 接入本地持久化，应用重启后保留用户选择。

3. **FundList 第二页完成实现**：
   - 将第二页重构为确认后的宽表格主视图。
   - 接入代码 / 名称即时过滤、空状态与 `详情分析` 按钮。

4. **Dashboard 同步联动**：
   - 首页涨跌幅、实时溢价、风险条改为走共享方向色映射。
   - 与第二页共用同一份全局配色状态。

## 验证

1. `npm run test -- --run`
2. `npm run build`
3. `npm run dev` 人工预览 `/funds` 与 `/`

## 当前状态

- 第二页 `FundList.vue` UI 与全局配色联动已完成。
- 下一步等待用户验收，再决定是否继续推进其他页面 UI 确认。
```

- [ ] **Step 5: 更新 AI 当前状态文档**

将 `docs/development/ai/current_state.md` 的“当前阶段”和“下一步行动”更新为：

```md
## 1. 当前阶段

项目处于 **UI 重构阶段的第二页实现完成节点**。
`FundList.vue` 的宽表格主视图、全局 `红多 / 绿多` 配色状态，以及 `Dashboard.vue` 的联动已经实现完成，并补齐了前端测试基线。

## 4. 下一步行动 (Next Actions)

1. 等待用户验收 `/funds` 与 `/` 的联动表现。
2. 如验收通过，再推进下一页面的 UI 确认或数据联动。
3. 继续保持 Mock 优先，不对未确认页面提前接入复杂可视化。
```

- [ ] **Step 6: 提交验证与文档更新**

```bash
git add docs/development/human/2026-04-01-daily-log.md docs/development/ai/current_state.md
git commit -m "docs: update frontend progress logs"
```

---

## 自检结果

- 规格覆盖：`FundList.vue` 宽表格布局、顶部控制栏、全局 `红多 / 绿多` 状态、`Dashboard.vue` 联动、Mock 优先、搜索过滤、空状态、`详情分析` 按钮、移动端横向滚动、前端验证命令，均已映射到具体任务。
- 占位符扫描：计划中未发现占位式措辞、延期描述或跨任务偷懒引用。
- 类型一致性：`ColorMode`、`MarketDirection`、`FundListItem`、`FundListRow`、`scoreDirection`、`changePct` 命名在测试、工具和页面任务中保持一致。
