# 启动先同步数据与 Windows MSI 命名修正 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让应用启动时先执行一次数据同步，并把 GitHub Release 中的 Windows 安装包名称从 `*_en-US.msi` 统一为不带地区后缀的 `*_x64.msi`。

**Architecture:** 前端增加一个统一的启动同步状态模块，负责在生产环境只执行一次 `sync_data`，并为 Dashboard/FundList 提供同步完成后的数据加载顺序与失败提示。Windows 发布侧不改 Tauri bundler 内部行为，只在 GitHub Actions 上传前对 MSI 产物做动态重命名。

**Tech Stack:** Vue 3、Vitest、Tauri 2、GitHub Actions、PowerShell

---

### Task 1: 为启动同步顺序补失败测试

**Files:**
- Modify: `src/views/__tests__/Dashboard.spec.ts`
- Modify: `src/views/__tests__/FundList.spec.ts`
- Create: `src/utils/__tests__/startupSync.spec.ts`

- [ ] **Step 1: 新增启动同步模块测试，先定义目标行为**

```ts
import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('startupSync', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('生产环境首次调用时先执行 sync_data，再标记 success', async () => {
    const invoke = vi.fn().mockResolvedValue({ funds_synced: 10, quotes_synced: 20, nav_synced: 5 })

    vi.doMock('@tauri-apps/api/core', () => ({ invoke }))

    const { ensureStartupSync, getStartupSyncState } = await import('../startupSync')

    await ensureStartupSync()

    expect(invoke).toHaveBeenCalledWith('invoke_engine', {
      method: 'sync_data',
      params: {},
    })
    expect(getStartupSyncState().status).toBe('success')
  })
})
```

- [ ] **Step 2: 运行新测试，确认红灯**

Run: `npm test -- src/utils/__tests__/startupSync.spec.ts`

Expected: FAIL，提示 `../startupSync` 不存在或导出缺失

- [ ] **Step 3: 在 Dashboard 测试中补“先同步后加载卡片”的失败断言**

```ts
it('首页挂载时先完成启动同步，再读取共享基金卡片数据', async () => {
  vi.resetModules()
  const ensureStartupSync = vi.fn().mockResolvedValue(undefined)
  const loadSharedFundCards = vi.fn().mockResolvedValue([])

  vi.doMock('../../utils/startupSync', () => ({
    ensureStartupSync,
    getStartupSyncState: () => ({ status: 'success', message: '' }),
  }))

  vi.doMock('../../utils/dashboardSignals', async () => {
    const actual = await vi.importActual<typeof import('../../utils/dashboardSignals')>(
      '../../utils/dashboardSignals',
    )

    return {
      ...actual,
      loadSharedFundCards,
    }
  })

  const { default: SyncDashboard } = await import('../Dashboard.vue')
  mount(SyncDashboard)

  await flushPromises()

  expect(ensureStartupSync).toHaveBeenCalledTimes(1)
  expect(loadSharedFundCards).toHaveBeenCalledTimes(1)
  expect(ensureStartupSync.mock.invocationCallOrder[0]).toBeLessThan(loadSharedFundCards.mock.invocationCallOrder[0])
})
```

- [ ] **Step 4: 在 FundList 测试中补“先同步后读取基金列表”的失败断言**

```ts
it('第二页挂载时先完成启动同步，再读取基金列表', async () => {
  vi.resetModules()
  const ensureStartupSync = vi.fn().mockResolvedValue(undefined)
  const invoke = vi.fn().mockResolvedValue([])

  vi.doMock('../../utils/startupSync', () => ({
    ensureStartupSync,
    getStartupSyncState: () => ({ status: 'success', message: '' }),
  }))

  vi.doMock('@tauri-apps/api/core', () => ({ invoke }))

  const { default: SyncFundList } = await import('../FundList.vue')
  mount(SyncFundList)

  await Promise.resolve()

  expect(ensureStartupSync).toHaveBeenCalledTimes(1)
  expect(invoke).toHaveBeenCalled()
  expect(ensureStartupSync.mock.invocationCallOrder[0]).toBeLessThan(invoke.mock.invocationCallOrder[0])
})
```

- [ ] **Step 5: 运行 Dashboard/FundList 相关测试，确认红灯**

Run: `npm test -- src/views/__tests__/Dashboard.spec.ts src/views/__tests__/FundList.spec.ts`

Expected: FAIL，提示当前页面尚未调用 `ensureStartupSync`


### Task 2: 实现统一的启动同步状态模块

**Files:**
- Create: `src/utils/startupSync.ts`
- Test: `src/utils/__tests__/startupSync.spec.ts`

- [ ] **Step 1: 创建最小启动同步模块实现**

```ts
export type StartupSyncStatus = 'idle' | 'syncing' | 'success' | 'error'

export interface StartupSyncState {
  status: StartupSyncStatus
  message: string
}

const state: StartupSyncState = {
  status: 'idle',
  message: '',
}

let syncPromise: Promise<void> | null = null

export function getStartupSyncState() {
  return state
}

export function resetStartupSyncForTest() {
  state.status = 'idle'
  state.message = ''
  syncPromise = null
}

export async function ensureStartupSync() {
  if (import.meta.env.DEV || import.meta.env.MODE === 'test') {
    state.status = 'success'
    state.message = ''
    return
  }

  if (syncPromise) {
    return syncPromise
  }

  state.status = 'syncing'
  state.message = ''

  syncPromise = (async () => {
    try {
      const { invoke } = await import('@tauri-apps/api/core')
      await invoke('invoke_engine', {
        method: 'sync_data',
        params: {},
      })
      state.status = 'success'
    } catch {
      state.status = 'error'
      state.message = '同步失败，当前显示本地旧数据'
    }
  })()

  await syncPromise
}
```

- [ ] **Step 2: 运行启动同步模块测试，确认转绿**

Run: `npm test -- src/utils/__tests__/startupSync.spec.ts`

Expected: PASS

- [ ] **Step 3: 补充“失败时返回 error 状态与提示文案”的测试**

```ts
it('同步失败时标记 error 并保留提示文案', async () => {
  const invoke = vi.fn().mockRejectedValue(new Error('sync failed'))
  vi.doMock('@tauri-apps/api/core', () => ({ invoke }))

  const { ensureStartupSync, getStartupSyncState } = await import('../startupSync')

  await ensureStartupSync()

  expect(getStartupSyncState()).toEqual({
    status: 'error',
    message: '同步失败，当前显示本地旧数据',
  })
})
```

- [ ] **Step 4: 运行测试，确认失败路径也通过**

Run: `npm test -- src/utils/__tests__/startupSync.spec.ts`

Expected: PASS


### Task 3: 让 Dashboard 和 FundList 在读数据前先执行启动同步

**Files:**
- Modify: `src/utils/dashboardSignals.ts`
- Modify: `src/views/FundList.vue`
- Modify: `src/views/Dashboard.vue`
- Modify: `src/views/__tests__/Dashboard.spec.ts`
- Modify: `src/views/__tests__/FundList.spec.ts`

- [ ] **Step 1: 在 `loadSharedFundCards()` 前先接入启动同步**

```ts
import { ensureStartupSync } from './startupSync'

export async function loadSharedFundCards(): Promise<SharedFundCard[]> {
  if (import.meta.env.DEV || import.meta.env.MODE === 'test') {
    return getSharedFundCards()
  }

  await ensureStartupSync()

  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const result = await invoke<DashboardSignal[]>('invoke_engine', {
      method: 'get_dashboard_signals',
      params: {},
    })

    return Array.isArray(result) ? toSharedFundCards(result) : getSharedFundCards()
  } catch {
    return getSharedFundCards()
  }
}
```

- [ ] **Step 2: 在 `FundList.vue` 的 `fetchFunds()` 中先执行启动同步**

```ts
import { ensureStartupSync, getStartupSyncState } from '../utils/startupSync'

async function fetchFunds() {
  if (import.meta.env.MODE === 'test' || import.meta.env.DEV) {
    funds.value = mockFunds
    return
  }

  await ensureStartupSync()

  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const response = await invoke<FundListItem[]>('invoke_engine', {
      method: 'get_fund_list',
      params: {},
    })

    funds.value = Array.isArray(response) ? response : mockFunds
  } catch {
    funds.value = mockFunds
  }
}
```

- [ ] **Step 3: 在 Dashboard / FundList 页面增加同步失败提示渲染**

```ts
const startupSyncState = getStartupSyncState()
```

```vue
<div v-if="startupSyncState.status === 'error'" data-test="startup-sync-error" class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
  {{ startupSyncState.message }}
</div>
```

- [ ] **Step 4: 运行 Dashboard/FundList 测试，确认从红灯转绿**

Run: `npm test -- src/views/__tests__/Dashboard.spec.ts src/views/__tests__/FundList.spec.ts`

Expected: PASS

- [ ] **Step 5: 再补“同步失败仍显示提示”的页面测试**

```ts
it('同步失败时显示启动同步失败提示', async () => {
  vi.resetModules()
  vi.doMock('../../utils/startupSync', () => ({
    ensureStartupSync: vi.fn().mockResolvedValue(undefined),
    getStartupSyncState: () => ({
      status: 'error',
      message: '同步失败，当前显示本地旧数据',
    }),
  }))

  const { default: FailureDashboard } = await import('../Dashboard.vue')
  const wrapper = mount(FailureDashboard)

  await flushPromises()

  expect(wrapper.get('[data-test="startup-sync-error"]').text()).toContain('同步失败')
})
```


### Task 4: 为 Windows MSI 上传重命名补失败测试与实现

**Files:**
- Modify: `src/utils/__tests__/version.spec.ts`
- Modify: `.github/workflows/release.yml`

- [ ] **Step 1: 在版本/workflow 测试中补“Windows 上传文件名不含 en-US”的失败断言**

```ts
import releaseWorkflow from '../../../.github/workflows/release.yml?raw'

it('Windows release 上传阶段会去掉 MSI 文件名中的 en-US 后缀', () => {
  expect(releaseWorkflow).toContain('Replace("_en-US", "")')
  expect(releaseWorkflow).toContain('ETF.Analyzer_${{ github.ref_name }}_x64.msi')
})
```

- [ ] **Step 2: 运行测试，确认红灯**

Run: `npm test -- src/utils/__tests__/version.spec.ts`

Expected: FAIL，提示 workflow 尚未包含 Windows MSI 重命名逻辑

- [ ] **Step 3: 修改 Windows 上传步骤，在上传前生成无 `en-US` 的目标文件名**

```yml
      - name: Upload Windows MSI
        if: runner.os == 'Windows'
        shell: pwsh
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          $msi = Get-ChildItem "src-tauri\target\${{ matrix.platform.target }}\release\bundle\msi\*.msi" | Select-Object -First 1
          $renamed = Join-Path $msi.DirectoryName ($msi.Name.Replace('_en-US', ''))
          Copy-Item $msi.FullName $renamed -Force
          gh release upload "${{ github.ref_name }}" $renamed --clobber
```
```

- [ ] **Step 4: 运行版本/workflow 测试，确认转绿**

Run: `npm test -- src/utils/__tests__/version.spec.ts`

Expected: PASS


### Task 5: 全量验证与发布准备

**Files:**
- Verify: `src/utils/startupSync.ts`
- Verify: `src/utils/dashboardSignals.ts`
- Verify: `src/views/FundList.vue`
- Verify: `src/views/Dashboard.vue`
- Verify: `.github/workflows/release.yml`

- [ ] **Step 1: 运行本次相关前端测试**

Run: `npm test -- src/utils/__tests__/startupSync.spec.ts src/utils/__tests__/version.spec.ts src/views/__tests__/Dashboard.spec.ts src/views/__tests__/FundList.spec.ts`

Expected: PASS

- [ ] **Step 2: 运行前端构建**

Run: `npm run build`

Expected: PASS

- [ ] **Step 3: 运行 Rust 类型检查**

Run: `cargo check --manifest-path src-tauri/Cargo.toml`

Expected: PASS

- [ ] **Step 4: 运行 Rust 测试**

Run: `cargo test --manifest-path src-tauri/Cargo.toml -- --test-threads=1`

Expected: PASS

- [ ] **Step 5: 运行 Python 测试**

Run: `pytest src-python/tests/`

Expected: PASS

- [ ] **Step 6: 如用户要求提交，再执行提交**

Run: `git add .github/workflows/release.yml src/utils/startupSync.ts src/utils/dashboardSignals.ts src/views/Dashboard.vue src/views/FundList.vue src/utils/__tests__/startupSync.spec.ts src/utils/__tests__/version.spec.ts src/views/__tests__/Dashboard.spec.ts src/views/__tests__/FundList.spec.ts docs/superpowers/specs/2026-04-05-startup-sync-and-windows-msi-name-design.md docs/superpowers/plans/2026-04-05-startup-sync-and-windows-msi-name-plan.md`

Run: `git commit -m "feat: sync data on startup and rename windows msi"`

Expected: commit 成功
