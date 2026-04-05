export type StartupSyncState =
  | { status: 'idle' }
  | { status: 'success' }
  | { status: 'error'; message: string }

const startupSyncErrorMessage = '同步失败，当前显示本地旧数据'

let startupSyncState: StartupSyncState = { status: 'idle' }
let startupSyncPromise: Promise<void> | null = null

export function getStartupSyncState(): StartupSyncState {
  return startupSyncState
}

export function ensureStartupSync(): Promise<void> {
  if (startupSyncPromise) {
    return startupSyncPromise
  }

  startupSyncPromise = (async () => {
    if (!import.meta.env.PROD) {
      startupSyncState = { status: 'success' }
      return
    }

    try {
      const { invoke } = await import('@tauri-apps/api/core')
      await invoke('invoke_engine', {
        method: 'sync_data',
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
