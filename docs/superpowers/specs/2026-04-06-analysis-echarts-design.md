# Analysis 页面图表真实化设计方案 (2026-04-06)

## 1. 背景与目标
目前 `Analysis.vue` 中使用的图表是依赖 CSS 和 SVG 硬编码写死的 Mock 图表区域，虽然有基础交互，但无法渲染多维度、大量的真实 K 线与分时数据。同时，顶栏的数据（当前价格、涨跌幅、估算策略、风险等）也使用了 mock 数据，并且与后端已提供的 `AnalysisService.get_analysis_data` 数据没有联通。

本方案旨在：
1. 安装并引入 `echarts` 与 `vue-echarts`。
2. 彻底移除前端对 `analysisMock.ts` 的依赖。
3. 替换当前硬编码的图表展示，引入两个专业的 ECharts 组件：
   - 分时图表（展示均线 `avgLinePoints` 和价格线 `linePoints` 以及成交量 `volumes`）。
   - K 线图表（展示 K 线 `candles` 和成交量 `volumes`）。
4. 在用户搜索或点击“共享卡片”传递 `code` 后，通过 Tauri API 发起对真实后端的 `get_analysis_data` 的调用，并驱动上方卡片及下侧图表的全面更新。

## 2. 依赖管理
需要向项目中安装图表库及其 Vue 3 包装器：
```bash
npm install echarts vue-echarts
```
（因为本项目为 Tauri+Vue，安装行为应在执行计划前或由子 agent 执行）

## 3. 前端数据流设计
### 3.1 Vue Store / 组件状态
- **移除** `getAnalysisMockByCode`, `searchAnalysisCandidates` 相关的假数据引入。
- 搜索建议功能：改为调用真实的 `invoke_engine('invoke_engine', { method: 'search_funds', params: { keyword } })` 实现候选列表。
- 获取详情数据：新增 `fetchAnalysisData(code)` 函数，调用真实的 `invoke_engine('invoke_engine', { method: 'get_analysis_data', params: { code } })`。
- 将返回的完整字典存储在 `activeAnalysis` （Ref） 中，并响应式地驱动页面渲染。
- 处理后端返回字段 `snake_case` 到前端使用 `camelCase`（如 `riskLevel`, `stopLoss` 等）的映射适配。

### 3.2 ECharts 封装与挂载
鉴于配置复杂，不建议将所有的 ECharts Option 写在巨大的 Vue 单文件中。
创建单独的适配器文件 `src/utils/chartAdapter.ts`：
- `buildIntradayOption(periodData, colorMode)`：生成分时图的 ECharts option，含两条折线和底部成交量柱状图，支持深浅色模式（红涨绿跌/绿涨红跌）自适应。
- `buildKLineOption(periodData, colorMode)`：生成 K线图（蜡烛图）的 option，包含蜡烛图层和底部成交量层。
在 `Analysis.vue` 的模板中：
```vue
<v-chart class="h-full w-full" :option="chartOption" autoresize />
```
其中 `chartOption` 是一个 `computed` 计算属性，依赖于 `activePeriod` 和 `colorMode` 进行重新计算。

## 4. 后端支持情况
`AnalysisService.get_analysis_data(code)` 已经完整实现了对于 `intraday`（分时）、`day/m5/m60/m120/week/month/quarter/year` 周期的历史行情读取，并且如果遇到非日线类分钟级数据，自带 fallback 从 `akshare` 联网获取补齐能力。
后端已经支持了我们本次前端 UI 所需要的绝大部分字段（`price`, `change`, `market`, `iopv`, `premium`, `riskLevel`，以及各周期下包含的 `candles`, `timeAxis`, `linePoints`, `volumes`）。
在本次改造中，我们主要集中力量在前端的重构和数据对接，后端无需大幅改动（除非发现个别字段格式有误需微调）。

## 5. 样式兼容
原版的 CSS 和 SVG 的 `analysis-chart-mock` 及其内联的 Hitbox、Tooltip 将被安全删除，换用 ECharts 自带的强大的 `tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } }` 组件。

## 6. 测试驱动 (TDD)
- **Vitest (前端)**：
  - 更新 `Analysis.spec.ts`：
  - 断言能够正确调用 `invoke_engine` 来搜索。
  - 断言选择 code 时，能够调用 `get_analysis_data` 并获取到数据。
  - 由于 ECharts 使用 Canvas/SVG 进行绘制，不属于标准的 DOM 测试范畴，因此主要测试 `v-chart` 的 `:option` 绑定数据是否被正确计算，而不是图表内的点或线。
