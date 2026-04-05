# ETF Analyzer - 场内基金智能分析工具

[![GitHub stars](https://img.shields.io/github/stars/zmx199299/etf-stock-selection-tool)](https://github.com/zmx199299/etf-stock-selection-tool/stargazers)
[![GitHub release](https://img.shields.io/github/v/release/zmx199299/etf-stock-selection-tool)](https://github.com/zmx199299/etf-stock-selection-tool/releases)
[![License](https://img.shields.io/github/license/zmx199299/etf-stock-selection-tool)](https://github.com/zmx199299/etf-stock-selection-tool/blob/main/LICENSE)

一款专为场内基金（ETF/LOF）投资者设计的桌面应用，提供实时行情、技术分析、形态识别、智能评分等功能。

## 功能特性

- **实时行情**：获取并展示 ETF/LOF 的实时价格、涨跌幅、成交量等数据
- **技术指标**：自动计算 MACD、RSI、布林带、均线等技术指标
- **形态识别**：智能识别 V 型反转、三连阳等经典 K 线形态
- **智能评分**：从趋势、动量、波动、成交量多维度综合评估基金
- **交易成本计算**：精确计算佣金、印花税等交易费用
- **全局配色方案**：用户可配置红涨绿跌/绿涨红跌显示方案

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + TailwindCSS |
| 桌面框架 | Tauri 2 (Rust) |
| 后端引擎 | Python 3 (JSON-RPC) |
| 数据源 | AkShare |
| 数据库 | SQLite |

## 环境要求

- **Python**: 3.8+
- **Node.js**: 18+
- **Rust**: 1.70+
- **TA-Lib**: 需要单独安装（见下方说明）

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/zmx199299/etf-stock-selection-tool.git
cd etf-stock-selection-tool
```

### 2. 安装 Python 依赖

```bash
# 创建虚拟环境（可选）
python3 -m venv .venv

# 激活虚拟环境
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 安装依赖
pip install -r src-python/requirements.txt
```

**注意**：TA-Lib 需要单独安装。请前往 [TA-Lib 官网](https://ta-lib.org/) 下载并编译，或使用社区提供的预编译包：
```bash
# Ubuntu/Debian
sudo apt-get install ta-lib

# macOS
brew install ta-lib

# Windows (使用预编译包)
# 下载 ta-lib-0.4.0-msvc.zip，解压后将 TA-Lib 放到适当位置
```

### 3. 安装 Node.js 依赖

```bash
npm install
```

### 4. 运行开发模式

```bash
# 同时启动前端和后端
npm run tauri dev
```

### 5. 构建生产版本

```bash
npm run tauri build
```

构建产物位于 `src-tauri/target/release/bundle/` 目录下。

## 项目结构

```
etf-stock-selection-tool/
├── src/                    # Vue 3 前端源码
├── src-tauri/              # Rust Tauri 源码
├── src-python/             # Python 引擎源码
│   ├── engine/             # 核心业务逻辑
│   │   ├── data/           # 数据源模块
│   │   ├── models/         # 数据库模块
│   │   └── scoring/        # 分析与评分模块
│   └── tests/              # 单元测试
├── docs/                   # 开发文档
├── dist/                   # 前端构建产物
└── package.json            # Node.js 配置
```

## 开发指南

### 运行测试

```bash
# Python 后端测试
pytest src-python/tests/

# Rust 类型检查
cargo check

# 前端构建检查
npm run build
```

### 代码规范

- 使用 TDD（测试驱动开发）模式
- 遵循项目 AGENTS.md 中的开发规范
- 提交前确保所有测试通过

## 许可证

本项目采用 [GNU General Public License v3.0 (GPLv3)](LICENSE) 许可证开源。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- GitHub: https://github.com/zmx199299/etf-stock-selection-tool
