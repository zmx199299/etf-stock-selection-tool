# Plan: 修复启动同步失败 + 按需自动抓取数据

## 问题背景

用户下载并运行 `v0.0.7` 安装包后，应用显示"启动同步失败，请注意核对当前数据状态"。经代码分析，发现以下问题：

1. **引擎未启动**：前端代码直接调用 `invoke_engine` 执行 `sync_data`，但从未调用 `start_engine` 启动 Python 引擎进程
2. **首次同步数据量过大**：当前实现会抓取所有基金的全部历史行情（从1990年至今），导致首次启动极慢
3. **用户期望**：首次启动快速看到近期数据，切换到技术分析页面时按需抓取完整历史数据

## 解决方案

### 核心策略

- **启动后**：自动抓取所有基金的**最近60个交易日**日线数据（后台进行）
- **切换到技术分析页时**：先抓取该基金的分钟线（1分线5天 + 5分线 + 60分线），再抓取全部历史日线
- **完全自动**：用户无感知，不需要手动操作

### 修改点概览

| 层级 | 文件 | 修改内容 |
|------|------|---------|
| 前端 | `src/main.ts` | 添加 `start_engine` 调用 |
| 后端 | `src-python/main.py` | 首次同步改为最近60天 |
| 后端 | `src-python/engine/sync.py` | 添加 `sync_fund_complete()` 方法 |
| 后端 | `src-python/engine/data/akshare_source.py` | 支持按日期范围抓取分钟线 |
| 后端 | `src-python/engine/server.py` | 注册新方法 `sync_fund_complete` |
| 前端 | `src/views/Analysis.vue` | 进入详情页时触发完整数据同步 |

---

## 详细实施步骤（TDD流程）

### Step 1: 修复启动引擎

#### RED - 编写测试

创建 `src/test/engineStartup.spec.ts`：

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { invoke } from '@tauri-apps/api/core'

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn()
}))

describe('引擎启动测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应用启动时应调用 start_engine 启动 Python 引擎', async () => {
    vi.mocked(invoke).mockResolvedValue('Engine started')
    
    // 导入并执行 bootstrap
    const { bootstrap } = await import('../main')
    await bootstrap()
    
    // 验证 invoke 被调用时传入了 'start_engine'
    expect(invoke).toHaveBeenCalledWith('start_engine')
  })

  it('如果引擎启动失败，不应阻塞应用启动', async () => {
    vi.mocked(invoke).mockRejectedValue(new Error('Engine failed to start'))
    
    // 验证启动逻辑不会抛出未捕获的异常
    const { bootstrap } = await import('../main')
    await expect(bootstrap()).resolves.not.toThrow()
  })
})
```

运行测试：
```bash
npm run test src/test/engineStartup.spec.ts -- --run
```

预期：测试失败（因为没有实现 start_engine 调用）

#### GREEN - 编写实现

修改 `src/main.ts`：

```typescript
export async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)
  useColorModeStore(pinia).hydrate()
  app.use(router)
  app.component('v-chart', ECharts)

  // 先启动 Python 引擎
  try {
    await invoke('start_engine')
  } catch (e) {
    console.error('Failed to start engine:', e)
  }

  await ensureStartupSync()

  app.mount('#app')
}
```

运行测试：
```bash
npm run test src/test/engineStartup.spec.ts -- --run
```

预期：测试通过

#### REFACTOR（如需要）

如果代码需要优化，在测试全绿的前提下重构。

---

### Step 2: 修改首次同步为最近60天

#### RED - 编写测试

创建 `src-python/tests/test_sync_limit_days.py`：

```python
import pytest
from unittest.mock import Mock
from engine.sync import DataSyncPipeline

def test_sync_all_with_limit_days():
    db = Mock()
    source = Mock()
    pipeline = DataSyncPipeline(db, source)
    
    pipeline.sync_fund_list = Mock(return_value=10)
    pipeline.sync_daily_quotes_for_all = Mock(return_value=1000)
    pipeline.sync_nav_for_all = Mock(return_value=50)
    
    result = pipeline.sync_all(limit_days=60)
    
    pipeline.sync_daily_quotes_for_all.assert_called_once_with(limit_days=60)
    assert result == {"funds_synced": 10, "quotes_synced": 1000, "nav_updated": 50}
```

运行测试：
```bash
pytest src-python/tests/test_sync_limit_days.py -v
```

预期：测试失败

#### GREEN - 编写实现

修改 `src-python/engine/sync.py`，添加 `limit_days` 参数。

---

### Step 3: 实现按需抓取完整数据

创建 `src-python/tests/test_sync_fund_complete.py` 编写测试。

---

### Step 4: 前端触发完整数据同步

修改 `src/views/Analysis.vue`，在 `fetchAnalysisData` 中先调用 `sync_fund_complete`。

---

## 测试验证

1. 全量测试通过
2. 开发环境测试
3. 打包测试
4. 增量同步验证
