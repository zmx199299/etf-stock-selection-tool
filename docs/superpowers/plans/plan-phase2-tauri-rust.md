# 阶段二：Tauri + Rust 中间层 — 实施计划

> 依赖阶段一完成

## Task 12: Tauri sidecar 配置

- [ ] 将 Python 引擎配置为 Tauri sidecar
- [ ] 配置 `tauri.conf.json` 中的 sidecar 路径
- [ ] 实现 Rust 侧启动/停止 Python 子进程
- [ ] 测试：应用启动时 Python 进程自动启动，关闭时自动终止
- [ ] 提交

## Task 13: JSON-RPC 消息路由

- [ ] Rust 侧实现 JSON-RPC 消息发送/接收（stdin/stdout）
- [ ] 定义 Tauri Command：`sync_data`, `run_analysis`, `get_config`, `set_config`
- [ ] 前端可通过 `invoke("sync_data")` 调用 Python 引擎
- [ ] 测试：前端调用 → Rust → Python → 返回结果
- [ ] 提交

## Task 14: 定时任务调度

- [ ] Rust 侧实现定时任务（基于 tokio cron 或类似方案）
- [ ] 读取配置中的阶段一/阶段二时间
- [ ] 交易日判断逻辑（周末跳过，节假日列表可配置）
- [ ] 阶段二净值重试逻辑（每30分钟，最晚23:00）
- [ ] 测试：定时触发 → 执行分析 → 写入日志
- [ ] 提交

## Task 15: 系统托盘与通知

- [ ] 实现系统托盘图标（最小化到托盘）
- [ ] 分析完成后弹出系统通知
- [ ] 托盘右键菜单：打开主窗口 / 立即运行 / 退出
- [ ] 测试
- [ ] 提交
