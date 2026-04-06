# 清理前端 Mock 数据与实现真实错误状态 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 彻底移除前端 Vue 组件中残留的 Mock 数据（假数据），在接口请求失败时实现优雅的错误处理和空状态（Empty State）展示。

**Architecture:** 
1. 删除已弃用的 `analysisMock.ts` 文件。
2. 针对 `FundList.vue`、`Config.vue`、`Scheduler.vue`、`Screening.vue`，移除内部定义的假数据常量（如 `mockFunds`、`mockTaxRates` 等）。
3. 增强这些组件在 `catch` 块或后端返回空数据时的处理逻辑，通常表现为清空数据列表、显示错误提示信息（如使用现有的 `ErrorMessage` 组件或直接显示友好的文本语）。

**Tech Stack:** Vue 3 + TypeScript, Tauri IPC, TailwindCSS, Vitest.

---

### Task 1: 清理分析模块残留 Mock 文件

**Files:**
- Delete: `src/utils/analysisMock.ts`
- Delete: `src/utils/__tests__/analysisMock.spec.ts`

- [ ] **Step 1: Delete the files**

```bash
rm src/utils/analysisMock.ts src/utils/__tests__/analysisMock.spec.ts
```

- [ ] **Step 2: Verify project builds**

Run: `npm run build && npm run test`
Expected: PASS (因为我们已经在之前移除了引用)

- [ ] **Step 3: Commit**

```bash
git add -u
git commit -m "chore(ui): remove deprecated analysisMock files"
```

---

### Task 2: 移除 FundList.vue 的 Mock 数据

**Files:**
- Modify: `src/views/FundList.vue`

- [ ] **Step 1: Write/Update the failing test (or prepare component)**
*这里主要是移除逻辑，测试如果涉及到 mockFunds 需要更新，但 FundList 目前测试可能是挂载测试。我们直接修改组件即可。*

- [ ] **Step 2: Update component to remove `mockFunds` and handle empty state**

```vue
// in src/views/FundList.vue
// 1. 找到并删除 `const mockFunds: FundListItem[] = [...]` 的整个定义 (大约第 156-218 行)
// 2. 修改 funds 的初始定义
// 修改前: const funds = ref<FundListItem[]>(import.meta.env.MODE === 'test' ? [...mockFunds] : [])
// 修改后: const funds = ref<FundListItem[]>([])

// 3. 修改 fetchFunds() 里的 catch 逻辑
// 找到:
/*
  } catch (e) {
    console.error('获取基金列表失败:', e)
    error.value = e instanceof Error ? e.message : String(e)
    funds.value = mockFunds
  } finally {
*/
// 修改为:
/*
  } catch (e) {
    console.error('获取基金列表失败:', e)
    error.value = e instanceof Error ? e.message : String(e)
    funds.value = []
  } finally {
*/

// 4. 修改 handleRefresh() 里的 catch 逻辑
// 找到:
/*
  } catch (e) {
    console.error('刷新基金列表失败:', e)
    funds.value = mockFunds
  } finally {
*/
// 修改为:
/*
  } catch (e) {
    console.error('刷新基金列表失败:', e)
    error.value = '刷新失败: ' + (e instanceof Error ? e.message : String(e))
    funds.value = []
  } finally {
*/

// 5. 确保模板中有空状态显示（已存在 <div v-else-if="!loading && funds.length === 0" ...>）
```

- [ ] **Step 3: Run test to verify it passes**

Run: `npm run build`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/views/FundList.vue
git commit -m "feat(ui): remove mockFunds and handle empty state in FundList"
```

---

### Task 3: 移除 Config.vue 的 Mock 数据

**Files:**
- Modify: `src/views/Config.vue`

- [ ] **Step 1: Update component to remove `mockTaxRates`**

```vue
// in src/views/Config.vue
// 1. 找到并删除 `const mockTaxRates = { ... }` (大约第 140-156 行)

// 2. 修改 fetchLegalTaxRates() 的 catch 逻辑
// 找到:
/*
  } catch (e) {
    console.error('Failed to fetch legal tax rates:', e)
    // Fallback to mock data if backend fails
    if (config.value.fees.etf.stampDuty === 0) {
      config.value.fees.etf.stampDuty = mockTaxRates.etf.stamp_duty
      config.value.fees.lof.stampDuty = mockTaxRates.lof.stamp_duty
      config.value.fees.stock.stampDuty = mockTaxRates.stock.stamp_duty
    }
  }
*/
// 修改为:
/*
  } catch (e) {
    console.error('Failed to fetch legal tax rates:', e)
    // Keep existing config values, just log the error or notify user
    // No fallback to mock data
  }
*/

// 3. 修改 resetFees() 函数
// 找到:
/*
  const resetFees = async () => {
    try {
      const rates = await invoke('invoke_engine', { method: 'fetch_legal_tax_rates' })
      // ...
    } catch (e) {
      console.error('Failed to reset fees:', e)
      config.value.fees.etf.stampDuty = mockTaxRates.etf.stamp_duty
      config.value.fees.lof.stampDuty = mockTaxRates.lof.stamp_duty
      config.value.fees.stock.stampDuty = mockTaxRates.stock.stamp_duty
    }
  }
*/
// 修改为:
/*
  const resetFees = async () => {
    try {
      const rates: any = await invoke('invoke_engine', { method: 'fetch_legal_tax_rates' })
      if (rates) {
        config.value.fees.etf.stampDuty = rates.etf.stamp_duty
        config.value.fees.lof.stampDuty = rates.lof.stamp_duty
        config.value.fees.stock.stampDuty = rates.stock.stamp_duty
      }
    } catch (e) {
      console.error('Failed to reset fees:', e)
      // Optional: Add a UI toast/notification here if available, else just log
    }
  }
*/
```

- [ ] **Step 2: Run test to verify it passes**

Run: `npm run build`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/views/Config.vue
git commit -m "feat(ui): remove mockTaxRates from Config"
```

---

### Task 4: 移除 Scheduler.vue 的 Mock 数据

**Files:**
- Modify: `src/views/Scheduler.vue`

- [ ] **Step 1: Update component to remove `mockSchedulerData`**

```vue
// in src/views/Scheduler.vue
// 1. 找到并删除 `const mockSchedulerData = { ... }` (大约第 53-61 行)

// 2. 修改 fetchSchedulerData() 的 catch 逻辑
// 找到:
/*
  } catch (e) {
    console.error('Failed to fetch scheduler data:', e)
    error.value = e instanceof Error ? e.message : String(e)
    if (tasks.value.length === 0) {
      tasks.value = mockSchedulerData.tasks
      logs.value = mockSchedulerData.logs
    }
  }
*/
// 修改为:
/*
  } catch (e) {
    console.error('Failed to fetch scheduler data:', e)
    error.value = e instanceof Error ? e.message : String(e)
    if (tasks.value.length === 0) {
      tasks.value = []
      logs.value = []
    }
  }
*/

// 3. 修改 handleRefresh() 的 catch 逻辑
// 找到:
/*
  } catch (e) {
    console.error('Failed to refresh scheduler data:', e)
    tasks.value = mockSchedulerData.tasks
    logs.value = mockSchedulerData.logs
  }
*/
// 修改为:
/*
  } catch (e) {
    console.error('Failed to refresh scheduler data:', e)
    error.value = '刷新失败: ' + (e instanceof Error ? e.message : String(e))
  }
*/
```

- [ ] **Step 2: Run test to verify it passes**

Run: `npm run build`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/views/Scheduler.vue
git commit -m "feat(ui): remove mockSchedulerData from Scheduler"
```

---

### Task 5: 移除 Screening.vue 的 Mock 数据

**Files:**
- Modify: `src/views/Screening.vue`

- [ ] **Step 1: Update component to remove `mockResults`**

```vue
// in src/views/Screening.vue
// 1. 找到并删除 `const mockResults = [ ... ]` (大约第 73-77 行)

// 2. 修改 runScreening() 的 catch 逻辑
// 找到:
/*
  } catch (e) {
    console.error('Screening failed:', e)
    error.value = e instanceof Error ? e.message : String(e)
    if (results.value.length === 0) {
      results.value = mockResults
    }
  }
*/
// 修改为:
/*
  } catch (e) {
    console.error('Screening failed:', e)
    error.value = e instanceof Error ? e.message : String(e)
    results.value = []
  }
*/

// 3. 修改 handleRefresh() 的 catch 逻辑
// 找到:
/*
  } catch (e) {
    console.error('Refresh failed:', e)
    results.value = mockResults
  }
*/
// 修改为:
/*
  } catch (e) {
    console.error('Refresh failed:', e)
    error.value = '刷新失败: ' + (e instanceof Error ? e.message : String(e))
    results.value = []
  }
*/
```

- [ ] **Step 2: Run test to verify it passes**

Run: `npm run build`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/views/Screening.vue
git commit -m "feat(ui): remove mockResults from Screening"
```
