# AGENTS.md — 场内基金筛选工具开发指南

## 1. 项目概述
每天收盘后运行，筛选符合日内V型反转条件的场内基金（ETF/LOF），
标注T+0/T+1属性，结合技术指标预测次日买入价值，
判断下一交易日是否停牌。

筛选条件（全部满足）：
  - 日内波动幅度 3.5% ~ 4.5%（振幅 = (最高-最低)/昨收）
  - 当日最低点相对昨收下跌 ≥ 1%（先跌）
  - 最高点 > 最低点（V型反转）
  - 连续 N 天（默认3天）均满足以上条件
  - 次日买入价值评分 ≥ 60 分
  - 下一交易日未停牌
  - 非货币基金（排除货币基金、货币ETF）

无结果时输出：
  暂时没有符合条件的基金
  筛选条件：
    - 日内波动幅度 3.5% ~ 4.5%
    - 当日最低点相对昨收下跌 ≥ 1%（先跌）
    - 最高点 > 最低点（V型反转）
    - 连续 3 天满足以上条件
    - 次日买入价值评分 ≥ 60 分
    - 下一交易日未停牌
    - 非货币基金

依赖：pandas, akshare, ta, requests, beautifulsoup4

### 网络环境说明（WSL）
运行环境为 WSL（Linux），Windows 网络正常。
akshare 大多数行情接口底层使用 curl_cffi，在 WSL 下出现 TLS 错误，**不可用**。
以下接口已改为直接使用 requests 调用替代：
- 历史K线：腾讯财经 `web.ifzq.gtimg.cn`（替代 akshare ETF/LOF hist）
- 基金代码列表：东方财富 `fund.eastmoney.com/js/fundcode_search.js`（替代 akshare spot）
- 停牌判断：腾讯财经 `qt.gtimg.cn` 批量实时行情（替代 akshare suspend）
- 交易日历：`ak.tool_trade_date_hist_sina()` 底层用 requests，**正常可用**

## 2. 虚拟环境（必须使用，避免污染系统 Python）
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
deactivate

## 3. 运行
python find_funds.py

## 4. Lint / Format / 类型检查
ruff check .
ruff format .
ruff check --fix .
mypy find_funds.py

## 5. 测试（重点 — 防止无法取得数据时程序崩溃）

### 5.1 命令
pytest
pytest tests/test_funds.py -v
pytest tests/test_funds.py::test_function -v
pytest --cov=find_funds --cov-report=term-missing

### 5.2 Mock 要求（所有外部依赖必须 mock，禁止依赖真实网络）
- akshare API：`ak.tool_trade_date_hist_sina` 等
- `requests.get` 调用（腾讯K线、东方财富基金列表、腾讯实时行情）
- 使用 `unittest.mock.patch` 或 `pytest-mock`

### 5.3 必须覆盖的测试场景
- API 成功返回 → 正常解析
- API 连接失败（ConnectionError）→ fallback 到模拟数据
- API 返回空数据 → 正确处理
- 交易时间判断 → 各时间段选择正确数据日期（9:30-15:00 含午休为交易时段）
- 非交易日判断 → 周末、法定节假日、调休上班但非交易日均正确识别
- T+0/T+1 判断 → 跨境/商品/债券/货币 ETF 为 T+0，A股 ETF/LOF 为 T+1
- 技术指标计算 → RSI/MACD/布林带数值与手工验算一致
- 买入评分 → 各信号组合得分合理
- 筛选逻辑 → 符合条件的被选中，不符合的被排除
- 停牌判断 → 被选基金下一交易日停牌则排除
- 无结果输出 → 无基金符合时打印条件说明
- main() 集成 → 全流程 mock 不报错

### 5.4 Fixture 示例
```python
@pytest.fixture
def sample_fund_dict():
    return {'510050': '华夏上证50ETF', '510300': '华泰柏瑞沪深300ETF'}

@pytest.fixture
def mock_tencent_kline(requests_mock):
    """mock 腾讯财经K线接口"""
    # JSONP 格式：kline_dayfqk={...}
    # 数据格式：[日期, 开盘, 收盘, 最高, 最低, 成交量]
    requests_mock.get(
        'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get',
        text='kline_dayfqk={"data":{"sh510050":{"day":[["2026-03-24","3.00","3.00","3.14","2.86","1000000"]]}}}'
    )

@pytest.fixture
def mock_trade_calendar(monkeypatch):
    def mock_func():
        return pd.DataFrame({'trade_date': [
            '2026-03-23','2026-03-24','2026-03-25','2026-03-26','2026-03-27'
        ]})
    monkeypatch.setattr(ak, 'tool_trade_date_hist_sina', mock_func)
```

## 6. 数据接口

### 6.1 实际使用的接口（全部通过 requests 直连）

#### 基金代码列表
- **东方财富**：`https://fund.eastmoney.com/js/fundcode_search.js`
- 返回 JS 变量赋值，含基金代码、名称、类型
- 类型字段：`ETF-股票`、`ETF-债券`、`LOF` 等；`货币` 类型已排除

#### 历史K线
- **腾讯财经前复权日K线**：`https://web.ifzq.gtimg.cn/appstock/app/fqkline/get`
- 参数：`param=sh510050,day,开始日期,结束日期,60,qfq`
- 返回 JSONP：`kline_dayfqk={...}`，数据格式：`[日期, 开盘, 收盘, 最高, 最低, 成交量]`
- 并发参数：`MAX_WORKERS = 20`（线程池）、全量2500只约需 **40-50秒**

#### 停牌判断（仅对初步筛选候选基金查询）
- **腾讯财经批量实时行情**：`https://qt.gtimg.cn/q=sh510050,sz159919,...`
- 支持逗号分隔批量查询；每批 `SUSPEND_BATCH_SIZE = 200` 只
- 判断依据：返回价格字段为 `0` 或空 → 视为停牌

#### 交易日历
- **akshare**：`ak.tool_trade_date_hist_sina()` → 完整 A 股交易日历（1990-2025），底层用 requests，**正常可用**

### 6.2 废弃的接口（WSL下TLS错误，不可用）
- `ak.fund_etf_hist_em` / `ak.fund_lof_hist_em` — 历史K线（curl_cffi，TLS失败）
- `ak.fund_etf_spot_em` / `ak.fund_lof_spot_em` — 实时行情（curl_cffi，TLS失败）
- `ak.news_trade_notify_suspend_baidu` — 停复牌（curl_cffi，TLS失败）
- 东方财富 `push2his` / `push2` 域名 — WSL下 RemoteDisconnected

### 6.3 交易时间判断（含午休 11:30-13:00）
A股交易时段 = 9:30 ~ 15:00（包含午休，整体视为交易时段）

判断逻辑：
```
if (hour < 9) or (hour == 9 and minute < 30) or (hour >= 15):
    → 非交易时段，使用当日（最近交易日）数据
else:
    → 交易时段（9:30-15:00，含午休），使用前一交易日数据
```

非交易日（周末/节假日/调休非交易日）→ 使用最近交易日数据

### 6.4 交易日历（调休处理）
使用 `ak.tool_trade_date_hist_sina()` 获取完整交易日列表，
自动排除调休上班但非交易日（如春节调休补班但股市不开盘）。

也可使用 `a_trade_calendar` 包：
```python
pip install a-trade-calendar
a_trade_calendar.is_trade_date('2026-01-26')  # 调休上班日，False
a_trade_calendar.get_pre_trade_date('2026-03-27', 1)  # 前一交易日
```

### 6.5 T+0 / T+1 判断
- **T+0**：跨境ETF、商品ETF、债券ETF、货币ETF
- **T+1**：A股股票型ETF、所有 LOF

判断方式：基金名称关键词匹配

T+0 关键词：`跨境、港股、恒生、纳斯达克、标普、德国、日经、黄金、白银、原油、商品、豆粕、有色、能源、债券、国债、短融、信用、可转债、货币、添益、日利`

### 6.6 技术指标（使用 ta 库，纯 Python，无需 C 编译）
- **RSI(14)**：< 30 超卖(+25分), 30-40 偏卖(+15分)
- **MACD(12,26,9)**：DIF上穿DEA金叉(+25分)
- **布林带(20,2)**：价格<下轨(+20分), 接近下轨(+10分)
- **MA(5/10/20)**：均线多头排列(+15分)
- **成交量**：放量(+10分)
- **V型反转特征**：已有筛选条件匹配(+15分)

总分 0-100，≥60 分为推荐买入

## 7. 代码风格
- **导入**：标准库→第三方→本地，组间空行；禁止函数内部 import
- **格式化**：black 兼容，行宽 88，4 空格缩进
- **类型注解**：Python 3.10+ 风格 `list[str]`，所有公共函数必须加
- **命名**：`snake_case`（函数/变量）、`PascalCase`（类）、`UPPER_SNAKE`（常量）
- **错误处理**：捕获具体异常（`requests.RequestException`, `KeyError`, `ValueError`）；用 `logging` 替代 `print`
- **文档字符串**：中文 docstring，三引号，含参数和返回值说明
- **注释**：中文
- **字符串格式化**：统一使用 f-string

## 8. 项目约定
- 网络请求必须设置 User-Agent header
- 数据获取失败必须有 fallback（模拟数据）
- 公共函数必须有类型注解和 docstring
- 每次修改后运行 `ruff check` 和 `pytest`
- 无符合条件基金时，必须输出筛选条件说明
- 选中的基金必须检查下一交易日是否停牌

## 9. 建议项目文件
- `pyproject.toml` — 元数据 + ruff/pytest/mypy 配置
- `requirements.txt` — pandas, akshare, ta, requests, beautifulsoup4
- `requirements-dev.txt` — ruff, mypy, pytest, pytest-cov, pytest-mock, a-trade-calendar
- `tests/conftest.py` — 共享 fixtures
- `tests/test_funds.py` — 测试文件
- `.gitignore` — .venv/, __pycache__/, .pytest_cache/
- `.pre-commit-config.yaml` — pre-commit hooks

## 10. 对话语言
- 与 AI 助手的所有对话采用中文
