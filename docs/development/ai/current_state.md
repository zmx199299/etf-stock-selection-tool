# ETF 智能分析系统 - AI 当前状态指针

**最后更新**: 2026-04-09
**当前版本**: v0.0.16

## 1. 当前阶段

当前阶段为 **v0.0.16 NAV 同步崩溃修复已完成，待推送触发 CI 构建**。修复了 NAV 同步因 NaN 净值导致 `NOT NULL constraint failed` 崩溃的问题。

## 2. 版本发布历史

| 版本 | 核心修复 | 状态 |
|------|----------|------|
| v0.0.5 | 三平台自动发布打通 | 已发布 |
| v0.0.8 | Python 引擎启动崩溃 (import + db.init) | 已发布 |
| v0.0.9 | 五重启动同步修复 | 已发布 |
| v0.0.10 | 生产模式 sidecar 路径修复 | 已发布 |
| v0.0.11 | 多源容错数据爬取 (em/sina 自动切换) | 已发布 |
| v0.0.12 | PyInstaller 打包修复 (--paths + --collect-data) | 已发布 |
| v0.0.13 | Windows 三重修复 (noconsole + py_mini_racer + 早期终止) | 已发布 |
| v0.0.14 | 后台同步触发修复 (has_daily_quotes + 独立数据源 + 日志刷新) | 已发布 |
| v0.0.15 | 三重修复 (WAL并发锁 + em源跳过 + 部分同步重试) | 已发布 |
| v0.0.16 | NAV 同步崩溃修复 (NaN 过滤 + per-fund 容错) | 待发布 |

## 3. 当前已完成内容

### 启动链路修复（v0.0.8 ~ v0.0.16）
- Python 引擎可正确启动（import 修复 + db.init）
- 前端不再触发全量同步（ping 替代 sync_data）
- Rust BufReader 持久化，不丢数据
- SQLite WAL 模式并发安全（后台同步与 RPC 主线程可同时写入）
- 生产模式 sidecar 路径正确定位
- 数据源容错（东方财富/新浪自动切换 + em 连续失败自动跳过）
- PyInstaller 正确打包所有模块和 native 库
- Windows 无终端窗口弹出
- 连续失败早期终止，避免 30 分钟无效重试
- 后台同步覆盖率检测，部分同步失败后自动重试
- NAV 同步正确过滤 NaN 净值 + 单基金失败不崩溃全部

### 页面功能
- Dashboard: 共享基金卡片信号总览，全局配色联动
- FundList: 宽表格页面，搜索/空状态/雪球入口
- Analysis: 九周期切换（分时/日K/5分/60分/120分/周K/月K/季K/年K）
- Scoring: 真实技术评分 + 交易建议
- Settings: 涨跌配色/卡片数量/关于/隐私声明

### 数据层
- `AkshareSource` 多源容错：`_em` + `_sina` 并发/降级，em 连续失败 5 次自动跳过
- `fetch_nav()` 使用 `pd.notna()` 过滤 NaN 净值
- 全量库 1754 只基金（排除货币/固收/债券），`has_market_data` 标记隔离
- `DataSyncPipeline` 完整同步管道 + 连续失败早期终止 + NAV per-fund 容错
- 后台线程自动同步（首次运行或覆盖率<80%时触发 60 天数据同步）
- SQLite WAL 模式启用，多线程并发安全

### 基础设施
- GitHub Actions 三平台构建 (Windows MSI / macOS DMG / Linux DEB+RPM+AppImage)
- PyInstaller 打包含所有 hidden-import + collect-all 依赖
- 全局红多/绿多配色、卡片数量设置
- 测试基线：Python 120 / Frontend 86

## 4. 当前约束

- 色彩方案（红涨绿跌/绿涨红跌）必须用户可配置，不得硬编码
- 继续遵循 Mock 优先原则
- 每次发版必须先同步版本号再推 tag

## 5. 下一步

- 推送 v0.0.16 tag 触发 CI 构建
- 用户 Windows 测试打包应用
- 继续推进业务功能：分钟线按需实时获取、前端真实联动与缓存策略
