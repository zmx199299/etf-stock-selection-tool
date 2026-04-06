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
