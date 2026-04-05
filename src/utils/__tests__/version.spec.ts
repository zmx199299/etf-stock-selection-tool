import { describe, expect, it } from 'vitest'

import packageJson from '../../../package.json'
import tauriConfig from '../../../src-tauri/tauri.conf.json'

describe('版本配置一致性', () => {
  it('前端 package.json 与 Tauri 配置中的版本号一致', () => {
    expect(packageJson.version).toBe(tauriConfig.version)
  })
})
