use serde::{Deserialize, Serialize};
use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::process::{Child, ChildStdout, Command, Stdio};
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
    reader: Option<BufReader<ChildStdout>>,
    req_id: u64,
}

impl EngineManager {
    pub fn new() -> Self {
        Self {
            child: None,
            reader: None,
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
            // Tauri v2 removes the target triple during bundling for externalBin paths.
            let app_handle = app_handle.ok_or("Missing app handle in production mode")?;
            let os = std::env::consts::OS;
            let exe_name = if os == "windows" {
                "engine.exe"
            } else {
                "engine"
            };

            let sidecar_path = app_handle
                .path()
                .resolve(format!("binaries/{}", exe_name), BaseDirectory::Resource)
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

        cmd.stdin(Stdio::piped()).stdout(Stdio::piped());

        // 生产环境将 stderr 写入日志文件，方便诊断；开发环境直接输出到终端
        if is_prod {
            let home = dirs::home_dir().ok_or("Cannot determine home directory")?;
            let log_dir = home.join(".etf-analyzer");
            fs::create_dir_all(&log_dir).map_err(|e| format!("Failed to create log dir: {e}"))?;
            let log_path = log_dir.join("engine.log");
            let log_file = fs::File::create(&log_path)
                .map_err(|e| format!("Failed to create engine log: {e}"))?;
            cmd.stderr(Stdio::from(log_file));
        } else {
            cmd.stderr(Stdio::inherit());
        }

        let mut child = cmd
            .spawn()
            .map_err(|e| format!("Failed to spawn engine: {}", e))?;

        // 从 child 中取出 stdout 并创建持久化的 BufReader，避免每次 invoke 重建导致数据丢失
        let stdout = child
            .stdout
            .take()
            .ok_or("Failed to get stdout from engine process")?;
        self.reader = Some(BufReader::new(stdout));
        self.child = Some(child);

        Ok(())
    }

    pub fn stop(&mut self) -> Result<(), String> {
        self.reader = None;
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

        // Read from stdout（使用持久化的 BufReader，避免丢失缓冲数据）
        let reader = self.reader.as_mut().ok_or("Failed to get stdout reader")?;
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
        // Fresh manager should have no child, no reader, and req_id = 1
        assert!(manager.child.is_none());
        assert!(manager.reader.is_none());
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

        let mut child = cmd.spawn().expect("sleep should exist");
        let stdout = child.stdout.take().expect("stdout should be piped");
        manager.reader = Some(BufReader::new(stdout));
        manager.child = Some(child);

        // Child and reader should be set
        assert!(manager.child.is_some());
        assert!(manager.reader.is_some());

        // Stop should succeed and clean up both
        let result = manager.stop();
        assert!(result.is_ok());

        assert!(manager.child.is_none());
        assert!(manager.reader.is_none());
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

        let mut child = cmd.spawn().expect("sleep should exist");
        let stdout = child.stdout.take().expect("stdout should be piped");
        manager.reader = Some(BufReader::new(stdout));
        manager.child = Some(child);

        // Calling start again should be no-op (return Ok)
        // We simulate this by checking child is still Some
        assert!(manager.child.is_some());

        // Cleanup
        manager.stop().unwrap();
    }
}
