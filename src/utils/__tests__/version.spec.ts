import { describe, expect, it } from 'vitest'

import packageJson from '../../../package.json'
import packageLockJson from '../../../package-lock.json'
import cargoPackage from '../../../src-tauri/Cargo.toml?raw'
import iconIcoUrl from '../../../src-tauri/icons/icon.ico?url'
import tauriConfig from '../../../src-tauri/tauri.conf.json'

const cargoPackageSection = cargoPackage.match(/\[package\]([\s\S]*?)(\n\[|$)/)?.[1] ?? ''
const cargoVersion = cargoPackageSection.match(/^version\s*=\s*"([^"]+)"/m)?.[1]

describe('版本配置一致性', () => {
  it('package.json、package-lock.json、tauri.conf.json、Cargo.toml 的版本号一致', () => {
    expect(packageJson.version).toBe(tauriConfig.version)
    expect(packageJson.version).toBe(packageLockJson.version)
    expect(packageJson.version).toBe(packageLockJson.packages[''].version)
    expect(packageJson.version).toBe(cargoVersion)
  })

  it('Windows 打包所需的 ico 图标已配置且文件存在', () => {
    expect(tauriConfig.bundle.icon).toContain('icons/icon.ico')
    expect(iconIcoUrl).toContain('icon.ico')
  })
})
