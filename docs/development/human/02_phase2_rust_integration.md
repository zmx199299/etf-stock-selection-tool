# 第二阶段开发文档：Rust 引擎管理与 IPC 桥接 (Human)

## 概述
第二阶段的重点是建立 Tauri 的中间层 (Rust) 以便与核心 Python 引擎进行通信。Rust 代码的作用是生命周期管理和消息转发，而不是重新实现业务逻辑。

## 引擎启动与管理 (`src-tauri/src/engine.rs`)
- **生命周期**：在 Tauri 启动时，Rust 层会生成一个新的子进程 (`std::process::Command`)。
  - **开发模式**：如果处于开发环境，Rust 会查找项目中的 Python 虚拟环境 (`.venv/bin/python`)，并直接执行 `src-python/main.py`。
  - **生产模式**：一旦我们准备发布，将会执行打包后的单文件可执行二进制（通过 Tauri 的 Sidecar 配置或 PyInstaller 生成的 `binaries/engine`）。
- **通信方式 (IPC)**：通过标准输入输出（stdin/stdout）进行进程间通信。数据格式严格采用 `JSON-RPC 2.0`。
- **状态维护**：Tauri 使用 `AppState` 中的 `Mutex<EngineManager>` 来在不同的命令调用间持久化引擎进程。

## Tauri Commands 暴露
Rust 向前端 Vue 暴露了以下指令 (Commands)：
1. `start_engine`：启动后台的分析计算服务。
2. `stop_engine`：安全关闭分析引擎。
3. `invoke_engine(method, params)`：万能转发接口。前端可以传递任意 method（如 `get_engine_status`, `analyze_etf`），Rust 会将其打包成 JSON-RPC 请求发给 Python，再将 Python 的响应解包传回前端。

## 下一步
接下来将进入前端开发阶段，我们需要通过这些暴露出来的 API，在 Vue 页面中展示系统状态并触发自动分析任务。
