# 第一阶段开发文档：Python 核心分析引擎 (Human)

## 概述
本项目的第一阶段集中于构建后端的纯 Python 核心分析引擎。该引擎负责场内基金（ETF/LOF）的数据获取、技术指标计算、形态识别、打分与交易成本预估。引擎最终通过标准输入输出（stdin/stdout）提供 JSON-RPC 服务，供上层的 Rust/Tauri 进程调用。

## 目录结构
所有的 Python 代码都位于 `src-python/` 目录下：
- `engine/`：核心业务代码
  - `data/`：数据源模块。包含基础接口 `base.py` 以及具体的 `akshare_source.py` 用于网络爬取。
  - `models/`：数据存储模块。`database.py` 负责 SQLite 本地数据库的管理、建表和数据存取。
  - `scoring/`：核心分析与打分逻辑。
    - `indicators.py`：基于 Pandas 和 TA-Lib 计算 MACD, RSI, BOLL, MA 等指标。
    - `scorer.py`：多维度（趋势、动量、波动、成交量）综合打分。
    - `patterns.py`：K线形态识别，例如日内 V 型反转。
    - `calculator.py`：交易成本与预算计算器，处理佣金、免5、印花税及净利润预估。
  - `utils/`：工具类，如 `config.py` 用于加载/保存 JSON 配置文件。
  - `server.py`：JSON-RPC 协议封装，使得 Python 进程能像服务端一样持续响应来自标准输入的请求。
- `tests/`：Pytest 测试代码，涵盖所有模块。

## 运行与测试指南
1. **环境准备**：
   请确保您位于项目的根目录，且已经通过 `python3 -m venv .venv` 创建并激活了虚拟环境。通过 `pip install -r src-python/requirements.txt` 安装依赖。
2. **运行测试**：
   本项目严格遵循 TDD（测试驱动开发）。要验证所有核心逻辑是否正常，请执行：
   ```bash
   pytest src-python/tests/
   ```
   如果输出显示 `33 passed`，代表所有模块工作正常。

## 架构设计要点
- **离线优先**：所有数据经过爬取后，会通过 `Database` 模块存入本地 SQLite。引擎默认只从本地计算，极大加快了计算速度。
- **配置化与多资产支持**：交易预算、手续费率等通过 `config.json` 动态配置。手续费（佣金、最低佣金、印花税）已经按照 `ETF`、`LOF`、`股票` 三种类型进行了独立拆分计算，满足复杂交易品种下的真实成本预估。
