# 预构建数据库生成器设计

日期: 2026-04-09

## 背景

用户下载安装 ETF Analyzer 后首次启动需要等待后台同步（60天日线，~30分钟），体验不佳。
需要提供一个预构建数据库供用户下载，以及一个可独立运行的生成脚本用于持续维护更新。

## 决策记录

| 问题 | 决策 |
|---|---|
| 数据库用途 | 独立发布包 — 作为 GitHub Release 附件供用户下载 |
| 数据范围 | 全量历史日线 + NAV（不含分钟线） |
| 脚本基础 | 基于 DataSyncPipeline + AkshareSource 重写（多源容错） |

## 设计

### 1. 脚本架构

**文件:** `src-python/sync_all.py`（重写现有文件）

**核心逻辑:**
```
初始化 Database(输出路径) + AkshareSource() + DataSyncPipeline(db, source)
  → pipeline.sync_all(limit_days=None)  # 全量历史日线 + NAV
  → 打印统计摘要
```

**命令行接口:**
```bash
# 默认输出到 data/etf_analyzer.db
.venv/bin/python src-python/sync_all.py

# 自定义输出路径
.venv/bin/python src-python/sync_all.py --output /path/to/output.db
```

### 2. 改动范围

| 文件 | 动作 | 说明 |
|---|---|---|
| `src-python/sync_all.py` | **重写** | 删除对 seed_sync 的依赖，改用 DataSyncPipeline |
| `src-python/engine/seed_sync.py` | **保留** | 不删除（其他模块可能引用），但 sync_all.py 不再使用 |
| `DataSyncPipeline` / `AkshareSource` / `Database` | **不改** | 已有代码零修改 |

### 3. 产出物

运行脚本后在指定目录生成 `etf_analyzer.db`，包含：
- `fund_info`: ~1700+ 只 ETF/LOF（排除货币/债券）
- `daily_quote`: 每只基金全量历史日线（sina 源，em 自动跳过）
- `fund_nav_history`: 每只基金的 NAV 历史
- 其他表（config, screening_result 等）: 空表，schema 完整

### 4. 测试策略

新增 `src-python/tests/test_sync_all.py`：
- Mock AkshareSource 和 DataSyncPipeline，验证脚本流程
- 验证：创建目录、初始化 DB、调用 sync_all(limit_days=None)、关闭 DB、打印统计
- 不做真实网络请求的集成测试（手动运行验证）

### 5. 发布流程

1. 本地运行 `sync_all.py` 生成 DB
2. 将 DB 文件作为 GitHub Release 附件上传
3. 用户下载后放入 `~/.etf-analyzer/` 目录即可使用
