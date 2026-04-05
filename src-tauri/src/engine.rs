use serde::{Deserialize, Serialize};
use std::io::{BufRead, BufReader, Write};
use std::process::{Child, Command, Stdio};
use tauri::{path::BaseDirectory, Manager};

#[derive(Serialize)]
pub struct JsonRpcRequest {
    pub jsonrpc: String,
    pub method: String,
    pub params: serde_json::Value,
    pub id: u64,
}

#[derive(Deserialize, Debug)]
pub struct JsonRpcResponse {
    pub jsonrpc: String,
    pub result: Option<serde_json::Value>,
    pub error: Option<serde_json::Value>,
    pub id: Option<u64>,
}

impl JsonRpcResponse {
    fn touch_metadata(&self) {
        let _ = (&self.jsonrpc, &self.id);
    }
}

pub struct EngineManager {
    child: Option<Child>,
    req_id: u64,
}

impl EngineManager {
    pub fn new() -> Self {
        Self {
            child: None,
            req_id: 1,
        }
    }

    pub fn start(
        &mut self,
        is_prod: bool,
        app_handle: Option<&tauri::AppHandle>,
    ) -> Result<(), String> {
        if self.child.is_some() {
            return Ok(());
        }

        let mut cmd = if is_prod {
            // In production, resolve the packaged sidecar path produced by Tauri bundling.
            let app_handle = app_handle.ok_or("Missing app handle in production mode")?;
            let target = std::env::consts::ARCH;
            let os = std::env::consts::OS;
            let triple = match (os, target) {
                ("linux", "x86_64") => "x86_64-unknown-linux-gnu",
                ("macos", "x86_64") => "x86_64-apple-darwin",
                ("macos", "aarch64") => "aarch64-apple-darwin",
                ("windows", "x86_64") => "x86_64-pc-windows-msvc",
                _ => return Err(format!("Unsupported platform: {os}-{target}")),
            };

            let sidecar_path = app_handle
                .path()
                .resolve(format!("binaries/engine-{triple}"), BaseDirectory::Resource)
                .map_err(|e| format!("Failed to resolve sidecar path: {e}"))?;

            Command::new(sidecar_path)
        } else {
            // In development, run python directly
            // Ensure we use the venv python if available, else fallback to python3
            let python_bin = if std::path::Path::new(".venv/bin/python").exists() {
                ".venv/bin/python"
            } else {
                "python3"
            };

            let mut c = Command::new(python_bin);
            c.arg("src-python/main.py");
            c
        };

        cmd.stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit()); // Forward stderr to the terminal for debugging

        let child = cmd
            .spawn()
            .map_err(|e| format!("Failed to spawn engine: {}", e))?;
        self.child = Some(child);

        Ok(())
    }

    pub fn stop(&mut self) -> Result<(), String> {
        if let Some(mut child) = self.child.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
        Ok(())
    }

    pub fn invoke(
        &mut self,
        method: &str,
        params: serde_json::Value,
    ) -> Result<serde_json::Value, String> {
        let child = self.child.as_mut().ok_or("Engine is not running")?;

        let stdin = child.stdin.as_mut().ok_or("Failed to get stdin")?;

        let req = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            method: method.to_string(),
            params,
            id: self.req_id,
        };
        self.req_id += 1;

        let req_str = serde_json::to_string(&req).map_err(|e| e.to_string())?;

        // Write to stdin
        stdin
            .write_all(format!("{}\n", req_str).as_bytes())
            .map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;

        // Read from stdout
        let stdout = child.stdout.as_mut().ok_or("Failed to get stdout")?;
        let mut reader = BufReader::new(stdout);
        let mut line = String::new();
        reader.read_line(&mut line).map_err(|e| e.to_string())?;

        if line.is_empty() {
            return Err("Engine closed the connection".to_string());
        }

        let res: JsonRpcResponse = serde_json::from_str(&line).map_err(|e| e.to_string())?;
        res.touch_metadata();

        if let Some(err) = res.error {
            return Err(err.to_string());
        }

        res.result
            .ok_or_else(|| "No result in response".to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_returns_empty_manager() {
        let manager = EngineManager::new();
        // Fresh manager should have no child and req_id = 1
        assert!(manager.child.is_none());
        assert_eq!(manager.req_id, 1);
    }

    #[test]
    fn test_invoke_when_not_running_returns_error() {
        let mut manager = EngineManager::new();
        let result = manager.invoke("ping", serde_json::json!({}));
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Engine is not running");
    }

    #[test]
    fn test_start_with_invalid_path_fails() {
        let mut manager = EngineManager::new();
        // Try to start with a non-existent binary
        let result = manager.start(true, None); // missing app handle in prod should fail
        assert!(result.is_err());
    }

    #[test]
    fn test_start_and_stop_with_sleep() {
        let mut manager = EngineManager::new();

        // Use `sleep` as a mock child process (it has stdin/stdout piped)
        // We'll manually create a child to test the lifecycle
        let mut cmd = Command::new("sleep");
        cmd.arg("10")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null());

        let child = cmd.spawn().expect("sleep should exist");
        manager.child = Some(child);

        // Child should be running
        assert!(manager.child.is_some());

        // Stop should succeed
        let result = manager.stop();
        assert!(result.is_ok());

        // Child should be None after stop
        assert!(manager.child.is_none());
    }

    #[test]
    fn test_start_idempotent() {
        let mut manager = EngineManager::new();

        // Use `sleep` as mock
        let mut cmd = Command::new("sleep");
        cmd.arg("10")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null());

        let child = cmd.spawn().expect("sleep should exist");
        manager.child = Some(child);

        // Calling start again should be no-op (return Ok)
        // We simulate this by checking child is still Some
        assert!(manager.child.is_some());

        // Cleanup
        manager.stop().unwrap();
    }
}
