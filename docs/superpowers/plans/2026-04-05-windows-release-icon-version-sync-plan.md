# Windows 发布修复与版本统一 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 Windows Tauri 打包缺少 `.ico` 图标的问题，并将前端显示版本、`package.json`、`src-tauri/tauri.conf.json`、`src-tauri/Cargo.toml` 与发布版本统一到 `v0.0.4`。

**Architecture:** 复用现有前端动态读取 `package.json` 版本的做法，不引入新的版本常量源。通过扩展 `src/utils/__tests__/version.spec.ts`，把版本一致性和 Windows `.ico` 资源要求固化为测试约束，然后以最小改动更新配置和图标资源。

**Tech Stack:** Vue 3、Vitest、Tauri 2、Rust、GitHub Actions

---

### Task 1: 扩展版本与图标约束测试

**Files:**
- Modify: `src/utils/__tests__/version.spec.ts`
- Test: `src/utils/__tests__/version.spec.ts`

- [ ] **Step 1: 写失败测试，覆盖 Cargo 版本与 Windows 图标要求**

```ts
import { describe, expect, it } from 'vitest'
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import packageJson from '../../../package.json'
import tauriConfig from '../../../src-tauri/tauri.conf.json'

const cargoTomlPath = resolve(process.cwd(), 'src-tauri/Cargo.toml')
const cargoToml = readFileSync(cargoTomlPath, 'utf-8')
const cargoVersion = cargoToml.match(/^version\s*=\s*"([^"]+)"/m)?.[1]
const iconIcoPath = resolve(process.cwd(), 'src-tauri/icons/icon.ico')

describe('版本配置一致性', () => {
  it('package.json、tauri.conf.json、Cargo.toml 的版本号一致', () => {
    expect(packageJson.version).toBe(tauriConfig.version)
    expect(packageJson.version).toBe(cargoVersion)
  })

  it('Windows 打包所需的 ico 图标已配置且文件存在', () => {
    expect(tauriConfig.bundle.icon).toContain('icons/icon.ico')
    expect(existsSync(iconIcoPath)).toBe(true)
  })
})
```

- [ ] **Step 2: 运行测试，确认先红灯**

Run: `npm test -- src/utils/__tests__/version.spec.ts`

Expected: FAIL

- `packageJson.version` 与 `cargoVersion` 不一致，或
- `tauriConfig.bundle.icon` 不包含 `icons/icon.ico`，或
- `src-tauri/icons/icon.ico` 文件不存在

- [ ] **Step 3: 如测试因正则未匹配 `Cargo.toml` 版本而报错，先修正测试读取方式，再回到红灯**

```ts
const cargoVersionMatch = cargoToml.match(/^version\s*=\s*"([^"]+)"/m)
expect(cargoVersionMatch?.[1]).toBeDefined()
const cargoVersion = cargoVersionMatch?.[1]
```

- [ ] **Step 4: 再次运行测试，确认失败原因变成真实业务缺口**

Run: `npm test -- src/utils/__tests__/version.spec.ts`

Expected: FAIL，且失败信息明确指向版本不一致或 `.ico` 缺失

- [ ] **Step 5: 暂不提交，继续下一任务实现最小修复**


### Task 2: 统一版本到 0.0.4

**Files:**
- Modify: `package.json`
- Modify: `src-tauri/tauri.conf.json`
- Modify: `src-tauri/Cargo.toml`
- Test: `src/views/__tests__/Settings.spec.ts`

- [ ] **Step 1: 更新 `package.json` 版本到 `0.0.4`**

```json
{
  "version": "0.0.4"
}
```

- [ ] **Step 2: 更新 `src-tauri/tauri.conf.json` 版本到 `0.0.4`**

```json
{
  "version": "0.0.4"
}
```

- [ ] **Step 3: 更新 `src-tauri/Cargo.toml` 版本到 `0.0.4`**

```toml
[package]
version = "0.0.4"
```

- [ ] **Step 4: 运行版本测试，确认 Cargo/前端/Tauri 三处版本一致**

Run: `npm test -- src/utils/__tests__/version.spec.ts`

Expected: 版本一致断言通过，但 `.ico` 相关断言仍失败

- [ ] **Step 5: 运行设置页测试，确认前端显示自动跟随为 `v0.0.4 预览版`**

Run: `npm test -- src/views/__tests__/Settings.spec.ts`

Expected: PASS


### Task 3: 补齐 Windows `.ico` 图标并登记到 Tauri 配置

**Files:**
- Create: `src-tauri/icons/icon.ico`
- Modify: `src-tauri/tauri.conf.json`
- Test: `src/utils/__tests__/version.spec.ts`

- [ ] **Step 1: 新增 `src-tauri/icons/icon.ico` 文件**

说明：使用已有应用图标导出的标准 `.ico` 文件，文件名必须是 `icon.ico`，路径必须是 `src-tauri/icons/icon.ico`。

- [ ] **Step 2: 将 `.ico` 文件加入 Tauri `bundle.icon` 列表**

```json
"icon": [
  "icons/32x32.png",
  "icons/128x128.png",
  "icons/256x256.png",
  "icons/512x512.png",
  "icons/icon.png",
  "icons/icon.ico"
]
```

- [ ] **Step 3: 运行版本测试，确认从红灯转绿灯**

Run: `npm test -- src/utils/__tests__/version.spec.ts`

Expected: PASS

- [ ] **Step 4: 如果测试仍失败，检查失败点是否为路径错误而不是格式错误**

Run: `npm test -- src/utils/__tests__/version.spec.ts --reporter=verbose`

Expected: 若失败，应明确指向配置路径或文件缺失；不要在未确认失败原因前继续改 workflow

- [ ] **Step 5: 暂不提交，继续做完整验证**


### Task 4: 运行项目级验证，确认修复未破坏其他栈

**Files:**
- Test: `src/utils/__tests__/version.spec.ts`
- Test: `src/views/__tests__/Settings.spec.ts`
- Verify: `package.json`
- Verify: `src-tauri/tauri.conf.json`
- Verify: `src-tauri/Cargo.toml`

- [ ] **Step 1: 运行与本次变更直接相关的前端测试**

Run: `npm test -- src/utils/__tests__/version.spec.ts src/views/__tests__/Settings.spec.ts`

Expected: PASS

- [ ] **Step 2: 运行前端构建验证**

Run: `npm run build`

Expected: PASS，生成根目录 `dist/`

- [ ] **Step 3: 运行 Rust 类型检查**

Run: `cargo check --manifest-path src-tauri/Cargo.toml`

Expected: PASS

- [ ] **Step 4: 运行 Rust 测试**

Run: `cargo test --manifest-path src-tauri/Cargo.toml -- --test-threads=1`

Expected: PASS

- [ ] **Step 5: 运行 Python 测试**

Run: `pytest src-python/tests/`

Expected: PASS


### Task 5: 发布前人工核对与后续动作边界

**Files:**
- Verify: `docs/superpowers/specs/2026-04-05-windows-release-icon-version-sync-design.md`
- Verify: `.github/workflows/release.yml`

- [ ] **Step 1: 人工核对本次目标发布版本是否为 `v0.0.4`**

核对项：

```text
package.json                -> 0.0.4
src-tauri/tauri.conf.json   -> 0.0.4
src-tauri/Cargo.toml        -> 0.0.4
Settings 页面显示           -> v0.0.4 预览版
发布 tag                    -> v0.0.4
```

- [ ] **Step 2: 确认本次不提前执行发布成功后的日志与清理动作**

```text
仅当 Windows / macOS / Linux 全部发布成功后，才进入：
1. 开发日志更新
2. AI 状态文档更新
3. 软件归档
4. 清理不要的文件
```

- [ ] **Step 3: 如用户要求提交代码，再执行非交互式 git 提交**

Run: `git add package.json src-tauri/tauri.conf.json src-tauri/Cargo.toml src-tauri/icons/icon.ico src/utils/__tests__/version.spec.ts docs/superpowers/specs/2026-04-05-windows-release-icon-version-sync-design.md docs/superpowers/plans/2026-04-05-windows-release-icon-version-sync-plan.md`

Run: `git commit -m "fix: restore windows bundle icon and sync release version"`

Expected: commit 成功

- [ ] **Step 4: 如用户要求发布，再使用 `v0.0.4` 创建并推送 tag**

```bash
git tag v0.0.4
git push origin main
git push origin v0.0.4
```

- [ ] **Step 5: 发布后只在三平台全绿时进入日志与归档阶段**

```text
未确认三平台全绿前，不得宣称“发布成功”。
```
