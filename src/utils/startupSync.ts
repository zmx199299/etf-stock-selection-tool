export type StartupSyncState =
  | { status: 'idle' }
  | { status: 'success' }
  | { status: 'error'; message: string }

const startupSyncErrorMessage = '引擎连接失败，当前显示本地旧数据'

let startupSyncState: StartupSyncState = { status: 'idle' }
let startupSyncPromise: Promise<void> | null = null

export function getStartupSyncState(): StartupSyncState {
  return startupSyncState
}

export function setStartupSyncError(message: string): void {
  startupSyncState = { status: 'error', message }
}

export function ensureStartupSync(): Promise<void> {
  if (startupSyncPromise) {
    return startupSyncPromise
  }

  // 如果已经被标记为 error（如引擎启动失败），不再尝试 ping
  if (startupSyncState.status === 'error') {
    startupSyncPromise = Promise.resolve()
    return startupSyncPromise
  }

  startupSyncPromise = (async () => {
    if (!import.meta.env.PROD) {
      startupSyncState = { status: 'success' }
      return
    }

    try {
      const { invoke } = await import('@tauri-apps/api/core')
      // 仅用 ping 确认引擎存活，数据同步由 Python 后台线程自动完成
      await invoke('invoke_engine', {
        method: 'ping',
        params: {},
      })
      startupSyncState = { status: 'success' }
    } catch {
      startupSyncState = {
        status: 'error',
        message: startupSyncErrorMessage,
      }
    }
  })()

  return startupSyncPromise
}
