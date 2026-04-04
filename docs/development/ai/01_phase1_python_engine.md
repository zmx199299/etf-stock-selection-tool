# Phase 1 Documentation: Python Core Engine (AI Context)

> 历史快照：本文记录的是早期 Phase 1 阶段状态，**不是当前项目真实状态**。继续开发时请优先读取 `docs/development/ai/current_state.md`。

## Architecture & State
- **Role**: Backend sub-process running as a sidecar via standard I/O (stdin/stdout).
- **Communication Protocol**: JSON-RPC 2.0. Incoming lines are parsed as requests, responses are written as single-line JSON to stdout.
- **Data Source**: Local SQLite database (`src-python/engine/models/database.py`). Network calls are strictly isolated to `AkshareDataSource` (`src-python/engine/data/akshare_source.py`).
- **Dependencies**: `pandas`, `akshare`, `TA-Lib`, `pytest`.

## Core Modules & API Contracts
1. **Database (`engine.models.database.Database`)**:
   - Manages SQLite connection.
   - Tables: `funds` (info), `daily_quotes` (historical data).
   - Expected flow: Network -> DB -> Memory (DataFrame) -> Calculations.
2. **Indicators (`engine.scoring.indicators.TechnicalIndicators`)**:
   - Input: Pandas DataFrame with `open, close, high, low, volume`.
   - Returns: DataFrame appended with `SMA_5, MACD, RSI_14, upper_band`, etc.
3. **Scorer (`engine.scoring.scorer.Scorer`)**:
   - `score(df)`: Calculates sub-scores (trend, momentum, volatility, volume) and a `total_score` (0-100), outputs signal strings (e.g. `强烈看多`).
4. **PatternRecognizer (`engine.scoring.patterns.PatternRecognizer`)**:
   - `detect_v_reversal(df)`: Uses K-line candlestick properties (lower shadow > body * 1.5, close near high) to detect intraday V-reversals.
5. **JSONRPCServer (`engine.server.JSONRPCServer`)**:
   - `register_method(name, func)`
   - `handle_request(req_str) -> res_str`
   - `run_stdio()`: Infinite loop blocking on `sys.stdin`.

## TDD Status
- 33 out of 33 tests passing. Total coverage spans DB schema, Network mocking, DataFrame manipulations, Mathematical formulas, and RPC string parsing.
- Future tasks relying on Python MUST maintain this 100% pass rate before committing changes.

## Moving to Phase 2 (Rust/Tauri)
- **Sidecar binary**: During local development in Rust, spawn `python src-python/main.py`. For release, package via PyInstaller into `src-tauri/binaries/`.
- **Rust Engine Module**: Needs a persistent process handle. Write requests via `ChildStdin`, read async via `ChildStdout`.
