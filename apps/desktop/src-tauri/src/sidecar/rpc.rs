//! JSON-RPC 客户端
//!
//! 提供与 Sidecar 通信的 JSON-RPC 2.0 客户端。
//!
//! @author Ysf
//! @date 2025-12-28

use serde::{Deserialize, Serialize};
use serde_json::Value;

/// JSON-RPC 请求
#[derive(Serialize, Debug)]
pub struct JsonRpcRequest {
    pub jsonrpc: String,
    pub id: u64,
    pub method: String,
    pub params: Value,
}

impl JsonRpcRequest {
    pub fn new(id: u64, method: &str, params: Value) -> Self {
        Self {
            jsonrpc: "2.0".to_string(),
            id,
            method: method.to_string(),
            params,
        }
    }
}

/// JSON-RPC 响应
#[derive(Deserialize, Debug)]
pub struct JsonRpcResponse {
    pub jsonrpc: String,
    pub id: Option<u64>,
    pub result: Option<Value>,
    pub error: Option<JsonRpcError>,
}

/// JSON-RPC 错误
#[derive(Deserialize, Debug)]
pub struct JsonRpcError {
    pub code: i32,
    pub message: String,
    pub data: Option<Value>,
}

impl JsonRpcResponse {
    /// 检查是否成功
    pub fn is_success(&self) -> bool {
        self.error.is_none()
    }

    /// 获取结果
    pub fn get_result(&self) -> Option<&Value> {
        self.result.as_ref()
    }

    /// 获取错误信息
    pub fn get_error_message(&self) -> Option<String> {
        self.error.as_ref().map(|e| e.message.clone())
    }
}

/// Graph 执行请求
#[derive(Serialize, Debug)]
pub struct ExecuteGraphRequest {
    pub graph_name: String,
    pub inputs: Value,
    pub user_id: String,
}

/// Graph 执行响应
#[derive(Deserialize, Debug)]
pub struct ExecuteGraphResponse {
    pub success: bool,
    pub data: Option<Value>,
    pub error: Option<String>,
}

/// 登录请求
#[derive(Serialize, Debug)]
pub struct LoginRequest {
    pub api_base_url: String,
    pub auth_token: String,
}

/// 登录响应
#[derive(Deserialize, Debug)]
pub struct LoginResponse {
    pub success: bool,
    pub user_id: Option<String>,
    pub error: Option<String>,
}

/// 模型列表响应
#[derive(Deserialize, Debug)]
pub struct ModelsResponse {
    pub models: Vec<ModelInfo>,
}

/// 模型信息
#[derive(Deserialize, Debug)]
pub struct ModelInfo {
    pub id: String,
    pub name: String,
    pub provider: String,
}
