#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Command, Stdio};
use std::io::{BufRead, BufReader, Write};
use std::sync::Mutex;
use tauri::{Manager, State};

struct EngineState {
    child: Mutex<Option<std::process::Child>>,
}

#[tauri::command]
fn start_engine(state: State<EngineState>) -> Result<String, String> {
    let mut child_lock = state.child.lock().map_err(|e| e.to_string())?;
    
    if child_lock.is_some() {
        return Ok("Engine already running".to_string());
    }

    let mut child = Command::new("python3")
        .arg("src-python/main.py")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to start engine: {}", e))?;

    // Send ping to verify
    if let Some(ref mut stdin) = child.stdin {
        stdin.write_all(b"{\"jsonrpc\":\"2.0\",\"method\":\"ping\",\"params\":{},\"id\":1}\n")
            .map_err(|e| e.to_string())?;
    }

    *child_lock = Some(child);
    Ok("Engine started".to_string())
}

#[tauri::command]
fn stop_engine(state: State<EngineState>) -> Result<String, String> {
    let mut child_lock = state.child.lock().map_err(|e| e.to_string())?;
    if let Some(mut child) = child_lock.take() {
        child.kill().map_err(|e| e.to_string())?;
    }
    Ok("Engine stopped".to_string())
}

#[tauri::command]
fn invoke_engine(state: State<EngineState>, method: String, params: serde_json::Value) -> Result<serde_json::Value, String> {
    let child_lock = state.child.lock().map_err(|e| e.to_string())?;
    let child = child_lock.as_ref().ok_or("Engine not running")?;
    
    let mut child = Command::new("python3")
        .arg("src-python/main.py")
        .arg("--once")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to start engine: {}", e))?;

    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    });

    if let Some(ref mut stdin) = child.stdin {
        stdin.write_all(format!("{}\n", request).as_bytes())
            .map_err(|e| e.to_string())?;
    }

    let output = child.wait_with_output()
        .map_err(|e| e.to_string())?;
    
    let response: serde_json::Value = serde_json::from_slice(&output.stdout)
        .map_err(|e| format!("Invalid response: {}", e))?;
    
    Ok(response)
}

fn main() {
    env_logger::init();
    
    tauri::Builder::default()
        .manage(EngineState {
            child: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            start_engine,
            stop_engine,
            invoke_engine
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}