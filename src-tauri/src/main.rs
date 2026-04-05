#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod engine;
use engine::EngineManager;
use std::sync::Mutex;
use tauri::{AppHandle, State};

struct AppState {
    engine: Mutex<EngineManager>,
}

#[tauri::command]
fn start_engine(state: State<AppState>, app_handle: AppHandle) -> Result<String, String> {
    let mut engine = state.engine.lock().map_err(|e| e.to_string())?;
    // Note: In real app, determine is_prod dynamically (e.g., via #[cfg(debug_assertions)])
    let is_prod = !cfg!(debug_assertions);
    engine.start(is_prod, Some(&app_handle))?;
    Ok("Engine started".to_string())
}

#[tauri::command]
fn stop_engine(state: State<AppState>) -> Result<String, String> {
    let mut engine = state.engine.lock().map_err(|e| e.to_string())?;
    engine.stop()?;
    Ok("Engine stopped".to_string())
}

#[tauri::command]
fn invoke_engine(
    state: State<AppState>,
    method: String,
    params: serde_json::Value,
) -> Result<serde_json::Value, String> {
    let mut engine = state.engine.lock().map_err(|e| e.to_string())?;
    engine.invoke(&method, params)
}

fn main() {
    env_logger::init();

    tauri::Builder::default()
        .manage(AppState {
            engine: Mutex::new(EngineManager::new()),
        })
        .invoke_handler(tauri::generate_handler![
            start_engine,
            stop_engine,
            invoke_engine
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
