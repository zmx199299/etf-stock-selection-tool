# 系统设置页设计文档

> 日期：2026-04-04
> 状态：用户确认通过

## 概述

为 FUNDFLOW 应用实现第四个页面「系统设置」（路由 `/settings`），将散落在各页面的可配置功能统一收纳，同时展示应用基本信息和法律声明。

## 页面定位

- 路由：`/settings`（已存在）
- 侧边栏导航：`⚙️ 系统设置`（已存在）
- 当前状态：空壳占位页，仅一行"页面开发中..."文字
- 目标：替换为完整的设置页面

## 布局方案

**单列卡片流**：沿用统一的 page shell（`bg-slate-50` + `p-4 md:p-6`），三张卡片从上到下排列。

卡片顺序：
1. Topbar — 标题 + 副标题（和其他页面一致的顶栏样式）
2. 卡片一：显示偏好
3. 卡片二：关于
4. 卡片三：隐私与免责声明

## 功能模块详细设计

### 卡片一：显示偏好

#### 1.1 涨跌配色（红多/绿多）

- 交互方式：和 Page 2、Page 3 顶栏相同的按钮切换组（`红多` / `绿多`）
- 数据源：复用已有的 `useColorModeStore()`（Pinia store）
- 存储：`localStorage` key `market-color-mode`
- 默认值：`cn`（红多）
- 联动：切换后全局所有页面即时响应
- **原页面按钮保留**：Page 2 和 Page 3 顶栏的快捷切换按钮不移除，状态通过 Pinia store 全局同步
- 辅助说明文字："切换后所有页面的涨跌颜色同步生效。也可以在「全量基金」和「技术分析」页面顶栏快捷切换。"

#### 1.2 首页/分析入口卡片数量

- 交互方式：预设档位下拉
- 档位选项：`6 支` / `8 支` / `10 支（默认）` / `12 支`
- 数据源：新建 Pinia store `useDisplaySettingsStore()`
- 存储：`localStorage` key `display-card-count`
- 默认值：`10`
- 联动改造：
  - `Dashboard.vue` 的 `fetchSignals()` 中 `.slice(0, 10)` 改为读取 store 的 `cardCount`
  - `dashboardSignals.ts` 的 `getAnalysisEntryCards()` 中 `.slice(0, 10)` 改为接受 `count` 参数
- 辅助说明文字："同时控制「今日行情」信号卡片和「技术分析」入口卡片的显示数量"

### 卡片二：关于

纯展示，无交互，无 store。数据以常量对象写在 `Settings.vue` 中。

| 字段 | 值 |
|------|------|
| 软件名称 | FUNDFLOW（蓝色加粗斜体，和侧边栏 logo 一致） |
| 版本 | v0.0.1 预览版 |
| 开源协议 | GPLv3 |
| 联网行为 | 仅抓取行情 + 跳转雪球 |

布局：2x2 网格，每个字段一个 `bg-slate-50` 圆角小卡片。

### 卡片三：隐私与免责声明

纯展示，无交互，无 store。文案以常量写在 `Settings.vue` 中。分三段，每段前有彩色圆点标识：

#### 隐私保护（蓝色圆点）
> 本软件为本地运行的单机工具，不收集、上传或存储任何用户个人信息。
> 联网行为仅限于：获取市场行情数据、跳转至雪球网站查看基金详情。除此之外不与任何外部服务器通信。

#### 数据安全（黄色圆点，警告色文字）
> 本软件仍处于早期开发阶段（预览版），开发者无法对数据的安全性和真实性做出保证。所有行情数据仅供参考，请用户自行核实。

#### 投资风险（红色圆点，红色文字）
> 投资有风险，入市需谨慎。本软件提供的所有分析结论、策略建议仅作为辅助参考，不构成任何投资建议。开发者不对任何投资决策及其结果承担责任，用户需风险自担。

## 新增文件

| 文件 | 用途 |
|------|------|
| `src/stores/displaySettings.ts` | 显示设置 Pinia store（cardCount） |
| `src/stores/__tests__/displaySettings.spec.ts` | store 单元测试 |
| `src/views/__tests__/Settings.spec.ts` | Settings 页面单元测试 |

## 修改文件

| 文件 | 改动 |
|------|------|
| `src/views/Settings.vue` | 替换空壳为完整设置页 |
| `src/views/Dashboard.vue` | `fetchSignals()` 中 `.slice(0, 10)` 改为读取 `displaySettings.cardCount`；`onMounted` 增加 `displaySettings.hydrate()` |
| `src/utils/dashboardSignals.ts` | `getAnalysisEntryCards()` 增加 `count` 参数替代硬编码 10 |
| `src/views/Analysis.vue` | 调用 `getAnalysisEntryCards()` 时传入 `displaySettings.cardCount`；`onMounted` 增加 `displaySettings.hydrate()` |

## 不修改的部分

- Page 2（FundList）和 Page 3（Analysis）顶栏的红多/绿多按钮：保留不动
- 路由配置：`/settings` 路由已存在，无需改动
- 侧边栏导航：`⚙️ 系统设置` 入口已存在，无需改动

## 数据流

```
Settings.vue
  ├─ useColorModeStore() (已有)
  │     ├─ mode: 'cn' | 'intl'
  │     ├─ setMode() → localStorage 'market-color-mode'
  │     └─ hydrate() ← localStorage
  │
  └─ useDisplaySettingsStore() (新建)
        ├─ cardCount: number (默认 10)
        ├─ setCardCount(n) → localStorage 'display-card-count'
        └─ hydrate() ← localStorage

Dashboard.vue ──读取──→ displaySettings.cardCount → signals.slice(0, cardCount)
Analysis.vue  ──读取──→ displaySettings.cardCount → getAnalysisEntryCards(code, cards, cardCount)
```

## hydrate 时机

`displaySettings.hydrate()` 在以下页面的 `onMounted` 中调用（和 `colorMode.hydrate()` 模式一致）：
- `Settings.vue` — 设置页自身需要显示当前值
- `Dashboard.vue` — 读取 cardCount 控制信号卡片数量
- `Analysis.vue` — 读取 cardCount 控制入口卡片数量

## 存储

所有设置项统一使用 `localStorage`，和现有 `colorMode` store 保持一致。

| key | 值类型 | 默认值 |
|-----|--------|--------|
| `market-color-mode` | `'cn'` \| `'intl'` | `'cn'` |
| `display-card-count` | `'6'` \| `'8'` \| `'10'` \| `'12'` | `'10'` |

## 测试策略

### displaySettings store 测试
- 默认值为 10
- `setCardCount()` 正确写入 localStorage
- `hydrate()` 正确从 localStorage 读取
- 无效值回退到默认值 10

### Settings.vue 页面测试
- page shell 渲染（`data-test="settings-shell"`）
- 显示偏好卡片渲染，红多/绿多切换功能正常
- 卡片数量下拉渲染，切换后 store 更新
- 关于卡片四个信息字段正确显示
- 隐私与免责声明三段文字正确渲染

### 联动测试
- Dashboard 读取 cardCount 控制显示数量
- Analysis 入口卡片读取 cardCount 控制显示数量

## data-test 属性规划

| 属性 | 元素 |
|------|------|
| `settings-shell` | 页面最外层 section |
| `settings-topbar` | 顶栏 |
| `settings-card-display` | 显示偏好卡片 |
| `settings-mode-cn` | 红多按钮 |
| `settings-mode-intl` | 绿多按钮 |
| `settings-card-count` | 卡片数量下拉 |
| `settings-card-about` | 关于卡片 |
| `settings-card-disclaimer` | 隐私与免责声明卡片 |
