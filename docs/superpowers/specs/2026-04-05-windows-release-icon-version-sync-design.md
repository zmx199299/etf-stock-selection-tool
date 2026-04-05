# Windows 发布修复与版本统一设计

## 背景

当前 GitHub Release 流程中，Linux 与 macOS 安装包已经可以产出，但 Windows `msi` 打包失败。结合现有工作流配置、Tauri 配置和图标目录现状，当前直接根因是 `src-tauri/icons/icon.ico` 缺失，且 `src-tauri/tauri.conf.json` 的 `bundle.icon` 未显式包含 `.ico` 文件。

同时，发布过程还有一个必须固化的规则：每次推送发布版本时，前端系统设置页显示版本、`package.json`、`src-tauri/tauri.conf.json`、`src-tauri/Cargo.toml` 以及 GitHub tag 必须保持一致，不能再只修改部分配置。

本次目标是在最小改动前提下修复 Windows 打包，并把版本同步约束写入测试，避免后续再次漏改。

## 目标

1. 修复 Windows 发布流程中因缺少 `.ico` 图标导致的 Tauri 打包失败。
2. 将本次发布版本统一提升到 `v0.0.4`。
3. 保证前端系统设置页显示 `v0.0.4 预览版`，并与配置文件版本保持一致。
4. 用自动化测试约束版本配置和 Windows 图标配置，降低再次回归的风险。

## 非目标

1. 不在本次处理中重构整个 release workflow。
2. 不在本次处理中清理所有重复图标文件或做 UI 改版。
3. 不在全部平台发布成功前提前写“发布成功”日志、归档软件或清理文件。

## 现状与根因

### Windows 打包失败

- `src-tauri/icons/` 目前存在多个 `.png` 图标文件。
- `src-tauri/icons/icon.ico` 当前不存在。
- `src-tauri/tauri.conf.json` 的 `bundle.icon` 当前仅包含 PNG 文件。
- Windows 打包阶段需要 `.ico` 资源，当前资源不完整，因此 bundler 失败。

### 版本同步风险

- 当前前端系统设置页通过 `package.json` 动态显示版本，显示格式为 `v${packageJson.version} 预览版`。
- 现有测试仅校验 `package.json` 与 `tauri.conf.json` 版本一致。
- `Cargo.toml` 尚未被纳入一致性测试。
- 发布 tag 与前端显示版本之间目前仍依赖人工同步，缺少显式检查。

## 方案比较

### 方案 A：最小修复并补测试（推荐）

做法：

1. 新增 `src-tauri/icons/icon.ico`。
2. 在 `src-tauri/tauri.conf.json` 的 `bundle.icon` 中加入 `icons/icon.ico`。
3. 将 `package.json`、`src-tauri/tauri.conf.json`、`src-tauri/Cargo.toml` 统一改为 `0.0.4`。
4. 扩展测试，校验三处版本一致，并校验 `bundle.icon` 包含 `icons/icon.ico`。

优点：

- 改动最小，最符合当前“先把 Windows 发布补通”的目标。
- 风险可控，不影响现有 Linux/macOS 已经跑通的主流程。
- 可以把“每次推送都同步版本号”的规则沉淀为测试约束。

缺点：

- 仍保留图标目录中一些重复命名文件，目录整洁性不是最优。

### 方案 B：补图标并顺手整理图标目录

做法：在方案 A 基础上，统一整理 `src-tauri/icons/`，移除旁路或重复命名资源。

优点：

- 图标目录更干净，长期维护更清晰。

缺点：

- 改动范围扩大，容易把当前“发布修复”变成“资源整理”，不利于快速止血。

### 方案 C：修改工作流绕开 Windows bundle

做法：暂时跳过 Windows `msi` 产物，仅保留编译或其他验证。

优点：

- 可以暂时避免当前失败点。

缺点：

- 不满足当前发布目标，不能视为完整修复。

## 最终设计

采用方案 A。

### 配置与资源变更

1. 新增 `src-tauri/icons/icon.ico`，作为 Windows bundler 所需资源。
2. 修改 `src-tauri/tauri.conf.json`：
   - `version` 从 `0.0.1` 改为 `0.0.4`
   - `bundle.icon` 增加 `icons/icon.ico`
3. 修改 `package.json`：`version` 从 `0.0.1` 改为 `0.0.4`
4. 修改 `src-tauri/Cargo.toml`：`version` 从 `0.0.1` 改为 `0.0.4`

### 前端版本显示

前端设置页继续保持当前实现方式，即直接从 `package.json` 读取版本号，显示为：

`v${packageJson.version} 预览版`

这样在 `package.json` 更新为 `0.0.4` 后，界面自动显示 `v0.0.4 预览版`，不需要额外引入第二套版本常量。

### 测试设计

按照 TDD 执行，先补失败测试，再做实现。

新增或扩展现有前端测试，覆盖以下约束：

1. `package.json`、`src-tauri/tauri.conf.json`、`src-tauri/Cargo.toml` 的版本号一致。
2. `src-tauri/tauri.conf.json` 的 `bundle.icon` 包含 `icons/icon.ico`。
3. 系统设置页显示文本与 `package.json.version` 保持一致，即 `v0.0.4 预览版`。

其中第 3 条当前已存在动态断言，只需要在统一版本后重新通过；第 1 条需要扩展测试覆盖 `Cargo.toml`；第 2 条需要新增断言。

### 验证方式

完成修改后，执行项目既有验证命令：

1. `npm test -- src/utils/__tests__/version.spec.ts src/views/__tests__/Settings.spec.ts`
2. `npm run build`
3. `cargo check --manifest-path src-tauri/Cargo.toml`
4. `cargo test --manifest-path src-tauri/Cargo.toml -- --test-threads=1`
5. `pytest src-python/tests/`

如果本地验证通过，再进入提交、推送和新的 GitHub tag 发布。

## 风险与控制

1. `.ico` 文件若格式不正确，Windows bundler 仍可能失败。
   - 控制：使用标准 `.ico` 文件并在发布前先做本地配置校验与常规构建验证。
2. 版本改动若只改部分文件，会再次造成界面与发布版本不一致。
   - 控制：把三处配置文件的一致性写进测试。
3. GitHub tag 若没有按 `v0.0.4` 推送，仍会出现“配置版本正确但发布标签不一致”。
   - 控制：本次执行时明确采用 `v0.0.4` 作为发布 tag，并在提交/发布步骤中按该版本推进。

## 实施边界

本次只处理 Windows 发布修复与版本统一，不处理发布成功后的日志补写、软件归档和文件清理。这些动作必须等三平台发布全部成功后再进行。
