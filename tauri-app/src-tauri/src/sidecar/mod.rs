//! Sidecar 进程管理模块
//!
//! 提供 Python Sidecar 进程的启动、通信和管理功能。
//!
//! @author Ysf
//! @date 2025-12-28

pub mod rpc;

use std::io::{BufRead, BufReader, Write};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::{Arc, Mutex};
use serde_json::Value;

/// Sidecar 管理器
pub struct SidecarManager {
    process: Option<Child>,
    stdin: Option<ChildStdin>,
    stdout: Option<Arc<Mutex<BufReader<ChildStdout>>>>,
    request_id: u64,
}

impl SidecarManager {
    /// 创建新的 Sidecar 管理器
    pub fn new() -> Self {
        Self {
            process: None,
            stdin: None,
            stdout: None,
            request_id: 0,
        }
    }

    /// 启动 Sidecar 进程
    pub fn spawn(&mut self, sidecar_path: &str) -> Result<(), String> {
        if self.process.is_some() {
            return Err("Sidecar 已经在运行".to_string());
        }

        let mut child = Command::new("python")
            .arg("-m")
            .arg("sidecar.main")
            .current_dir(sidecar_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .map_err(|e| format!("启动 Sidecar 失败: {}", e))?;

        self.stdin = child.stdin.take();
        self.stdout = child.stdout.take().map(|s| Arc::new(Mutex::new(BufReader::new(s))));
        self.process = Some(child);

        Ok(())
    }

    /// 发送 JSON-RPC 请求
    pub fn call(&mut self, method: &str, params: Value) -> Result<Value, String> {
        let stdin = self.stdin.as_mut().ok_or("Sidecar 未启动")?;
        let stdout = self.stdout.as_ref().ok_or("Sidecar 未启动")?;

        self.request_id += 1;
        let request = serde_json::json!({
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params,
        });

        // 发送请求
        let request_str = serde_json::to_string(&request)
            .map_err(|e| format!("序列化请求失败: {}", e))?;

        writeln!(stdin, "{}", request_str)
            .map_err(|e| format!("发送请求失败: {}", e))?;
        stdin.flush()
            .map_err(|e| format!("刷新缓冲区失败: {}", e))?;

        // 读取响应
        let mut stdout_guard = stdout.lock()
            .map_err(|e| format!("获取 stdout 锁失败: {}", e))?;

        let mut response_line = String::new();
        stdout_guard.read_line(&mut response_line)
            .map_err(|e| format!("读取响应失败: {}", e))?;

        let response: Value = serde_json::from_str(&response_line)
            .map_err(|e| format!("解析响应失败: {}", e))?;

        // 检查错误
        if let Some(error) = response.get("error") {
            return Err(format!("RPC 错误: {}", error));
        }

        Ok(response.get("result").cloned().unwrap_or(Value::Null))
    }

    /// 关闭 Sidecar 进程
    pub fn shutdown(&mut self) -> Result<(), String> {
        if let Some(mut process) = self.process.take() {
            // 尝试优雅关闭
            if let Err(_) = self.call("shutdown", Value::Null) {
                // 如果优雅关闭失败，强制终止
                let _ = process.kill();
            }
            let _ = process.wait();
        }

        self.stdin = None;
        self.stdout = None;

        Ok(())
    }

    /// 检查 Sidecar 是否运行中
    pub fn is_running(&mut self) -> bool {
        if let Some(ref mut process) = self.process {
            match process.try_wait() {
                Ok(Some(_)) => {
                    // 进程已退出
                    self.process = None;
                    self.stdin = None;
                    self.stdout = None;
                    false
                }
                Ok(None) => true,
                Err(_) => false,
            }
        } else {
            false
        }
    }

    /// 健康检查
    pub fn health_check(&mut self) -> Result<bool, String> {
        let result = self.call("health_check", Value::Null)?;
        Ok(result.get("status").and_then(|s| s.as_str()) == Some("ok"))
    }
}

impl Drop for SidecarManager {
    fn drop(&mut self) {
        let _ = self.shutdown();
    }
}

impl Default for SidecarManager {
    fn default() -> Self {
        Self::new()
    }
}
