# ETF 智能分析系统 - AI 当前状态指针

**最后更新**: 2026-04-01 晚 (UTC+8)

## 1. 当前阶段

项目已进入 **UI 全面重构阶段**。
基于用户的极简 HTML 原型，已经 100% 对齐了**全局布局 (MainLayout)** 和**首页 (Dashboard 瀑布流)**。

## 2. 核心架构约束回顾

- 前端：Vite + Vue 3 + Tailwind CSS v4 + Tauri 2
- 后端：Python (JSON-RPC) + Rust (中间层管理)
- **TDD 原则**：在处理跨栈或数据变更时严格遵循红绿重构。
- **UI 原则**：绝不“画蛇添足”。用户提供 HTML/CSS 样例时，应 100% 逐字复制其 DOM 和 class，只做必要的 Vue `v-for` 改造。必须优先用 mock 数据打样确认。

## 3. 已完成里程碑

- Python 引擎开发与验证。
- Rust IPC 桥接层。
- Tailwind CSS v4 集成完毕。
- 路由结构简化完成（`/`, `/funds`, `/analysis`, `/settings`）。
- **Dashboard 首页视觉原型100%还原完成**。
- **全局市场配色基础设施完成**：已提供 `colorMode` Pinia store、localStorage 持久化和方向颜色映射工具。

## 4. 下一步行动 (Next Actions)

**下一步首要任务：**
在已完成的全局配色基础设施上，继续推进设置页接入与页面级颜色消费，但需严格按用户确认顺序执行，不得提前改动未授权页面。

*注意：不要擅自对后端数据接口进行更改，直到所有页面的前端 UI（Mock 状态）均被用户确认。*
