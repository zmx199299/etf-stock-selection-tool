# 阶段四：打包与文档 — 实施计划

> 依赖阶段三完成

## Task 22: Python 引擎打包为独立二进制

- [ ] 使用 PyInstaller 将 Python 引擎打包为单文件二进制
- [ ] 配置 Tauri sidecar 指向打包后的二进制
- [ ] 测试：打包后的二进制可独立运行 JSON-RPC
- [ ] 跨平台测试（Linux / Windows / macOS）
- [ ] 提交

## Task 23: Tauri 应用打包

- [ ] 配置 `tauri.conf.json` 的打包参数（应用名、图标、版本）
- [ ] `npm run tauri build` 生成安装包
- [ ] Linux: .deb / .AppImage
- [ ] Windows: .msi / .exe
- [ ] macOS: .dmg
- [ ] 测试：安装包可正常安装和运行
- [ ] 提交

## Task 24: 编写文档

- [ ] 用户使用手册 (`docs/user-guide.md`)
- [ ] 指标说明文档 (`docs/indicators.md`)
- [ ] 开发文档 (`docs/developer-guide.md`)
- [ ] API 接口文档 (`docs/api-reference.md`)
- [ ] 提交
