# Phase 3 Documentation: Frontend Vue & Visualization (AI Context)

> 历史快照：本文记录的是早期 Phase 3 阶段状态，**不是当前项目真实状态**。继续开发时请优先读取 `docs/development/ai/current_state.md`。

## File Structure & Current State
- `src/layouts/MainLayout.vue`: Global layout with sidebar and RouterView
- `src/views/Dashboard.vue`: Overview page with stats grid and mock signals table
- `src/views/Screening.vue`: Pattern screening with checkboxes and result cards
- `src/views/Scoring.vue`: Fund analysis with score breakdown, circle chart, and trade advice
- `src/views/Config.vue`: Trading configuration form with budget, fees, thresholds, and cost preview
- `src/views/Scheduler.vue`: Task scheduler with task list and execution logs
- `src/router/index.ts`: Vue Router setup with nested routes under MainLayout
- `src/vite-env.d.ts`: TypeScript shim for .vue files

## Current Implementation Status
- All pages are complete with **Mock Data Only** (no real Tauri IPC integration yet)
- CSS uses Tailwind-inspired custom classes (no Tailwind installed yet, but structure matches Tailwind semantics)
- No ECharts integration yet - chart placeholder exists in Scoring.vue
- No calls to `@tauri-apps/api` yet

## Next Tasks
1. **Integrate Tauri IPC**: Replace mock data with `invoke()` calls to Rust commands (`invoke_engine`, `start_engine`, `stop_engine`)
2. **Integrate ECharts**: Add `echarts` and `vue-echarts` to render candlestick charts in Scoring.vue
3. **Error Handling**: Add proper error states and loading states for all async operations
4. **Data Persistence**: Connect Config.vue to local storage or Rust config management

## Key Technical Decisions
- Component structure: `<script setup lang="ts">` for all SFCs
- State management: Simple `ref()`/`computed()` for now; consider Pinia if state becomes complex
- Styling approach: Scoped CSS per component for isolation
