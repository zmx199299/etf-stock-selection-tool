import { afterEach, describe, expect, it, vi } from 'vitest'

function createDeferred() {
  let resolve!: () => void
  const promise = new Promise<void>((resolver) => {
    resolve = resolver
  })

  return { promise, resolve }
}

afterEach(() => {
  vi.doUnmock('vue')
  vi.doUnmock('pinia')
  vi.doUnmock('../App.vue')
  vi.doUnmock('../router')
  vi.doUnmock('../router/index')
  vi.doUnmock('../stores/colorMode')
  vi.doUnmock('../utils/startupSync')
  vi.resetModules()
  vi.clearAllMocks()
})

describe('前端测试基线', () => {
  it('可以读写 localStorage', () => {
    localStorage.setItem('smoke-key', 'smoke-value')

    expect(localStorage.getItem('smoke-key')).toBe('smoke-value')
  })

  it('应用启动时会先完成启动同步再执行 mount', async () => {
    vi.resetModules()
    vi.stubEnv('TEST', 'true')

    const startupSync = createDeferred()
    const ensureStartupSync = vi.fn().mockImplementation(() => startupSync.promise)
    const hydrate = vi.fn()
    const mount = vi.fn()
    const use = vi.fn().mockReturnThis()
    const component = vi.fn().mockReturnThis()
    const createApp = vi.fn(() => ({
      use,
      component,
      mount,
    }))
    const createPinia = vi.fn(() => ({ pinia: true }))

    vi.doMock('vue', () => ({
      createApp,
    }))
    vi.doMock('pinia', () => ({
      createPinia,
    }))
    vi.doMock('../App.vue', () => ({
      default: {},
    }))
    vi.doMock('../router', () => ({
      default: { name: 'router' },
    }))
    vi.doMock('../router/index', () => ({
      default: { name: 'router' },
    }))
    vi.doMock('../stores/colorMode', () => ({
      useColorModeStore: vi.fn(() => ({ hydrate })),
    }))
    vi.doMock('../utils/startupSync', () => ({
      ensureStartupSync,
    }))

    const { bootstrap } = await import('../main')
    const bootPromise = bootstrap()
    await Promise.resolve()

    expect(ensureStartupSync).toHaveBeenCalledTimes(1)
    expect(mount).not.toHaveBeenCalled()

    startupSync.resolve()
    await bootPromise

    expect(mount).toHaveBeenCalledWith('#app')
    expect(ensureStartupSync.mock.invocationCallOrder[0]).toBeLessThan(mount.mock.invocationCallOrder[0])
  })
})
