# 预构建数据库生成器设计

日期: 2026-04-09

## 背景

用户下载安装 ETF Analyzer 后首次启动需要等待后台同步（60天日线，~30分钟），体验不佳。
需要提供一个预构建数据库供用户下载，以及一个 GitHub Actions 每日自动构建流水线。

## 决策记录

| 问题 | 决策 |
|---|---|
| 数据库用途 | 独立发布包 — 作为 GitHub Release 附件供用户下载 |
| 数据范围 | 全量历史日线 + NAV（不含分钟线） |
| 脚本基础 | 基于 DataSyncPipeline + AkshareSource 重写（多源容错） |
| 发布方式 | 固定 Release（tag: `database-latest`），每天覆盖更新附件 |
| 自动构建 | GitHub Actions cron 每天北京时间 ~6:00（UTC 22:00）自动运行 |

## 设计

### 1. 脚本架构

**文件:** `src-python/sync_all.py`（重写现有文件）

**核心逻辑:**
```
初始化 Database(输出路径) + AkshareSource() + DataSyncPipeline(db, source)
  → pipeline.sync_all(limit_days=None)  # 全量历史日线 + NAV
  → 打印统计摘要（基金数、日线条数、NAV条数、耗时、DB大小）
```

**命令行接口:**
```bash
# 默认输出到 data/etf_analyzer.db
.venv/bin/python src-python/sync_all.py

# 自定义输出路径
.venv/bin/python src-python/sync_all.py --output /path/to/output.db
```

### 2. GitHub Actions 每日构建

**文件:** `.github/workflows/daily-db.yml`

**触发条件:**
- `schedule`: cron `0 22 * * *`（UTC 22:00 = 北京时间 06:00，交易日开盘前）
- `workflow_dispatch`: 支持手动触发

**流程:**
1. checkout 代码
2. 安装 Python 3.13 + requirements.txt
3. 运行 `python src-python/sync_all.py --output data/etf_analyzer.db`
4. gzip 压缩：`etf_analyzer_YYYYMMDD.db.gz`
5. 创建或更新固定 Release（tag: `database-latest`），覆盖附件
6. Release body 标注生成日期和数据统计

**用户下载链接（始终不变）:**
`https://github.com/<owner>/<repo>/releases/tag/database-latest`

**资源预估:**
- 运行时间: ~30-60 分钟（sina 源 ~1700 只基金全量日线）
- DB 大小: ~100-200MB raw, ~30-60MB gzip
- GitHub Actions 6 小时时限，充足

### 3. 改动范围

| 文件 | 动作 | 说明 |
|---|---|---|
| `src-python/sync_all.py` | **重写** | 删除对 seed_sync 的依赖，改用 DataSyncPipeline |
| `.github/workflows/daily-db.yml` | **新增** | 每日 cron 构建 + Release 发布 |
| `src-python/engine/seed_sync.py` | **保留** | 不删除，但 sync_all.py 不再使用 |
| `DataSyncPipeline` / `AkshareSource` / `Database` | **不改** | 已有代码零修改 |

### 4. 产出物

运行脚本后生成 `etf_analyzer.db`，包含：
- `fund_info`: ~1700+ 只 ETF/LOF（排除货币/债券）
- `daily_quote`: 每只基金全量历史日线（sina 源，em 自动跳过）
- `fund_nav_history`: 每只基金的 NAV 历史
- 其他表（config, screening_result 等）: 空表，schema 完整

### 5. 测试策略

新增 `src-python/tests/test_sync_all.py`：
- Mock AkshareSource 和 DataSyncPipeline，验证脚本流程
- 验证：参数解析、创建目录、初始化 DB、调用 sync_all(limit_days=None)、关闭 DB、打印统计
- 不做真实网络请求的集成测试（手动运行 + CI 每日验证）

### 6. 用户使用流程

1. 访问 Release 页面 `database-latest`
2. 下载 `etf_analyzer_YYYYMMDD.db.gz`
3. 解压后放入 `~/.etf-analyzer/etf_analyzer.db`
4. 启动应用，数据覆盖率 >80%，后台同步自动跳过
