import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

describe('startupSync', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.doUnmock('@tauri-apps/api/core')
    vi.unstubAllEnvs()
    vi.clearAllMocks()
    vi.resetModules()
  })

  it('生产环境首次 ensureStartupSync 会调用 ping 确认引擎存活，并把状态置为 success', async () => {
    const invoke = vi.fn().mockResolvedValue('pong')

    vi.doMock('@tauri-apps/api/core', () => ({ invoke }))
    vi.stubEnv('PROD', true)

    const { ensureStartupSync, getStartupSyncState } = await import('../startupSync')

    await ensureStartupSync()

    expect(invoke).toHaveBeenCalledWith('invoke_engine', {
      method: 'ping',
      params: {},
    })
    expect(getStartupSyncState().status).toBe('success')
  })

  it('同步失败时会把状态置为 error 并返回统一提示', async () => {
    const invoke = vi.fn().mockRejectedValue(new Error('boom'))

    vi.doMock('@tauri-apps/api/core', () => ({ invoke }))
    vi.stubEnv('PROD', true)

    const { ensureStartupSync, getStartupSyncState } = await import('../startupSync')

    await expect(ensureStartupSync()).resolves.toBeUndefined()

    expect(invoke).toHaveBeenCalledWith('invoke_engine', {
      method: 'ping',
      params: {},
    })
    expect(getStartupSyncState()).toEqual({
      status: 'error',
      message: '引擎连接失败，当前显示本地旧数据',
    })
  })

  it('同一轮启动多次调用只会复用同一个同步 promise', async () => {
    const invoke = vi.fn().mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 0)),
    )

    vi.doMock('@tauri-apps/api/core', () => ({ invoke }))
    vi.stubEnv('PROD', true)

    const { ensureStartupSync } = await import('../startupSync')

    const first = ensureStartupSync()
    const second = ensureStartupSync()

    expect(first).toBe(second)

    await Promise.all([first, second])

    expect(invoke).toHaveBeenCalledTimes(1)
  })

  it('非生产环境不会触发 invoke 但状态仍可用', async () => {
    const invoke = vi.fn()

    vi.doMock('@tauri-apps/api/core', () => ({ invoke }))
    vi.stubEnv('PROD', false)

    const { ensureStartupSync, getStartupSyncState } = await import('../startupSync')

    await expect(ensureStartupSync()).resolves.toBeUndefined()

    expect(invoke).not.toHaveBeenCalled()
    expect(getStartupSyncState()).toEqual({ status: 'success' })
  })

  it('setStartupSyncError 可直接将状态置为 error（供引擎启动失败时使用）', async () => {
    const { setStartupSyncError, getStartupSyncState } = await import('../startupSync')

    setStartupSyncError('引擎进程启动失败')

    expect(getStartupSyncState()).toEqual({
      status: 'error',
      message: '引擎进程启动失败',
    })
  })

  it('setStartupSyncError 后 ensureStartupSync 不再发起网络调用', async () => {
    const invoke = vi.fn()

    vi.doMock('@tauri-apps/api/core', () => ({ invoke }))
    vi.stubEnv('PROD', true)

    const { setStartupSyncError, ensureStartupSync, getStartupSyncState } = await import('../startupSync')

    setStartupSyncError('引擎未启动')
    await ensureStartupSync()

    expect(invoke).not.toHaveBeenCalled()
    expect(getStartupSyncState().status).toBe('error')
  })
})
