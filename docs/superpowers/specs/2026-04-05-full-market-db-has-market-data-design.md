# 全量库严格全量 + 标记隔离 设计规格

> **目标**：将数据库初始化从"单只失败即中断"升级为"严格全量入库 + 无场内交易基金标记隔离"，确保 1753 只全量 ETF+LOF 均入库，其中约 22 只无场内交易行情的 LOF 通过 `has_market_data=0` 标记隔离，不污染 `daily_quote` 业务语义。

**最后更新**: 2026-04-05

---

## 1. 背景与问题定义

### 1.1 当前问题

`sync_all.py` 在全量导入场内 ETF+LOF 时，遇到约 22 只 LOF 无法从新浪获取历史行情数据，脚本抛出 `RuntimeError` 并中断导入。

### 1.2 根因

这 22 只 LOF 在新浪分类页（`fund_etf_category_sina('LOF基金')`）中 `最新价=0.0`、`成交量=0`，说明它们当前**没有场内交易活动**（可能是暂停上市、流动性枯竭或退市状态）。但它们的净值数据正常（最新净值日期到 2026-04-03），基金本身仍然活跃。

### 1.3 失败样本（22 只）

```
160137, 160420, 160516, 160634, 160636, 161628, 161721, 161723,
162107, 163209, 164401, 164402, 164818, 164905, 164908, 165310,
165312, 165523, 165524, 165526, 166802, 167503
```

### 1.4 用户要求

- 严格全量：所有 1753 只基金必须入库
- 不伪造数据：不能用净值替代市场日线
- 不中断导入：单只基金缺失行情不应阻止整体导入

---

## 2. 设计方案

### 2.1 核心思路

在 `fund_info` 表中新增 `has_market_data` 字段，用于标记基金是否有真实场内交易行情：

- `has_market_data=1`：有场内交易行情（正常 ETF/LOF）
- `has_market_data=0`：无场内交易行情（当前 22 只 LOF）

导入流程改为：
1. 全量 `fund_info` 入库（含 `has_market_data` 标记）
2. 仅对 `has_market_data=1` 的基金拉取历史日线
3. 全量基金回填最新净值

### 2.2 数据流

```
新浪 ETF 分类页 (fund_etf_category_sina)
    → etf_rows（含成交量、最新价字段）
新浪 LOF 分类页 (fund_etf_category_sina)
    → lof_rows（含成交量、最新价字段）
        ↓
build_full_market_fund_records()
    → 读取 etf_rows/lof_rows 的成交量/最新价
    → 如果 成交量==0 且 最新价==0 → has_market_data=0
    → 否则 → has_market_data=1
        ↓
upsert_fund_info() 写入 fund_info
        ↓
遍历 fund_records:
    → has_market_data=0: 跳过行情拉取，记录日志
    → has_market_data=1: 正常拉取 fund_etf_hist_sina
        → 若意外返回空: 记录警告，更新 has_market_data=0，跳过
        ↓
全量基金回填最新净值（包括 has_market_data=0 的）
        ↓
输出统计报告
```

---

## 3. 模块设计

### 3.1 数据库层 (`engine/models/database.py`)

**改动**：

1. `_create_tables()` 中 `fund_info` 表新增字段：
   ```sql
   has_market_data INTEGER DEFAULT 1
   ```

2. `upsert_fund_info()` 中 INSERT/UPDATE 语句增加 `has_market_data` 字段。

3. 新增方法 `get_all_funds_with_market_data()`：
   ```python
   def get_all_funds_with_market_data(self) -> list[dict]:
       c = self.conn.cursor()
       c.execute("SELECT * FROM fund_info WHERE is_excluded=0 AND has_market_data=1")
       return [dict(r) for r in c.fetchall()]
   ```

4. `get_all_active_funds()` 保持不变（仍为 `WHERE is_excluded=0`），因为 `has_market_data` 是辅助标记，不决定"是否排除"。

### 3.2 种子同步层 (`engine/seed_sync.py`)

**改动**：

1. `build_full_market_fund_records()` 的 `add_rows()` 内部逻辑：
   - 从 `row` 中读取 `成交量` 和 `最新价` 字段（新浪分类页提供）
   - 如果两者均为 0（或转换后为 0），则 `has_market_data=0`
   - 否则 `has_market_data=1`

2. 返回的 record 结构新增 `has_market_data` 字段：
   ```python
   {
       "code": code,
       "name": name,
       "fund_type": market_label,
       "invest_type": ...,
       "t_plus": ...,
       "list_date": "",
       "is_excluded": 0,
       "has_market_data": 1,  # 新增
   }
   ```

### 3.3 同步脚本 (`sync_all.py`)

**改动**：

1. 第 2 步（拉取历史日线）逻辑改为：
   ```python
   for fund in fund_records:
       if fund.get("has_market_data", 1) == 0:
           logger.info(f"  跳过 {code} {name}（无场内交易行情）")
           continue
       quotes = fetch_market_quotes(code)
       if not quotes:
           logger.warning(f"  警告: {code} {name} 有行情标记但返回空，更新为无行情")
           db.update_has_market_data(code, 0)
           continue
       db.upsert_daily_quotes(quotes)
   ```

2. 第 3 步（净值回填）保持不变，全量基金都回填。

3. 最终输出新增统计：
   ```
   基金列表: 1753 只（有行情: 1731, 无行情: 22）
   市场日线: XXX 条
   最新净值: 1753 条
   ```

### 3.4 数据库层新增方法

**`update_has_market_data(code, value)`**：
```python
def update_has_market_data(self, code: str, value: int):
    c = self.conn.cursor()
    c.execute("UPDATE fund_info SET has_market_data=? WHERE code=?", (value, code))
    self.conn.commit()
```

---

## 4. 测试设计

### 4.1 `test_database.py`

- 测试 `fund_info` 表包含 `has_market_data` 字段
- 测试 `get_all_funds_with_market_data()` 正确过滤
- 测试 `update_has_market_data()` 正确更新

### 4.2 `test_seed_sync.py`

- 测试 `build_full_market_fund_records()` 对 `成交量=0` 且 `最新价=0` 的 LOF 标记 `has_market_data=0`
- 测试正常基金标记 `has_market_data=1`

### 4.3 `test_sync_all.py`

- 测试 mock 场景：部分基金 `has_market_data=0` 时，跳过行情拉取但不中断
- 测试 mock 场景：`has_market_data=1` 但行情返回空时，记录警告并更新标记
- 验证最终统计输出正确

---

## 5. 预期结果

| 指标 | 预期值 |
|------|--------|
| `fund_info` 总数 | 1753 |
| `has_market_data=1` | ~1731 |
| `has_market_data=0` | ~22 |
| `daily_quote` 记录数 | 仅包含有行情基金的历史日线 |
| `fund_nav_history` 记录数 | 1753（每只基金一条最新净值快照） |
| 导入过程 | 不中断，输出完整统计报告 |

---

## 6. 后续影响

### 6.1 服务层

- `FundService.get_all_active_funds()` 当前使用 `get_all_active_funds()`（`is_excluded=0`），会包含无行情基金
- 后续如需仅展示有行情的基金，可改用 `get_all_funds_with_market_data()`
- `get_fund_list` 接口当前返回全量活跃基金，无行情基金的技术指标计算会因 `daily_quote` 为空而返回空值或默认值——这是正确行为

### 6.2 前端

- FundList 页面会展示无行情基金，但技术指标列会显示空/默认值
- 后续可考虑在前端对 `has_market_data=0` 的基金做视觉区分（如灰色行、"无交易数据"标签）

### 6.3 打包分发

- 种子 SQLite 包含全量 1753 只基金
- 无行情基金在库中可查，但无 `daily_quote` 记录
- 用户可通过 `has_market_data` 字段自行过滤
