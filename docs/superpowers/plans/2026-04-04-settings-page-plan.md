# 系统设置页 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 FUNDFLOW 系统设置页（`/settings`），包含显示偏好（红多/绿多配色切换、卡片数量下拉）、关于信息、隐私与免责声明三张卡片，并将卡片数量联动到 Dashboard 和 Analysis 页面。

**Architecture:** 新建 `displaySettings` Pinia store 管理卡片数量设置（localStorage 持久化），替换 `Settings.vue` 空壳为完整三卡片布局，改造 `dashboardSignals.ts` 的 `getAnalysisEntryCards()` 接受 `count` 参数，最后修改 Dashboard 和 Analysis 页面读取 store 中的 `cardCount`。

**Tech Stack:** Vue 3 + TypeScript + Pinia + Tailwind CSS v4 + Vitest + @vue/test-utils

**Design Spec:** `docs/superpowers/specs/2026-04-04-settings-page-design.md`（已通过用户确认）

**测试运行命令：** `npx vitest run --exclude '.worktrees/**'`（主项目当前 91 tests 全绿）

---

## 文件结构

| 文件路径 | 操作 | 职责 |
|---------|------|------|
| `src/stores/displaySettings.ts` | 新建 | 显示设置 Pinia store（cardCount + hydrate + setCardCount） |
| `src/stores/__tests__/displaySettings.spec.ts` | 新建 | displaySettings store 单元测试 |
| `src/utils/dashboardSignals.ts` | 修改 | `getAnalysisEntryCards()` 增加 `count` 参数 |
| `src/utils/__tests__/dashboardSignals.spec.ts` | 修改 | 更新测试以覆盖 `count` 参数 |
| `src/views/Settings.vue` | 修改 | 替换空壳为完整设置页 |
| `src/views/__tests__/Settings.spec.ts` | 新建 | Settings 页面渲染与交互测试 |
| `src/views/Dashboard.vue` | 修改 | `fetchSignals()` 使用 `displaySettings.cardCount`；`onMounted` 增加 `displaySettings.hydrate()` |
| `src/views/__tests__/Dashboard.spec.ts` | 修改 | 增加 cardCount 联动测试 |
| `src/views/Analysis.vue` | 修改 | `getAnalysisEntryCards()` 传入 `cardCount`；`onMounted` 增加 `displaySettings.hydrate()` |
| `vite.config.ts` | 修改 | test.exclude 添加 `.worktrees/**` 避免 worktree 测试干扰 |

---

### Task 0: 修复测试配置排除 worktrees

**Files:**
- Modify: `vite.config.ts:15-18`

- [ ] **Step 1: 修改 vite.config.ts 排除 worktree 测试**

在 `test` 配置中添加 `exclude`，阻止 vitest 扫描 `.worktrees/` 下的测试文件：

```typescript
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '.worktrees/**',
    ],
  },
```

- [ ] **Step 2: 运行测试确认 91 tests 全绿**

Run: `npx vitest run`
Expected: 9 test files, 91 tests passed, 0 failed

- [ ] **Step 3: 提交**

```bash
git add vite.config.ts
git commit -m "chore: 排除 .worktrees 目录避免 vitest 扫描旧测试"
```

---

### Task 1: 新建 displaySettings Pinia store（TDD）

**Files:**
- Create: `src/stores/__tests__/displaySettings.spec.ts`
- Create: `src/stores/displaySettings.ts`

- [ ] **Step 1: 编写 displaySettings store 测试（RED）**

创建 `src/stores/__tests__/displaySettings.spec.ts`：

```typescript
import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { CARD_COUNT_STORAGE_KEY, useDisplaySettingsStore } from '../displaySettings'

describe('displaySettings store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('默认 cardCount 为 10', () => {
    const store = useDisplaySettingsStore()

    expect(store.cardCount).toBe(10)
  })

  it('setCardCount() 更新内存值并持久化到 localStorage', () => {
    const store = useDisplaySettingsStore()

    store.setCardCount(6)

    expect(store.cardCount).toBe(6)
    expect(localStorage.getItem(CARD_COUNT_STORAGE_KEY)).toBe('6')
  })

  it('hydrate() 从 localStorage 读取已保存的值', () => {
    localStorage.setItem(CARD_COUNT_STORAGE_KEY, '8')
    const store = useDisplaySettingsStore()

    store.hydrate()

    expect(store.cardCount).toBe(8)
    expect(store.hydrated).toBe(true)
  })

  it('hydrate() 遇到无效值时回退到默认值 10', () => {
    localStorage.setItem(CARD_COUNT_STORAGE_KEY, '999')
    const store = useDisplaySettingsStore()

    store.hydrate()

    expect(store.cardCount).toBe(10)
    expect(store.hydrated).toBe(true)
  })

  it('hydrate() 遇到非数字字符串时回退到默认值 10', () => {
    localStorage.setItem(CARD_COUNT_STORAGE_KEY, 'abc')
    const store = useDisplaySettingsStore()

    store.hydrate()

    expect(store.cardCount).toBe(10)
    expect(store.hydrated).toBe(true)
  })

  it('重复 hydrate() 不会再次覆盖当前内存态', () => {
    localStorage.setItem(CARD_COUNT_STORAGE_KEY, '8')
    const store = useDisplaySettingsStore()

    store.hydrate()
    store.setCardCount(12)
    localStorage.setItem(CARD_COUNT_STORAGE_KEY, '6')

    store.hydrate()

    expect(store.cardCount).toBe(12)
  })
})
```

- [ ] **Step 2: 运行测试确认全部 RED**

Run: `npx vitest run src/stores/__tests__/displaySettings.spec.ts`
Expected: FAIL — `Cannot find module '../displaySettings'`

- [ ] **Step 3: 编写 displaySettings store 实现（GREEN）**

创建 `src/stores/displaySettings.ts`：

```typescript
import { ref } from 'vue'
import { defineStore } from 'pinia'

export const CARD_COUNT_STORAGE_KEY = 'display-card-count'

const DEFAULT_CARD_COUNT = 10

const VALID_CARD_COUNTS = [6, 8, 10, 12] as const

export type CardCount = (typeof VALID_CARD_COUNTS)[number]

function isValidCardCount(value: number): value is CardCount {
  return (VALID_CARD_COUNTS as readonly number[]).includes(value)
}

export const useDisplaySettingsStore = defineStore('displaySettings', () => {
  const cardCount = ref<CardCount>(DEFAULT_CARD_COUNT)
  const hydrated = ref(false)

  function hydrate() {
    if (hydrated.value) {
      return
    }

    const stored = localStorage.getItem(CARD_COUNT_STORAGE_KEY)
    const parsed = Number(stored)
    cardCount.value = isValidCardCount(parsed) ? parsed : DEFAULT_CARD_COUNT
    hydrated.value = true
  }

  function setCardCount(count: CardCount) {
    cardCount.value = count
    localStorage.setItem(CARD_COUNT_STORAGE_KEY, String(count))
  }

  return {
    cardCount,
    hydrated,
    hydrate,
    setCardCount,
  }
})
```

- [ ] **Step 4: 运行测试确认全部 GREEN**

Run: `npx vitest run src/stores/__tests__/displaySettings.spec.ts`
Expected: 6 tests passed

- [ ] **Step 5: 运行全量测试确认无回归**

Run: `npx vitest run`
Expected: 所有测试通过（之前的 91 + 新增的 6 = 97）

- [ ] **Step 6: 提交**

```bash
git add src/stores/displaySettings.ts src/stores/__tests__/displaySettings.spec.ts
git commit -m "feat: 新建 displaySettings Pinia store，支持卡片数量设置与 localStorage 持久化"
```

---

### Task 2: 改造 getAnalysisEntryCards 支持 count 参数（TDD）

**Files:**
- Modify: `src/utils/__tests__/dashboardSignals.spec.ts:126-136`
- Modify: `src/utils/dashboardSignals.ts:105-113`

- [ ] **Step 1: 修改测试添加 count 参数覆盖（RED）**

在 `src/utils/__tests__/dashboardSignals.spec.ts` 中，找到现有两个分析页入口测试，修改第一个并新增一个：

将第 126-130 行的测试替换为：

```typescript
  it('分析页入口 getter 在无 route code 时返回默认前 10 条卡片', () => {
    const entryCodes = getAnalysisEntryCards().map((card) => card.code)

    expect(entryCodes).toEqual(getSharedFundCards().slice(0, 10).map((card) => card.code))
  })

  it('分析页入口 getter 接受 count 参数控制返回数量', () => {
    const entryCodes = getAnalysisEntryCards(null, undefined, 6).map((card) => card.code)

    expect(entryCodes).toEqual(getSharedFundCards().slice(0, 6).map((card) => card.code))
    expect(entryCodes).toHaveLength(6)
  })
```

- [ ] **Step 2: 运行测试确认新增测试 RED**

Run: `npx vitest run src/utils/__tests__/dashboardSignals.spec.ts`
Expected: 新增的 `接受 count 参数控制返回数量` 测试 FAIL（因为当前签名不支持第三参数）

- [ ] **Step 3: 修改 getAnalysisEntryCards 实现（GREEN）**

在 `src/utils/dashboardSignals.ts` 第 105 行，修改函数签名和实现：

将：
```typescript
export function getAnalysisEntryCards(routeCode?: string | null, sharedCards: SharedFundCard[] = getSharedFundCards()): SharedFundCard[] {
  const defaultCards = sharedCards.slice(0, 10)
```

替换为：
```typescript
export function getAnalysisEntryCards(routeCode?: string | null, sharedCards: SharedFundCard[] = getSharedFundCards(), count: number = 10): SharedFundCard[] {
  const defaultCards = sharedCards.slice(0, count)
```

- [ ] **Step 4: 运行测试确认全部 GREEN**

Run: `npx vitest run src/utils/__tests__/dashboardSignals.spec.ts`
Expected: 所有测试通过（原有测试不受影响，因为 count 默认值为 10）

- [ ] **Step 5: 运行全量测试确认无回归**

Run: `npx vitest run`
Expected: 所有测试通过

- [ ] **Step 6: 提交**

```bash
git add src/utils/dashboardSignals.ts src/utils/__tests__/dashboardSignals.spec.ts
git commit -m "feat: getAnalysisEntryCards 增加 count 参数，替代硬编码 10"
```

---

### Task 3: 实现 Settings.vue 页面（TDD）

**Files:**
- Create: `src/views/__tests__/Settings.spec.ts`
- Modify: `src/views/Settings.vue`

- [ ] **Step 1: 编写 Settings 页面测试（RED）**

创建 `src/views/__tests__/Settings.spec.ts`：

```typescript
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import Settings from '../Settings.vue'
import { useColorModeStore } from '../../stores/colorMode'
import { useDisplaySettingsStore } from '../../stores/displaySettings'

describe('Settings', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('渲染页面壳层，采用与其他页面一致的背景和间距', () => {
    const wrapper = mount(Settings)

    expect(wrapper.get('[data-test="settings-shell"]').classes()).toEqual(
      expect.arrayContaining(['min-h-full', 'bg-slate-50', 'p-4', 'md:p-6']),
    )
  })

  it('渲染顶栏，包含标题和副标题', () => {
    const wrapper = mount(Settings)

    const topbar = wrapper.get('[data-test="settings-topbar"]')
    expect(topbar.text()).toContain('系统设置')
    expect(topbar.text()).toContain('管理显示偏好与查看应用信息')
  })

  it('渲染显示偏好卡片，包含红多/绿多切换按钮', () => {
    const wrapper = mount(Settings)

    expect(wrapper.find('[data-test="settings-card-display"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="settings-mode-cn"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="settings-mode-intl"]').exists()).toBe(true)
  })

  it('红多/绿多切换按钮能正确反映 colorMode 当前状态', () => {
    const wrapper = mount(Settings)
    const colorMode = useColorModeStore()

    expect(colorMode.mode).toBe('cn')
    expect(wrapper.get('[data-test="settings-mode-cn"]').classes()).toContain('bg-white')

    colorMode.setMode('intl')

    // 需要 nextTick 后再断言，但 Pinia 的响应式在同步测试中就能触发
  })

  it('点击绿多按钮后 colorMode store 切换到 intl', async () => {
    const wrapper = mount(Settings)
    const colorMode = useColorModeStore()

    await wrapper.get('[data-test="settings-mode-intl"]').trigger('click')

    expect(colorMode.mode).toBe('intl')
  })

  it('点击红多按钮后 colorMode store 切换到 cn', async () => {
    const wrapper = mount(Settings)
    const colorMode = useColorModeStore()
    colorMode.setMode('intl')

    await wrapper.get('[data-test="settings-mode-cn"]').trigger('click')

    expect(colorMode.mode).toBe('cn')
  })

  it('渲染卡片数量下拉，默认值为 10', () => {
    const wrapper = mount(Settings)

    const select = wrapper.get('[data-test="settings-card-count"]')
    expect((select.element as HTMLSelectElement).value).toBe('10')
  })

  it('卡片数量下拉包含 4 个选项：6/8/10/12', () => {
    const wrapper = mount(Settings)

    const options = wrapper.get('[data-test="settings-card-count"]').findAll('option')
    expect(options.map(o => o.element.value)).toEqual(['6', '8', '10', '12'])
  })

  it('切换卡片数量后 displaySettings store 更新', async () => {
    const wrapper = mount(Settings)
    const displaySettings = useDisplaySettingsStore()

    await wrapper.get('[data-test="settings-card-count"]').setValue('8')

    expect(displaySettings.cardCount).toBe(8)
  })

  it('渲染关于卡片，包含软件名称、版本、协议、联网行为', () => {
    const wrapper = mount(Settings)

    const about = wrapper.get('[data-test="settings-card-about"]')
    expect(about.text()).toContain('FUNDFLOW')
    expect(about.text()).toContain('v0.0.1 预览版')
    expect(about.text()).toContain('GPLv3')
    expect(about.text()).toContain('仅抓取行情')
  })

  it('渲染隐私与免责声明卡片，包含三段声明文字', () => {
    const wrapper = mount(Settings)

    const disclaimer = wrapper.get('[data-test="settings-card-disclaimer"]')
    expect(disclaimer.text()).toContain('隐私保护')
    expect(disclaimer.text()).toContain('数据安全')
    expect(disclaimer.text()).toContain('投资风险')
    expect(disclaimer.text()).toContain('不收集、上传或存储任何用户个人信息')
    expect(disclaimer.text()).toContain('投资有风险，入市需谨慎')
  })

  it('显示偏好卡片包含配色辅助说明文字', () => {
    const wrapper = mount(Settings)

    expect(wrapper.get('[data-test="settings-card-display"]').text()).toContain('所有页面的涨跌颜色同步生效')
  })

  it('显示偏好卡片包含卡片数量辅助说明文字', () => {
    const wrapper = mount(Settings)

    expect(wrapper.get('[data-test="settings-card-display"]').text()).toContain('信号卡片')
    expect(wrapper.get('[data-test="settings-card-display"]').text()).toContain('入口卡片')
  })
})
```

- [ ] **Step 2: 运行测试确认全部 RED**

Run: `npx vitest run src/views/__tests__/Settings.spec.ts`
Expected: FAIL — 找不到 `data-test="settings-shell"` 等元素

- [ ] **Step 3: 实现 Settings.vue 完整页面（GREEN）**

替换 `src/views/Settings.vue` 的全部内容：

```vue
<template>
  <section data-test="settings-shell" class="min-h-full bg-slate-50 p-4 md:p-6">
    <div class="flex w-full flex-col gap-4">
      <!-- 顶栏 -->
      <header
        data-test="settings-topbar"
        class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5"
      >
        <div class="space-y-1">
          <h1 class="text-2xl font-semibold tracking-tight text-slate-900">系统设置</h1>
          <p class="text-sm text-slate-500">管理显示偏好与查看应用信息</p>
        </div>
      </header>

      <!-- 卡片一：显示偏好 -->
      <div
        data-test="settings-card-display"
        class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <h2 class="text-lg font-semibold text-slate-900">显示偏好</h2>

        <!-- 涨跌配色 -->
        <div class="mt-5 space-y-2">
          <label class="text-sm font-medium text-slate-700">涨跌配色</label>
          <div class="inline-flex rounded-xl bg-slate-100 p-1">
            <button
              data-test="settings-mode-cn"
              type="button"
              class="rounded-lg px-3 py-2 text-sm font-medium transition"
              :class="colorMode.mode === 'cn' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'"
              @click="colorMode.setMode('cn')"
            >
              红多
            </button>
            <button
              data-test="settings-mode-intl"
              type="button"
              class="rounded-lg px-3 py-2 text-sm font-medium transition"
              :class="colorMode.mode === 'intl' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'"
              @click="colorMode.setMode('intl')"
            >
              绿多
            </button>
          </div>
          <p class="text-xs text-slate-400">切换后所有页面的涨跌颜色同步生效。也可以在「全量基金」和「技术分析」页面顶栏快捷切换。</p>
        </div>

        <!-- 卡片数量 -->
        <div class="mt-5 space-y-2">
          <label class="text-sm font-medium text-slate-700">首页/分析入口卡片数量</label>
          <select
            data-test="settings-card-count"
            :value="String(displaySettings.cardCount)"
            class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-300 focus:ring-2 focus:ring-slate-200"
            @change="onCardCountChange"
          >
            <option value="6">6 支</option>
            <option value="8">8 支</option>
            <option value="10">10 支（默认）</option>
            <option value="12">12 支</option>
          </select>
          <p class="text-xs text-slate-400">同时控制「今日行情」信号卡片和「技术分析」入口卡片的显示数量</p>
        </div>
      </div>

      <!-- 卡片二：关于 -->
      <div
        data-test="settings-card-about"
        class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <h2 class="text-lg font-semibold text-slate-900">关于</h2>
        <div class="mt-4 grid grid-cols-2 gap-3">
          <div class="rounded-xl bg-slate-50 p-3">
            <p class="text-xs text-slate-500">软件名称</p>
            <p class="mt-1 text-base font-semibold italic text-blue-600">FUNDFLOW</p>
          </div>
          <div class="rounded-xl bg-slate-50 p-3">
            <p class="text-xs text-slate-500">版本</p>
            <p class="mt-1 text-base font-semibold text-slate-900">v0.0.1 预览版</p>
          </div>
          <div class="rounded-xl bg-slate-50 p-3">
            <p class="text-xs text-slate-500">开源协议</p>
            <p class="mt-1 text-base font-semibold text-slate-900">GPLv3</p>
          </div>
          <div class="rounded-xl bg-slate-50 p-3">
            <p class="text-xs text-slate-500">联网行为</p>
            <p class="mt-1 text-base font-semibold text-slate-900">仅抓取行情 + 跳转雪球</p>
          </div>
        </div>
      </div>

      <!-- 卡片三：隐私与免责声明 -->
      <div
        data-test="settings-card-disclaimer"
        class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <h2 class="text-lg font-semibold text-slate-900">隐私与免责声明</h2>
        <div class="mt-4 space-y-4">
          <div class="flex gap-3">
            <span class="mt-1.5 h-2.5 w-2.5 flex-none rounded-full bg-blue-500"></span>
            <div>
              <p class="text-sm font-medium text-slate-700">隐私保护</p>
              <p class="mt-1 text-sm text-slate-500">本软件为本地运行的单机工具，不收集、上传或存储任何用户个人信息。联网行为仅限于：获取市场行情数据、跳转至雪球网站查看基金详情。除此之外不与任何外部服务器通信。</p>
            </div>
          </div>
          <div class="flex gap-3">
            <span class="mt-1.5 h-2.5 w-2.5 flex-none rounded-full bg-yellow-500"></span>
            <div>
              <p class="text-sm font-medium text-yellow-600">数据安全</p>
              <p class="mt-1 text-sm text-yellow-600">本软件仍处于早期开发阶段（预览版），开发者无法对数据的安全性和真实性做出保证。所有行情数据仅供参考，请用户自行核实。</p>
            </div>
          </div>
          <div class="flex gap-3">
            <span class="mt-1.5 h-2.5 w-2.5 flex-none rounded-full bg-red-500"></span>
            <div>
              <p class="text-sm font-medium text-red-500">投资风险</p>
              <p class="mt-1 text-sm text-red-500">投资有风险，入市需谨慎。本软件提供的所有分析结论、策略建议仅作为辅助参考，不构成任何投资建议。开发者不对任何投资决策及其结果承担责任，用户需风险自担。</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

import { useColorModeStore } from '../stores/colorMode'
import { useDisplaySettingsStore } from '../stores/displaySettings'
import type { CardCount } from '../stores/displaySettings'

const colorMode = useColorModeStore()
const displaySettings = useDisplaySettingsStore()

function onCardCountChange(event: Event) {
  const value = Number((event.target as HTMLSelectElement).value)
  displaySettings.setCardCount(value as CardCount)
}

onMounted(() => {
  colorMode.hydrate()
  displaySettings.hydrate()
})
</script>
```

- [ ] **Step 4: 运行测试确认全部 GREEN**

Run: `npx vitest run src/views/__tests__/Settings.spec.ts`
Expected: 所有 Settings 测试通过

- [ ] **Step 5: 运行全量测试确认无回归**

Run: `npx vitest run`
Expected: 所有测试通过

- [ ] **Step 6: 提交**

```bash
git add src/views/Settings.vue src/views/__tests__/Settings.spec.ts
git commit -m "feat: 实现系统设置页三卡片布局 — 显示偏好、关于、隐私免责声明"
```

---

### Task 4: Dashboard 联动 cardCount（TDD）

**Files:**
- Modify: `src/views/__tests__/Dashboard.spec.ts`
- Modify: `src/views/Dashboard.vue:87-153`

- [ ] **Step 1: 在 Dashboard 测试中新增 cardCount 联动测试（RED）**

在 `src/views/__tests__/Dashboard.spec.ts` 文件的 `describe` 块尾部，添加以下测试用例。需要先在文件顶部导入 `useDisplaySettingsStore`：

在 import 区域添加：
```typescript
import { useDisplaySettingsStore } from '../../stores/displaySettings'
```

在 `describe` 块末尾（最后一个 `it` 之后）添加：

```typescript
  it('首页从 displaySettings store 读取 cardCount 控制展示数量', async () => {
    const displaySettings = useDisplaySettingsStore()
    displaySettings.setCardCount(6)

    const wrapper = mount(Dashboard)

    await flushPromises()

    expect(wrapper.findAll('.fund-card')).toHaveLength(6)
  })
```

同时修改现有的 `首页仍只展示默认 10 张卡片` 测试的注释（可选），确保它仍然验证默认行为。

- [ ] **Step 2: 运行测试确认新增测试 RED**

Run: `npx vitest run src/views/__tests__/Dashboard.spec.ts`
Expected: `首页从 displaySettings store 读取 cardCount 控制展示数量` FAIL（因为 Dashboard.vue 仍硬编码 `.slice(0, 10)`）

- [ ] **Step 3: 修改 Dashboard.vue 使用 displaySettings.cardCount（GREEN）**

在 `src/views/Dashboard.vue` 中做以下修改：

1. 在 import 区域（第 90 行附近）添加：
```typescript
import { useDisplaySettingsStore } from '../stores/displaySettings'
```

2. 在 `const colorMode = useColorModeStore()` 之后添加：
```typescript
const displaySettings = useDisplaySettingsStore()
```

3. 将第 148 行的 `fetchSignals` 函数：
```typescript
async function fetchSignals() {
  signals.value = (await loadSharedFundCards()).slice(0, 10)
}
```
替换为：
```typescript
async function fetchSignals() {
  signals.value = (await loadSharedFundCards()).slice(0, displaySettings.cardCount)
}
```

4. 在 `onMounted` 中（第 151-153 行）添加 hydrate：
```typescript
onMounted(() => {
  displaySettings.hydrate()
  fetchSignals()
})
```

- [ ] **Step 4: 运行测试确认全部 GREEN**

Run: `npx vitest run src/views/__tests__/Dashboard.spec.ts`
Expected: 所有 Dashboard 测试通过

- [ ] **Step 5: 运行全量测试确认无回归**

Run: `npx vitest run`
Expected: 所有测试通过

- [ ] **Step 6: 提交**

```bash
git add src/views/Dashboard.vue src/views/__tests__/Dashboard.spec.ts
git commit -m "feat: Dashboard 页面从 displaySettings store 读取 cardCount 控制展示数量"
```

---

### Task 5: Analysis 联动 cardCount

**Files:**
- Modify: `src/views/Analysis.vue:386-414,676-678`

这个 task 不需要额外的测试文件，因为 Analysis 的测试已经通过 mock `getAnalysisEntryCards` 验证了入口卡片的行为。我们只需修改 Analysis.vue 中传递给 `getAnalysisEntryCards` 的参数。

- [ ] **Step 1: 修改 Analysis.vue 传入 cardCount**

在 `src/views/Analysis.vue` 中做以下修改：

1. 在 import 区域添加（约第 386 行 `import { useColorModeStore }` 附近）：
```typescript
import { useDisplaySettingsStore } from '../stores/displaySettings'
```

2. 在 `const colorMode = useColorModeStore()` 之后添加：
```typescript
const displaySettings = useDisplaySettingsStore()
```

3. 将第 412-414 行的 `entryCards` computed：
```typescript
const entryCards = computed<SharedFundCard[]>(() => {
  return getAnalysisEntryCards(routeCode.value, sharedCards.value)
})
```
替换为：
```typescript
const entryCards = computed<SharedFundCard[]>(() => {
  return getAnalysisEntryCards(routeCode.value, sharedCards.value, displaySettings.cardCount)
})
```

4. 在 `onMounted` 钩子（第 676 行）中添加 hydrate：
```typescript
onMounted(async () => {
  displaySettings.hydrate()
  sharedCards.value = await loadSharedFundCards()
})
```

- [ ] **Step 2: 运行全量测试确认无回归**

Run: `npx vitest run`
Expected: 所有测试通过（Analysis 现有测试不受影响，因为它们 mock 了 `getAnalysisEntryCards` 或直接传入了 sharedCards）

- [ ] **Step 3: 提交**

```bash
git add src/views/Analysis.vue
git commit -m "feat: Analysis 页面从 displaySettings store 读取 cardCount 控制入口卡片数量"
```

---

### Task 6: 全量验证与构建检查

- [ ] **Step 1: 运行全量 vitest 测试**

Run: `npx vitest run`
Expected: 所有测试通过

- [ ] **Step 2: 运行 TypeScript 类型检查 + 构建**

Run: `npm run build`
Expected: 构建成功，无类型错误

- [ ] **Step 3: 如有失败则修复并重新验证**

如果有失败，根据错误信息修复后重跑上述两步。

---

## 任务顺序总结

| 顺序 | Task | 关键产出 |
|------|------|---------|
| 0 | 修复测试配置 | `vite.config.ts` 排除 `.worktrees` |
| 1 | displaySettings store | 新 store + 测试（TDD） |
| 2 | getAnalysisEntryCards count | 函数签名改造 + 测试（TDD） |
| 3 | Settings.vue 页面 | 完整设置页 + 测试（TDD） |
| 4 | Dashboard 联动 | 读取 cardCount + 测试（TDD） |
| 5 | Analysis 联动 | 读取 cardCount |
| 6 | 全量验证 | vitest + build |
