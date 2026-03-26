# 场内基金 V 型反转筛选工具

每天收盘后运行，自动筛选符合日内 V 型反转条件的场内基金（ETF / LOF），标注 T+0 / T+1 属性，结合技术指标预测次日买入价值，并判断下一交易日是否停牌。

## 筛选条件

以下条件**全部满足**才会入选：

| 条件 | 说明 |
|------|------|
| 日内振幅 3.5% ~ 4.5% | 振幅 = (最高 - 最低) / 昨收 |
| 最低点相对昨收下跌 ≥ 1% | 当天必须先跌 |
| 最高点 > 最低点 | 形成 V 型反转 |
| 连续 3 天满足以上条件 | 排除偶发信号 |
| 次日买入价值评分 ≥ 60 分 | 技术指标综合评分 |
| 下一交易日未停牌 | 实时查询停牌状态 |
| 非货币基金 | 排除货币 ETF / 货币基金 |

无结果时会打印筛选条件说明，不会静默退出。

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/zmx199299/etf-stock-selection-tool.git
cd etf-stock-selection-tool
```

### 2. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
python find_funds.py
```

首次运行约需 **40 ~ 50 秒**（并发拉取约 2500 只基金历史行情），之后输出符合条件的基金列表或无结果说明。

示例输出：

```
22:35:24 [INFO] ===== 场内基金V型反转筛选工具 =====
22:35:25 [INFO] 交易日历加载成功，共 8797 个交易日
22:35:25 [INFO] 分析日期：2026-03-26，下一交易日：2026-03-27
22:35:25 [INFO] 场内基金列表加载成功，共 2471 只（ETF + LOF）
22:36:12 [INFO] 历史数据加载完成，有效基金 1845/2471 只
22:36:13 [INFO] V型反转初步筛选：0 只候选基金

暂时没有符合条件的基金
筛选条件：
  - 日内波动幅度 3.5% ~ 4.5%
  - 当日最低点相对昨收下跌 ≥ 1.0%（先跌）
  - 最高点 > 最低点（V型反转）
  - 连续 3 天满足以上条件
  - 次日买入价值评分 ≥ 60 分
  - 下一交易日未停牌
  - 非货币基金
```

## 项目结构

```
.
├── find_funds.py          # 主程序
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # 共享 fixtures
│   └── test_funds.py      # 单元测试（51 个）
├── AGENTS.md              # 项目开发规范（AI 提示词）
├── pyproject.toml         # 项目配置（ruff / pytest / mypy）
├── requirements.txt       # 运行依赖
├── requirements-dev.txt   # 开发依赖
├── LICENSE                # GPL v3
└── README.md
```

## 数据接口

> 运行环境为 WSL（Linux），akshare 大多数接口因 TLS 问题不可用，全部改用 `requests` 直连。

| 用途 | 接口 | 说明 |
|------|------|------|
| 基金代码列表 | 东方财富 `fund.eastmoney.com/js/fundcode_search.js` | 全量 ETF + LOF，约 2500 只 |
| 历史 K 线 | 腾讯财经 `web.ifzq.gtimg.cn` | 前复权日 K 线，20 线程并发 |
| 停牌判断 | 腾讯财经 `qt.gtimg.cn` 批量实时行情 | 仅查询候选基金，每批 200 只 |
| 交易日历 | akshare `tool_trade_date_hist_sina()` | 底层用 requests，正常可用 |

## 技术指标评分规则

总分 100 分，**≥ 60 分**为推荐买入。

| 指标 | 条件 | 得分 |
|------|------|------|
| RSI(14) | < 30（超卖） | +25 |
| RSI(14) | 30 ~ 40（偏弱） | +15 |
| MACD(12,26,9) | DIF 上穿 DEA（金叉） | +25 |
| 布林带(20,2) | 价格 < 下轨 | +20 |
| 布林带(20,2) | 价格接近下轨（< 下轨 + 0.5%）| +10 |
| MA5 / MA10 / MA20 | 多头排列（MA5 > MA10 > MA20） | +15 |
| 成交量 | 当日放量（> 5 日均量 × 1.5） | +10 |
| V 型反转特征 | 已通过筛选条件 | +15 |

## T+0 / T+1 判断规则

- **T+0**：基金名称包含以下任意关键词  
  `跨境、港股、恒生、纳斯达克、标普、德国、日经、黄金、白银、原油、商品、豆粕、有色、能源、债券、国债、短融、信用、可转债、货币、添益、日利、互联网、油气`
- **T+1**：其余 A 股股票型 ETF 及所有 LOF

## 开发

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 代码检查 & 格式化
ruff check .
ruff format .

# 类型检查
mypy find_funds.py

# 运行测试（51 个，全部 mock，不依赖真实网络）
pytest tests/ -v

# 覆盖率报告
pytest --cov=find_funds --cov-report=term-missing
```

## License

本项目基于 [GNU General Public License v3.0](LICENSE) 开源。
