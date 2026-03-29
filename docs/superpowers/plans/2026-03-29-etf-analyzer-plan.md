# 场内基金自动化分析系统 — 实施计划（总览）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建跨平台桌面应用，每日收盘后自动采集场内基金数据并输出交易建议

**Architecture:** Tauri 桌面壳 + Python 分析引擎 (sidecar) + Vue 3 前端，通过 JSON-RPC 通信，SQLite 存储

**Tech Stack:** Python 3.10+ / pandas / akshare / ta-lib / SQLite / Rust / Tauri 2 / Vue 3 / TypeScript / ECharts / Tailwind CSS

**Design Doc:** `docs/superpowers/specs/2026-03-29-etf-analyzer-design.md`

---

## 实施阶段总览

| 阶段 | 内容 | 产出 | 计划文件 |
|------|------|------|----------|
| 0 | 环境搭建与项目初始化 | 可运行的空项目骨架 | 本文件 Task 1-2 |
| 1 | Python 分析引擎 | 可 CLI 独立运行的完整分析引擎 | `plan-phase1-python-engine.md` |
| 2 | Tauri + Rust 中间层 | sidecar 管理、JSON-RPC 通信、定时调度 | `plan-phase2-tauri-rust.md` |
| 3 | Vue 前端页面 | 5个页面（每个页面由用户确认后开发） | `plan-phase3-vue-frontend.md` |
| 4 | 打包与文档 | 跨平台安装包、完整文档 | `plan-phase4-packaging.md` |

**关键约束：**
- 编码开始前提醒用户更换模型
- 每个前端页面 UI 需用户逐一确认后再开发
- 安装系统级工具前需用户确认

---

## Task 1: 环境搭建

**Files:**
- Create: `etf-test/.venv/` (Python 虚拟环境)
- Create: `etf-test/src-python/requirements.txt`
- Create: `etf-test/package.json`
- Create: `etf-test/.gitignore`

- [ ] **Step 1: 确认系统级工具**

提醒用户确认已安装：Python 3.10+, Node.js 18+, Rust toolchain。
检查命令：
```bash
python3 --version
node --version
rustc --version
```

- [ ] **Step 2: 初始化 git 仓库**

```bash
cd /home/zmx/codelearn/etf-test
git init
```

- [ ] **Step 3: 创建 .gitignore**

```
.venv/
node_modules/
target/
__pycache__/
*.pyc
data/*.db
dist/
.DS_Store
```

- [ ] **Step 4: 创建 Python 虚拟环境并安装依赖**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

创建 `src-python/requirements.txt`：
```
akshare>=1.12.0
pandas>=2.0.0
numpy>=1.24.0
ta-lib>=0.4.28
```

```bash
pip install -r src-python/requirements.txt
```

注意：ta-lib 需要系统级 TA-Lib C 库，安装前需确认：
```bash
# Ubuntu/Debian
sudo apt-get install libta-lib-dev
# 或者用 conda: conda install -c conda-forge ta-lib
```

- [ ] **Step 5: 初始化 Tauri 项目**

```bash
npm create tauri-app@latest . -- --template vue-ts
npm install
```

- [ ] **Step 6: 验证项目可启动**

```bash
npm run tauri dev
```
Expected: Tauri 窗口弹出，显示 Vue 默认页面

- [ ] **Step 7: 提交**

```bash
git add .
git commit -m "chore: init project with Tauri + Vue + Python venv"
```

---

## Task 2: 项目目录结构搭建

**Files:**
- Create: `src-python/engine/__init__.py`
- Create: `src-python/engine/data/__init__.py`
- Create: `src-python/engine/screener/__init__.py`
- Create: `src-python/engine/scoring/__init__.py`
- Create: `src-python/engine/models/__init__.py`
- Create: `src-python/main.py`
- Create: `src-python/tests/`
- Create: `data/`

- [ ] **Step 1: 创建 Python 引擎目录结构**

```
src-python/
├── engine/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── base.py          ← 数据源抽象接口
│   │   └── akshare_source.py ← akshare 实现
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py       ← SQLite 数据库操作
│   ├── screener/
│   │   ├── __init__.py
│   │   └── pattern.py        ← 日内形态筛选
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── indicators.py     ← 技术指标计算
│   │   ├── scorer.py         ← 综合评分
│   │   └── cost.py           ← 交易成本与资金分配
│   └── config.py             ← 配置管理
├── tests/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_screener.py
│   ├── test_scoring.py
│   └── test_cost.py
└── main.py                    ← JSON-RPC 入口
```

- [ ] **Step 2: 创建所有空 __init__.py 和占位文件**

- [ ] **Step 3: 创建 data/ 目录用于 SQLite 数据库**

```bash
mkdir -p data
touch data/.gitkeep
```

- [ ] **Step 4: 提交**

```bash
git add .
git commit -m "chore: scaffold Python engine directory structure"
```

---

后续任务见各阶段计划文件。开发顺序：先完成阶段 1（Python 引擎），确保 CLI 可独立运行测试，再接入 Tauri。
