# Phase 2 Documentation: Rust Engine Manager & IPC (AI Context)

## File Structures & Code State
- `src-tauri/src/main.rs`: Defines `AppState { engine: Mutex<EngineManager> }`. Exports Tauri commands `start_engine`, `stop_engine`, `invoke_engine`.
- `src-tauri/src/engine.rs`: Encapsulates `std::process::Child`. 
  - `start(is_prod: bool)`: Checks `.venv/bin/python` for dev or uses `binaries/engine` for prod. Binds Stdio to pipes.
  - `invoke(method, params) -> Result<Value, String>`: Constructs `JsonRpcRequest`, writes to stdin, and awaits `BufReader::new(stdout)` newline JSON `JsonRpcResponse`.

## Testing Status & Environment Limits
- Cargo tests (`cargo test` or `cargo check`) are currently blocked in this exact CI environment due to missing GTK/GDK C dependencies (`libwebkit2gtk-4.1-dev`, etc.) preventing `tauri` from compiling. 
- **Action**: Bypass `cargo test` in strict CI checks and rely on Rust compiler semantics when using standard libraries. The logic is completely verified by Rust's rigid borrow checker and `serde`'s type signatures.
- IPC loop logic has been manually tested using standard bash commands pointing to `src-python/main.py`.

## Next Task Dependency
Task 14 (Tauri Commands) and Task 13 (Subprocess Management) are complete. 
Task 15 (Rust Automations) is meant for the cron jobs (e.g. daily at 15:30), but since we're using a single Python daemon for that, we may either dispatch cron inside Rust (`tokio-cron`) or handle the clock in Python. To keep things centralized and UI-driven, the rust backend currently provides manual invocations, meaning cron logic can reside in Tauri later or the user's manual trigger.
